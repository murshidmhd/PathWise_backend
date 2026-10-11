from rest_framework import serializers
from .models import CareerRoadmap, RoadmapMilestone


class RoadmapMilestoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoadmapMilestone
        fields = [
            "id",
            "title",
            "description",
            "age_range",
            "duration",
            "skills_to_learn",
            "exams_to_take",
            "resources",
            "node_position",
            "is_completed",
            "completed_at",  # ← add this
            "order_number",
        ]


class CareerRoadmapSerializer(serializers.ModelSerializer):
    milestones = RoadmapMilestoneSerializer(many=True, read_only=True)

    class Meta:
        model = CareerRoadmap
        fields = [
            "id",
            "career_title",
            "title",
            "status",
            "milestones",
            "created_at",
        ]


# serializers.py
class MilestoneCompleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoadmapMilestone
        fields = ["id", "is_completed", "completed_at"]
        read_only_fields = ["completed_at"]
