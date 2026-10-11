from django.db import models

# Create your models here.
from students.models import StudentProfile
from assessments.models import Assessment


class CareerRoadmap(models.Model):
    STATUS_CHOICES = [
        ("active", "Active"),
        ("completed", "Completed"),
        ("archived", "Archived"),
    ]

    student = models.ForeignKey(
        StudentProfile,
        on_delete=models.CASCADE,
        related_name="roadmaps",
    )
    assessment = models.ForeignKey(
        Assessment,
        on_delete=models.CASCADE,
        related_name="roadmaps",
        null=True,
        blank=True,
    )
    career_title = models.CharField(max_length=255)
    normalized_career_title = models.CharField(max_length=255, null=True, blank=True)
    title = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="active",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["student", "normalized_career_title"],
                name="unique_student_roadmap_title",
            )
        ]

    def __str__(self):
        return f"{self.student} → {self.career_title}"


class RoadmapMilestone(models.Model):
    roadmap = models.ForeignKey(
        CareerRoadmap,
        on_delete=models.CASCADE,
        related_name="milestones",
    )
    title = models.CharField(max_length=255, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    age_range = models.CharField(max_length=50, null=True, blank=True)
    duration = models.CharField(max_length=50, null=True, blank=True)
    skills_to_learn = models.JSONField(default=list)
    exams_to_take = models.JSONField(default=list)
    resources = models.JSONField(default=list)
    node_position = models.JSONField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    order_number = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order_number"]

    def __str__(self):
        return f"{self.roadmap.career_title} → {self.title}"
