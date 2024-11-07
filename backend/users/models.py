import base64
import re

from django.core.files.base import ContentFile
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError

from api.constants import (
    MAX_LENGTH_EMAIL, MAX_LENGTH_FIRST_NAME,
    MAX_LENGTH_LAST_NAME, MAX_LENGTH_USERNAME,
    VALID_USERNAME_REGEX
    )


def user_avatar_path(instance, filename):
    """Возвращает путь для загрузки аватара пользователя."""
    return f'avatars/user_{instance.id}/{filename}'


def validate_username(value):
    """
    Функция для проверки корректности имени пользователя.
    Запрещает использовать "me", и спец. символы, отличные от разрешенных.
    """
    if value.lower() == 'me':
        raise ValidationError(
            'Использование "me" в качестве имени пользователя запрещено.',
            code='invalid_username')

    invalid_chars = re.sub(VALID_USERNAME_REGEX, '', value)

    if invalid_chars:
        raise ValidationError(
            f'Имя пользователя содержит недопустимые символы: {invalid_chars}.'
            'Разрешены только буквы, цифры, и символы @/./+/-/_',
            code='invalid_characters'
        )


class CustomUser(AbstractUser):
    """Модель пользователя"""
    username = models.CharField(
        'Имя пользователя',
        max_length=MAX_LENGTH_USERNAME,
        unique=True,
        validators=[validate_username],
    )
    email = models.EmailField(
        max_length=MAX_LENGTH_EMAIL,
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
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"

    def __str__(self):
        return self.username

    def set_avatar(self, base64_data):
        """
        Устанавливает аватар из строки Base64.
        """
        if base64_data.startswith('data:image/jpeg;base64,'):
            suffix, base64_data = 'jpg', base64_data.split(',')[1]
        elif base64_data.startswith('data:image/png;base64,'):
            suffix, base64_data = 'png', base64_data.split(',')[1]
        else:
            raise ValidationError('Неподдерживаемый формат изображения.')

        image_data = base64.b64decode(base64_data)
        image_file = ContentFile(image_data, name=f'avatar.{suffix}')

        self.avatar.save(f'avatar.{suffix}', image_file, save=True)


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
        verbose_name = "Подписка"
        verbose_name_plural = "Подписки"
        ordering = ['user']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_follow_model'
            )
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
