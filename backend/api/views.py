from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from users.models import CustomUser, Follow

from .filters import IngredientFilterSet, RecipeFilterSet, TagFilterSet
from .models import (FavoriteRecipe, Ingredient, Recipe, RecipeIngredient,
                     ShoppingList, Tag)
from .pagination import PageLimitPaginator
from .permissions import RoleBasedPermission
from .serializers import (AvatarSerializer, FollowerSerializer,
                          ImageSerializer, IngredientSerializer,
                          PasswordSerializer, RecipeListSerializer,
                          RecipeSerializer, SignUpUserSerializer,
                          TagSerializer, UserSerializer)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet пользователя"""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        """Регистрирует нового пользователя."""
        serializer = SignUpUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = SignUpUserSerializer(
                user, context={'request': request})
            return Response(
                response_serializer.data,
                status=status.HTTP_201_CREATED
            )
        return Response({'errors': serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['GET'],
            permission_classes=(permissions.IsAuthenticated, ))
    def me(self, request):
        serializer = UserSerializer(
            request.user,
            context={'request': request}
        )
        return Response(data=serializer.data)

    @action(detail=False, methods=['GET'],
            permission_classes=(permissions.IsAuthenticated,))
    def get_profile(self, request):
        """Профиль пользователя"""
        serializer = UserSerializer(
            request.user, context={'request': request}
        )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'],
            permission_classes=(permissions.AllowAny,))
    def subscriptions(self, request):
        """Авторы, на которых подписан пользователь."""
        user = request.user
        subscriptions = Follow.objects.filter(user=user)
        authors = [follow.author for follow in subscriptions]

        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = FollowerSerializer(page, many=True,
                                            context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = FollowerSerializer(authors, many=True,
                                        context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['POST'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
        """Обновление пароля"""
        serializer = PasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        current_password = serializer.validated_data['current_password']
        new_password = serializer.validated_data['new_password']
        user = get_object_or_404(self.get_queryset(),
                                 username=request.user.username)

        if not user.check_password(current_password):
            return Response({'current_password': 'Текущий пароль неверен.'},
                            status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["PUT", "DELETE"],
            permission_classes=[IsAuthenticated],
            url_path='me/avatar')
    def set_avatar(self, request):
        """Добавить/удалить аватар"""
        if request.method == "PUT":
            serializer = AvatarSerializer(
                instance=request.user, data=request.data, partial=True
            )
            if 'avatar' not in request.data:
                return Response(
                    {"error": 'Поле "avatar" обязательно для заполнения.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        request.user.avatar = None
        request.user.save()
        return Response({"avatar": None}, status=status.HTTP_204_NO_CONTENT)


class FollowViewSet(viewsets.ViewSet):
    """Управление подписками пользователей."""
    permission_classes = [IsAuthenticated]
    serializer_class = FollowerSerializer
    pagination_class = PageLimitPaginator

    def create(self, request, user_id):
        """
        Создание подписки на выбранного пользователя.
        Пользователь не может подписаться на себя или повторно подписаться.
        """
        author_to_follow = get_object_or_404(CustomUser, id=user_id)

        if author_to_follow == request.user:
            return Response(
                {"detail": "Вы не можете подписаться на себя."},
                status=status.HTTP_400_BAD_REQUEST
            )

        if request.user.follower.filter(author=author_to_follow).exists():
            return Response(
                {"detail": 'Вы уже подписаны на данного пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        Follow.objects.create(user=request.user, author=author_to_follow)
        serializer = FollowerSerializer(author_to_follow,
                                        context={'request': request})

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, user_id):
        """
        Удаление подписки на выбранного пользователя.
        """
        author_to_unfollow = get_object_or_404(CustomUser, id=user_id)
        follow_instance = request.user.follower.filter(
            author=author_to_unfollow
        )

        if follow_instance.exists():
            follow_instance.delete()
            return Response(
                {"detail": 'Вы успешно отписались.'},
                status=status.HTTP_204_NO_CONTENT
            )

        return Response(
            {"detail": 'Вы не подписаны на данного пользователя.'},
            status=status.HTTP_400_BAD_REQUEST
        )


class TagViewSet(viewsets.ModelViewSet):
    """Управление тегами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    filterset_class = TagFilterSet

    def list(self, request):
        """Список тегов."""
        name = request.query_params.get('name', None)
        queryset = Tag.objects.filter(
            name__icontains=name) if name else Tag.objects.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Запрещает создание тега."""
        raise MethodNotAllowed(method='POST')

    def update(self, request, *args, **kwargs):
        """Запрещает обновление тега."""
        raise MethodNotAllowed(method='PUT')

    def destroy(self, request, *args, **kwargs):
        """Запрещает удаление тега."""
        raise MethodNotAllowed(method='DELETE')


class IngredientViewSet(viewsets.ModelViewSet):
    """Обрабатывает запросы к ингредиентам."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filterset_class = IngredientFilterSet

    def list(self, request):
        """Получает список ингредиентов."""
        name = request.query_params.get('name', None)
        queryset = Ingredient.objects.filter(
            name__icontains=name) if name else Ingredient.objects.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        """Запрещает создание ингредиента."""
        raise MethodNotAllowed(method='POST')

    def update(self, request, *args, **kwargs):
        """Запрещает обновление ингредиента."""
        raise MethodNotAllowed(method='PUT')

    def destroy(self, request, *args, **kwargs):
        """Запрещает удаление ингредиента."""
        raise MethodNotAllowed(method='DELETE')


