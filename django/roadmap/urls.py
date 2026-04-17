from django.urls import path
from .views import (
    MilestoneCompleteView,
    CustomRoadmapView,
    RoadmapListView,
    RoadmapDetailView,
    GenerateRoadmapView,
    GetRoadmapView,
)

urlpatterns = [
    path(
        "<int:assessment_id>/generate/",
        GenerateRoadmapView.as_view(),
        name="roadmap-generate",
    ),
    path("<int:assessment_id>/", GetRoadmapView.as_view(), name="roadmap-get"),
    path("milestone/<int:milestone_id>/complete/", MilestoneCompleteView.as_view()),
    path(
        "<int:assessment_id>/custom/",
        CustomRoadmapView.as_view(),
        name="roadmap-custom-generate",
    ),
    path("history/", RoadmapListView.as_view(), name="roadmap-history"),
    path(
        "detail/<int:roadmap_id>/", RoadmapDetailView.as_view(), name="roadmap-detail"
    ),
]
