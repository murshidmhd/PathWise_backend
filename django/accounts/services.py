import os
import secrets

from backend import settings as backend_settings
from counselors.models import CounselorProfile
from counselors.serializers import create_counselor_profile
from django.contrib.auth import authenticate
from django.conf import settings
from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
import requests
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from students.serializers import create_student_profile

from .models import User
from .tasks import send_otp_email_task
from .utils import create_otp


class ServiceError(Exception):
    def __init__(self, detail, status_code=400):
        normalized_detail = {"message": detail} if isinstance(detail, str) else detail
        super().__init__(normalized_detail)
        self.detail = normalized_detail
        self.status_code = status_code


def _issue_tokens(user):
    refresh = RefreshToken.for_user(user)
    return {
        "access": str(refresh.access_token),
        "refresh": str(refresh),
    }


def _is_valid_recaptcha(token):
    if settings.DEBUG:
        return True

    response = requests.post(
        settings.RECAPTCHA_VERIFY_URL,
        data={
            "secret": settings.RECAPTCHA_SECRET_KEY,
            "response": token,
        },
        timeout=5,
    )
    return response.json().get("success", False)


def _create_user_from_registration(validated_data):
    registration_data = dict(validated_data)
    registration_data.pop("confirm_password", None)

    qualification = registration_data.pop("qualification", None)
    experience_years = registration_data.pop("experience_years", None)
    specialization = registration_data.pop("specialization", None)
    certificate = registration_data.pop("certificate", None)

    user = User.objects.create_user(
        email=registration_data["email"],
        password=registration_data["password"],
        role=registration_data["role"],
        first_name=registration_data.get("first_name", ""),
        last_name=registration_data.get("last_name", ""),
    )
    user.is_active = True
    user.save()

    if user.role == "student":
        create_student_profile(user=user)
    elif user.role == "counselor":
        create_counselor_profile(
            user=user,
            qualification=qualification,
            experience_years=experience_years,
            specialization=specialization,
            certificate_url=certificate,
        )

    return user


def registration(validated_data, recaptcha_token):
    if not _is_valid_recaptcha(recaptcha_token):
        raise ServiceError({"error": "Invalid reCAPTCHA"})

    pending_data = dict(validated_data)
    email = pending_data["email"]
    certificate = pending_data.pop("certificate", None)

    if pending_data["role"] == "counselor":
        if not pending_data.get("qualification"):
            raise ServiceError("Qualification is required for counselors")
        if not certificate:
            raise ServiceError("Certificate upload is required for counselors")

    if certificate:
        pending_data["certificate_temp_path"] = default_storage.save(
            f"pending_certificates/{certificate.name}",
            certificate,
        )

    cache.set(f"pending_registration:{email}", pending_data, timeout=600)
    otp = create_otp(email)
    send_otp_email_task.delay(email, otp)

    return {"message": "OTP sent", "email": email}


def verify_registration_otp(email, otp):
    cached_otp = cache.get(f"otp:{email}")
    if not cached_otp or cached_otp != otp:
        raise ServiceError({"message": "Invalid or expired OTP"})

    pending_user = cache.get(f"pending_registration:{email}")
    if not pending_user:
        raise ServiceError(
            {"message": "OTP expired or registration not found. Please register again."}
        )

    if pending_user.get("email") != email:
        raise ServiceError({"message": "Email mismatch. Please register again."})

    certificate_temp_path = pending_user.pop("certificate_temp_path", None)
    if certificate_temp_path and default_storage.exists(certificate_temp_path):
        with default_storage.open(certificate_temp_path, "rb") as cert_file:
            pending_user["certificate"] = ContentFile(
                cert_file.read(),
                name=os.path.basename(certificate_temp_path),
            )

    user = _create_user_from_registration(pending_user)
    tokens = _issue_tokens(user)

    cache.delete(f"otp:{email}")
    cache.delete(f"pending_registration:{email}")

    return {
        "status_code": 201,
        "data": {
            "message": "User registered successfully",
            "role": user.role,
            "access": tokens["access"],
            "code": "APPROVED" if user.role == "counselor" else "REGISTER_SUCCESS",
        },
        "refresh_token": tokens["refresh"],
    }


def resend_registration_otp(email):
    pending_user = cache.get(f"pending_registration:{email}")
    if not pending_user:
        raise ServiceError(
            {
                "message": "No pending registration found for this email. Please register again."
            }
        )

    otp = create_otp(email)
    send_otp_email_task.delay(email, otp)
    return {"message": "OTP resent successfully", "email": email}


