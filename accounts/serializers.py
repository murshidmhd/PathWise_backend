from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):

    confirm_password = serializers.CharField(write_only=True)
    # print("SERIALIZER")

    qualification = serializers.CharField(required=False, allow_blank=True)
    experience_years = serializers.IntegerField(required=False, allow_null=True)
    specialization = serializers.CharField(required=False, allow_blank=True)
    certificate = serializers.FileField(
        required=False,
        allow_null=True,
    )

    # print("SERIALIZER")

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "confirm_password",
            "role",
            "qualification",
            "experience_years",
            "specialization",
            "certificate",
        ]

    # print("i am here create")

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters.")
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )
        if not any(c.islower() for c in value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )
        # if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in value):
        #     raise serializers.ValidationError(
        #         "Password must contain at least one special character."
        #     )
        return value

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data


class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "role"]


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)


class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters.")
        if not any(c.isupper() for c in value):
            raise serializers.ValidationError(
                "Password must contain at least one uppercase letter."
            )
        if not any(c.islower() for c in value):
            raise serializers.ValidationError(
                "Password must contain at least one lowercase letter."
            )
        if not any(c.isdigit() for c in value):
            raise serializers.ValidationError(
                "Password must contain at least one number."
            )
        return value

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")
        return data


class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()


class CompleteGoogleRegistrationSerializer(serializers.Serializer):
    temp_token = serializers.CharField()
    role = serializers.ChoiceField(choices=User.ROLE_CHOICES)
