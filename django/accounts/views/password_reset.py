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
