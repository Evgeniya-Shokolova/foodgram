from django.contrib import admin

from .models import (FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
                     ShoppingList, Tag)


class RecipeIngredientInline(admin.TabularInline):
    """Inline для ингредиентов в рецепте"""
    model = RecipeIngredient
    extra = 1
    min_num = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


class RecipeTagInline(admin.TabularInline):
    """Inline для тегов"""
    model = Recipe.tags.through
    extra = 0
    verbose_name = 'Тег'
    verbose_name_plural = 'Теги'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов с учетом ингредиентов и тегов"""
    list_display = ('id', 'name', 'author', 'cooking_time', 'pub_date')
    list_filter = ('author', 'tags')
    search_fields = ('name', 'author__username')
    inlines = (RecipeIngredientInline, RecipeTagInline)
    readonly_fields = ('pub_date',)
    save_on_top = True

    def get_inline_instances(self, request, obj=None):
        """Проверяем доступность инлайнов и переопределяем их"""
        inlines = super().get_inline_instances(request, obj)
        return [inline for inline in inlines]


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):
    """
    Интерфейс администратора для управления экземплярами модели FavoriteRecipe.
    """

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):
    """
    Интерфейс администратора для управления экземплярами модели ShoppingList.
    """

    list_display = ('user', 'recipe')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """
    Интерфейс администратора для управления экземплярами модели Tag.
    """

    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    """
    Интерфейс администратора для управления экземплярами модели Ingredient.
    """

    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
