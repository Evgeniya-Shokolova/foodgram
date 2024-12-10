from django.contrib import admin

from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingList,
    Tag,
)


class RecipeIngredientInline(admin.TabularInline):
    """Inline для ингредиентов в рецепте"""
    model = RecipeIngredient
    extra = 1
    min_num = 1
    verbose_name = 'Ингредиент'
    verbose_name_plural = 'Ингредиенты'


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    """Админка для рецептов с учетом ингредиентов и тегов"""
    list_display = ('id', 'name', 'author', 'cooking_time', 'pub_date')
    list_filter = ('author', 'tags')
    search_fields = ('name', 'author__username')
    inlines = (RecipeIngredientInline,)
    readonly_fields = ('pub_date',)
    save_on_top = True


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
