from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    message = 'Admin role required'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser or user.is_staff:
            return True
        profile = getattr(user, 'trainer_profile', None)
        return bool(profile and profile.role == 'admin')


class IsTrainerRole(BasePermission):
    message = 'Trainer role required'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        profile = getattr(user, 'trainer_profile', None)
        return bool(profile and profile.role == 'trainer')


class IsPlayerRole(BasePermission):
    message = 'Player role required'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        profile = getattr(user, 'trainer_profile', None)
        return bool(profile and profile.role == 'player')
