# urls.py
# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DriverViewSet,
    DriverLoginView,
    DriverLogoutView,
    DriverProfileView,
    DriverTokenRefreshView
)

router = DefaultRouter()
router.register(r'driver', DriverViewSet, basename='driver')

urlpatterns = [
    path('drivera/login/', DriverLoginView.as_view()),
    path('drivera/logout/', DriverLogoutView.as_view()),
    path('drivera/profile/', DriverProfileView.as_view()),
    path('drivera/refresh/', DriverTokenRefreshView.as_view()),
    path('', include(router.urls)),
]