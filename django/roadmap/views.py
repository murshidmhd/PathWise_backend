from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CareerRoadmapSerializer
from .services import RoadmapServiceError, generate_roadmap, get_roadmap
from django.utils import timezone
from .models import CareerRoadmap, RoadmapMilestone


class GenerateRoadmapView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assessment_id):
        try:
            roadmap = generate_roadmap(request.user, assessment_id)
        except RoadmapServiceError as exc:
            return Response(exc.detail, status=exc.status_code)

        return Response(CareerRoadmapSerializer(roadmap).data, status=201)


class GetRoadmapView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, assessment_id):
        try:
            roadmap = get_roadmap(request.user, assessment_id)
        except RoadmapServiceError as exc:
            return Response(exc.detail, status=exc.status_code)

        return Response(CareerRoadmapSerializer(roadmap).data)


class MilestoneCompleteView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, milestone_id):
        try:
            milestone = RoadmapMilestone.objects.get(
                id=milestone_id,
                roadmap__student__user=request.user,  # ownership check
            )
        except RoadmapMilestone.DoesNotExist:
            return Response({"detail": "Milestone not found."}, status=404)

        # Toggle
        milestone.is_completed = not milestone.is_completed
        milestone.completed_at = timezone.now() if milestone.is_completed else None
        milestone.save(update_fields=["is_completed", "completed_at"])

        return Response(
            {
                "id": milestone.id,
                "is_completed": milestone.is_completed,
                "completed_at": milestone.completed_at,
            }
        )


class CustomRoadmapView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assessment_id=None):
        career_title = request.data.get("career_title")

        if not career_title:
            return Response({"detail": "Career title is required."}, status=400)

            

        try:
            roadmap = generate_roadmap(
                request.user,
                assessment_id=assessment_id,
                custom_career_title=career_title,
            )
        except RoadmapServiceError as exc:
            return Response(exc.detail, status=exc.status_code)

        return Response(CareerRoadmapSerializer(roadmap).data, status=201)


class RoadmapListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        roadmaps = CareerRoadmap.objects.filter(student__user=request.user).order_by(
            "-created_at"
        )
        serializer = CareerRoadmapSerializer(roadmaps, many=True)
        return Response(serializer.data)


class RoadmapDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, roadmap_id):
        try:
            roadmap = CareerRoadmap.objects.prefetch_related("milestones").get(
                id=roadmap_id, student__user=request.user
            )
        except CareerRoadmap.DoesNotExist:
            return Response({"detail": "Roadmap not found."}, status=404)

        return Response(CareerRoadmapSerializer(roadmap).data)
