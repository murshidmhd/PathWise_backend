from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StudentProfile
from .serializers import StudentProfileSerializer


class StudentProfileMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = StudentProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({"error": "Student profile not found"}, status=404)
        serializer = StudentProfileSerializer(profile)
        return Response(serializer.data, status=200)

    def patch(self, request):
        profile = StudentProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({"error": "Student profile not found"}, status=404)
        serializer = StudentProfileSerializer(
            profile, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)
