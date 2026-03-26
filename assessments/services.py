from collections import Counter

from django.db import transaction
from django.utils import timezone

from students.models import StudentProfile

from .models import Assessment, AssessmentAnswer, AssessmentReport, Question


RIASEC_LABELS = {
    "R": "Realistic",
    "I": "Investigative",
    "A": "Artistic",
    "S": "Social",
    "E": "Enterprising",
    "C": "Conventional",
}

CAREER_SUGGESTIONS = {
    "R": ["Mechanical Engineer", "Civil Engineer", "Architecture"],
    "I": ["Data Scientist", "Doctor", "Research Analyst"],
    "A": ["Graphic Designer", "Writer", "Animator"],
    "S": ["Teacher", "Psychologist", "Counselor"],
    "E": ["Entrepreneur", "Marketing Manager", "Sales Lead"],
    "C": ["Accountant", "Banking Professional", "Operations Analyst"],
}

STRENGTH_MAP = {
    "R": "practical problem solving",
    "I": "analytical thinking",
    "A": "creative expression",
    "S": "helping and collaboration",
    "E": "leadership and communication",
    "C": "organization and structure",
}

WEAKNESS_MAP = {
    "R": "abstract-only work",
    "I": "fast social situations",
    "A": "very repetitive tasks",
    "S": "high-pressure competition",
    "E": "routine-heavy workflows",
    "C": "unclear or chaotic environments",
}
import google.generativeai as genai
from backend import settings
from backend.settings import GEMINI_API_KEY


class ServiceError(Exception):
    def __init__(self, detail, status_code=400):
        normalized_detail = {"message": detail} if isinstance(detail, str) else detail
        super().__init__(normalized_detail)
        self.detail = normalized_detail
        self.status_code = status_code


def _get_student_profile(user):
    try:
        return StudentProfile.objects.get(user=user)
    except StudentProfile.DoesNotExist as exc:
        raise ServiceError("Student profile not found.", status_code=404) from exc


import google.generativeai as genai
from django.conf import settings


def _generate_report_text(
    personality_type, interest_areas, recommended_careers, strengths, weaknesses
):
    try:
        print(GEMINI_API_KEY)
        genai.configure(api_key=GEMINI_API_KEY)
        # model = genai.GenerativeModel("gemini-3.1-flash-lite-preview")
        model = genai.GenerativeModel("gemini-2.5-flash-lite")

        prompt = f"""
        You are a career counselor for Indian students aged 15-25.
        Write a short, encouraging career guidance report (3-4 sentences) based on:
        - Personality type: {personality_type}
        - Top interests: {', '.join(interest_areas)}
        - Recommended careers: {', '.join(recommended_careers)}
        - Strengths: {', '.join(strengths)}
        - Weaknesses: {', '.join(weaknesses)}
        Write in simple English. Be positive and motivating.
        """

        response = model.generate_content(prompt)
        print("this is the response text", response.text)
        return response.text

    except Exception as e:
        print("GEMINI ERROR:", e)  # ← add this
        return (
            f"Your strongest personality trend is {personality_type}. "
            f"Top interests: {', '.join(interest_areas) if interest_areas else 'Not enough data'}."
        )


def _build_report_data(personality_counts, interest_counts):
    if not personality_counts:
        return {
            "personality_type": None,
            "interest_areas": [],
            "recommended_careers": [],
            "strengths": [],
            "weaknesses": [],
            "report_text": "Assessment completed successfully.",
        }

    top_personality_codes = [code for code, _count in personality_counts.most_common(3)]
    personality_labels = [RIASEC_LABELS[code] for code in top_personality_codes]
    primary_code = top_personality_codes[0]

    recommended_careers = []
    for code in top_personality_codes:
        recommended_careers.extend(CAREER_SUGGESTIONS.get(code, []))

    interest_areas = (
        [area for area, _count in interest_counts.most_common(3)]
        if interest_counts
        else []
    )

    return {
        "personality_type": RIASEC_LABELS[primary_code],
        "interest_areas": interest_areas,
        "recommended_careers": recommended_careers[:6],
        "strengths": [STRENGTH_MAP[code] for code in top_personality_codes],
        "weaknesses": [WEAKNESS_MAP[code] for code in top_personality_codes],
        "report_text": _generate_report_text(
            RIASEC_LABELS[primary_code],
            interest_areas,
            recommended_careers[:6],
            [STRENGTH_MAP[code] for code in top_personality_codes],
            [WEAKNESS_MAP[code] for code in top_personality_codes],
        ),
    }


from django.conf import settings


