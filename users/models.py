from django.db import models

from django.contrib.auth.models import AbstractUser
from django.db import models


from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")

        email = self.normalize_email(email)

        user = self.model(email=email, **extra_fields)

        user.set_password(password)

        user.save(using=self._db)

        return user

    def create_superuser(self, email, password=None, **extra_fields):

        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("role", "admin")
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):

    ROLE_CHOICES = [
        ("student", "Student"),
        ("parent", "Parent"),
        ("counselor", "Counselor"),
        ("admin", "Admin"),
    ]

    username = None  # remove username login
    email = models.EmailField(unique=True)
    objects = UserManager()

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    is_active = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    google_id = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = [
        "first_name",
        "last_name",
    ]  # this is basically when we create the super user that time its ask for the this two filds also

    def __str__(self):
        return self.email


from django.db import models
from django.utils import timezone


class OTP(models.Model):
    email = models.EmailField()
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_expired(self):
        # OTP expires after 5 minutes
        return (timezone.now() - self.created_at).seconds > 300

    def __str__(self):
        return f"{self.email} - {self.otp}"


class CounselorProfile(models.Model):

    APPROVAL_CHOICES = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=255)
    phone = models.CharField(max_length=15, null=True)
    city = models.CharField(max_length=100, null=True)
    state = models.CharField(max_length=100, null=True)
    experience_years = models.IntegerField(null=True, default="hey")
    qualification = models.CharField(max_length=255, null=True, default="hey")
    specialization = models.CharField(max_length=255, null=True)
    bio = models.TextField(null=True)
    certificate_url = models.FileField(upload_to="certificates/", null=True, blank=True)
    approval_status = models.CharField(
        max_length=20, choices=APPROVAL_CHOICES, default="pending"
    )
    rejection_reason = models.TextField(blank=True, null=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    total_students = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    profile_photo = models.CharField(max_length=500, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


# students/models.py

from django.db import models


class StudentProfile(models.Model):

    GENDER_CHOICES = [
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
        ("prefer_not_to_say", "Prefer not to say"),
    ]

    EDUCATION_CHOICES = [
        ("class_9", "Class 9"),
        ("class_10", "Class 10"),
        ("class_11", "Class 11"),
        ("class_12", "Class 12"),
        ("graduate", "Graduate"),
        ("postgraduate", "Postgraduate"),
    ]

    STREAM_CHOICES = [
        ("science", "Science"),
        ("commerce", "Commerce"),
        ("arts", "Arts"),
        ("not_decided", "Not Decided"),
    ]

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="student_profile"
    )
    full_name = models.CharField(max_length=255)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(
        max_length=20, choices=GENDER_CHOICES, null=True, blank=True
    )
    phone = models.CharField(max_length=15, null=True, blank=True)
    profile_photo = models.CharField(max_length=500, null=True, blank=True)
    city = models.CharField(max_length=100, null=True, blank=True)
    state = models.CharField(max_length=100, null=True, blank=True)
    education_level = models.CharField(
        max_length=30, choices=EDUCATION_CHOICES, null=True, blank=True
    )
    stream = models.CharField(
        max_length=30, choices=STREAM_CHOICES, null=True, blank=True
    )
    is_onboarded = models.BooleanField(default=False)
    assessment_taken = models.BooleanField(default=False)
    roadmap_created = models.BooleanField(default=False)
    profile_completed = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.full_name} ({self.user.email})"
