from rest_framework.permissions import SAFE_METHODS, BasePermission


class RoleBasedPermission(BasePermission):
    """
    Кастомное разрешение, позволяющее управлять объектом
    в зависимости от роли пользователя.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        if request.user.is_authenticated:
            return True
        return False

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if request.user.is_authenticated:
            if request.user.is_staff:
                return True
            if request.user == obj.author:
                return True
        return False
