from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CounselorProfile
from .serializers import CounselorProfileSerializer
from rest_framework.parsers import MultiPartParser, FormParser

class CounselorProfileView(APIView):
    permission_classes = [IsAuthenticated]
    # parser_classes = [MultiPartParser, FormParser]

    def get(self, request):

        try:
            profile = CounselorProfile.objects.get(user=request.user)
        except CounselorProfile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=404)

        serializer = CounselorProfileSerializer(profile)
        return Response(serializer.data)

    def patch(self, request):

        try:

            profile = CounselorProfile.objects.get(user=request.user)

        except CounselorProfile.DoesNotExist:
            return Response({"detail": "Profile not found."}, status=404)

        serializer = CounselorProfileSerializer(
            profile, data=request.data, partial=True
        )

        if serializer.is_valid():
            serializer.save()

            return Response(serializer.data)
        return Response(serializer.errors, status=400)
