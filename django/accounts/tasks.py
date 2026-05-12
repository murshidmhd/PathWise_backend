import os
import time
from celery import shared_task
from django.conf import settings
from .utils import send_otp_email


@shared_task
def send_otp_email_task(email, otp):
    """
    Asynchronously sends the OTP email via Celery.
    """
    send_otp_email(email, otp)


@shared_task
def cleanup_pending_certificates():
    """
    Periodically cleans up certificate files older than 10 minutes
    from the pending_certificates directory.
    """
    # Using BASE_DIR because media root isn't explicitly defined in settings
    pending_dir = os.path.join(settings.BASE_DIR, "pending_certificates")
    if not os.path.exists(pending_dir):
        return

    now = time.time()
    count = 0
    for filename in os.listdir(pending_dir):
        file_path = os.path.join(pending_dir, filename)
        if os.path.isfile(file_path):
            # Check if file is older than 10 minutes (600 seconds) plus some buffer (e.g. 15 min total)
            if os.stat(file_path).st_mtime < now - 900:
                try:
                    os.remove(file_path)
                    count += 1
                except Exception as e:
                    print(f"Failed to delete {file_path}: {e}")

    return f"Cleaned up {count} expired certificate files."
