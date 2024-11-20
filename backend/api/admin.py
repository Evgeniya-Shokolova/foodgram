from django.contrib import admin

from api.models import (
    Recipe, Tag, Ingredient,
    ShoppingList, FavoriteRecipe
)

@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):

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
        return obj.favorite_recipes.count() > 0


@admin.register(FavoriteRecipe)
class FavoriteRecipeAdmin(admin.ModelAdmin):

    list_display = ('user', 'recipe')
    search_fields = ('user__username', 'recipe__name')


@admin.register(ShoppingList)
class ShoppingListAdmin(admin.ModelAdmin):

    list_display = ('user', 'recipe')


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):

    list_display = ('name', 'slug')
    search_fields = ('name',)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    
    list_display = ('name', 'measurement_unit')
    search_fields = ('name',)
