from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from users.models import CustomUser, Follow


@admin.register(CustomUser)
class UserAdmin(UserAdmin):
    """
    Интерфейс администратора для управления экземплярами модели CustomUser.
    """
    list_display = (
        'username',
        'first_name',
        'last_name',
        'email',
        'avatar'
    )
    list_filter = ('email', 'username')
    search_fields = ('username',)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """
    Интерфейс администратора для управления экземплярами модели Follow.
    """
    list_display = (
        'user',
        'author'
    )
    list_filter = ('user', 'author')
    search_fields = ('user',)
