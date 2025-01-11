from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("admin/", admin.site.urls),
    path('api/', include('app.urls')),
    path('', include('limajs.urls')),  # Ajout de l'URL racine pour limajs
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  # Pour les fichiers statiques