import csv
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from api.models import (FavoriteRecipe, Ingredient,
                        Recipe, ShoppingList, Tag, RecipeIngredient)
from rest_framework import permissions, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed
from rest_framework.exceptions import PermissionDenied
from users.models import Follow, CustomUser
from api.permissions import RoleBasedPermission
from api.serializers import (FollowerSerializer,
                             PasswordSerializer,
                             IngredientSerializer,
                             TagSerializer,
                             UserSerializer,
                             AvatarSerializer,
                             SignUpUserSerializer,
                             RecipeSerializer,
                             ImageSerializer)
from api.pagination import PageLimitPaginator
from api.filters import RecipeFilterSet


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageLimitPaginator
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        """Регистрирует нового пользователя."""
        serializer = SignUpUserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            response_serializer = UserSerializer(
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
            permission_classes=(permissions.IsAuthenticated,))
    def subscriptions(self, request):
        subscriptions = self.get_queryset().filter(
            following__user=request.user
            ).order_by('pk')
        paginated_subscriptions = self.paginate_queryset(subscriptions)

        serializer = FollowerSerializer(
            paginated_subscriptions if paginated_subscriptions is not None else subscriptions,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(
            serializer.data) if paginated_subscriptions else Response(
                serializer.data, status=status.HTTP_200_OK
                )
    
    @action(detail=False, methods=['POST'],
            permission_classes=[IsAuthenticated])
    def set_password(self, request):
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

    def create(self, request, user_id):
        author_to_follow = get_object_or_404(CustomUser, id=user_id)

        if author_to_follow == request.user:
           return Response({"detail": "Вы не можете подписаться на себя."}, status=status.HTTP_400_BAD_REQUEST)

        if request.user.follower.filter(author=author_to_follow).exists():
            return Response({"detail": "Вы уже подписаны на данного пользователя."}, status=status.HTTP_400_BAD_REQUEST)

        Follow.objects.create(user=request.user, author=author_to_follow)
        serializer = FollowerSerializer(author_to_follow, context={'request': request})

        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
        

    def destroy(self, request, user_id):
        if not request.user.is_authenticated:
            return Response({"detail": "Аутентификация требуется."}, status=status.HTTP_401_UNAUTHORIZED)

        author_to_unfollow = get_object_or_404(CustomUser, id=user_id)
        follow_instance = request.user.follower.filter(author=author_to_unfollow)

        if follow_instance.exists():
            follow_instance.delete()
            return Response('Успешная отписка',
                            status=status.HTTP_204_NO_CONTENT)

        return Response({"detail": "Вы не подписаны на данного пользователя."}, status=status.HTTP_400_BAD_REQUEST)

class TagViewSet(viewsets.ModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter]
    search_fields = ['name']

    def list(self, request):
        name = request.query_params.get('name', None)
        queryset = Tag.objects.filter(name__icontains=name) if name else Tag.objects.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed(method='POST')


class IngredientViewSet(viewsets.ModelViewSet):
    """Обрабатывает запросы к ингредиентам."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    search_fields = ['name']

    def list(self, request):
        """Получает список ингредиентов."""

        name = request.query_params.get('name', None)
        queryset = Ingredient.objects.filter(name__icontains=name) if name else Ingredient.objects.all()
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
    """**Обрабатывает запросы к рецептам.**"""

    queryset = Recipe.objects.all()
    serializer_class = RecipeSerializer
    pagination_class = PageLimitPaginator
    permission_classes = [RoleBasedPermission]
    filterset_class = RecipeFilterSet
    http_method_names = ['get', 'post', 'patch', 'delete']

    def create(self, request, *args, **kwargs):
        """**Создание рецепта.**"""
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
            return Response({"detail": "Вы не можете обновить этот рецепт."}, status=status.HTTP_403_FORBIDDEN)

        serializer = self.get_serializer(recipe_instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if 'ingredients' in request.data:
            ingredients_data = request.data.get('ingredients', [])
            recipe_instance.ingredients.clear()
            self._get_ingredients(ingredients_data, recipe_instance)

        return Response(serializer.data, status=status.HTTP_200_OK)

    def delete_recipe(self, request, model_class, recipe_id, error_type):

        recipe = get_object_or_404(Recipe, pk=recipe_id)
        user = self.request.user

        if recipe.author != user:
            return Response({'errors': 'У вас нет прав для удаления этого рецепта!'}, status=status.HTTP_403_FORBIDDEN)

        existing_entry = model_class.objects.filter(recipe=recipe, user=user).first()

        if not existing_entry:
            return self._handle_not_found_error(error_type)

        existing_entry.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    def _handle_not_found_error(self, error_type):
        error_messages = {
            'FAVORITE': 'Этот рецепт не в избранном!',
            'SHOP_LIST': 'Этот рецепт не в корзине покупок!'
        }
        return Response({'errors': error_messages.get(error_type, 'Ошибка!')}, status=status.HTTP_400_BAD_REQUEST)

    def _get_ingredients(self, ingredient_data_list, recipe_instance):
        """**Получение объектов ингредиентов и связывание их с рецептом.**"""
        ingredient_objs = []
        for ingredient_data in ingredient_data_list:
            ingredient_instance = get_object_or_404(Ingredient, pk=ingredient_data['id'])
            if not RecipeIngredient.objects.filter(recipe=recipe_instance, ingredient=ingredient_instance, amount=ingredient_data['amount']).exists():
                ingredient_objs.append(
                    RecipeIngredient(recipe=recipe_instance, ingredient=ingredient_instance, amount=ingredient_data['amount'])
                )
        RecipeIngredient.objects.bulk_create(ingredient_objs)

    @action(detail=False, methods=['GET'], permission_classes=(IsAuthenticated,))
    def export_shopping_cart(self, request):
        """Экспорт списка покупок в CSV."""
        ingredients = self.get_ingredients_for_shopping_list()

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.csv"'
        writer = csv.writer(response)
        writer.writerow(['Ingredient', 'Quantity'])

        for ingredient in ingredients:
            writer.writerow([ingredient.name, ingredient.quantity])

        return response

    @action(['POST', 'DELETE'], detail=True, permission_classes=[IsAuthenticated], url_path='image')
    def set_image_recipe(self, request, pk=None):
        """Управление изображением рецепта."""
        recipe = self.get_object()

        if request.method == "POST":
            serializer = ImageSerializer(instance=recipe, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response(serializer.data, status=status.HTTP_200_OK)

        recipe.image = None
        recipe.save()
        return Response({"image": None}, status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['GET'], url_path='get-link', permission_classes=[AllowAny])
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, pk=pk)
        short_link = f'http://{request.get_host()}/api/recipes/{recipe.id}/'
        return Response({'short-link': short_link}, status=status.HTTP_200_OK)


class ShoppingViewSet(viewsets.ModelViewSet):
    """ ViewSet для управления списком покупок. """
    permission_classes = (permissions.IsAuthenticated,)

    def generic_create(self, request, id, related_name, model_class):
        recipe = get_object_or_404(Recipe, id=id)
        user = request.user

        if getattr(user, related_name).filter(recipe=recipe).exists():
            return Response({"detail": "Рецепт уже добавлен в корзину."}, status=status.HTTP_400_BAD_REQUEST)

        model_class.objects.create(user=user, recipe=recipe)
        return Response({"detail": "Рецепт добавлен в корзину."}, status=status.HTTP_201_CREATED)

    def generic_destroy(self, request, id, related_name):
        recipe = get_object_or_404(Recipe, id=id)
        user = request.user

        shopping_item = getattr(user, related_name).filter(recipe=recipe)
        if shopping_item.exists():
            shopping_item.delete()
            return Response({"detail": "Рецепт удалён из корзины."}, status=status.HTTP_204_NO_CONTENT)

        return Response({"detail": "Рецепт не найден в корзине."}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, id):
        return self.generic_create(request, id, 'shopping_list_recipes', ShoppingList)

    def destroy(self, request, id):
        return self.generic_destroy(request, id, 'shopping_list_recipes')

    @action(detail=False, methods=['get'])
    def download_shopping_list(self, request):
        user = request.user
        items = user.shoppinglist_set.all()

        if not items:
            return Response({"detail": "Список покупок пуст."}, status=status.HTTP_404_NOT_FOUND)

        shopping_list_content = "\n".join([f"{item.recipe.name} - {item.recipe.amount}" for item in items])

        response = HttpResponse(shopping_list_content, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response


class FavoriteRecipeViewSet(viewsets.ModelViewSet):
    permission_classes = (permissions.IsAuthenticated,)

    def generic_create(self, request, id, related_name, model_class):
        recipe = get_object_or_404(Recipe, id=id)
        user = request.user


        if getattr(user, related_name).filter(recipe=recipe).exists():
            return Response({"detail": "Рецепт уже добавлен в избранное."}, status=status.HTTP_400_BAD_REQUEST)

        model_class.objects.create(user=user, recipe=recipe)
        return Response({"detail": "Рецепт добавлен в избранное."}, status=status.HTTP_201_CREATED)

    def generic_destroy(self, request, id, related_name):
        recipe = get_object_or_404(Recipe, id=id)
        user = request.user

        favorite_item = getattr(user, related_name).filter(recipe=recipe)
        if favorite_item.exists():
            favorite_item.delete()
            return Response({"detail": "Рецепт удалён из избранного."}, status=status.HTTP_204_NO_CONTENT)

        return Response({"detail": "Рецепт не найден в избранном."}, status=status.HTTP_400_BAD_REQUEST)

    def create(self, request, id):
        return self.generic_create(request, id, 'favorite_recipes', FavoriteRecipe)

    def destroy(self, request, id):
        return self.generic_destroy(request, id, 'favorite_recipes')
