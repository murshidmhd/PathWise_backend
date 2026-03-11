from django.urls import path

from .views import StudentProfileMeView


urlpatterns = [
    path("me/", StudentProfileMeView.as_view(), name="student-profile-me"),
]
