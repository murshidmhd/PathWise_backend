from rest_framework import serializers

from counselors.models import CounselorProfile, CounselorRequest
from students.models import StudentProfile


class AdminStudentListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    is_verified = serializers.BooleanField(source="user.is_verified", read_only=True)
    created_at = serializers.DateTimeField(source="user.created_at", read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "full_name",
            "email",
            "role",
            "phone",
            "city",
            "state",
            "education_level",
            "stream",
            "assessment_taken",
            "roadmap_created",
            "profile_completed",
            "is_active",
            "is_verified",
            "created_at",
        ]


class AdminCounselorListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    role = serializers.CharField(source="user.role", read_only=True)
    is_active = serializers.BooleanField(source="user.is_active", read_only=True)
    is_verified = serializers.BooleanField(source="user.is_verified", read_only=True)
    created_at = serializers.DateTimeField(source="user.created_at", read_only=True)

    class Meta:
        model = CounselorProfile
        fields = [
            "id",
            "full_name",
            "email",
            "role",
            "phone",
            "city",
            "state",
            "experience_years",
            "qualification",
            "specialization",
            "approval_status",
            "rejection_reason",
            "rating",
            "is_available",
            "is_active",
            "is_verified",
            "created_at",
        ]


class AdminApprovalSerializer(serializers.ModelSerializer):
    email = serializers.CharField(source="user.email", read_only=True)
    document = serializers.FileField(source="certificate_url")

    class Meta:
        model = CounselorProfile
        fields = [
            "id",
            "full_name",
            "email",
            "approval_status",
            "document",
            "created_at",
        ]


class RejectSerializer(serializers.Serializer):
    reason = serializers.CharField(required=True)


class AssignedCounselorSummarySerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = CounselorProfile
        fields = [
            "id",
            "full_name",
            "email",
        ]


class AdminAssignCounselorSerializer(serializers.ModelSerializer):
    assigned_counselor = serializers.PrimaryKeyRelatedField(
        queryset=CounselorProfile.objects.select_related("user"),
        allow_null=True,
        required=True,
    )
    assigned_counselor_detail = AssignedCounselorSummarySerializer(
        source="assigned_counselor",
        read_only=True,
    )

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "full_name",
            "assigned_counselor",
            "assigned_counselor_detail",
        ]
        read_only_fields = ["id", "full_name", "assigned_counselor_detail"]

    def validate_assigned_counselor(self, counselor):
        if counselor is None:
            return counselor

        if counselor.user.role != "counselor":
            raise serializers.ValidationError("Selected user is not a counselor.")

        return counselor


class AdminCounselorRequestSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.full_name", read_only=True)
    counselor_name = serializers.CharField(source="counselor.full_name", read_only=True)
    student_email = serializers.EmailField(source="student.user.email", read_only=True)

    class Meta:
        model = CounselorRequest
        fields = [
            "id",
            "student",
            "student_name",
            "student_email",
            "counselor",
            "counselor_name",
            "message",
            "status",
            "created_at",
        ]
