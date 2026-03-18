from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView
from ..serializers import (
    CompleteGoogleRegistrationSerializer,
    GoogleAuthSerializer,
)
from ..services import (
    ServiceError,
    authenticate_google_user,
    complete_google_registration,
)


class GoogleAuthView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "google_auth"

    @extend_schema(
        tags=["Auth"],
        request=GoogleAuthSerializer,
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
    )
    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = authenticate_google_user(serializer.validated_data["token"])
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)

        response = Response(result["data"], status=200)
        if "refresh_token" not in result:
            return response

        response.set_cookie(
            key="refresh_token",
            value=result["refresh_token"],
            httponly=True,
            secure=result.get("cookie_secure", False),
            samesite=result.get("cookie_samesite", "Lax"),
            max_age=7 * 24 * 60 * 60,
        )
        return response


class CompleteGoogleRegistrationView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CompleteGoogleRegistrationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            result = complete_google_registration(
                serializer.validated_data["temp_token"],
                serializer.validated_data["role"],
            )
            response = Response(result["data"], status=result["status_code"])
            response.set_cookie(
                key="refresh_token",
                value=result["refresh_token"],
                httponly=True,
                secure=False,
                max_age=7 * 24 * 60 * 60,
            )
            return response
        except ServiceError as exc:
            return Response(exc.detail, status=exc.status_code)
