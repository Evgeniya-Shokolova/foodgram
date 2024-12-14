from django.shortcuts import get_object_or_404, redirect

from recipes.models import Recipe


def redirect_to_recipe_view(request, short_id):
    """Перенаправляет на страницу рецепта по короткому ID."""
    recipe = get_object_or_404(Recipe, short_id=short_id)
    return redirect(f'/recipes/{recipe.id}/')