def list_questions():
    count = settings.ASSESSMENT_QUESTIONS_PER_SECTION
    aptitude = Question.objects.filter(section="aptitude").order_by("?")[:count]
    personality = Question.objects.filter(section="personality").order_by("?")[:count]
    interest = Question.objects.filter(section="interest").order_by("?")[:count]
    return list(aptitude) + list(personality) + list(interest)


def start_assessment(user):
    student = _get_student_profile(user)
    existing = Assessment.objects.filter(student=student).first()

    if existing and existing.status == "started":
        return existing, False

    if existing and existing.status == "completed":
        raise ServiceError(
            {
                "message": "Assessment already completed.",
                "assessment_id": existing.id,
                "status": existing.status,
            },
            status_code=409,
        )

    assessment = Assessment.objects.create(
        student=student,
        status="started",
        attempt_number=1,
    )
    return assessment, True


@transaction.atomic
def submit_assessment(user, assessment_id, answers, time_taken=None):
    student = _get_student_profile(user)

    # select_for_update
    # this is raw level lock it prevent the double submission
    try:
        assessment = Assessment.objects.select_for_update().get(
            id=assessment_id,
            student=student,
        )
    except Assessment.DoesNotExist as exc:
        raise ServiceError("Assessment not found.", status_code=404) from exc

    if assessment.status == "completed":
        raise ServiceError("Assessment already completed.")

    if not answers:
        raise ServiceError("At least one answer is required.")

    question_ids = [answer["question_id"] for answer in answers]
    if len(question_ids) != len(set(question_ids)):
        raise ServiceError("Duplicate question answers are not allowed.")

    required_question_ids = list(Question.objects.values_list("id", flat=True))
    missing_required_question_ids = [
        question_id
        for question_id in required_question_ids
        if question_id not in set(question_ids)
    ]
    # if missing_required_question_ids:
    #     raise ServiceError(
    #         {
    #             "message": "All assessment questions must be answered before submission.",
    #             "question_ids": missing_required_question_ids,
    #         }
    #     )

    questions = Question.objects.in_bulk(question_ids)
    missing_question_ids = [
        question_id for question_id in question_ids if question_id not in questions
    ]
    if missing_question_ids:
        raise ServiceError(
            {
                "message": "Some questions were not found.",
                "question_ids": missing_question_ids,
            }
        )

    aptitude_score = 0
    personality_counts = Counter()
    interest_counts = Counter()

    for answer in answers:
        question = questions[answer["question_id"]]
        selected_answer = answer["selected_answer"]
        is_correct = None

        if question.section == "aptitude":
            is_correct = selected_answer == question.correct_answer
            if is_correct:
                aptitude_score += question.marks

        elif question.section == "personality":
            riasec_type = getattr(question, f"option_{selected_answer}_type", None)
            if riasec_type:
                personality_counts[riasec_type] += 1

        elif question.section == "interest":
            interest_area = question.sub_section
            if interest_area:
                interest_counts[interest_area] += 1

        AssessmentAnswer.objects.update_or_create(
            assessment=assessment,
            question=question,
            defaults={
                "selected_answer": selected_answer,
                "is_correct": is_correct,
            },
        )

    report_data = _build_report_data(personality_counts, interest_counts)

    print(report_data)

    assessment.aptitude_score = aptitude_score
    assessment.personality_score = sum(personality_counts.values())
    assessment.interest_score = sum(interest_counts.values())
    assessment.total_score = aptitude_score
    assessment.time_taken = time_taken
    assessment.status = "completed"
    assessment.completed_at = timezone.now()
    assessment.save()

    AssessmentReport.objects.update_or_create(
        assessment=assessment,
        defaults={
            "student": student,
            **report_data,
        },
    )

    student.assessment_taken = True
    student.save(update_fields=["assessment_taken"])

    return assessment


def get_latest_assessment(user):
    student = _get_student_profile(user)
    assessment = Assessment.objects.filter(student=student).first()
    if not assessment:
        raise ServiceError("No assessment found.", status_code=404)
    return assessment


def get_assessment_report(user, assessment_id):
    student = _get_student_profile(user)

    try:
        assessment = Assessment.objects.get(id=assessment_id, student=student)
    except Assessment.DoesNotExist as exc:
        raise ServiceError("Assessment not found.", status_code=404) from exc

    if assessment.status != "completed":
        raise ServiceError("Assessment report is only available after completion.")

    try:
        return assessment.report
    except AssessmentReport.DoesNotExist as exc:
        raise ServiceError("Assessment report not found.", status_code=404) from exc
