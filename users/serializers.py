from rest_framework import serializers
from .models import User


class RegisterSerializer(serializers.ModelSerializer):

    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            "email",
            "password",
            "role"
        ]

    def create(self, validated_data):

        email = validated_data.get("email")
        password = validated_data.get("password")
        role = validated_data.get("role")

        user = User.objects.create_user(
            email=email,
            password=password,
            role=role
        )

        return user
    
    
    