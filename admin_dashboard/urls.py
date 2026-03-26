from django.urls import path

from .views import (
    AdminUserListView,
    PendingCounselorApprovalListView,
    AdminApprovalListView,
    AdminAssignCounselorView,
    ApproveCounselorView,
    RejectCounselorView,
)


urlpatterns = [
    path("users/", AdminUserListView.as_view(), name="admin-user-list"),
    path(
        "counselors/pending/",
        PendingCounselorApprovalListView.as_view(),
        name="admin-pending-counselors",
    ),
    path("approvals/", AdminApprovalListView.as_view()),
    # urls.py
    path("approvals/<int:pk>/approve/", ApproveCounselorView.as_view()),
    path("approvals/<int:pk>/reject/", RejectCounselorView.as_view()),
    path(
        "students/<int:student_id>/assign-counselor/",
        AdminAssignCounselorView.as_view(),
        name="admin-assign-counselor",
    ),
]
