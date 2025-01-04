# urls.py
# urls.py
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    UserProfileView,
    LogoutView,
    DriverViewSet
)

urlpatterns = [
    # Authentication URLs
    path('auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/logout/', LogoutView.as_view(), name='auth_logout'),
    path('auth/profile/', UserProfileView.as_view(), name='user_profile'),
    
    # Driver URLs
    path('driver/verify-nfc/', DriverViewSet.as_view({'post': 'verify_nfc'}), name='verify_nfc'),
    path('driver/update-location/', DriverViewSet.as_view({'post': 'update_location'}), name='update_location'),
    path('driver/today-passengers/', DriverViewSet.as_view({'get': 'today_passengers'}), name='today_passengers'),
]