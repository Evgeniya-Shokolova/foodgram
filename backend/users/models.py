from api.constants import (MAX_LENGTH_FIRST_NAME, MAX_LENGTH_LAST_NAME,
                           MAX_LENGTH_USERNAME)
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.db import models


def user_avatar_path(instance, filename):
    """Возвращает путь для загрузки аватара пользователя."""
    return f'avatars/user_{instance.id}/{filename}'


class CustomUser(AbstractUser):
    """Модель пользователя"""
    username = models.CharField(
        'Имя пользователя',
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        validators=[UnicodeUsernameValidator()],
    )
    email = models.EmailField(
        unique=True,
        verbose_name='Электронная почта'
    )
    first_name = models.CharField(
        max_length=MAX_LENGTH_FIRST_NAME,
        verbose_name='Имя'
    )
    last_name = models.CharField(
        max_length=MAX_LENGTH_LAST_NAME,
        verbose_name='Фамилия'
    )
    avatar = models.ImageField(
        'Аватар',
        upload_to=user_avatar_path,
        blank=True,
        null=True
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username


class Follow(models.Model):
    """Модель подписок"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        ordering = ['user']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow_model'
            )
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
