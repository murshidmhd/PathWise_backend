from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from counselors.models import CounselorProfile, CounselorRequest
from students.models import StudentProfile

from .permissions import IsAdminUserRole
from .serializers import (
    AdminAssignCounselorSerializer,
    AdminCounselorListSerializer,
    AdminStudentListSerializer,
    AdminCounselorRequestSerializer,
    AdminApprovalSerializer,
    RejectSerializer,
)
from .services import ApprovalService


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


class AdminApprovalListView(ListAPIView):
    serializer_class = AdminApprovalSerializer
    permission_classes = [IsAdminUserRole]

    def get_queryset(self):
        return (
            CounselorProfile.objects.filter(approval_status="pending")
            .select_related("user")
            .order_by("-id")
        )


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

        # SEND NOTIFICATION TO STUDENT
        if student.assigned_counselor:
            from notifications.utils import send_notification
            
            # Notify Student
            send_notification(
                user_id=student.user.id,
                title="Counselor Assigned! 🎓",
                message=f"Admin has assigned {student.assigned_counselor.full_name} as your mentor. You can now start chatting!",
                notification_type="mentor_assignment",
                data={"counselor_id": student.assigned_counselor.id}
            )

            # Notify Counselor
            send_notification(
                user_id=student.assigned_counselor.user.id,
                title="New Student Assigned! 👤",
                message=f"Admin has assigned a new student, {student.full_name}, to you. Check your student list to get started.",
                notification_type="student_assignment",
                data={"student_id": student.id}
            )

        return Response(
            AdminAssignCounselorSerializer(student).data,
            status=status.HTTP_200_OK,
        )


class AdminCounselorRequestListView(APIView):
    permission_classes = [IsAdminUserRole]

    def get(self, request):
        status_filter = request.query_params.get("status", "pending")
        requests = (
            CounselorRequest.objects.select_related(
                "student", "counselor", "student__user", "counselor__user"
            )
            .filter(status=status_filter)
            .order_by("-created_at")
        )

        serializer = AdminCounselorRequestSerializer(requests, many=True)
        return Response(serializer.data)


class AdminCounselorRequestActionView(APIView):
    permission_classes = [IsAdminUserRole]

    def post(self, request, pk):
        counselor_request = get_object_or_404(CounselorRequest, pk=pk)
        action = request.data.get("action")  # "approve" or "reject"

        if action == "approve":
            # Update student profile
            student = counselor_request.student
            student.assigned_counselor = counselor_request.counselor
            student.save()

            # Update request status
            counselor_request.status = "approved"
            counselor_request.save()

            # Reject other pending requests for this student
            CounselorRequest.objects.filter(student=student, status="pending").exclude(
                pk=pk
            ).update(status="rejected")

            # SEND NOTIFICATION
            from notifications.utils import send_notification
            send_notification(
                user_id=student.user.id,
                title="Counselor Request Accepted! 🎉",
                message=f"Good news! Your request for counselor {counselor_request.counselor.full_name} has been approved. You can now start chatting.",
                notification_type="mentor_request",
                data={"counselor_id": counselor_request.counselor.id}
            )

            return Response({"message": "Request approved and counselor assigned."})

        elif action == "reject":
            counselor_request.status = "rejected"
            counselor_request.save()
            return Response({"message": "Request rejected."})

        return Response({"error": "Invalid action."}, status=400)
