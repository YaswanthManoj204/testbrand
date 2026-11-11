from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DomainViewSet,
    IndustryViewSet,
    BusinessCardViewSet,
    WebsiteViewSet,
    platform_health,
)

router = DefaultRouter()
router.register(r'domains', DomainViewSet, basename='domain')
router.register(r'industries', IndustryViewSet, basename='industry')
router.register(r'cards', BusinessCardViewSet, basename='card')
router.register(r'websites', WebsiteViewSet, basename='website')

urlpatterns = [
    path('health/', platform_health, name='platform-health'),
    path('', include(router.urls)),
]

