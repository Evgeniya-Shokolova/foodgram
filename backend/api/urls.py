from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.routers import DefaultRouter
from api.views import (FollowViewSet, IngredientViewSet, FavoriteRecipeController,
                       ShoppingCartController, TagViewSet, UserViewSet)

# Создаем маршрутизатор
router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', FavoriteRecipeController, basename='recipe')

# Определяем URL-шаблоны
urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),

    path('api/auth/token/login/', TokenCreateView.as_view(), name='token_login'),
    path('api/auth/token/logout/', TokenDestroyView.as_view(), name='token_logout'),

    path('api/', include(router.urls)),

    # Подписка на пользователей
    path('api/users/<int:user_id>/subscribe/', 
         FollowViewSet.as_view({'post': 'create', 'delete': 'destroy'}),
         name='subscribe'),

    # Управление покупками
    path('api/recipes/<int:id>/shopping_cart/', 
         ShoppingCartController.as_view({'post': 'create', 'delete': 'destroy'}),
         name='shopping_cart'),

    # Обновление аватара
    path('api/users/me/avatar/',
         UserViewSet.as_view({'put': 'set_avatar'}),
         name='update_avatar_me'),

    path('api/recipes/<int:id>/favorite/', 
         FavoriteRecipeController.as_view({'post': 'create', 'delete': 'destroy'}),
         name='favorite'),

    # Обновление аватара для конкретного пользователя
    path('api/users/<int:id>/avatar/',
         UserViewSet.as_view({'put': 'set_avatar'}),
         name='update_avatar'),
]


if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
        )
