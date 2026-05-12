from django.conf import settings
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
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="student_profile",
    )
    assigned_counselor = models.ForeignKey(
        "counselors.CounselorProfile",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="assigned_students",
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


class UserSkill(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="skills"
    )
    name = models.CharField(max_length=100)
    level = models.IntegerField(default=0)  # 0 to 100
    category = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - {self.name} ({self.level}%)"


class SkillRecommendation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="skill_recommendations",
    )
    skill_name = models.CharField(max_length=100)
    reason = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.email} - Recommend {self.skill_name}"

