from rest_framework import serializers

from .models import StudentProfile


class StudentProfileSerializer(serializers.ModelSerializer):

    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "email",  # the extra field you added
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
            "created_at",
            "updated_at",
        ]
        read_only_fields = (
            "id",
            "user",
            "created_at",
            "updated_at",
            "is_onboarded",
            "assessment_taken",
            "roadmap_created",
            "profile_completed",
        )


def create_student_profile(user):
    full_name = f"{user.first_name} {user.last_name}".strip() or user.email
    return StudentProfile.objects.create(user=user, full_name=full_name)
