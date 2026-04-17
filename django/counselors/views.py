from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import CounselorProfile, CounselorReview, CounselorRequest
from .permissions import IsCounselorUserRole, IsStudentUserRole
from students.models import StudentProfile
from .serializers import (
    CounselorProfileSerializer,
    CounselorReviewSerializer,
    CounselorStudentDetailSerializer,
    CounselorStudentListSerializer,
    AvailableCounselorSerializer,
    CounselorRequestSerializer,
)


class CounselorReviewView(APIView):
    permission_classes = [IsAuthenticated, IsStudentUserRole]

    def post(self, request, counselor_id):
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        counselor_profile = get_object_or_404(CounselorProfile, id=counselor_id)

        # check if student is assigned to this counselor
        if student_profile.assigned_counselor != counselor_profile:
            return Response(
                {"detail": "You can only rate your assigned counselor."}, status=403
            )

        data = request.data.copy()
        data["counselor"] = counselor_profile.id
        data["student"] = student_profile.id

        serializer = CounselorReviewSerializer(data=data)
        if serializer.is_valid():
            serializer.save(student=student_profile, counselor=counselor_profile)

            # Recalculate counselor average rating
            reviews = CounselorReview.objects.filter(counselor=counselor_profile)
            avg_rating = sum([r.rating for r in reviews]) / len(reviews)
            counselor_profile.rating = avg_rating
            counselor_profile.save(update_fields=["rating"])

            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class CounselorReviewListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, counselor_id):
        reviews = CounselorReview.objects.filter(counselor_id=counselor_id).order_by(
            "-created_at"
        )
        serializer = CounselorReviewSerializer(reviews, many=True)
        return Response(serializer.data)


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


class AvailableCounselorListView(ListAPIView):
    permission_classes = [IsAuthenticated, IsStudentUserRole]
    serializer_class = AvailableCounselorSerializer

    def get_queryset(self):
        return CounselorProfile.objects.filter(
            approval_status="approved", is_available=True
        ).order_by("-rating")


# you want to check this area 

class CounselorRequestView(APIView):
    permission_classes = [IsAuthenticated, IsStudentUserRole]

    def post(self, request):
        student_profile = get_object_or_404(StudentProfile, user=request.user)

        # Check if student already has a pending request
        if CounselorRequest.objects.filter(
            student=student_profile, status="pending"
        ).exists():
            return Response(
                {"detail": "You already have a pending counselor request."}, status=400
            )

        serializer = CounselorRequestSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(student=student_profile)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)

    def get(self, request):
        student_profile = get_object_or_404(StudentProfile, user=request.user)
        requests = CounselorRequest.objects.filter(student=student_profile).order_by(
            "-created_at"
        )
        serializer = CounselorRequestSerializer(requests, many=True)
        return Response(serializer.data)
