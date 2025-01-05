# permissions.py
from rest_framework import permissions

class IsDriver(permissions.BasePermission):
    message = "Seuls les chauffeurs ont accès à cette ressource."

    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            request.user.user_type == 'DRIVER'
        )