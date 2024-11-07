import csv
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from api.models import (FavoriteRecipe, Ingredient,
                        Recipe, ShoppingList, Tag)
from rest_framework import permissions, status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import MethodNotAllowed

from users.models import Follow, CustomUser
from api.filters import RecipeFilter
from api.permissions import RoleBasedPermission
from api.serializers import (FollowerSerializer,
                             DetailedAmountIngredientSerializer,
                             PasswordSerializer,
                             IngredientSerializer,
                             TagSerializer,
                             UserSerializer,
                             BriefRecipeSerializer,
                             RecipeEntrySerializer,
                             AvatarSerializer, SignUpUserSerializer)
from api.pagination import PageLimitPaginator
from users.models import CustomUser


class UserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = UserSerializer
    pagination_class = PageLimitPaginator
    permission_classes = (permissions.AllowAny,)

    def create(self, request, *args, **kwargs):
        """
        Регистрирует нового пользователя.
        Принимает следующие поля в запросе:
        - username
        - email
        - password
        """
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
    def user_subscriptions(self, request):
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
            permission_classes=(permissions.IsAuthenticated,))
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
            permission_classes=[permissions.IsAuthenticated],
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
    permission_classes = (permissions.IsAuthenticated,)

    def follow(self, request, user_id):
        author_to_follow = get_object_or_404(CustomUser, pk=user_id)
        if author_to_follow != request.user and not request.user.follower.filter(author=author_to_follow).exists():
            Follow.objects.create(user=request.user, author=author_to_follow)
            serializer = FollowerSerializer(
                author_to_follow, context={'request': request}
                )
            return Response(serializer.data, status.HTTP_201_CREATED)
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def unfollow(self, request, user_id):
        author_to_unfollow = get_object_or_404(CustomUser, pk=user_id)
        follow_instance = request.user.follower.filter(
            author=author_to_unfollow
            )
        if follow_instance.exists():
            follow_instance.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response(status=status.HTTP_400_BAD_REQUEST)


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
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    search_fields = ['name']

    def list(self, request):
        name = request.query_params.get('name', None)
        queryset = Ingredient.objects.filter(name__icontains=name) if name else Ingredient.objects.all()
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request, *args, **kwargs):
        raise MethodNotAllowed(method='POST')

    def update(self, request, *args, **kwargs):
        raise MethodNotAllowed(method='PUT')

    def destroy(self, request, *args, **kwargs):
        raise MethodNotAllowed(method='DELETE')


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    serializer_class = DetailedAmountIngredientSerializer
    pagination_class = PageLimitPaginator
    permission_classes = (RoleBasedPermission,)
    filter_backends = (RecipeFilter,)

    def get_serializer_class(self):
        if self.action in ['create', 'partial_update']:
            return RecipeEntrySerializer
        return DetailedAmountIngredientSerializer

    @action(detail=False, methods=['GET'],
            permission_classes=(permissions.IsAuthenticated,))
    def export_shopping_cart(self, request):
        ingredients = self.get_ingredients_for_shopping_list()

        response = HttpResponse(content_type='text/csv')
        response[
            'Content-Disposition'
            ] = 'attachment; filename="shopping_list.csv"'

        writer = csv.writer(response)
        writer.writerow(['Ingredient', 'Quantity'])

        for ingredient in ingredients:
            writer.writerow([ingredient.name, ingredient.quantity])

        return response


class GenericCreateDeleteMixin:
    def generic_create(self, request, recipe_id, attribute_name, model_class):
        recipe_instance = get_object_or_404(Recipe, pk=recipe_id)
        related_queryset = getattr(recipe_instance, attribute_name)

        if not related_queryset.filter(user=request.user).exists():
            model_class.objects.create(
                user=request.user,
                recipe=recipe_instance
            )
            serializer = BriefRecipeSerializer(
                recipe_instance, context={'request': request}
                )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(status=status.HTTP_400_BAD_REQUEST)

    def generic_destroy(self, request, recipe_id, attribute_name):
        recipe_instance = get_object_or_404(Recipe, pk=recipe_id)
        related_queryset = getattr(recipe_instance, attribute_name)
        user_related_data = related_queryset.filter(user=request.user)

        if user_related_data.exists():
            user_related_data.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)

        return Response(status=status.HTTP_400_BAD_REQUEST)


class ShoppingCartController(viewsets.ViewSet, GenericCreateDeleteMixin):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, id):
        return self.generic_create(
            request, id, 'shopping_list_recipes', ShoppingList
            )

    def destroy(self, request, id):
        return self.generic_destroy(request, id, 'shopping_list_recipes')


class FavoriteRecipeController(viewsets.ViewSet, GenericCreateDeleteMixin):
    permission_classes = (permissions.IsAuthenticated,)

    def create(self, request, id):
        return self.generic_create(
            request, id, 'favorite_recipes', FavoriteRecipe
            )

    def destroy(self, request, id):
        return self.generic_destroy(request, id, 'favorite_recipes')
