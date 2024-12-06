from django_filters import rest_framework as filters
from recipes.models import Ingredient, Recipe


class RecipeFilterSet(filters.FilterSet):
    """Фильтр по рецептов"""

    is_favorited = filters.BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_shopping_cart')
    author = filters.NumberFilter(field_name='author_id')
    tags = filters.AllValuesMultipleFilter(field_name='tags__slug')

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')

    def filter_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite_recipes__user=self.request.user)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_shopping_carts__user=self.request.user)
        return queryset


class IngredientFilterSet(filters.FilterSet):
    """Фильтр по ингридиентам"""

    class Meta:
        model = Ingredient
        fields = ('name', )
