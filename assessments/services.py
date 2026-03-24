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

CAREER_RECOMMENDATIONS = {
    "R": ["Mechanical Engineer", "Architect", "Technician"],
    "I": ["Data Analyst", "Scientist", "Researcher"],
    "A": ["Graphic Designer", "Writer", "Content Creator"],
    "S": ["Teacher", "Psychologist", "Counselor"],
    "E": ["Entrepreneur", "Sales Manager", "Business Development Executive"],
    "C": ["Accountant", "Banking Professional", "Operations Executive"],
}

STRENGTH_MAP = {
    "R": "practical problem solving",
    "I": "analytical thinking",
    "A": "creative expression",
    "S": "helping and collaboration",
    "E": "leadership and persuasion",
    "C": "organization and accuracy",
}

WEAKNESS_MAP = {
    "R": "abstract discussion",
    "I": "fast social decision-making",
    "A": "highly repetitive work",
    "S": "competitive pressure",
    "E": "routine-heavy tasks",
    "C": "ambiguous environments",
}


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


def _build_report_payload(type_counts):
    if not type_counts:
        return {
            "personality_type": None,
            "interest_areas": [],
            "recommended_careers": [],
            "strengths": [],
            "weaknesses": [],
            "report_text": "No assessment insights are available yet.",
        }

    ranked_types = [code for code, _ in type_counts.most_common(3)]
    primary_type = ranked_types[0]
    interest_areas = [RIASEC_LABELS[code] for code in ranked_types]
    recommended_careers = []
    for code in ranked_types:
        recommended_careers.extend(CAREER_RECOMMENDATIONS.get(code, []))

    return {
        "personality_type": RIASEC_LABELS[primary_type],
        "interest_areas": interest_areas,
        "recommended_careers": recommended_careers[:6],
        "strengths": [STRENGTH_MAP[code] for code in ranked_types],
        "weaknesses": [WEAKNESS_MAP[code] for code in ranked_types],
        "report_text": (
            f"Your strongest assessment trend is {RIASEC_LABELS[primary_type]}. "
            f"You also showed alignment with {', '.join(interest_areas[1:])}."
            if len(interest_areas) > 1
            else f"Your strongest assessment trend is {RIASEC_LABELS[primary_type]}."
        ),
    }


def list_questions():
    return Question.objects.all()


def start_assessment(user):
    student = _get_student_profile(user)

    existing_assessment = Assessment.objects.filter(
        student=student,
        status="started",
    ).first()
    if existing_assessment:
        return existing_assessment

    attempt_number = Assessment.objects.filter(student=student).count() + 1
    return Assessment.objects.create(
        student=student,
        status="started",
        attempt_number=attempt_number,
    )


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

    question_ids = [item["question_id"] for item in answers]
    if len(question_ids) != len(set(question_ids)):
        raise ServiceError("Duplicate question answers are not allowed.")

    questions = Question.objects.in_bulk(question_ids)
    # so basically the in_bulck is a method i used bucause it return a dictionary with the

    """{
        this is the output look so we take simple the the result 
     1: <Question object>,
     5: <Question object>,
     12: <Question object>,
     }"""

    missing_ids = [
        question_id for question_id in question_ids if question_id not in questions
    ]
    if missing_ids:
        raise ServiceError(
            {"message": "Some questions were not found.", "question_ids": missing_ids}
        )

    aptitude_score = 0
    personality_score = 0
    interest_score = 0
    type_counts = Counter()

    for item in answers:
        question = questions[item["question_id"]]
        selected_answer = item["selected_answer"]

        is_correct = None
        if question.section == "aptitude":
            is_correct = selected_answer == question.correct_answer
            if is_correct:
                aptitude_score += question.marks
        elif question.section == "personality":
            personality_score += 1
        elif question.section == "interest":
            interest_score += 1

        selected_type = getattr(question, f"option_{selected_answer}_type", None)
        if selected_type:
            type_counts[selected_type] += 1

        AssessmentAnswer.objects.update_or_create(
            assessment=assessment,
            question=question,
            defaults={
                "selected_answer": selected_answer,
                "is_correct": is_correct,
            },
        )

    total_score = aptitude_score + personality_score + interest_score
    assessment.status = "completed"
    assessment.aptitude_score = aptitude_score
    assessment.personality_score = personality_score
    assessment.interest_score = interest_score
    assessment.total_score = total_score
    assessment.time_taken = time_taken
    assessment.completed_at = timezone.now()
    assessment.save()

    report_payload = _build_report_payload(type_counts)
    AssessmentReport.objects.update_or_create(
        assessment=assessment,
        defaults={
            "student": student,
            **report_payload,
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

    try:
        return assessment.report
    except AssessmentReport.DoesNotExist as exc:
        raise ServiceError("Assessment report not found.", status_code=404) from exc
