from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StudentProfile
from .serializers import StudentProfileSerializer


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
        try:
            profile = StudentProfile.objects.get(user=request.user)

        except StudentProfile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=404)

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
