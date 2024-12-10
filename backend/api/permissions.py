from rest_framework.permissions import IsAuthenticatedOrReadOnly, SAFE_METHODS


class IsAuthorOrReadOnly(IsAuthenticatedOrReadOnly):
    """
    Кастомное разрешение, позволяющее управлять объектом
    только автору или предоставлять доступ на чтение.
    """

    def has_object_permission(self, request, view, obj):
        return (
            request.method in SAFE_METHODS or (
                request.user.is_authenticated and request.user == obj.author
            )
        )
