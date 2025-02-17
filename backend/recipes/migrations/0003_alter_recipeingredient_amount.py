# Generated by Django 3.2.3 on 2024-12-14 21:03

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('recipes', '0002_recipe_short_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='recipeingredient',
            name='amount',
            field=models.PositiveIntegerField(validators=[django.core.validators.MinValueValidator(1, message='Должно быть больше 1'), django.core.validators.MaxValueValidator(32000, message='Должно быть меньше 32000')], verbose_name='Количество ингредиента'),
        ),
    ]
