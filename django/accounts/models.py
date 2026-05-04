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
        extra_fields.setdefault("role", "platform_admin")  # ← CHANGED
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_verified", True)
        extra_fields.setdefault("is_approved", True)  # ← ADDED

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    ROLE_CHOICES = [
        ("student", "Student"),
        ("counselor", "Counselor"),
        ("admin", "Admin"),
        ("platform_admin", "Platform Admin"),  # ← ADDED
    ]

    username = None
    email = models.EmailField(unique=True)
    objects = UserManager()

    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)

    google_id = models.CharField(max_length=255, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]
    # this is basically when we create the super user that time its ask for the this two filds also

    def __str__(self):
        return self.email

    @property
    def is_platform_admin(self):
        return self.role == "platform_admin"

    @property
    def is_tenant_admin(self):
        return self.role == "admin"
