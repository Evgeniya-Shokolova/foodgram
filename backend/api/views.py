from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed

from users.models import Follow, CustomUser
from api.models import (FavoriteRecipe, Ingredient,
                        Recipe, ShoppingList, Tag, RecipeIngredient)
from api.permissions import RoleBasedPermission
from api.serializers import (FollowerSerializer,
                             PasswordSerializer,
                             IngredientSerializer,
                             TagSerializer,
                             UserSerializer,
                             AvatarSerializer,
                             SignUpUserSerializer,
                             RecipeSerializer,
                             ImageSerializer,
                             RecipeListSerializer)
from api.pagination import PageLimitPaginator
from api.filters import RecipeFilterSet, IngredientFilterSet, TagFilterSet


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        """Регистрирует нового пользователя."""
        serializer = SignUpUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = SignUpUserSerializer(
                user, context={'request': request}
                )
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
        serializer = UserSerializer(
            request.user, context={'request': request}
            )
        return Response(serializer.data, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'],
            permission_classes=(permissions.AllowAny,))
    def subscriptions(self, request):
        """Возвращает список авторов, на которых подписан пользователь."""
        user = request.user
        subscriptions = Follow.objects.filter(user=user)
        authors = [follow.author for follow in subscriptions]

        page = self.paginate_queryset(authors)
        if page is not None:
            serializer = FollowerSerializer(
                page, many=True, context={'request': request}
                )
            return self.get_paginated_response(serializer.data)

        serializer = FollowerSerializer(
            authors, many=True, context={'request': request}
            )
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
        """Добавить аватар"""
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
    permission_classes = [IsAuthenticated]
    serializer_class = FollowerSerializer
    pagination_class = PageLimitPaginator

    def create(self, request, user_id):
        author_to_follow = get_object_or_404(CustomUser, id=user_id)

        if author_to_follow == request.user:
            return Response(
                {"detail": "Вы не можете подписаться на себя."},
                status=status.HTTP_400_BAD_REQUEST
                )

        if request.user.follower.filter(author=author_to_follow).exists():
            return Response(
                {"detail": "Вы уже подписаны на данного пользователя."},
                status=status.HTTP_400_BAD_REQUEST
                )

        Follow.objects.create(user=request.user, author=author_to_follow)
        serializer = FollowerSerializer(
            author_to_follow, context={'request': request}
            )

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def destroy(self, request, user_id):
        author_to_unfollow = get_object_or_404(CustomUser, id=user_id)
        follow_instance = request.user.follower.filter(
            author=author_to_unfollow
            )

        if follow_instance.exists():
            follow_instance.delete()
            return Response(
                {"detail": "Успешная отписка."},
                status=status.HTTP_204_NO_CONTENT
                )

        return Response(
            {"detail": "Вы не подписаны на данного пользователя."},
            status=status.HTTP_400_BAD_REQUEST
            )


