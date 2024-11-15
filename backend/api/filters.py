from django_filters import rest_framework as filters
from api.models import Recipe, Ingredient, Tag


class RecipeFilterSet(filters.FilterSet):
    is_favorited = filters.BooleanFilter(method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(method='filter_shopping_cart')
    author = filters.NumberFilter(field_name='author_id')
    tags = filters.ModelMultipleChoiceFilter(field_name='tags__slug', queryset=Tag.objects.all(), to_field_name='slug')

    class Meta:
        model = Recipe
        fields = ('is_favorited', 'is_in_shopping_cart', 'author', 'tags')

    def filter_favorited(self, queryset, name, value):
        """Фильтруйте рецепты на основе того, добавлены ли они в избранное пользователем."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorite_recipes__user=self.request.user)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        """Фильтруйте рецепты на основе того, находятся ли они в корзине покупок пользователя."""
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_shopping_carts__user=self.request.user)
        return queryset


class IngredientFilterSet(filters.FilterSet):
    """Фильтр по ингридиентам"""
    class Meta:
        model = Ingredient
        fields = ('name', )


class TagFilterSet(filters.FilterSet):
    """Фильтр по тегам"""
    class Meta:
        model = Tag
        fields = ['name']

    def filter_favorited(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(favorited_by=self.request.user)
        return queryset

    def filter_shopping_cart(self, queryset, name, value):
        if value and self.request.user.is_authenticated:
            return queryset.filter(in_carts=self.request.user)
        return queryset
