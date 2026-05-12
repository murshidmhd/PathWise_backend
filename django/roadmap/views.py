from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import CareerRoadmapSerializer
from .services import RoadmapServiceError, generate_roadmap, get_roadmap
from django.utils import timezone
from .models import CareerRoadmap, RoadmapMilestone
from payments.services import PointService


class GenerateRoadmapView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, assessment_id):
        # Charge 1 SkillPoint
        success, balance = PointService.spend_points(
            user=request.user,
            amount=1,
            description=f"Generated AI Roadmap for Assessment #{assessment_id}",
        )

        if not success:
            return Response(
                {
                    "detail": "Insufficient SkillPoints. Please top up your wallet.",
                    "balance": balance,
                },
                status=402,
            )  # 402 Payment Required

        try:
            roadmap = generate_roadmap(request.user, assessment_id)
            
            # NOTIFY STUDENT
            try:
                from notifications.utils import send_notification
                send_notification(
                    user_id=request.user.id,
                    title="Roadmap Ready! 🚀",
                    message=f"Your AI-generated career roadmap for {roadmap.career_title} is complete. Start exploring your milestones!",
                    notification_type="system",
                    data={"roadmap_id": roadmap.id}
                )
            except Exception as e:
                print(f"DEBUG: Roadmap notification failed: {e}")
                
        except RoadmapServiceError as exc:
            # Optional: Refund if generation fails
            PointService.add_points(
                request.user,
                1,
                "REFUND",
                f"Refund for failed roadmap generation (#{assessment_id})",
            )
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

        # Charge 1 SkillPoint
        success, balance = PointService.spend_points(
            user=request.user,
            amount=1,
            description=f"Generated Custom Roadmap: {career_title}",
        )

        if not success:
            return Response(
                {
                    "detail": "Insufficient SkillPoints. Please top up your wallet.",
                    "balance": balance,
                },
                status=402,
            )

        try:
            roadmap = generate_roadmap(
                request.user,
                assessment_id=assessment_id,
                custom_career_title=career_title,
            )

            # NOTIFY STUDENT
            try:
                from notifications.utils import send_notification
                send_notification(
                    user_id=request.user.id,
                    title="Custom Roadmap Ready! ✨",
                    message=f"Your custom career roadmap for {career_title} has been generated successfully.",
                    notification_type="system",
                    data={"roadmap_id": roadmap.id}
                )
            except Exception as e:
                print(f"DEBUG: Custom Roadmap notification failed: {e}")

        except RoadmapServiceError as exc:
            # Refund if fails
            PointService.add_points(
                request.user,
                1,
                "REFUND",
                f"Refund for failed custom roadmap: {career_title}",
            )
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
