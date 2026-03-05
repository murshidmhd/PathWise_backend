from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):

    confirm_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "first_name",
            "last_name",
            "email",
            "password",
            "confirm_password",
            "role",
        ]

    def validate(self, data):

        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match")

        return data

    def create(self, validated_data):

        email = validated_data.get("email")
        password = validated_data.get("password")
        role = validated_data.get("role")

        user = User.objects.create_user(email=email, password=password, role=role)
        user.is_active = True
        user.save()

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

        print(email, password)

        User = get_user_model()
        user_obj = User.objects.filter(email=email).first()
        if not user_obj or not user_obj.check_password(password):
            raise serializers.ValidationError("Invalid credentials")

        if not user_obj.is_active:
            raise serializers.ValidationError("Account is not active")

        user = authenticate(username=email, password=password)
        if not user:
            raise serializers.ValidationError("Authentication failed")
        print(f"user is this:{user}")

        data["user"] = user
        return data


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "email", "role"]


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6)
    
