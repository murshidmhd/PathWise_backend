from django.urls import path

from .views import (
    AssessmentQuestionsView,
    AssessmentReportView,
    LatestAssessmentView,
    StartAssessmentView,
    SubmitAssessmentView,
)


urlpatterns = [
    path("questions/", AssessmentQuestionsView.as_view(), name="assessment-questions"),
    path("start/", StartAssessmentView.as_view(), name="assessment-start"),
    path("<int:assessment_id>/submit/", SubmitAssessmentView.as_view(), name="assessment-submit"),
    path("latest/", LatestAssessmentView.as_view(), name="assessment-latest"),
    path("<int:assessment_id>/report/", AssessmentReportView.as_view(), name="assessment-report"),
]
