from django.urls import path

from .views import CounselorProfileView


urlpatterns = [
    path("profile/", CounselorProfileView.as_view(), name="counselor-profile"),
]
