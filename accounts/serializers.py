from rest_framework import serializers
from .models import User
from students.serializers import create_student_profile
from counselors.serializers import create_counselor_profile


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
        if not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in value):
            raise serializers.ValidationError(
                "Password must contain at least one special character."
            )
        return value

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")

        if data["role"] == "counselor":
            if not data.get("qualification"):
                raise serializers.ValidationError(
                    "Qualification is required for counselors"
                )
            if not data.get("certificate"):
                raise serializers.ValidationError(
                    "Certificate upload is required for counselors"
                )
        return data

    def create(self, validated_data):

        # print(validated_data)

        validated_data.pop("confirm_password")
        qualification = validated_data.pop("qualification", None)
        experience_years = validated_data.pop("experience_years", None)
        specialization = validated_data.pop("specialization", None)
        certificate = validated_data.pop("certificate", None)

        # print(certificate)

        role = validated_data.get("role")
        email = validated_data.get("email")
        password = validated_data.get("password")
        first_name = validated_data.get("first_name", "")
        last_name = validated_data.get("last_name", "")

        user = User.objects.create_user(
            email=email,
            password=password,
            role=role,
            first_name=first_name,
            last_name=last_name,
        )
        user.is_active = True
        user.save()

        # print("i am her before the role check")

        if role == "student":
            create_student_profile(user=user)

        elif role == "parent":
            # ParentProfile.objects.create(user=user)
            pass

        elif role == "counselor":
            create_counselor_profile(
                user=user,
                qualification=qualification,
                experience_years=experience_years,
                specialization=specialization,
                certificate_url=certificate,
            )

        return user


from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from rest_framework import serializers


class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):

        email = data.get("email")
        password = data.get("password")

        # print(email, password)

        User = get_user_model()
        user_obj = User.objects.filter(email=email).first()
        if not user_obj or not user_obj.check_password(password):
            raise serializers.ValidationError("Invalid credentials")

        if not user_obj.is_active:
            raise serializers.ValidationError("Account is not active")

        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError("Authentication failed")
        # print(f"user is this:{user}")

        data["user"] = user
        return data


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "role"]


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
