from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from djoser.views import TokenCreateView, TokenDestroyView

from rest_framework.routers import DefaultRouter

from api.views import IngredientViewSet, RecipeViewSet, TagViewSet, UserViewSet

router = DefaultRouter()
router.register('users', UserViewSet, basename='user')
router.register('tags', TagViewSet, basename='tag')
router.register('ingredients', IngredientViewSet, basename='ingredient')
router.register('recipes', RecipeViewSet, basename='recipe')


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
]

if settings.DEBUG:
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
