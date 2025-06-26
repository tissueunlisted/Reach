# C:\entc\reach_app\urls.py

from django.contrib import admin
from django.urls import path, include # Import include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core_app.urls')), # Include URLs from core_app
]
