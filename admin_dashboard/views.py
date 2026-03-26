from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView

from counselors.models import CounselorProfile
from students.models import StudentProfile

from .permissions import IsAdminUserRole
from .serializers import (
    AdminAssignCounselorSerializer,
    AdminCounselorListSerializer,
    AdminStudentListSerializer,
)


class AdminUserListView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        students = StudentProfile.objects.select_related("user").order_by("-created_at")
        counselors = CounselorProfile.objects.select_related("user").order_by(
            "-created_at"
        )

        return Response(
            {
                "students": AdminStudentListSerializer(students, many=True).data,
                "counselors": AdminCounselorListSerializer(counselors, many=True).data,
            }
        )


class PendingCounselorApprovalListView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        pending_counselors = (
            CounselorProfile.objects.select_related("user")
            .filter(approval_status="pending")
            .order_by("-created_at")
        )

        return Response(
            {
                "pending_counselors": AdminCounselorListSerializer(
                    pending_counselors, many=True
                ).data
            }
        )


# views.py

from rest_framework.generics import ListAPIView
from django.db.models import Q
from accounts.models import User
from .serializers import AdminApprovalSerializer
from .permissions import IsAdminUserRole


# views.py

from rest_framework.generics import ListAPIView
from counselors.models import CounselorProfile
from .serializers import AdminApprovalSerializer
from .permissions import IsAdminUserRole


class AdminApprovalListView(ListAPIView):
    serializer_class = AdminApprovalSerializer
    permission_classes = [IsAdminUserRole]

    def get_queryset(self):
        return (
            CounselorProfile.objects.filter(approval_status="pending")
            .select_related("user")
            .order_by("-id")
        )


# views.py

from rest_framework.response import Response
from rest_framework import status

from counselors.models import CounselorProfile
from .permissions import IsAdminUserRole
from .services import ApprovalService
from .serializers import RejectSerializer
 

class ApproveCounselorView(APIView):
    permission_classes = [IsAdminUserRole]

    def post(self, request, pk):
        profile = get_object_or_404(CounselorProfile, pk=pk)

        try:
            ApprovalService.approve(profile)
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        return Response({"message": "Counselor approved successfully"})


class RejectCounselorView(APIView):
    permission_classes = [IsAdminUserRole]

    def post(self, request, pk):
        profile = get_object_or_404(CounselorProfile, pk=pk)

        serializer = RejectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            ApprovalService.reject(profile, serializer.validated_data["reason"])
        except ValueError as e:
            return Response({"error": str(e)}, status=400)

        return Response({"message": "Counselor rejected successfully"})


class AdminAssignCounselorView(APIView):
    permission_classes = [IsAdminUserRole]

    def patch(self, request, student_id):
        student = get_object_or_404(
            StudentProfile.objects.select_related(
                "user",
                "assigned_counselor",
                "assigned_counselor__user",
            ),
            pk=student_id,
        )

        serializer = AdminAssignCounselorSerializer(
            student,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        student.refresh_from_db()

        return Response(
            AdminAssignCounselorSerializer(student).data,
            status=status.HTTP_200_OK,
        )
