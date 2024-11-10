import re
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from rest_framework.response import Response
from django.contrib.auth.password_validation import (
    validate_password,
    ValidationError
    )

from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers, status

from api.constants import MAX_LENGTH_EMAIL, MAX_LENGTH_USERNAME
from .models import Recipe, Tag, Ingredient, RecipeIngredient, CustomUser, FavoriteRecipe, ShoppingList


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор аватара."""
    avatar = Base64ImageField()

    class Meta:
        model = CustomUser
        fields = ('avatar',)


class ImageSerializer(serializers.ModelSerializer):
    """Сериализатор картинки рецепта."""
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'tags', 'cooking_time')


class SignUpUserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=MAX_LENGTH_EMAIL,
        required=True
    )
    username = serializers.CharField(
        max_length=MAX_LENGTH_USERNAME,
        required=True
    )
    password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def validate(self, attrs):
        """
        Проверяет уникальность имени пользователя и адреса электронной почты.
        """
        username = attrs.get('username')
        email = attrs.get('email')

        if not re.match(r'^[\w.@+-]+$', username):
            raise serializers.ValidationError('Имя пользователя может содержать только буквы, цифры и символы @/./+/-/_.')

        if username == 'me' and 'username':
            raise serializers.ValidationError('Недопустимое имя пользователя!')

        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                'Это имя пользователя уже кому-то принадлежит!'
            )

        if CustomUser.objects.filter(email=email).exists():
            raise serializers.ValidationError('Этот email уже занят!')

        return attrs

    def create(self, validated_data):
        """Создает нового пользователя с заданными данными и паролем."""
        password = validated_data.pop('password', None)
        user_instance = self.Meta.model(**validated_data)

        if password:
            user_instance.set_password(password)
        user_instance.save()

        return user_instance


class UserSerializer(serializers.ModelSerializer):
    """Сериализатор для пользователей."""

    avatar = Base64ImageField(required=False, allow_null=True)
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed'
        )

    def get_is_subscribed(self, user):
        """
        Определяет подписан ли текущий пользователь на данного пользователя.
        """
        current_user = self.context.get('request').user
        return (
            current_user.is_authenticated and
            user.following.filter(user=current_user).exists()
        ) if current_user else False


class FollowerSerializer(UserSerializer):
    """Сериализатор для отображения информации о пользователе и его рецептах."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count',
        )

    def get_recipes(self, user_instance):
        """Получение списка рецептов, созданных пользователем."""
        recipes_queryset = user_instance.recipes.all()
        recipe_serializer = RecipeSerializer(recipes_queryset, many=True)
        return recipe_serializer.data

    def get_recipes_count(self, user_instance):
        """Возвращает общее количество рецептов, созданных пользователем."""
        return user_instance.recipes.count()


class PasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля пользователя."""
    new_password = serializers.CharField(max_length=150)
    current_password = serializers.CharField(max_length=150)

    def validate_new_password(self, value):
        """Валидация нового пароля, проверка его соответствия требованиям."""
        try:
            validate_password(value)
        except ValidationError as e:
            raise serializers.ValidationError({'new_password': list(e.messages)})
        return value

    def validate(self, attrs):
        """Проверка, что новый пароль отличается от текущего."""
        if attrs['current_password'] == attrs['new_password']:
            raise serializers.ValidationError(
                {'new_password': 'Новый пароль должен отличаться от текущего.'}
                )
        return attrs

    def update(self, instance, validated_data):
        """Обновление пароля пользователя."""
        if not instance.check_password(validated_data['current_password']):
            raise serializers.ValidationError(
                {'current_password': 'Неправильный пароль.'}
                )

        instance.set_password(validated_data['new_password'])
        instance.save()
        return validated_data


class TagSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения информации о теге."""
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Ingredient.
    """

    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')

    def validate_quantity(self, value):
        if value < 1:
            raise serializers.ValidationError("Количество ингредиента должно быть положительным числом.")
        return value


class IngredientCreateSerializer(serializers.ModelSerializer):
    """Серилизатор для добавления ингридиентов"""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения списка рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeAmountIngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображении информации об ингредиентах.
    """
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
        )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Количество должно быть положительным числом.")
        return value


class DetailedRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подробной информации о рецепте."""
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField(required=False)
    author = UserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = RecipeAmountIngredientSerializer(many=True, read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'tags',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time',
        )

    def get_is_favorited(self, obj):
        return self.get_chosen_recipe(obj, FavoriteRecipe)

    def get_is_in_shopping_cart(self, obj):
        return self.get_chosen_recipe(obj, ShoppingList)


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""
    ingredients = IngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
            many=True,
            queryset=Tag.objects.all()
        )
    image = Base64ImageField(required=True)
    author = UserSerializer(read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'image', 'text', 'ingredients', 'author',
            'tags', 'cooking_time', 'is_favorited', 'is_in_shopping_cart'
        )

    def validate(self, data):
        required_fields = ['name', 'ingredients', 'cooking_time', 'tags']
        for field in required_fields:
            if field not in data or not data[field]:
                raise serializers.ValidationError(f"{field} требуется.")

        if 'image' not in data or not data['image']:
            raise serializers.ValidationError("Поле 'image' обязательно для заполнения.")

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError("Рецепт должен содержать хотя бы один ингредиент.")

        ingredient_ids = []
        for ingredient in value:
            if ingredient['amount'] < 1:
                raise serializers.ValidationError("Количество ингредиента должно быть не менее 1.")

            if ingredient['id'] in ingredient_ids:
                raise serializers.ValidationError("Ингредиенты не должны повторяться.")

            ingredient_ids.append(ingredient['id'])

        return value

    def validate_tags(self, value):
        if not value:
            raise serializers.ValidationError("Рецепт должен содержать хотя бы один тег.")

        tag_ids = []
        for tag in value:
            if tag in tag_ids:
                raise serializers.ValidationError("Теги не должны повторяться.")
            tag_ids.append(tag)
        if not value:
            raise serializers.ValidationError("Рецепт должен содержать хотя бы один тег.")

        return value

    def create(self, validated_data):
        """Создание рецепта."""
        ingredients = validated_data.pop('ingredients')
        tags = validated_data.pop('tags')
        recipe = Recipe.objects.create(**validated_data)
        self.update_or_create_ingredient(recipe=recipe, ingredients=ingredients)
        recipe.tags.set(tags)
        return recipe

    def __create_tags(self, tags, recipe):
        """Метод добавления тега"""
        recipe.tags.set(tags)

    def update(self, instance, validated_data):
        """Метод обновления рецепта"""
        ingredients = validated_data.pop('ingredients', None)
        tags = validated_data.pop('tags', None)

        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.image = validated_data.get('image', instance.image)
        instance.cooking_time = validated_data.get('cooking_time', instance.cooking_time)
        instance.save()

        if tags is not None:
            self.__create_tags(tags, instance)

        if ingredients is not None:
            self._update_ingredients(ingredients, instance)

        return instance

    def _update_ingredients(self, ingredient_data_list, recipe_instance):
        """Обновление объектов ингредиентов и связывание их с рецептом."""
        RecipeIngredient.objects.filter(recipe=recipe_instance).delete()
        self.update_or_create_ingredient(recipe_instance, ingredient_data_list)

    def update_or_create_ingredient(self, recipe, ingredients) -> None:
        recipe.ingredients.clear()
        ingredient_list = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            ) for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(ingredient_list)

    def get_chosen_recipe(self, obj, model) -> bool:
        """Метод получения статуса выбранного рецепта для избранного и списка покупок."""
        user = self.context['request'].user
        if user.is_anonymous:
            return False
        return model.objects.filter(user=user, recipe=obj).exists()

    def get_is_favorited(self, obj):
        """Узнать, является ли рецепт избранным."""
        return self.get_chosen_recipe(obj, FavoriteRecipe)

    def get_is_in_shopping_cart(self, obj):
        """Узнать, находится ли рецепт в списке покупок."""
        return self.get_chosen_recipe(obj, ShoppingList)
