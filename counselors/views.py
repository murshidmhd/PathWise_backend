from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CounselorProfile
from .serializers import CounselorProfileSerializer


class CounselorProfileMeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = CounselorProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({"error": "Counselor profile not found"}, status=404)
        serializer = CounselorProfileSerializer(profile)
        return Response(serializer.data, status=200)

    def patch(self, request):
        profile = CounselorProfile.objects.filter(user=request.user).first()
        if not profile:
            return Response({"error": "Counselor profile not found"}, status=404)
        serializer = CounselorProfileSerializer(
            profile, data=request.data, partial=True
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=200)
        return Response(serializer.errors, status=400)
