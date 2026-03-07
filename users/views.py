from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.throttling import ScopedRateThrottle
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    VerifyOTPSerializer,
)
import base64
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache

from .utils import send_otp_email

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


class RegisterView(APIView):
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_send"

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)

        if serializer.is_valid():
            email = serializer.validated_data.get("email")
            pending_data = dict(serializer.validated_data)
            certificate = pending_data.pop("certificate", None)

            # File objects are not cache/session serializable, so store file content.
            if certificate:
                pending_data["certificate_meta"] = {
                    "name": certificate.name,
                    "content_type": getattr(
                        certificate, "content_type", "application/octet-stream"
                    ),
                    "data": base64.b64encode(certificate.read()).decode("utf-8"),
                }

            cache.set(f"pending_registration:{email}", pending_data, timeout=600)
            send_otp_email(email)
            return Response(
                {"message": "OTP sent", "email": email},
                status=status.HTTP_200_OK,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


from .models import CounselorProfile, OTP


class VerifyOTPView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "otp_verify"

    def post(self, request):
        otp_serializer = VerifyOTPSerializer(data=request.data)
        if not otp_serializer.is_valid():
            return Response(otp_serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        email = otp_serializer.validated_data["email"]
        otp_entered = otp_serializer.validated_data["otp"]

        try:
            otp_record = OTP.objects.get(email=email, otp=otp_entered)
        except OTP.DoesNotExist:
            return Response(
                {"message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Check if OTP is expired
        if otp_record.is_expired():
            otp_record.delete()
            return Response(
                {"message": "OTP expired"}, status=status.HTTP_400_BAD_REQUEST
            )

        # OTP is valid — now load pending registration from cache
        pending_user = cache.get(f"pending_registration:{email}")
        if not pending_user:
            return Response(
                {"message": "OTP expired or registration not found. Please register again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if pending_user.get("email") != email:
            return Response(
                {"message": "Email mismatch. Please register again."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        certificate_meta = pending_user.pop("certificate_meta", None)
        if certificate_meta:
            pending_user["certificate"] = SimpleUploadedFile(
                name=certificate_meta["name"],
                content=base64.b64decode(certificate_meta["data"]),
                content_type=certificate_meta["content_type"],
            )

        serializer = RegisterSerializer(data=pending_user)
        if serializer.is_valid():
            serializer.save()

            # Cleanup
            otp_record.delete()
            cache.delete(f"pending_registration:{email}")

            return Response(
                {"message": "User registered successfully"},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    def post(self, request):

        serializer = LoginSerializer(data=request.data)
        print(request.data)

        if serializer.is_valid():

            user = serializer.validated_data["user"]

            if user.role == "counselor":
                counselor_profile = CounselorProfile.objects.filter(user=user).first()
                approval_status = (
                    counselor_profile.approval_status if counselor_profile else "pending"
                )

                if approval_status == "rejected":
                    return Response(
                        {
                            "code": "REJECTED",
                            "message": "Your application was rejected.",
                            "reason": (counselor_profile.rejection_reason if counselor_profile else None)
                            or "No reason provided.",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

                if approval_status != "approved":
                    return Response(
                        {
                            "code": "PENDING_APPROVAL",
                            "message": "Application status is under review.",
                        },
                        status=status.HTTP_403_FORBIDDEN,
                    )

            refresh = RefreshToken.for_user(user)

            response = Response(
                {
                    "role": user.role,
                    "access": str(refresh.access_token),
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

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(APIView):
    def post(self, request):

        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {"error": "Refresh token not found"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)

            return Response({"access": access_token})

        except TokenError:
            return Response(
                {"error": "Invalid refresh token"}, status=status.HTTP_401_UNAUTHORIZED
            )


from rest_framework.permissions import IsAuthenticated


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):

        serializer = UserSerializer(request.user)

        return Response(serializer.data)


from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class LogoutView(APIView):

    def post(self, request):

        try:
            refresh_token = request.COOKIES.get("refresh_token")

            if not refresh_token:
                return Response(
                    {"error": "Refresh token not found"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            token = RefreshToken(refresh_token)
            token.blacklist()

            response = Response(
                {"message": "Logged out successfully"}, status=status.HTTP_200_OK
            )

            response.delete_cookie("refresh_token")

            return response

        except Exception:
            return Response(
                {"error": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )


from google.oauth2 import id_token
from google.auth.transport import requests as google_requests


from backend import settings
from django.contrib.auth import get_user_model
from .models import User


class GoogleAuthView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "google_auth"

    def post(self, request):
        print("here look", self.request.data)
        token = request.data.get("token")
        role    = request.data.get('role', None)


        try:
            google_user = id_token.verify_oauth2_token(
                token, google_requests.Request(), settings.GOOGLE_CLIENT_ID
            )
        except ValueError:
            return Response(
                {"message": "Invalid Google token"}, status=status.HTTP_400_BAD_REQUEST
            )

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
            status=status.HTTP_200_OK,
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
