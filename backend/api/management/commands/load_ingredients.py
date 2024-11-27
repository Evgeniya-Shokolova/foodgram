import json
import os

from api.models import Ingredient
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Импорт ингредиентов'

    def handle(self, *args, **kwargs):
        json_file_path = os.path.join(
            settings.BASE_DIR, 'data', 'ingredients.json'
        )
        try:
            with open(json_file_path, 'r', encoding='utf-8') as json_file:
                ingredients = json.load(json_file)
                for ingredient in ingredients:
                    Ingredient.objects.create(**ingredient)
            self.stdout.write(self.style.SUCCESS(
                'Ингредиенты успешно импортированы!'
            ))
        except Exception as error:
            self.stderr.write(self.style.ERROR(
                f'Ошибка при импорте ингредиентов: {error}'
            ))
