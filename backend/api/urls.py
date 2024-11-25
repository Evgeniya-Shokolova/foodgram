from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from djoser.views import TokenCreateView, TokenDestroyView
from rest_framework.routers import DefaultRouter

from .views import (FollowViewSet, IngredientViewSet, RecipeViewSet,
                    TagViewSet, UserViewSet)

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register(r'recipes', RecipeViewSet, basename='recipe')
# router.register('shopping_cart', RecipeViewSet, basename='shopping_cart')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.authtoken')),
    path('api/auth/token/login/',
         TokenCreateView.as_view(),
         name='token_login'),
    path('api/auth/token/logout/',
         TokenDestroyView.as_view(),
         name='token_logout'),
    path('api/', include(router.urls)),
    path('api/users/<int:user_id>/subscribe/',
         FollowViewSet.as_view({'post': 'create', 'delete': 'destroy'}),
         name='subscribe'),
    # path('api/recipes/<int:pk>/get_link/',
    # RecipeViewSet.as_view({'get': 'get_link'}),
    # name='get_link'),
    path('api/users/me/avatar/',
         UserViewSet.as_view({'put': 'set_avatar'}),
         name='update_avatar_me'),
    path('api/users/<int:id>/avatar/',
         UserViewSet.as_view({'put': 'set_avatar'}),
         name='update_avatar')
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
