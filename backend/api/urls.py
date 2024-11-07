from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.routers import DefaultRouter
from api.views import (FollowViewSet, IngredientViewSet,
                       FavoriteRecipeController,
                       ShoppingCartController,
                       TagViewSet, UserViewSet)

router_v1 = DefaultRouter()
router_v1.register('users', UserViewSet, basename='user')
router_v1.register('tags', TagViewSet, basename='tag')
router_v1.register('ingredients', IngredientViewSet, basename='ingredient')
router_v1.register('recipes', FavoriteRecipeController, basename='recipe')

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Аутентификация
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    
    path('api/auth/token/login/', TokenCreateView.as_view(), name='token_login'),
    path('api/auth/token/logout/', TokenDestroyView.as_view(), name='token_logout'),

    # API V1
    path('api/v1/', include(router_v1.urls)),

    # Обратная поддержка для /api/users/
    path('api/users/', include(router_v1.urls)),

    # Дополнительные маршруты, не покрытые router
    # Подписка на пользователей
    path('api/v1/users/<int:user_id>/subscribe/', 
         FollowViewSet.as_view({'post': 'create', 'delete': 'destroy'}), 
         name='subscribe'),

    # Картинки покупок
    path('api/v1/recipes/<int:id>/shopping_cart/', 
         ShoppingCartController.as_view({'post': 'create', 'delete': 'destroy'}), 
         name='shopping_cart'),

    # Обновление аватарки текущего пользователя
    path('api/v1/users/me/avatar/', 
         UserViewSet.as_view({'put': 'update_avatar'}), 
         name='update_avatar_me'),

    # Создание/удаление избранного
    path('api/v1/recipes/<int:id>/favorite/', 
         FavoriteRecipeController.as_view({'post': 'create', 'delete': 'destroy'}), 
         name='favorite'),

    # Обновление аватарки пользователя по ID
    path('api/v1/users/<int:id>/avatar/', 
         UserViewSet.as_view({'put': 'update_avatar'}), 
         name='update_avatar'),
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
        )