from rest_framework.views import APIView
from rest_framework.response import Response

from rest_framework import serializers, status
from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    UserSerializer,
    VerifyOTPSerializer,
)
from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer

from .utils import send_otp_email

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


class RegisterView(APIView):
    @extend_schema(
        request=RegisterSerializer,
        responses={
            201: inline_serializer(
                name="RegisterSuccessResponse",
                fields={"message": serializers.CharField()},
            ),
            400: OpenApiResponse(description="Validation error"),
        },
    )
    def post(self, request):
        serilaizer = RegisterSerializer(data=request.data)

        if serilaizer.is_valid():
            request.session["pending_user"] = request.data

            email = request.data.get("email")
            send_otp_email(email)
            return Response(
                {"message": "OTP sent to your email"},
                status=status.HTTP_200_OK,
            )

        return Response(serilaizer.errors, status=status.HTTP_400_BAD_REQUEST)


from .models import OTP

    
class VerifyOTPView(APIView):
    @extend_schema(
        request=VerifyOTPSerializer,
        responses={
            201: inline_serializer(
                name="VerifyOTPSuccessResponse",
                fields={"message": serializers.CharField()},
            ),
            400: OpenApiResponse(description="Invalid OTP or expired session"),
        },
    )
    def post(self, request):
        email = request.data.get("email")
        otp_entered = request.data.get("otp")

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

        # OTP is valid — now save the user
        pending_user = request.session.get("pending_user")
        if not pending_user:
            return Response(
                {"message": "Session expired, please register again"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = RegisterSerializer(data=pending_user)
        if serializer.is_valid():
            serializer.save()

            # Cleanup
            otp_record.delete()
            del request.session["pending_user"]

            return Response(
                {"message": "User registered successfully"},
                status=status.HTTP_201_CREATED,
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    @extend_schema(
        request=LoginSerializer,
        responses={
            200: inline_serializer(
                name="LoginSuccessResponse",
                fields={"access": serializers.CharField()},
            ),
            400: OpenApiResponse(description="Invalid credentials"),
        },
    )
    def post(self, request):

        serializer = LoginSerializer(data=request.data)
        # print(request.data)

        if serializer.is_valid():

            user = serializer.validated_data["user"]

            refresh = RefreshToken.for_user(user)

            response = Response(
                {
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
    @extend_schema(
        request=None,
        responses={
            200: inline_serializer(
                name="RefreshTokenSuccessResponse",
                fields={"access": serializers.CharField()},
            ),
            401: OpenApiResponse(description="Invalid or missing refresh token"),
        },
    )
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
from .serializers import UserSerializer


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer)
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
