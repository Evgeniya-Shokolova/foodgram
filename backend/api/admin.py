from django.contrib import admin

from .models import FavoriteRecipe, Ingredient, Recipe, ShoppingList, Tag


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """
    Интерфейс администратора для управления экземплярами модели Recipe.
    """

    list_display = (
        'author',
        'name',
        'cooking_time',
        'is_favorite',
        'pub_date',
    )
    search_fields = ('name', 'author__username')
    list_filter = ('pub_date', 'tags',)

    def is_favorite(self, obj):
        """
        Определяет, отмечен ли данный рецепт как любимый.
        """
        return obj.favorite_recipes.count() > 0


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
