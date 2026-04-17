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


class CounselorReview(models.Model):
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="counselor_reviews",
    )
    counselor = models.ForeignKey(
        CounselorProfile,
        on_delete=models.CASCADE,
        related_name="reviews",
    )
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("student", "counselor")

    def __str__(self):
        return f"Review by {self.student.full_name} for {self.counselor.full_name}"


class CounselorRequest(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    student = models.ForeignKey(
        "students.StudentProfile",
        on_delete=models.CASCADE,
        related_name="counselor_requests",
    )
    counselor = models.ForeignKey(
        CounselorProfile,
        on_delete=models.CASCADE,
        related_name="student_requests",
    )
    message = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # A student can only have one pending request at a time for ANY counselor
        # Or maybe one pending request per counselor?
        # Let's go with one pending request per student-counselor pair to be safe,
        # but we'll enforce "only one pending total" in the view logic.
        unique_together = ("student", "counselor", "status")

    def __str__(self):
        return f"Request from {self.student.full_name} to {self.counselor.full_name} ({self.status})"
