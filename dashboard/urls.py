"""
URL configuration for dashboard app.
"""

from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('sso/<str:app_name>/', views.sso_redirect, name='sso_redirect'),
]