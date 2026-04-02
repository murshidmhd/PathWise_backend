from django.urls import path

from .views import StudentProfileTrackingView, StudentProfileView

urlpatterns = [
    path("profile/", StudentProfileView.as_view(), name="student-profile"),
    path("tracking/", StudentProfileTrackingView.as_view(), name="student-tracking"),
]
