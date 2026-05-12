import json
import logging

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from firebase_admin import messaging

from .models import FCMDevice, Notification

logger = logging.getLogger(__name__)


def notification_payload(notification):
    return {
        "id": notification.id,
        "event_id": notification.event_id,
        "user_id": notification.user_id,
        "type": notification.type,
        "title": notification.title,
        "message": notification.message,    
        "data": notification.data,
        "is_read": notification.is_read,
        "created_at": notification.created_at.isoformat(),
    }


def broadcast_notification(notification):
    channel_layer = get_channel_layer()
    group_name = f"user_{notification.user_id}"
    print(f"--- DEBUG: Broadcasting notification to group {group_name}: {notification.title} ---")
    async_to_sync(channel_layer.group_send)(
        group_name,
        {
            "type": "notify",
            "notification": notification_payload(notification),
        },
    )


def send_push_notification(notification):
    devices = FCMDevice.objects.filter(user_id=notification.user_id)
    tokens = list(devices.values_list("fcm_token", flat=True))
    if not tokens:
        return

    data = {
        key: str(value)
        for key, value in {
            **(notification.data or {}),
            "notification_id": notification.id,
            "type": notification.type,
        }.items()
        if value is not None
    }
    message = messaging.MulticastMessage(
        notification=messaging.Notification(
            title=notification.title,
            body=notification.message,
        ),
        data=data,
        tokens=tokens,
    )

    try:
        if hasattr(messaging, "send_each_for_multicast"):
            response = messaging.send_each_for_multicast(message)
        else:
            response = messaging.send_multicast(message)
    except Exception:
        logger.exception("Failed to send FCM notification %s", notification.id)
        return

    invalid_tokens = []
    for token, result in zip(tokens, getattr(response, "responses", [])):
        if not result.success:
            invalid_tokens.append(token)

    if invalid_tokens:
        FCMDevice.objects.filter(fcm_token__in=invalid_tokens).delete()

    logger.info(
        "Notification %s FCM sent: success=%s failed=%s",
        notification.id,
        getattr(response, "success_count", 0),
        getattr(response, "failure_count", 0),
    )


def deliver_notification(notification):
    broadcast_notification(notification)
    send_push_notification(notification)


def _json_data(value):
    if not value:
        return {}
    if isinstance(value, dict):
        return value
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return {}


def create_notification_from_event(event):
    event_id = event.get("event_id")
    defaults = {
        "user_id": int(event["user_id"]),
        "type": event.get("type") or "system",
        "title": event["title"],
        "message": event["message"],
        "data": _json_data(event.get("data")),
    }

    if event_id:
        notification, created = Notification.objects.get_or_create(
            event_id=event_id,
            defaults=defaults,
        )
    else:
        notification = Notification.objects.create(**defaults)
        created = True

    return notification, created


def send_notification(user_id, title, message, data=None, notification_type="system"):
    notification = Notification.objects.create(
        user_id=user_id,
        type=notification_type,
        title=title,
        message=message,
        data=data or {},
    )
    deliver_notification(notification)
    return notification
