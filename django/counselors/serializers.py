from rest_framework import serializers

from students.models import StudentProfile

from .models import CounselorProfile


class CounselorProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    certificate_url = serializers.FileField(required=False, allow_null=True)

    class Meta:
        model = CounselorProfile
        fields = [
            "id",
            "user_id",
            "email",
            "full_name",
            "phone",
            "city",
            "state",
            "experience_years",
            "qualification",
            "specialization",
            "bio",
            "certificate_url",
            "approval_status",
            "rejection_reason",
            "rating",
            "total_students",
            "is_available",
            "profile_photo",
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "id",
            "user",
            "created_at",
            "updated_at",
            "approval_status",
            "rejection_reason",
            "rating",
            "total_students",
            "certificate_url",
        )


def create_counselor_profile(
    user,
    qualification=None,
    experience_years=None,
    specialization=None,
    certificate_url=None,
):
    full_name = f"{user.first_name} {user.last_name}".strip() or user.email
    return CounselorProfile.objects.create(
        user=user,
        full_name=full_name,
        qualification=qualification,
        experience_years=experience_years,
        specialization=specialization,
        certificate_url=certificate_url,
        approval_status="pending",
    )


class CounselorStudentListSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "user_id",
            "full_name",
            "email",
            "phone",
            "city",
            "state",
            "education_level",
            "stream",
            "assessment_taken",
            "roadmap_created",
            "profile_completed",
            "created_at",
        ]


class CounselorStudentDetailSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    assigned_counselor = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "email",
            "full_name",
            "date_of_birth",
            "gender",
            "phone",
            "profile_photo",
            "city",
            "state",
            "education_level",
            "stream",
            "is_onboarded",
            "assessment_taken",
            "roadmap_created",
            "profile_completed",
            "assigned_counselor",
            "created_at",
            "updated_at",
        ]
