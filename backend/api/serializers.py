import re

from django.contrib.auth.password_validation import (ValidationError,
                                                     validate_password)
from drf_extra_fields.fields import Base64ImageField
from rest_framework import serializers
from users.models import CustomUser, Follow

from .constants import MAX_LENGTH_EMAIL, MAX_LENGTH_USERNAME
from .models import (FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
                     ShoppingList, Tag)


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
    """Регистрация нового пользователя"""

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
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )

    def validate(self, user_data):
        """
        Проверяет уникальность имени пользователя и адреса электронной почты.
        """
        username = user_data.get('username')
        email_address = user_data.get('email')

        if not re.match(r'^[\w.@+-]+$', username):
            raise serializers.ValidationError(
                'Имя пользователя должно содержать только буквы,'
                'цифры и символы @/./+/-/_.'
            )

        if username.lower() == 'me':
            raise serializers.ValidationError('Недопустимое имя пользователя!')

        if CustomUser.objects.filter(username=username).exists():
            raise serializers.ValidationError(
                'Это имя пользователя уже используется.'
            )

        if CustomUser.objects.filter(email=email_address).exists():
            raise serializers.ValidationError(
                'Этот email уже зарегистрирован.'
            )

        return user_data

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
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
        )

    def get_is_subscribed(self, user):
        """
        Определяет подписан ли текущий пользователь на данного пользователя.
        """
        request = self.context.get('request')
        if request is not None:
            current_user = request.user
            return (
                current_user.is_authenticated and user.following.filter
                (user=current_user).exists()
            )
        return False


class FollowerSerializer(UserSerializer):
    """
    Сериализатор для отображения информации
    о пподписчике и его рецептах.
    """
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'email',
            'is_subscribed',
            'avatar',
            'recipes_count',
            'recipes'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return Follow.objects.filter(user=user, author=obj).exists()

    def get_recipes_count(self, obj):
        return obj.recipes.count()

    def get_recipes(self, obj):
        request = self.context.get('request')
        limit = request.GET.get('recipes_limit')
        queryset = Recipe.objects.filter(author=obj)
        if limit:
            queryset = queryset[:int(limit)]
        return RecipeListSerializer(queryset, many=True,
                                    context=self.context).data


class PasswordSerializer(serializers.Serializer):
    """Сериализатор для изменения пароля пользователя."""
    new_password = serializers.CharField(max_length=150)
    current_password = serializers.CharField(max_length=150)

    def validate_new_password(self, value):
        """Валидация нового пароля, проверка его соответствия требованиям."""
        try:
            validate_password(value)
        except ValidationError as error:
            raise serializers.ValidationError(
                {'new_password': list(error.messages)}
            )
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
            raise serializers.ValidationError(
                'Количество ингредиента должно быть положительным числом.'
            )
        return value


class IngredientCreateSerializer(serializers.ModelSerializer):
    """Серилизатор для добавления ингридиентов"""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'amount')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Количество должно быть больше нуля.'
            )
        return value


class RecipeListSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения списка рецептов."""

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')


class RecipeAmountIngredientSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения информации об ингредиентах.
    """
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )
    amount = serializers.IntegerField()

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                'Количество должно быть положительным числом.'
            )
        return value


class DetailedRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для отображения подробной информации о рецепте."""
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    author = UserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    ingredients = RecipeAmountIngredientSerializer(
        many=True,
        source='recipe_ingredients'
    )

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
        """Проверить, является ли рецепт избранным для пользователя."""
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return False
        user = request.user
        if user.is_anonymous:
            return False
        return FavoriteRecipe.objects.filter(user=user, recipe=obj).exists()

    def get_is_in_shopping_cart(self, obj):
        """Проверить, есть ли рецепт в списке покупок пользователя."""
        request = self.context.get('request')
        if not request or not hasattr(request, 'user'):
            return False
        user = request.user
        if user.is_anonymous:
            return False
        return ShoppingList.objects.filter(user=user, recipe=obj).exists()


class RecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для создания рецепта."""
    ingredients = IngredientCreateSerializer(many=True)
    tags = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Tag.objects.all()
    )
    image = Base64ImageField(required=False, allow_null=True)

    class Meta:
        model = Recipe
        fields = (
            'id', 'name', 'ingredients', 'tags',
            'text', 'image', 'cooking_time',
        )

    def to_representation(self, instance):
        """Возвращение развернутого представления рецепта."""
        return DetailedRecipeSerializer(instance, context=self.context).data

    def validate(self, data):
        """Проверка данных перед созданием рецепта."""
        required_fields = ['name', 'ingredients', 'cooking_time', 'tags']
        if self.instance is None:
            for field in required_fields:
                if field not in data or not data[field]:
                    raise serializers.ValidationError(
                        f'{field} обязательное поле.'
                    )
            if 'image' not in data or data['image'] is None:
                raise serializers.ValidationError(
                    'Изображение является обязательным полем.'
                )
        else:
            for field in required_fields[:-1]:
                if field not in data or not data[field]:
                    raise serializers.ValidationError(
                        f'{field} обязательное поле.'
                    )
        if 'image' not in data:
            data['image'] = self.instance.image

        return data

    def validate_ingredients(self, value):
        """Проверка списка ингредиентов."""
        if not value:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один ингредиент.'
            )
        unique_ids = set()
        for ingredient in value:
            ingredient_id = ingredient['id']
            if ingredient_id in unique_ids:
                raise serializers.ValidationError(
                    'Ингредиенты не должны повторяться.'
                )
            if ingredient['amount'] < 1:
                raise serializers.ValidationError(
                    'Количество ингредиента должно быть не менее 1.'
                )
            unique_ids.add(ingredient_id)
        return value

    def validate_tags(self, value):
        """Проверка списка тегов."""
        if not value:
            raise serializers.ValidationError(
                'Рецепт должен содержать хотя бы один тег.'
            )
        tag_ids = []
        for tag in value:
            if tag in tag_ids:
                raise serializers.ValidationError(
                    'Теги не должны повторяться.'
                )
            tag_ids.append(tag)
        return value

    def create(self, validated_data):
        """Создание рецепта с ингредиентами и тегами."""
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags', [])
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        recipe_ingredients = []
        for ingredient in ingredients:
            recipe_ingredients.append(
                RecipeIngredient(
                    recipe=recipe,
                    ingredient=ingredient['id'],
                    amount=ingredient['amount']
                )
            )
        RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return recipe

    def update(self, instance, validated_data):
        """Обновление рецепта с ингредиентами и тегами."""
        instance.name = validated_data.get('name', instance.name)
        instance.text = validated_data.get('text', instance.text)
        instance.cooking_time = validated_data.get('cooking_time',
                                                   instance.cooking_time)

        if 'image' in validated_data:
            instance.image = validated_data.get('image')
        instance.save()

        tags = validated_data.get('tags', None)
        if tags is not None:
            instance.tags.set(tags)
        ingredients_data = validated_data.get('ingredients', None)
        if ingredients_data is not None:
            instance.recipe_ingredients.all().delete()
            recipe_ingredients = []
            for ingredient in ingredients_data:
                amount = ingredient['amount']
                recipe_ingredients.append(
                    RecipeIngredient(
                        recipe=instance,
                        ingredient=ingredient['id'],
                        amount=amount
                    )
                )
            RecipeIngredient.objects.bulk_create(recipe_ingredients)
        return instance
