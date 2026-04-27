from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StudentProfile, UserSkill, SkillRecommendation
from .serializers import StudentProfileSerializer, UserSkillSerializer, SkillRecommendationSerializer
from roadmap.models import CareerRoadmap


def calculate_profile_completion(profile):
    fields = [
        profile.full_name,
        profile.date_of_birth,
        profile.gender,
        profile.phone,
        profile.city,
        profile.state,
        profile.education_level,
        profile.stream,
    ]
    # We skip profile_photo so it doesn't penalize students if they don't upload one
    filled = sum(1 for f in fields if f)
    return int((filled / len(fields)) * 100)



class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        print("hey", request.user)
        profile = StudentProfile.objects.get_or_create(user=request.user)[0]

        serializer = StudentProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):

        try:
            profile = StudentProfile.objects.get(user=request.user)

        except StudentProfile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=404)

        serializer = StudentProfileSerializer(profile, data=request.data, partial=True)

        if serializer.is_valid():
            profile = serializer.save()
            profile.profile_completed = calculate_profile_completion(profile)
            profile.save(update_fields=["profile_completed", "updated_at"])

            return Response(serializer.data)
        return Response(serializer.errors, status=400)


class StudentProfileTrackingView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            profile = StudentProfile.objects.get(user=request.user)
        except StudentProfile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=404)

        current = calculate_profile_completion(profile)
        if profile.profile_completed != current:
            profile.profile_completed = current
            profile.save(update_fields=["profile_completed", "updated_at"])

        return Response(
            {
                "is_onboarded": profile.is_onboarded,
                "assessment_taken": profile.assessment_taken,
                "roadmap_created": profile.roadmap_created,
                "profile_completed": profile.profile_completed,
            }
        )


class SkillAnalysisView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # 1. Get User Skills
        skills = UserSkill.objects.filter(user=user)
        skills_data = UserSkillSerializer(skills, many=True).data

        # 2. Get Recommendations
        recommendations = SkillRecommendation.objects.filter(user=user)
        rec_data = SkillRecommendationSerializer(recommendations, many=True).data

        # 3. Gap Analysis (Based on Roadmap)
        roadmap = CareerRoadmap.objects.filter(student__user=user, status="active").first()
        gap_analysis = {"required_skill": "None", "match_rate": 100}

        if roadmap:
            # Simple logic: find first non-completed milestone skills
            milestone = roadmap.milestones.filter(is_completed=False).first()
            if milestone and milestone.skills_to_learn:
                # Find a skill the user doesn't have yet or has low level
                user_skill_names = [s.name.lower() for s in skills]
                for skill_needed in milestone.skills_to_learn:
                    if skill_needed.lower() not in user_skill_names:
                        gap_analysis = {
                            "required_skill": skill_needed,
                            "match_rate": 85,  # Placeholder for complex logic
                        }
                        break

        return Response(
            {
                "skills": skills_data,
                "recommendations": rec_data,
                "gap_analysis": gap_analysis,
            }
        )