def login_user(email, password, recaptcha_token):
    if not _is_valid_recaptcha(recaptcha_token):
        raise ServiceError({"error": "Invalid reCAPTCHA"})

    user = User.objects.filter(email=email).first()
    if user and user.google_id:
        raise ServiceError(
            "This account was created with Google. Please continue with Google sign-in."
        )
    if not user or not user.check_password(password):
        raise ServiceError("Invalid credentials")
    if not user.is_active:
        raise ServiceError("Account is not active")

    authenticated_user = authenticate(username=email, password=password)
    if not authenticated_user:
        raise ServiceError("Authentication failed")

    if authenticated_user.role == "counselor":
        counselor_profile = CounselorProfile.objects.filter(
            user=authenticated_user
        ).first()
        approval_status = (
            counselor_profile.approval_status if counselor_profile else "pending"
        )

        if approval_status == "rejected":
            raise ServiceError(
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
                status_code=403,
            )

        if approval_status != "approved":
            raise ServiceError(
                {
                    "code": "PENDING_APPROVAL",
                    "message": "Application status is under review.",
                },
                status_code=403,
            )

    tokens = _issue_tokens(authenticated_user)
    return {
        "data": {
            "role": authenticated_user.role,
            "access": tokens["access"],
            "code": (
                "APPROVED"
                if authenticated_user.role == "counselor"
                else "LOGIN_SUCCESS"
            ),
        },
        "refresh_token": tokens["refresh"],
    }


def refresh_access_token(refresh_token):
    if not refresh_token:
        raise ServiceError({"error": "Refresh token not found"}, status_code=401)

    try:
        refresh = RefreshToken(refresh_token)
    except TokenError as exc:
        raise ServiceError({"error": "Invalid refresh token"}, status_code=401) from exc

    return {"access": str(refresh.access_token)}


def logout_user(refresh_token):
    if not refresh_token:
        raise ServiceError({"error": "Refresh token not found"})

    try:
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception as exc:
        raise ServiceError({"error": "Invalid token"}) from exc

    return {"message": "Logged out successfully"}


def authenticate_google_user(token):
    try:
        google_user = id_token.verify_oauth2_token(
            token, google_requests.Request(), backend_settings.GOOGLE_CLIENT_ID
        )
    except ValueError as exc:
        raise ServiceError({"message": "Invalid Google token"}) from exc

    google_id = google_user.get("sub")
    email = google_user.get("email")
    first_name = google_user.get("given_name", "")
    last_name = google_user.get("family_name", "")

    user = User.objects.filter(email=email).first()
    if not user:
        temp_token = secrets.token_urlsafe(32)
        cache.set(
            f"google_temp:{temp_token}",
            {
                "email": email,
                "first_name": first_name,
                "last_name": last_name,
                "google_id": google_id,
            },
            timeout=600,
        )
        return {
            "data": {"is_new_user": True, "temp_token": temp_token},
        }

    tokens = _issue_tokens(user)
    return {
        "data": {
            "access": tokens["access"],
            "is_new_user": False,
            "role": user.role,
        },
        "refresh_token": tokens["refresh"],
        "cookie_secure": True,
        "cookie_samesite": "Lax",
    }


def complete_google_registration(temp_token, role):
    user_data = cache.get(f"google_temp:{temp_token}")
    if not user_data:
        raise ServiceError({"message": "Invalid or expired token"})

    user = User.objects.create_user(
        email=user_data["email"],
        role=role,
        first_name=user_data.get("first_name", ""),
        last_name=user_data.get("last_name", ""),
        google_id=user_data.get("google_id"),
    )

    if role == "student":
        create_student_profile(user=user)

    cache.delete(f"google_temp:{temp_token}")
    tokens = _issue_tokens(user)

    return {
        "status_code": 201,
        "data": {"access": tokens["access"]},
        "refresh_token": tokens["refresh"],
    }


def send_password_reset_otp(email):
    if not User.objects.filter(email=email).exists():
        raise ServiceError("No account found with this email.")

    otp = create_otp(email)
    send_otp_email_task.delay(email, otp)
    return {"message": "Password reset OTP sent successfully."}


def reset_password(email, otp, new_password):
    cached_otp = cache.get(f"otp:{email}")
    if not cached_otp or cached_otp != otp:
        raise ServiceError({"message": "Invalid or expired OTP"})

    user = User.objects.filter(email=email).first()
    if not user:
        raise ServiceError({"message": "User not found"}, status_code=404)

    user.set_password(new_password)
    user.save()
    cache.delete(f"otp:{email}")

    return {"message": "Password reset successful."}
