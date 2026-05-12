from django.db import models


class FCMDevice(models.Model):
    user_id = models.IntegerField(db_index=True)
    fcm_token = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"User {self.user_id} - {self.fcm_token[:10]}..."


class Notification(models.Model):
    user_id = models.IntegerField(db_index=True)
    event_id = models.CharField(max_length=120, unique=True, null=True, blank=True)
    type = models.CharField(max_length=30, default="system")
    title = models.CharField(max_length=255)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user_id", "is_read", "-created_at"]),
            models.Index(fields=["user_id", "-created_at"]),
        ]

    def __str__(self):
        return f"User {self.user_id} - {self.title}"
