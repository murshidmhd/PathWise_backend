from rest_framework.permissions import BasePermission


class IsAdminUserRole(BasePermission):
    message = "Only admin users can access this endpoint."

    def has_permission(self, request, view):
        user = request.user
        return bool(
            user
            and user.is_authenticated
            and (user.role == "admin" or user.is_staff or user.is_superuser)
        )

