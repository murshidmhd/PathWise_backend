from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
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
        tags=["Auth"],
        request=VerifyOTPSerializer,
        responses={201: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
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
        tags=["Auth"],
        request=ResendOTPSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = resend_registration_otp(serializer.validated_data["email"])
            return Response(result, status=200)
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)
