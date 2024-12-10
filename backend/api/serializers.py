from rest_framework import serializers

from drf_extra_fields.fields import Base64ImageField

from recipes.models import (
    FavoriteRecipe,
    Ingredient,
    Recipe,
    RecipeIngredient,
    ShoppingList,
    Tag,
)
from users.models import CustomUser, Follow


class AvatarSerializer(serializers.ModelSerializer):
    """Сериализатор аватара."""
    avatar = Base64ImageField()

    class Meta:
        model = CustomUser
        fields = ('avatar',)

    def validate(self, attrs):
        """
        Проверяем наличие поля avatar при добавлении.
        """
        if 'avatar' not in attrs or not attrs['avatar']:
            raise serializers.ValidationError(
                {'avatar': 'Поле "avatar" обязательно для заполнения.'}
            )
        return attrs


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
        Определяет, подписан ли текущий пользователь на данного пользователя.
        """
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated
            and Follow.objects.filter(user=request.user,
                                      author=user).exists()
        )


class FollowerCreateSerializer(serializers.ModelSerializer):
    """Сериализатор для создания подписки."""

    class Meta:
        model = Follow
        fields = ('user', 'author')

    def validate(self, data):
        user = data['user']
        author = data['author']
        if user == author:
            raise serializers.ValidationError(
                'Вы не можете подписаться на себя.'
            )
        if Follow.objects.filter(user=user, author=author).exists():
            raise serializers.ValidationError(
                'Вы уже подписаны на данного пользователя.'
            )

        return data

    def to_representation(self, instance):
        """
        Возвращаем информацию о пользователе,
        на которого была создана подписка.
        """
        return FollowerRetrieveSerializer(instance.author,
                                          context=self.context).data


class FollowerRetrieveSerializer(UserSerializer):
    """Сериализатор для отображения подписанного пользователя."""
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta:
        model = CustomUser
        fields = UserSerializer.Meta.fields + (
            'recipes_count',
            'recipes'
        )

    def get_recipes_count(self, obj):
        """Подсчет общего количества рецептов пользователя."""
        return obj.recipes.count()

    def get_recipes(self, obj):
        """Получение списка рецептов автора с учетом лимита."""
        queryset = Recipe.objects.filter(author=obj)
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        try:
            if recipes_limit is not None:
                recipes_limit = int(recipes_limit)
                if recipes_limit > 0:
                    queryset = queryset[:recipes_limit]
        except (ValueError, TypeError):
            pass

        return RecipeListSerializer(queryset, many=True,
                                    context=self.context).data


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


class IngredientCreateSerializer(serializers.ModelSerializer):
    """Серилизатор для добавления ингридиентов"""
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

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
    Сериализатор для отображения информации об ингредиентах.
    """
    id = serializers.PrimaryKeyRelatedField(queryset=Ingredient.objects.all())
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = RecipeIngredient
        fields = ('id', 'name', 'measurement_unit', 'amount')


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
        return bool(
            request and request.user.is_authenticated
            and FavoriteRecipe.objects.filter(user=request.user,
                                              recipe=obj).exists()
        )

    def get_is_in_shopping_cart(self, obj):
        """Проверить, есть ли рецепт в списке покупок пользователя."""
        request = self.context.get('request')
        return bool(
            request and request.user.is_authenticated
            and ShoppingList.objects.filter(user=request.user,
                                            recipe=obj).exists()
        )


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
        """Проверка данных перед созданием и обновлением рецепта."""
        tags = data.get('tags')
        if not tags:
            raise serializers.ValidationError(
                {'tags': 'Рецепт должен содержать хотя бы один тег.'}
            )
        if len(tags) != len(set(tags)):
            raise serializers.ValidationError(
                {'tags': 'Теги не должны повторяться.'}
            )

        ingredients = data.get('ingredients')
        if not ingredients:
            raise serializers.ValidationError(
                {'ingredients':
                 'Рецепт должен содержать хотя бы один ингредиент.'}
            )
        ingredient_ids = [ingredient['id'] for ingredient in ingredients]
        if len(ingredient_ids) != len(set(ingredient_ids)):
            raise serializers.ValidationError({
                'ingredients': 'Ингредиенты не должны повторяться.'}
            )

        if 'image' not in data or data['image'] is None:
            raise serializers.ValidationError(
                'Изображение является обязательным полем.'
            )
        if 'image' not in data:
            data['image'] = self.instance.image

        return data

    def create(self, validated_data):
        """Создание рецепта с ингредиентами и тегами."""
        ingredients = validated_data.pop('ingredients', [])
        tags = validated_data.pop('tags', [])
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        recipe.tags.set(tags)
        self._create_recipe_ingredients(recipe, ingredients)
        return recipe

    @staticmethod
    def _create_recipe_ingredients(recipe, ingredients):
        """Создание ингредиентов для рецепта."""
        recipe_ingredients = [
            RecipeIngredient(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )
            for ingredient in ingredients
        ]
        RecipeIngredient.objects.bulk_create(recipe_ingredients)

    def update(self, instance, validated_data):
        """Обновление рецепта с ингредиентами и тегами."""
        ingredients = validated_data.pop('ingredients', None)
        if ingredients:
            instance.recipe_ingredients.all().delete()
            self._create_recipe_ingredients(instance, ingredients)

        if 'tags' in validated_data:
            tags = validated_data.get('tags')
            instance.tags.set(tags)

        return super().update(instance, validated_data)


class ShoppingCartSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в корзину."""

    class Meta:
        model = ShoppingList
        fields = ('user', 'recipe')
        validators = [
            serializers.UniqueTogetherValidator(
                queryset=ShoppingList.objects.all(),
                fields=('user', 'recipe'),
                message='Рецепт уже добавлен в корзину.'
            )
        ]

    def validate(self, data):
        """Дополнительная валидация перед сохранением."""
        user = data['user']
        recipe = data['recipe']
        if ShoppingList.objects.filter(user=user, recipe=recipe).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже добавлен в корзину.'
            )
        return data

    def to_representation(self, instance):
        """Возвращает информацию о рецепте."""
        return RecipeListSerializer(instance.recipe, context=self.context).data


class FavoriteRecipeSerializer(serializers.ModelSerializer):
    """Сериализатор для добавления рецепта в избранное"""
    class Meta:
        model = FavoriteRecipe
        fields = ('user', 'recipe')
        validators = [serializers.UniqueTogetherValidator(
            queryset=FavoriteRecipe.objects.all(),
            fields=('user', 'recipe'),
            message='Рецепт уже добавлен в избранное'
        )]

    def vaidate(self, data):
        """Дополнительная валидация для рецептв"""
        user = data['user']
        recipe = data['recipe']
        if FavoriteRecipe.objects.filter(user=user,
                                         recipe=recipe).exists():
            raise serializers.ValidationError(
                'Этот рецепт уже добавлен в избранное'
            )
        return data

    def to_representation(self, instance):
        """Возвращает информацию о рецепте."""
        return RecipeListSerializer(instance.recipe, context=self.context).data
