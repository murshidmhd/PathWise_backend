import json
import google.generativeai as genai
from django.conf import settings
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from assessments.models import AssessmentReport
from students.models import StudentProfile
from .models import CareerRoadmap, RoadmapMilestone


class RoadmapServiceError(Exception):
    def __init__(self, detail, status_code=400):
        normalized_detail = {"message": detail} if isinstance(detail, str) else detail
        super().__init__(normalized_detail)
        self.detail = normalized_detail
        self.status_code = status_code


def _get_student_profile(user):
    try:
        return StudentProfile.objects.get(user=user)
    except StudentProfile.DoesNotExist as exc:
        raise RoadmapServiceError(
            "Student profile not found.", status_code=404
        ) from exc


def _generate_roadmap_from_gemini(
    career_title, personality_type, interest_areas, strengths
):
    genai.configure(api_key=settings.GEMINI_API_KEY)
    model = genai.GenerativeModel("gemini-2.5-flash-lite")

    prompt = f"""
    You are a career counselor for Indian students aged 15-25.
    Create a career roadmap for a student who wants to become a {career_title}.

    Student profile:
    - Personality type: {personality_type}
    - Interest areas: {", ".join(interest_areas)}
    - Strengths: {", ".join(strengths)}

    Return ONLY a JSON object with this exact structure, no extra text:
    {{
        "title": "Your {career_title} Journey",
        "milestones": [
            {{
                "order_number": 1,
                "title": "Milestone title",
                "description": "What to do in this milestone",
                "age_range": "15-17",
                "duration": "6 months",
                "skills_to_learn": ["skill1", "skill2"],
                "exams_to_take": ["exam1"],
                "resources": [
                    {{"title": "Resource name", "url": "https://example.com", "type": "course"}}
                ],
                "node_position": {{"x": 100, "y": 0}}
            }}
        ]
    }}

    Create 5 milestones total. Each milestone should have increasing x position by 250.
    Make it specific for Indian students — include Indian exams, colleges, and resources.
    """

    response = model.generate_content(prompt)
    clean = response.text.replace("```json", "").replace("```", "").strip()
    return json.loads(clean)


def generate_roadmap(user, assessment_id, custom_career_title=None):
    student = _get_student_profile(user)

    CareerRoadmap.objects.filter(student=student, assessment_id=assessment_id).update(
        status="archived"   
    )

    # check if roadmap already exists
    existing = CareerRoadmap.objects.filter(
        student=student,
        assessment_id=assessment_id,
        status="active",
    ).first()

    if existing:
        return existing

    # get assessment report
    try:
        report = AssessmentReport.objects.get(
            assessment_id=assessment_id, student=student
        )
    except AssessmentReport.DoesNotExist as exc:
        raise RoadmapServiceError(
            "Assessment report not found.", status_code=404
        ) from exc

    # get top career
    # Use custom title if provided, otherwise fallback to assessment
    career_title = custom_career_title or (
        report.recommended_careers[0] if report.recommended_careers else None
    )

    if not career_title:
        raise RoadmapServiceError(
            "Please provide a career title or complete your assessment."
        )

    # generate from gemini
    roadmap_data = _generate_roadmap_from_gemini(
        career_title=career_title,
        personality_type=report.personality_type or "",
        interest_areas=report.interest_areas or [],
        strengths=report.strengths or [],
    )

    # save roadmap
    roadmap = CareerRoadmap.objects.create(
        student=student,
        assessment_id=assessment_id,
        career_title=career_title,
        title=roadmap_data.get("title"),
        status="active",
    )

    # save milestones
    milestones = []
    for m in roadmap_data.get("milestones", []):
        milestones.append(
            RoadmapMilestone(
                roadmap=roadmap,
                title=m.get("title"),
                description=m.get("description"),
                age_range=m.get("age_range"),
                duration=m.get("duration"),
                skills_to_learn=m.get("skills_to_learn", []),
                exams_to_take=m.get("exams_to_take", []),
                resources=m.get("resources", []),
                node_position=m.get("node_position"),
                order_number=m.get("order_number"),
            )
        )
    RoadmapMilestone.objects.bulk_create(milestones)

    # --- SEND NOTIFICATION ---
    try:
        # 1. Broadcaster (WebSocket)
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"user_{user.id}",
            {
                "type": "notify",
                "notification": {
                    "title": "Roadmap Ready! 🚀",
                    "message": f"Your career roadmap for {career_title} is now available.",
                    "type": "ROADMAP_GENERATED",
                    "data": {"roadmap_id": str(roadmap.id)}
                }
            }
        )
    except Exception as e:
        # We don't want to fail the roadmap creation if notification fails
        print(f"Error sending roadmap notification: {e}")

    return roadmap


def get_roadmap(user, assessment_id):
    student = _get_student_profile(user)

    try:
        return CareerRoadmap.objects.prefetch_related("milestones").get(
            student=student,
            assessment_id=assessment_id,
            status="active",
        )
    except CareerRoadmap.DoesNotExist as exc:
        raise RoadmapServiceError("Roadmap not found.", status_code=404) from exc
