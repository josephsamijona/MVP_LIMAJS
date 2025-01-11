from django.urls import path
from .views import GalaxyHomeView

app_name = 'limajs'

urlpatterns = [
    path('', GalaxyHomeView.as_view(), name='home'),
]