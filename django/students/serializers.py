from rest_framework import serializers

from .models import StudentProfile
from payments.models import Wallet


class StudentProfileSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(source="user.email", read_only=True)
    user_id = serializers.IntegerField(source="user.id", read_only=True)
    counselor_details = serializers.SerializerMethodField()

    def get_counselor_details(self, obj):
        if not obj.assigned_counselor:
            return None
        c = obj.assigned_counselor
        return {
            "id": c.id,
            "user_id": c.user.id,
            "full_name": c.full_name,
            "phone": c.phone,
            "city": c.city,
            "state": c.state,
            "experience_years": c.experience_years,
            "qualification": c.qualification,
            "specialization": c.specialization,
            "bio": c.bio,
            "rating": str(c.rating),
            "profile_photo": c.profile_photo,
            "is_available": c.is_available,
        }

    wallet = serializers.SerializerMethodField()

    def get_wallet(self, obj):
        wallet, created = Wallet.objects.get_or_create(user=obj.user)
        return {
            "balance": wallet.balance,
            "is_welcome_gift_claimed": wallet.is_welcome_gift_claimed,
        }

    class Meta:
        model = StudentProfile
        fields = [
            "id",
            "user_id",
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
            "counselor_details",
            "wallet",
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
