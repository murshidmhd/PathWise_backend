from rest_framework import serializers

from .models import StudentProfile


class StudentProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentProfile
        fields = "__all__"
        read_only_fields = ("id", "user", "created_at", "updated_at")


def create_student_profile(user):
    full_name = f"{user.first_name} {user.last_name}".strip() or user.email
    return StudentProfile.objects.create(user=user, full_name=full_name)
