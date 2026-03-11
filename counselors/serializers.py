from rest_framework import serializers

from .models import CounselorProfile


class CounselorProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = CounselorProfile
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "updated_at")


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
