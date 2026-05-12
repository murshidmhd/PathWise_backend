from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from ..serializers import ResendOTPSerializer, VerifyOTPSerializer
from ..services import ServiceError, resend_registration_otp, verify_registration_otp


class VerifyOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_verify"

    @extend_schema(
        summary="Verify registration OTP",
        description="Verifies the OTP sent to the user's email during registration. On success, completes account creation and returns a JWT access token.",
        request=VerifyOTPSerializer,
        responses={
            200: OpenApiResponse(
                description="OTP verified, account created",
                response=inline_serializer(
                    name="VerifyOTPResponse",
                    fields={
                        "access": drf_serializers.CharField(),
                        "role": drf_serializers.CharField(),
                    },
                ),
            ),
            400: OpenApiResponse(description="Invalid or expired OTP"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        otp_serializer = VerifyOTPSerializer(data=request.data)
        otp_serializer.is_valid(raise_exception=True)

        try:
            result = verify_registration_otp(
                otp_serializer.validated_data["email"],
                otp_serializer.validated_data["otp"],
            )
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)

        response = Response(result["data"], status=result["status_code"])
        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            httponly=True,
            secure=False,
            max_age=7 * 24 * 60 * 60,
        )
        return response


class ResendOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_send"

    @extend_schema(
        summary="Resend registration OTP",
        description="Resends the OTP email to the user if the previous one expired.",
        request=ResendOTPSerializer,
        responses={
            200: OpenApiResponse(
                description="OTP resent successfully",
                response=inline_serializer(
                    name="ResendOTPResponse",
                    fields={"message": drf_serializers.CharField()},
                ),
            ),
            400: OpenApiResponse(description="Email not found or already registered"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = resend_registration_otp(serializer.validated_data["email"])
            return Response(result, status=200)
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)
