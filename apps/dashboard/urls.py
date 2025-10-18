"""
URL configuration for Dashboard app
"""
from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard_view, name='main'),
    path('launch/<str:app_key>/', views.app_launcher_view, name='app_launcher'),
]
