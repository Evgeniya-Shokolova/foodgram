from django.db.models import Sum
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from djoser.views import UserViewSet as DjoserUserViewSet

from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ReadOnlyModelViewSet

from api.filters import IngredientFilterSet, RecipeFilterSet
from api.pagination import PageLimitPaginator
from api.permissions import IsAuthorOrReadOnly
from api.serializers import (AvatarSerializer, FavoriteRecipeSerializer,
                             FollowerCreateSerializer,
                             FollowerRetrieveSerializer, IngredientSerializer,
                             RecipeSerializer, ShoppingCartSerializer,
                             TagSerializer, UserSerializer)
from recipes.models import (FavoriteRecipe, Ingredient, Recipe,
                            RecipeIngredient, ShoppingList, Tag)
from users.models import CustomUser, Follow


class UserViewSet(DjoserUserViewSet):
    """ViewSet пользователя"""
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    permission_classes = (permissions.AllowAny,)
    pagination_class = PageLimitPaginator

    @action(detail=False, methods=['GET'],
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """Переопределяем djoser метод `me`, ограничиваем доступ"""
        return super().me(request)

    @action(detail=False, methods=['PUT'], url_path='me/avatar',
            permission_classes=[IsAuthenticated])
    def set_avatar(self, request):
        """Добавить/удалить аватар"""
        serializer = AvatarSerializer(
            instance=request.user, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_200_OK)

    @set_avatar.mapping.delete
    def delete_avatar(self, request):
        """Удаление аватара"""
        request.user.avatar.delete()
        request.user.save()
        return Response(
            {'message': 'Фото успешно удалено.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['GET'],
            permission_classes=[permissions.IsAuthenticated])
    def subscriptions(self, request):
        """Получение авторов, на которых подписан пользователь"""
        queryset = CustomUser.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = FollowerRetrieveSerializer(
            page, many=True, context={'request': request})
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['POST'],
            permission_classes=[IsAuthenticated], url_path="subscribe")
    def subscribe(self, request, id=None):
        """Создание подписки на пользователя."""
        user_to_follow = get_object_or_404(CustomUser, id=id)
        serializer = FollowerCreateSerializer(
            data={'user': request.user.id, 'author': user_to_follow.id},
            context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        response_data = FollowerRetrieveSerializer(
            user_to_follow, context={'request': request}
        ).data

        return Response(response_data, status=status.HTTP_201_CREATED)

    @subscribe.mapping.delete
    def remove_subscription(self, request, id=None):
        """Удаление подписки на пользователя."""
        user_to_follow = get_object_or_404(CustomUser, id=id)
        deleted_count, _ = Follow.objects.filter(
            user=request.user, author=user_to_follow
        ).delete()
        if not deleted_count:
            return Response(
                {'detail': 'Вы не подписаны на данного пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'detail': 'Вы успешно отписались.'},
            status=status.HTTP_204_NO_CONTENT
        )


class TagViewSet(ReadOnlyModelViewSet):
    """Управление тегами."""
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    pagination_class = None


class IngredientViewSet(ReadOnlyModelViewSet):
    """Обрабатывает запросы к ингредиентам."""
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filterset_class = IngredientFilterSet
    search_fields = ('^name',)
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    """Обрабатывает запросы к рецептам."""
    queryset = Recipe.objects.prefetch_related(
        'recipe_ingredients__ingredient', 'tags'
    )
    serializer_class = RecipeSerializer
    pagination_class = PageLimitPaginator
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilterSet
    permission_classes = [IsAuthorOrReadOnly]
    http_method_names = ['get', 'post', 'patch', 'delete']

    @action(detail=True, methods=['GET'], url_path='get-link',
            permission_classes=[permissions.AllowAny])
    def get_link(self, request, pk=None):
        """Возвращает короткую ссылку на рецепт."""
        recipe = get_object_or_404(Recipe, id=pk)
        full_url = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return Response({'short-link': full_url}, status=status.HTTP_200_OK)

    @action(detail=False, methods=['GET'],
            url_path='get-link')
    def redirect_to_recipe(self, request, pk=None):
        """Перенаправляет пользователя по короткой ссылке рецепта."""
        recipe = get_object_or_404(Recipe, id=pk)
        full_url = request.build_absolute_uri(f'/recipes/{recipe.id}/')
        return HttpResponseRedirect(full_url)

    @action(methods=['POST'], detail=True,
            permission_classes=[IsAuthenticated])
    def shopping_cart(self, request, pk=None):
        """Добавление ингридиентов рецепта в корзину"""
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id, 'recipe': recipe.id}
        serializer = ShoppingCartSerializer(data=data,
                                            context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @shopping_cart.mapping.delete
    def remove_shopping_cart(self, request, pk=None):
        """Удаление рецепта из корзины."""
        recipe = get_object_or_404(Recipe, id=pk)
        shopping_item = ShoppingList.objects.filter(user=request.user,
                                                    recipe=recipe)
        if not shopping_item.exists():
            return Response(
                {'detail': 'Рецепт отсутствует в корзине пользователя.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        shopping_item.delete()

        return Response(
            {'detail': 'Рецепт был успешно удалён из корзины.'},
            status=status.HTTP_204_NO_CONTENT
        )

    @action(detail=False, methods=['GET'],
            permission_classes=[permissions.IsAuthenticated],
            url_path='download_shopping_cart')
    def download_shopping_cart(self, request):
        """Список покупок"""
        user = request.user
        recipes_in_cart = ShoppingList.objects.filter(
            user=user).values_list('recipe', flat=True)
        ingredients = (
            RecipeIngredient.objects.filter(recipe__in=recipes_in_cart)
            .values('ingredient__name',
                    'ingredient__measurement_unit')
            .annotate(total_amount=Sum('amount'))
        )
        response_content = '\n'.join(
            f'{item["ingredient__name"]}'
            f'({item["ingredient__measurement_unit"]}) - '
            f'{item["total_amount"]}'
            for item in ingredients
        )
        response = HttpResponse(response_content, content_type='text/plain')
        response[
            'Content-Disposition'] = 'attachment; filename="shopping_list.txt"'
        return response

    @action(methods=['POST'], detail=True,
            permission_classes=[IsAuthenticated])
    def favorite(self, request, pk=None):
        """Избранные рецепты"""
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'user': request.user.id, 'recipe': recipe.id}
        serializer = FavoriteRecipeSerializer(data=data,
                                              context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED
        )

    @favorite.mapping.delete
    def remove_favorite(self, request, pk=None):
        """Удаление рецепта из избранного"""
        recipe = get_object_or_404(Recipe, id=pk)
        favorite_item_deleted, _ = FavoriteRecipe.objects.filter(
            user=request.user,
            recipe=recipe
        ).delete()
        if not favorite_item_deleted:
            return Response(
                {'detail': 'Рецепт не найден в избранном.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        return Response(
            {'detail': 'Рецепт был успешно удалён из избранного.'},
            status=status.HTTP_204_NO_CONTENT
        )
