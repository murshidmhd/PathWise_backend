from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import FCMDevice, Notification
from .serializers import NotificationSerializer


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


class NotificationListView(APIView):
    def get(self, request):
        user_id = request.query_params.get("user_id")
        print("user_id", user_id)
        if not user_id:
            return Response(
                {"error": "user_id is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        notifications = Notification.objects.filter(user_id=user_id).order_by(
            "-created_at"
        )
        serializer = NotificationSerializer(notifications, many=True)
        return Response(serializer.data)


class MarkNotificationReadView(APIView):
    def post(self, request, pk):
        try:
            notification = Notification.objects.get(pk=pk)
            notification.is_read = True
            notification.save()
            return Response({"message": "Notification marked as read"})
        except Notification.DoesNotExist:
            return Response(
                {"error": "Notification not found"}, status=status.HTTP_404_NOT_FOUND
            )


class SendNotificationView(APIView):
    """
    Internal API view to send a notification from other services.
    """

    def post(self, request):
        from .utils import send_notification

        user_id = request.data.get("user_id")
        title = request.data.get("title")
        message = request.data.get("message")
        notification_type = request.data.get("type", "system")
        data = request.data.get("data", {})

        if not all([user_id, title, message]):
            return Response(
                {"error": "user_id, title, and message are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        notification = send_notification(
            user_id=user_id,
            title=title,
            message=message,
            data=data,
            notification_type=notification_type,
        )

        return Response(
            {"message": "Notification sent", "id": notification.id},
            status=status.HTTP_201_CREATED,
        )
