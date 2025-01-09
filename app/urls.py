# urls.py
# urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from .views import (
    DriverViewSet,
    DriverLoginView,
    DriverLogoutView,
    DriverProfileView,
    DriverTokenRefreshView, passenger_login, passenger_logout
    
)

router = DefaultRouter()
router.register(r'driver', DriverViewSet, basename='driver')

urlpatterns = [
    path('drivera/login/', DriverLoginView.as_view()),
    path('drivera/logout/', DriverLogoutView.as_view()),
    path('drivera/profile/', DriverProfileView.as_view()),
    path('drivera/refresh/', DriverTokenRefreshView.as_view()),
    path('passenger/login/', passenger_login, name='passenger_login'),
    path('passenger/logout/', passenger_logout, name='passenger_logout'),
    path('passenger/dashboard/', views.PassengerDashboardView.as_view(), name='passenger_dashboard'),
    path('passenger/schedules/', views.RouteScheduleView.as_view(), name='passenger_schedules'),
    path('passenger/history/', views.TravelHistoryView.as_view(), name='passenger_history'),
    path('passenger/tracking/', views.BusTrackingView.as_view(), name='passenger_tracking'),
    
    # URLs pour les API (mises à jour en temps réel et filtres)
    path('api/schedules/', views.get_route_schedule, name='api_route_schedules'),
    path('api/history/filter/', views.filter_travel_history, name='api_travel_history'),
    path('api/bus/locations/', views.get_real_time_bus_locations, name='api_bus_locations'),
    path('api/notifications/unread/', views.get_unread_notifications, name='api_unread_notifications'),
    path('api/notifications/<int:notification_id>/read/', views.mark_notification_as_read, name='api_read_notification'),
    path('', include(router.urls)),
]