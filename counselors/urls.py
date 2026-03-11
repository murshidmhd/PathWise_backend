from django.urls import path

from .views import CounselorProfileMeView


urlpatterns = [
    path("me/", CounselorProfileMeView.as_view(), name="counselor-profile-me"),
]
