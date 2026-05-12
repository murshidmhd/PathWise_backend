from django.urls import path

from .views import (
    CounselorAssignedStudentDetailView,
    CounselorAssignedStudentListView,
    CounselorProfileView,
    CounselorReviewListView,
    CounselorReviewView,
    AvailableCounselorListView,
    CounselorRequestView,
    CounselorFilterOptionsView,
    ToggleFavoriteCounselorView,
    FavoriteCounselorListView,
)


urlpatterns = [
    path("filter-options/", CounselorFilterOptionsView.as_view(), name="filter-options"),
    path("profile/", CounselorProfileView.as_view(), name="counselor-profile"),
    path(
        "reviews/<int:counselor_id>/",
        CounselorReviewListView.as_view(),
        name="counselor-review-list",
    ),
    path(
        "rate/<int:counselor_id>/",
        CounselorReviewView.as_view(),
        name="counselor-rate",
    ),
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
    path(
        "available/",
        AvailableCounselorListView.as_view(),
        name="available-counselors",
    ),
    path(
        "request/",
        CounselorRequestView.as_view(),
        name="counselor-request",
    ),
    path("favorites/", FavoriteCounselorListView.as_view(), name="favorite-list"),
    path(
        "<int:counselor_id>/favorite/",
        ToggleFavoriteCounselorView.as_view(),
        name="toggle-favorite",
    ),
]
