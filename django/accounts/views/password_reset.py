from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from ..serializers import ForgotPasswordSerializer, ResetPasswordSerializer
from ..services import ServiceError, reset_password, send_password_reset_otp


class ForgotPasswordView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_send"

    @extend_schema(
        summary="Send password reset OTP",
        description="Sends a one-time password (OTP) to the user's email to initiate a password reset.",
        request=ForgotPasswordSerializer,
        responses={
            200: OpenApiResponse(
                description="OTP sent to email",
                response=inline_serializer(
                    name="ForgotPasswordResponse",
                    fields={"message": drf_serializers.CharField()},
                ),
            ),
            400: OpenApiResponse(description="Email not found"),
        },
        tags=["Password Reset"],
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = send_password_reset_otp(serializer.validated_data["email"])
            return Response(result, status=200)
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)


class ResetPasswordView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_verify"

    @extend_schema(
        summary="Reset password with OTP",
        description="Resets the user's password after verifying the OTP sent to their email.",
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(
                description="Password reset successful",
                response=inline_serializer(
                    name="ResetPasswordResponse",
                    fields={"message": drf_serializers.CharField()},
                ),
            ),
            400: OpenApiResponse(description="Invalid OTP or password validation error"),
        },
        tags=["Password Reset"],
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = reset_password(
                serializer.validated_data["email"],
                serializer.validated_data["otp"],
                serializer.validated_data["password"],
            )
            return Response(result, status=200)
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)
