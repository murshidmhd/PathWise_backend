from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FCMDevice


class FCMTokenView(APIView):
    def post(self, request):
        user_id = request.data.get("user_id")
        token = request.data.get("token")

        if not user_id or not token:
            return Response(
                {"error": "user_id and token are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Update or create the device token for this user
        FCMDevice.objects.update_or_create(
            fcm_token=token, defaults={"user_id": user_id}
        )

        return Response(
            {"message": "Token registered successfully"}, status=status.HTTP_201_CREATED
        )
