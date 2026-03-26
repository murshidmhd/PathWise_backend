from django.urls import path

from .views import (
    CounselorAssignedStudentDetailView,
    CounselorAssignedStudentListView,
    CounselorProfileView,
)


urlpatterns = [
    path("profile/", CounselorProfileView.as_view(), name="counselor-profile"),
    path(
        "students/",
        CounselorAssignedStudentListView.as_view(),
        name="counselor-student-list",
    ),
    path(
        "students/<int:student_id>/",
        CounselorAssignedStudentDetailView.as_view(),
        name="counselor-student-detail",
    ),
]
