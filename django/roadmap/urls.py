from django.urls import path
from .views import GenerateRoadmapView, GetRoadmapView, MilestoneCompleteView 

urlpatterns = [
    path(
        "<int:assessment_id>/generate/",
        GenerateRoadmapView.as_view(),
        name="roadmap-generate",
    ),
    path("<int:assessment_id>/", GetRoadmapView.as_view(), name="roadmap-get"),
    path("milestone/<int:milestone_id>/complete/", MilestoneCompleteView.as_view()),
]
