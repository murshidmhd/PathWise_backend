from django.db import models

class FCMDevice(models.Model):
    user_id = models.IntegerField()  # store user id directly, no FK
    fcm_token = models.TextField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"User {self.user_id} - {self.fcm_token[:10]}..."