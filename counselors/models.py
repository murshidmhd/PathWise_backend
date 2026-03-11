from django.conf import settings
from django.db import models


class CounselorProfile(models.Model):
    APPROVAL_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="counselor_profile",
    )
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, null=True)
    city = models.CharField(max_length=100, null=True)
    state = models.CharField(max_length=100, null=True)
    experience_years = models.IntegerField(null=True, blank=True)
    qualification = models.CharField(max_length=255, null=True, blank=True)
    specialization = models.CharField(max_length=255, null=True, blank=True)
    bio = models.TextField(null=True, blank=True)
    certificate_url = models.FileField(upload_to="certificates/", null=True, blank=True)
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_CHOICES,
        default="pending",
    )
    rejection_reason = models.TextField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_students = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    profile_photo = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.user.email
