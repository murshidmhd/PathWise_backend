from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import StudentProfile
from .serializers import StudentProfileSerializer


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated


class StudentProfileView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        print("hey" , request.user)
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
            serializer.save()

            return Response(serializer.data)
        return Response(serializer.errors, status=400)
