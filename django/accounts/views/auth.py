from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework.parsers import FormParser, MultiPartParser , JSONParser
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from ..serializers import LoginSerializer, RegisterSerializer
from ..services import (
    ServiceError,
    registration,
    login_user,
    logout_user,
    refresh_access_token,
)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [JSONParser,MultiPartParser, FormParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_send"

    @extend_schema(
        summary="Register a new user",
        description="Initiates user registration. Sends an OTP to the provided email for verification. Accepts multipart/form-data (required for certificate upload).",
        request=RegisterSerializer,
        responses={
            200: OpenApiResponse(
                description="OTP sent successfully",
                response=inline_serializer(
                    name="RegisterSuccessResponse",
                    fields={
                        "message": drf_serializers.CharField(),
                        "email": drf_serializers.EmailField(),
                    },
                ),
            ),
            400: OpenApiResponse(description="Validation error or reCAPTCHA failure"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        try:
            serializer = RegisterSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            result = registration(
                serializer.validated_data,
                request.data.get("recaptcha_token"),
            )
            return Response(result, status=200)
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(
        summary="Login with email and password",
        description="Authenticates a user and returns a JWT access token. Sets an HttpOnly refresh token cookie.",
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description="Login successful",
                response=inline_serializer(
                    name="LoginSuccessResponse",
                    fields={
                        "access": drf_serializers.CharField(),
                        "role": drf_serializers.CharField(),
                    },
                ),
            ),
            401: OpenApiResponse(description="Invalid credentials"),
            403: OpenApiResponse(description="Account pending approval or rejected"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = login_user(
                serializer.validated_data["email"],
                serializer.validated_data["password"],
                request.data.get("recaptcha_token"),
            )
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)

        response = Response(result["data"], status=200)
        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            httponly=True,
            secure=False,
            max_age=7 * 24 * 60 * 60,
        )
        return response


class RefreshTokenView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Refresh access token",
        description="Uses the HttpOnly refresh_token cookie to issue a new JWT access token.",
        request=None,
        responses={
            200: OpenApiResponse(
                description="New access token",
                response=inline_serializer(
                    name="RefreshTokenResponse",
                    fields={"access": drf_serializers.CharField()},
                ),
            ),
            401: OpenApiResponse(description="Refresh token missing or expired"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        try:
            result = refresh_access_token(request.COOKIES.get("refresh_token"))
            return Response(result, status=200)
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        summary="Logout user",
        description="Blacklists the refresh token and clears the HttpOnly cookie.",
        request=None,
        responses={
            200: OpenApiResponse(description="Logged out successfully"),
        },
        tags=["Authentication"],
    )
    def post(self, request):
        try:
            result = logout_user(request.COOKIES.get("refresh_token"))
            response = Response(result, status=200)
            response.delete_cookie("refresh_token")
            return response
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)
