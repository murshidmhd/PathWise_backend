from rest_framework.permissions import BasePermission


class IsCounselorUserRole(BasePermission):
    message = "Only counselor users can access this endpoint."

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.role == "counselor")
