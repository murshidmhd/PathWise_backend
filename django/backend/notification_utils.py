import logging
import requests
from django.conf import settings

logger = logging.getLogger(__name__)

def send_notification(user_id, title, message, notification_type="system", data=None):
    """
    Sends a notification to the WebSocket service.
    """
    # In production, use the internal service URL
    # In development, use localhost
    base_url = "http://websocket:8001" if not settings.DEBUG else "http://localhost:8001"
    url = f"{base_url}/notifications/send/"

    payload = {
        "user_id": user_id,
        "title": title,
        "message": message,
        "type": notification_type,
        "data": data or {}
    }

    try:
        response = requests.post(url, json=payload, timeout=5)
        response.raise_for_status()
        return True
    except Exception as e:
        logger.error(f"Failed to send notification to WebSocket service: {e}")
        return False
