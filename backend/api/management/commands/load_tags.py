import json

from api.models import Tag
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Импорт тегов'

    def handle(self, *args, **kwargs):
        file_path = settings.BASE_DIR / 'data' / 'tags.json'
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        Tag.objects.bulk_create((
            Tag(**item) for item in data),
            ignore_conflicts=True
        )
        self.stdout.write(self.style.SUCCESS('Теги успешно загружены!'))
