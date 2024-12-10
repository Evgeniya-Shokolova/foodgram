import random
import string

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from users.models import CustomUser

from api.constants import (MAX_AMOUNT_INGR, MAX_COOKING_TIME,
                           MAX_LENGTH_INGRIDIENT_NAME,
                           MAX_LENGTH_MEASUREMENT_UNIT, MAX_LENGTH_RECIPE_NAME,
                           MAX_LENGTH_TAG_NAME, MIN_AMOUNT_INGR,
                           MIN_COOKING_TIME, MAX_LENGTH_SHORT_LINK)


class Tag(models.Model):
    """Модель для тегов"""
    name = models.CharField(
        verbose_name='Название тега',
        max_length=MAX_LENGTH_TAG_NAME,
        unique=True,
    )
    slug = models.SlugField(
        unique=True,
        max_length=MAX_LENGTH_TAG_NAME,
        verbose_name='Слаг тега',
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'

    def __str__(self):
        return f'Tag: {self.name} (Slug: {self.slug})'


class Ingredient(models.Model):
    """Модель для ингредиентов"""
    name = models.CharField(
        verbose_name='Название ингредиента',
        max_length=MAX_LENGTH_INGRIDIENT_NAME
    )
    measurement_unit = models.CharField(
        verbose_name='Единицы измерения ингредиента',
        max_length=MAX_LENGTH_MEASUREMENT_UNIT
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        unique_together = ('name', 'measurement_unit')

    def __str__(self):
        return f'{self.name} ({self.measurement_unit})'


class Recipe(models.Model):
    """Модель для рецептов"""
    author = models.ForeignKey(
        CustomUser,
        verbose_name='Автор рецепта',
        on_delete=models.CASCADE,
        related_name='recipes'
    )
    name = models.CharField(
        verbose_name='Название рецепта',
        max_length=MAX_LENGTH_RECIPE_NAME
    )
    image = models.ImageField(
        verbose_name='Картинка рецепта',
        upload_to='recipes/',
        help_text='Картинка вашего рецепта'
    )
    text = models.TextField(
        verbose_name='Текст рецепта',
        help_text='Описание рецепта'
    )
    ingredients = models.ManyToManyField(
        Ingredient,
        related_name='recipes',
        verbose_name='Ингредиенты рецепта',
        through='RecipeIngredient'
    )
    tags = models.ManyToManyField(
        Tag,
        related_name='recipes',
        verbose_name='Тэги рецепта'
    )
    cooking_time = models.PositiveSmallIntegerField(
        verbose_name='Время приготовления рецепта',
        validators=[
            MinValueValidator(MIN_COOKING_TIME,
                              message='Слишком быстро, '
                              'время приготовления должно быть больше'
                              f' - {MIN_COOKING_TIME}'),
            MaxValueValidator(MAX_COOKING_TIME,
                              message='Слишком долго, '
                              'время приготовления должно быть меньше'
                              f' - {MAX_COOKING_TIME}')
        ],

    )
    pub_date = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True
    )
    short_id = models.CharField(
        max_length=MAX_LENGTH_SHORT_LINK,
        unique=True,
        blank=True,
        help_text='Короткое значение ссылки рецепта'
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return f'Рецепт: {self.name} (Автор: {self.author})'

    def generate_short_id(self):
        """Создает случайную строку для short_id"""
        characters = string.ascii_letters + string.digits
        return ''.join(random.choices(characters, k=MAX_LENGTH_SHORT_LINK))

    def save(self, *args, **kwargs):
        """Генерируем short_id только при создании нового объекта"""
        if not self.short_id:
            self.short_id = self.generate_short_id()
            while Recipe.objects.filter(short_id=self.short_id).exists():
                self.short_id = self.generate_short_id()
        super().save(*args, **kwargs)


class RecipeIngredient(models.Model):
    """Модель ингредиентов для рецепта"""
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name='Название ингредиента',
        on_delete=models.CASCADE,
        related_name='ingredients_recipe'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
        related_name='recipe_ingredients'
    )
    amount = models.PositiveIntegerField(
        verbose_name='Количество ингредиента',
        validators=[
            MinValueValidator(MIN_AMOUNT_INGR,
                              message=f'Должно быть больше {MIN_AMOUNT_INGR}'),
            MaxValueValidator(MAX_AMOUNT_INGR,
                              message=f'Должно быть меньше {MAX_AMOUNT_INGR}')
        ],
    )

    class Meta:
        verbose_name = 'Ингредиент в рецептах с количеством'
        verbose_name_plural = 'Ингредиенты в рецептах с количеством'
        ordering = ('ingredient',)
        constraints = [
            models.UniqueConstraint(
                fields=['ingredient', 'recipe'],
                name='unique_ingredient_recipe'
            )
        ]

    def __str__(self):
        return (
            f'{self.ingredient.name} - {self.amount}'
            f'{self.ingredient.measurement_unit}'
        )


class FavoriteRecipe(models.Model):
    """Модель избранного рецепта"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name='Повар'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='favorite_recipes',
        verbose_name='Избранный рецепт',
    )

    class Meta:
        verbose_name = 'Избранный рецепт'
        verbose_name_plural = 'Избранные рецепты'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_favorite_model'
            )
        ]

    def __str__(self):
        return f'{self.user.username} добавил {self.recipe.name} в избранное'


class ShoppingList(models.Model):
    """Модель списка покупок"""
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='shopping_carts',
        verbose_name='Покупатель'
    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='in_shopping_carts',
        verbose_name='Рецепт для покупки'
    )

    class Meta:
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'
        ordering = ('user',)
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'recipe'],
                name='unique_shopping_list_model'
            )
        ]

    def __str__(self):
        return f'{self.recipe.name} в корзине у {self.user.username}'
