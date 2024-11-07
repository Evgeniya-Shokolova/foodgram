import base64

from django.core.exceptions import ValidationError as DjangoValidationError
from django.core.files.base import ContentFile
from django.shortcuts import get_object_or_404
from django.contrib.auth.password_validation import (
    validate_password,
    ValidationError
    )

from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers

from api.constants import MAX_LENGTH_EMAIL, MAX_LENGTH_USERNAME
from api.models import Recipe, Tag, Ingredient, RecipeIngredient
from users.models import CustomUser


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            format, imgstr = data.split(';base64,')
            ext = format.split('/')[-1]
            data = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)

        return super().to_internal_value(data)


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор аватара."""
    avatar = Base64ImageField()

    class Meta:
        model = CustomUser
        fields = ('avatar',)


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

        if username == 'me':
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
        """Получение рецептов пользователя."""
        recipes_queryset = user_instance.recipes.all()
        recipe_serializer = BriefRecipeSerializer(recipes_queryset, many=True)
        return recipe_serializer.data

    def get_recipes_count(self, user_instance):
        """Возвращает общее количество рецептов пользователя."""
        return user_instance.recipes.count()


class PasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(max_length=150)
    current_password = serializers.CharField(max_length=150)

    def validate_new_password(self, value):
        """Валидация нового пароля."""
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
    class Meta:
        model = Tag
        fields = ('id', 'name', 'slug')


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class DetailedAmountIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name')
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit'
        )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


class BasicAmountIngredientSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')


class BriefRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения основного списка рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class DetailedRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подробной информации о рецепте."""
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()
    author = UserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = DetailedAmountIngredientSerializer(read_only=True, many=True)

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

    def get_is_favorited(self, recipe_instance):
        """Проверка, находится ли рецепт в избранном у пользователя."""
        return self._is_recipe_in_user_list(recipe_instance, 'favorite_recipes')

    def get_is_in_shopping_cart(self, recipe_instance):
        """Проверка, находится ли рецепт в корзине у пользователя."""
        return self._is_recipe_in_user_list(
            recipe_instance, 'shopping_list_recipes'
            )

    def _is_recipe_in_user_list(self, recipe_instance, list_attr):
        """Находится ли рецепт в списке пользователя."""
        user = self.context['request'].user
        return user.is_authenticated and getattr(
            recipe_instance, list_attr
            ).filter(user=user).exists()


class RecipeEntrySerializer(DetailedRecipeSerializer):
    """Сериализатор для создания и обновления рецептов."""
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    ingredients = BasicAmountIngredientSerializer(many=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'tags', 'author', 'ingredients',
            'is_favorited', 'is_in_shopping_cart', 'name',
            'image', 'text', 'cooking_time',
        )

    def process_validated_data(self, validated_data):
        """Разбивка входных данных на теги и ингредиенты."""
        tags_list = validated_data.pop('tags')
        ingredient_data_list = validated_data.pop('ingredients')

        ingredient_objs = self._get_ingredients(ingredient_data_list)

        return tags_list, ingredient_objs

    def _get_ingredients(self, ingredient_data_list):
        """Получение объектов ингредиентов."""
        ingredient_objs = []
        for ingredient_data in ingredient_data_list:
            ingredient_instance = get_object_or_404(
                Ingredient, pk=ingredient_data['id']
                )
            ingred_obj, created = RecipeIngredient.objects.get_or_create(
                ingredient=ingredient_instance,
                amount=ingredient_data['amount']
            )
            ingredient_objs.append(ingred_obj)
        return ingredient_objs

    def create(self, validated_data):
        """Создание нового рецепта."""
        return self._save_recipe(validated_data)

    def update(self, recipe_instance, validated_data):
        """Обновление существующего рецепта."""
        super().update(recipe_instance, validated_data)
        return self._save_recipe(validated_data, recipe_instance)

    def _save_recipe(self, validated_data, recipe_instance=None):
        """Сохранение рецепта, используя переданные данные."""
        author = self.context['request'].user
        tags_list, ingred_objs = self.process_validated_data(validated_data)

        if recipe_instance:
            recipe_instance = super().update(recipe_instance, validated_data)
        else:
            recipe_instance = Recipe.objects.create(
                author=author, **validated_data
                )

        recipe_instance.tags.set(tags_list)
        recipe_instance.ingredients.set(ingred_objs)

        return recipe_instance
