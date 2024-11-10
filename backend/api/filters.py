from django_filters import rest_framework as filters
from rest_framework.filters import SearchFilter
from .models import Recipe


class RecipeFilterSet(filters.FilterSet):
    """Фильтр по рецептам"""
    is_favorited = filters.BooleanFilter(field_name='favorited_by', method='filter_favorited')
    is_in_shopping_cart = filters.BooleanFilter(field_name='in_carts', method='filter_in_cart')
    author = filters.NumberFilter(field_name='author_id')
    tags = filters.CharFilter(field_name='tags__slug', lookup_expr='in')

    class Meta:
        model = Recipe
        fields = ['is_favorited', 'is_in_shopping_cart', 'author', 'tags']

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)

    def filter_favorited(self, queryset, name, value):
        if value and self.request:
            return queryset.filter(favorited_by=self.request.user)
        return queryset

    def filter_in_cart(self, queryset, name, value):
        if value and self.request:
            return queryset.filter(in_carts=self.request.user)
        return queryset

class IngredientFilter(SearchFilter):
    """Фильтр по ингридиентам"""
    search_param = 'name'

