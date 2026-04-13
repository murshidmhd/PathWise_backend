from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from firebase_admin import messaging
from .models import FCMDevice
import logging

logger = logging.getLogger(__name__)


def send_notification(user_id, title, message, data=None):
    """
    Sends a notification to a specific user via Websocket and FCM.
    """
    # 1. Send via Websocket (Channels)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"user_{user_id}",
        {"type": "notify", "title": title, "message": message, "data": data or {}},
    )

    # 2. Send via FCM (Push Notifications)
    devices = FCMDevice.objects.filter(user_id=user_id)
    tokens = [device.fcm_token for device in devices]

    if tokens:
        fcm_message = messaging.MulticastMessage(
            notification=messaging.Notification(
                title=title,
                body=message,
            ),
            data=data or {},
            tokens=tokens,
        )
        try:
            response = messaging.send_multicast(fcm_message)
            logger.info(
                f"FCM: Successfully sent {response.success_count} messages; "
                f"failed {response.failure_count} messages."
            )
        except Exception as e:
            logger.error(f"FCM Error: {str(e)}")



            
