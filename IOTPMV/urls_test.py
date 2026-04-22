"""Minimal URL configuration for tests — avoids importing xhtml2pdf/cairo."""
from django.contrib import admin
from django.urls import path

urlpatterns = [
    path('admin/', admin.site.urls),
]
