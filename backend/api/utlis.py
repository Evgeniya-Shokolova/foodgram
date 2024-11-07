from django.http import HttpResponse, JsonResponse
from django.db.models import Sum
from collections import defaultdict
from api.models import Ingredient, Recipe

def shopping_list(user, format='text'):
    """Функция скачивания списка ингредиентов в различных форматах."""

    ingredients = Ingredient.objects.filter(recipe__shopping_list__user=user) \
        .values('ingredient__name', 'ingredient__measurement_unit', 'recipe__name') \
        .annotate(total_amount=Sum('amount'))

    grouped_ingredients = defaultdict(lambda: defaultdict(lambda: defaultdict(int)))


    for item in ingredients:
        recipe_name = item['recipe__name']
        ingredient_name = item['ingredient__name']
        measurement_unit = item['ingredient__measurement_unit']
        total_amount = item['total_amount']

        grouped_ingredients[recipe_name][ingredient_name]['amount'] += total_amount
        grouped_ingredients[recipe_name][ingredient_name]['unit'] = measurement_unit

    if format == 'json':
        return JsonResponse(grouped_ingredients)

    text_shop_list = 'Список покупок:\n\n'
    for recipe_name, ingredients in grouped_ingredients.items():
        text_shop_list += f'Рецепт: {recipe_name}\n'
        for ingredient, details in ingredients.items():
            text_shop_list += f'{ingredient} - {details["amount"]} {details["unit"]}\n'
        text_shop_list += '\n'

    response = HttpResponse(text_shop_list, content_type='text/plain')
    response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'

    return response