class RecipeViewSet(viewsets.ModelViewSet):
    """Обрабатывает запросы к рецептам."""
    queryset = Recipe.objects.prefetch_related(
        'recipe_ingredients__ingredient', 'tags'
    )
    serializer_class = RecipeSerializer
    pagination_class = PageLimitPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet
    permission_classes = [RoleBasedPermission]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_permissions(self):
        """Определяет права доступа к действиям."""
        if self.action == 'get_link':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def perform_create(self, serializer):
        """Создание рецепта вместе с ингредиентами."""
        ingredients_data = self.request.data.get('ingredients', [])
        recipe = serializer.save(author=self.request.user)
        self.manage_ingredients(recipe, ingredients_data)

    def perform_update(self, serializer):
        """Обновление рецепта вместе с ингредиентами."""
        recipe_instance = self.get_object()
        ingredients_data = self.request.data.get('ingredients', [])
        serializer.save()
        self.manage_ingredients(recipe_instance, ingredients_data)

    def manage_ingredients(self, recipe, ingredients_data):
        """
        Обновление ингредиентов рецепта: добавление новых,
        обновление существующих и удаление тех, которые отсутствуют в запросе.
        """
        existing_ingredients_dict = {
            ingredient.ingredient_id: ingredient
            for ingredient in RecipeIngredient.objects.filter(recipe=recipe)
        }
        new_ingredients_ids = []
        for ingredient_data in ingredients_data:
            ingredient_id = ingredient_data['id']
            new_ingredients_ids.append(ingredient_id)
            if ingredient_id in existing_ingredients_dict:
                existing_ingredient = existing_ingredients_dict[ingredient_id]
                new_amount = ingredient_data['amount']
                if existing_ingredient.amount != new_amount:
                    existing_ingredient.amount = new_amount
                    existing_ingredient.save()
            else:
                ingredient_instance = get_object_or_404(Ingredient,
                                                        id=ingredient_id)
                RecipeIngredient.objects.create(
                    recipe=recipe,
                    ingredient=ingredient_instance,
                    amount=ingredient_data['amount']
                )
        RecipeIngredient.objects.filter(recipe=recipe).exclude(
            ingredient_id__in=new_ingredients_ids
        ).delete()

    @action(['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated], url_path='image')
    def set_image_recipe(self, request, pk=None):
        """Управление изображением рецепта."""
        recipe = self.get_object()

        if request.method == "POST":
            serializer = ImageSerializer(instance=recipe,
                                         data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)

        recipe.image = None
        recipe.save()
        return Response({"detail": 'Изображение удалено.'},
                        status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['GET'], url_path='get-link',
            permission_classes=[permissions.AllowAny])
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = f'http: //{request.get_host()}/recipes/{recipe.id}/'
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавление ингридиентов рецепта в корзину"""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        if request.method == 'POST':
            if ShoppingList.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"detail": 'Рецепт уже в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingList.objects.create(user=user, recipe=recipe)
            serializer = RecipeListSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            shopping_item = ShoppingList.objects.filter(user=user,
                                                        recipe=recipe)
            if not shopping_item.exists():
                return Response(
                    {"detail": 'Рецепт не найден в корзине.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            shopping_item.delete()
            serializer = RecipeListSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """Список покупок"""
        user = request.user
        shopping_list_items = ShoppingList.objects.filter(
            user=user).select_related('recipe')
        ingredients = []
        for item in shopping_list_items:
            recipe_ingredients = item.recipe.ingredients.all()
            ingredients.extend(recipe_ingredients)
        unique_ingredients = {
            ingredient.name: ingredient for ingredient in ingredients
        }
        response_content = '\n'.join(
            f'{name} ({ingredient.measurement_unit})' for name,
            ingredient in unique_ingredients.items())
        response = HttpResponse(response_content, content_type='text/plain')
        response[
            'Content-Disposition'
        ] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Избранные рецепты"""
        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        if request.method == 'POST':
            if FavoriteRecipe.objects.filter(user=user,
                                             recipe=recipe).exists():
                return Response(
                    {"detail": 'Рецепт уже добавлен в избранное.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            FavoriteRecipe.objects.create(user=user, recipe=recipe)
            serializer = RecipeListSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            favorite_item = FavoriteRecipe.objects.filter(user=user,
                                                          recipe=recipe)
            if not favorite_item.exists():
                return Response(
                    {"detail": 'Рецепт не найден в избранном.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            favorite_item.delete()
            serializer = RecipeListSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
