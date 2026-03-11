from rest_framework.views import APIView
from rest_framework.response import Response
import requests

from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.throttling import ScopedRateThrottle
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    VerifyOTPSerializer,
)
import os
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.core.cache import cache

from .utils import send_otp_email
from django.conf import settings

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework.permissions import AllowAny, IsAuthenticated
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema


def is_valid_recaptcha(token):
    if settings.DEBUG:
        return True
    data = {
        "secret": settings.RECAPTCHA_SECRET_KEY,
        "response": token,
    }
    response = requests.post(
        "https://www.google.com/recaptcha/api/siteverify",
        data=data,
        timeout=5,
    )
    return response.json().get("success", False)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_send"

    @extend_schema(
        tags=["Auth"],
        request=RegisterSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
    )
    def post(self, request):

        try:
            token = request.data.get("recaptcha_token")
            print(token)
            if not is_valid_recaptcha(token):
                return Response({"error": "Invalid reCAPTCHA"}, status=400)

            serializer = RegisterSerializer(data=request.data)

            if serializer.is_valid():

                email = serializer.validated_data.get("email")
                pending_data = dict(serializer.validated_data)
                certificate = pending_data.pop("certificate", None)

                if certificate:
                    pending_data["certificate_temp_path"] = default_storage.save(
                        f"pending_certificates/{certificate.name}",
                        certificate,
                    )

                cache.set(f"pending_registration:{email}", pending_data, timeout=600)
                send_otp_email(email)
                return Response(
                    {"message": "OTP sent", "email": email},
                    status=200,
                )
        except Exception as e:
            print("Save error:", e)  # 👈 check your terminal for the real error
            return Response({"message": "Registration failed"}, status=500)

        return Response(serializer.errors, status=400)


from .models import OTP
from counselors.models import CounselorProfile


class VerifyOTPView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_verify"

    @extend_schema(
        tags=["Auth"],
        request=VerifyOTPSerializer,
        responses={
            201: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
    )
    def post(self, request):
        otp_serializer = VerifyOTPSerializer(data=request.data)
        print("serilazer adith otp", otp_serializer)
        if not otp_serializer.is_valid():
            return Response(otp_serializer.errors, status=400)

        email = otp_serializer.validated_data["email"]
        otp_entered = otp_serializer.validated_data["otp"]

        try:
            otp_record = OTP.objects.get(email=email, otp=otp_entered)
        except OTP.DoesNotExist:
            return Response({"message": "Invalid OTP"}, status=400)

        # Check if OTP is expired
        if otp_record.is_expired():
            OTP.objects.filter(email=email, otp=otp_entered).delete()
            return Response({"message": "OTP expired"}, status=400)

        # OTP is valid — now load pending registration from cache
        pending_user = cache.get(f"pending_registration:{email}")
        if not pending_user:
            return Response(
                {
                    "message": "OTP expired or registration not found. Please register again."
                },
                status=400,
            )

        if pending_user.get("email") != email:
            return Response(
                {"message": "Email mismatch. Please register again."},
                status=400,
            )

        print("hey")

        certificate_temp_path = pending_user.pop("certificate_temp_path", None)
        if certificate_temp_path and default_storage.exists(certificate_temp_path):
            with default_storage.open(certificate_temp_path, "rb") as cert_file:
                pending_user["certificate"] = ContentFile(
                    cert_file.read(),
                    name=os.path.basename(certificate_temp_path),
                )

        print(pending_user)

        serializer = RegisterSerializer(data=pending_user)
        if serializer.is_valid():

            OTP.objects.filter(email=email, otp=otp_entered).delete()
            cache.delete(f"pending_registration:{email}")

            serializer.save()

            print("hey i am inside the serializer")

            # Cleanup

            return Response(
                {"message": "User registered successfully"},
                status=201,
            )

        return Response(serializer.errors, status=400)


class LoginView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(
        tags=["Auth"],
        request=LoginSerializer,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
            403: OpenApiTypes.OBJECT,
        },
    )
    def post(self, request):
        token = request.data.get("recaptcha_token")
        if not is_valid_recaptcha(token):
            return Response({"error": "Invalid reCAPTCHA"}, status=400)

        serializer = LoginSerializer(data=request.data)
        print(request.data)

        if serializer.is_valid():

            user = serializer.validated_data["user"]

            if user.role == "counselor":
                counselor_profile = CounselorProfile.objects.filter(user=user).first()
                approval_status = (
                    counselor_profile.approval_status
                    if counselor_profile
                    else "pending"
                )

                if approval_status == "rejected":
                    return Response(
                        {
                            "code": "REJECTED",
                            "message": "Your application was rejected.",
                            "reason": (
                                counselor_profile.rejection_reason
                                if counselor_profile
                                else None
                            )
                            or "No reason provided.",
                        },
                        status=403,
                    )

                if approval_status != "approved":
                    return Response(
                        {
                            "code": "PENDING_APPROVAL",
                            "message": "Application status is under review.",
                        },
                        status=403,
                    )

            refresh = RefreshToken.for_user(user)

            response = Response(
                {
                    "role": user.role,
                    "access": str(refresh.access_token),
                    "code": "APPROVED" if user.role == "counselor" else "LOGIN_SUCCESS",
                }
            )
            response.set_cookie(
                key="refresh_token",
                value=str(refresh),
                httponly=True,
                secure=False,
                max_age=7 * 24 * 60 * 60,
            )
            return response

        return Response(serializer.errors, status=400)


class RefreshTokenView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        request=None,
        responses={
            200: OpenApiTypes.OBJECT,
            401: OpenApiTypes.OBJECT,
        },
    )
    def post(self, request):

        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {"error": "Refresh token not found"},
                status=401,
            )

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            return Response({"access": access_token})

        except TokenError:
            return Response({"error": "Invalid refresh token"}, status=401)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=["Auth"],
        responses={200: UserSerializer, 401: OpenApiTypes.OBJECT},
    )
    def get(self, request):

        serializer = UserSerializer(request.user)

        return Response(serializer.data)


from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response


class LogoutView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    @extend_schema(
        tags=["Auth"],
        request=None,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
    )
    def post(self, request):

        try:
            refresh_token = request.COOKIES.get("refresh_token")

            if not refresh_token:
                return Response(
                    {"error": "Refresh token not found"},
                    status=400,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            response = Response({"message": "Logged out successfully"}, status=200)

            response.delete_cookie("refresh_token")

            return response

        except Exception:
            return Response({"error": "Invalid token"}, status=400)


from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


from backend import settings as backend_settings
from .models import User


class GoogleAuthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "google_auth"

    @extend_schema(
        tags=["Auth"],
        request=OpenApiTypes.OBJECT,
        responses={
            200: OpenApiTypes.OBJECT,
            400: OpenApiTypes.OBJECT,
        },
    )
    def post(self, request):
        print("here look", self.request.data)
        token = request.data.get("token")

        try:
            google_user = id_token.verify_oauth2_token(
                token, google_requests.Request(), backend_settings.GOOGLE_CLIENT_ID
            )
        except ValueError:
            return Response({"message": "Invalid Google token"}, status=400)

        email = google_user.get("email")
        first_name = google_user.get("given_name", "")
        last_name = google_user.get("family_name", "")

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": first_name,
                "last_name": last_name,
                "email": email,
            },
        )

        refresh = RefreshToken.for_user(user)

        response = Response(
            {"access": str(refresh.access_token), "is_new_user": created},
            status=200,
        )

        response.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="Lax",
            max_age=7 * 24 * 60 * 60,
        )

        return response