class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    filterset_class = TagFilterSet

    def list(self, request):
        name = request.query_params.get('name', None)
        queryset = Tag.objects.filter(
            name__icontains=name
            ) if name else Tag.objects.all()
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
            name__icontains=name
            ) if name else Ingredient.objects.all()
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
    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = PageLimitPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet
    permission_classes = [RoleBasedPermission]
    http_method_names = ['get', 'post', 'patch', 'delete']

    def get_permissions(self):
        if self.action == 'get_link':
            permission_classes = [permissions.AllowAny]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset

    def create(self, request, *args, **kwargs):
        """Создание рецепта."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        recipe = serializer.save(author=request.user)

        ingredients_data = request.data.get('ingredients', [])
        if ingredients_data:
            self._get_ingredients(ingredients_data, recipe)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Обновление рецептв"""
        recipe_instance = self.get_object()

        if recipe_instance.author != request.user:
            return Response(
                {"detail": "Вы не можете обновить этот рецепт."},
                status=status.HTTP_403_FORBIDDEN
                )

        serializer = self.get_serializer(
            recipe_instance, data=request.data, partial=True
            )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if 'ingredients' in request.data and request.data['ingredients']:
            recipe_instance.ingredients.clear()
            ingredients_data = request.data.get('ingredients', [])
            self._get_ingredients(ingredients_data, recipe_instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete_recipe(self, model_class, recipe_id, error_type, action):
        recipe = get_object_or_404(Recipe, pk=recipe_id)
        user = self.request.user
        if recipe.author != user:
            return Response(
                {'errors': 'У вас нет прав для выполнения этого действия!'},
                status=status.HTTP_403_FORBIDDEN
                )

        existing_entry = model_class.objects.filter(
            recipe=recipe, user=user
            ).first()

        if action == 'delete':
            if not existing_entry:
                return self._handle_not_found_error(error_type)
            return Response(
                {'message': 'Рецепт успешно удален.'},
                status=status.HTTP_204_NO_CONTENT
                )
        elif action == 'edit':
            pass

        return Response(
            {'errors': 'Неверное действие!'},
            status=status.HTTP_400_BAD_REQUEST
            )

    def _get_ingredients(self, ingredient_data_list, recipe_instance):
        """**Получение объектов ингредиентов и связывание их с рецептом.**"""
        ingredient_objs = []
        for ingredient_data in ingredient_data_list:
            ingredient_instance = get_object_or_404(
                Ingredient, pk=ingredient_data['id']
                )
            if not RecipeIngredient.objects.filter(recipe=recipe_instance, ingredient=ingredient_instance, amount=ingredient_data['amount']).exists():
                ingredient_objs.append(
                    RecipeIngredient(
                        recipe=recipe_instance,
                        ingredient=ingredient_instance,
                        amount=ingredient_data['amount']
                        )
                        )
            RecipeIngredient.objects.bulk_create(ingredient_objs)

    @action(['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated], url_path='image')
    def set_image_recipe(self, request, pk=None):
        """Управление изображением рецепта."""
        recipe = self.get_object()

        if request.method == "POST":
            serializer = ImageSerializer(instance=recipe,
                                         data=request.data,
                                         partial=True
                                         )
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)

        recipe.image = None
        recipe.save()
        return Response({"image": None}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['GET'], url_path='get-link',
            permission_classes=[permissions.AllowAny])
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = f'http://{request.get_host()}/recipes/{recipe.id}/'
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):

        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user

        if request.method == 'POST':
            if ShoppingList.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"detail": "Рецепт уже добавлен в корзину."},
                    status=status.HTTP_400_BAD_REQUEST
                    )

            ShoppingList.objects.create(user=user, recipe=recipe)
            serializer = IngredientSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            shopping_item = ShoppingList.objects.filter(
                user=user, recipe=recipe
                )
            if not shopping_item.exists():
                return Response(
                    {"detail": "Рецепт не найден в корзине."},
                    status=status.HTTP_400_BAD_REQUEST
                    )
            shopping_item.delete()
            serializer = RecipeListSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)

    @action(detail=False, methods=["get"],
            permission_classes=[permissions.IsAuthenticated],
            url_path="download_shopping_cart")
    def download_shopping_cart(self, request):

        user = request.user
        shopping_list_items = ShoppingList.objects.filter(
            user=user).select_related('recipe')
        ingredients = []
        for item in shopping_list_items:
            recipe_ingredients = item.recipe.ingredients.all()
            ingredients.extend(recipe_ingredients)
        unique_ingredients = {
            ingredient.name: ingredient for ingredient in ingredients}
        response_content = '\n'.join(
            f"{name} ({ingredient.measurement_unit})" for name,
            ingredient in unique_ingredients.items())
        response = HttpResponse(response_content, content_type='text/plain')
        response[
            'Content-Disposition'
            ] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(methods=['POST', 'DELETE'], detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):

        recipe = get_object_or_404(Recipe, id=pk)
        user = request.user
        if request.method == 'POST':
            if FavoriteRecipe.objects.filter(
                user=user, recipe=recipe
                ).exists():
                return Response(
                    {"detail": "Рецепт уже добавлен в избранное."},
                    status=status.HTTP_400_BAD_REQUEST)

            FavoriteRecipe.objects.create(user=user, recipe=recipe)
            serializer = RecipeListSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_201_CREATED)

        elif request.method == 'DELETE':
            favorite_item = FavoriteRecipe.objects.filter(
                user=user, recipe=recipe
                )
            if not favorite_item.exists():
                return Response(
                    {"detail": "Рецепт не найден в избранном."},
                    status=status.HTTP_400_BAD_REQUEST
                    )
            favorite_item.delete()
            serializer = RecipeListSerializer(recipe)
            return Response(serializer.data, status=status.HTTP_204_NO_CONTENT)
