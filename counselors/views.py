from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CounselorProfile
from .permissions import IsCounselorUserRole
from .serializers import (
    CounselorProfileSerializer,
    CounselorStudentDetailSerializer,
    CounselorStudentListSerializer,
)
from students.models import StudentProfile


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


class CounselorAssignedStudentListView(APIView):
    permission_classes = [IsCounselorUserRole]

    def get(self, request):
        try:
            counselor_profile = CounselorProfile.objects.get(user=request.user)
        except CounselorProfile.DoesNotExist:
            return Response({"detail": "Counselor profile not found."}, status=404)

        students = (
            StudentProfile.objects.select_related(
                "user",
                "assigned_counselor",
                "assigned_counselor__user",
            )
            .filter(assigned_counselor=counselor_profile)
            .order_by("-created_at")
        )

        serializer = CounselorStudentListSerializer(students, many=True)
        return Response(serializer.data)


class CounselorAssignedStudentDetailView(APIView):
    permission_classes = [IsCounselorUserRole]

    def get(self, request, student_id):
        try:
            counselor_profile = CounselorProfile.objects.get(user=request.user)
        except CounselorProfile.DoesNotExist:
            return Response({"detail": "Counselor profile not found."}, status=404)

        try:
            student = StudentProfile.objects.select_related(
                "user",
                "assigned_counselor",
                "assigned_counselor__user",
            ).get(id=student_id, assigned_counselor=counselor_profile)
        except StudentProfile.DoesNotExist:
            return Response(
                {"detail": "Student not found or not assigned to you."}, status=404
            )

        serializer = CounselorStudentDetailSerializer(student)
        return Response(serializer.data)
