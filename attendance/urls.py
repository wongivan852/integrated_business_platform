"""
URL configuration for attendance app.
"""

from django.urls import path
from . import views

app_name = 'attendance'

urlpatterns = [
    path('', views.attendance_dashboard, name='dashboard'),
    path('profile/setup/', views.profile_setup, name='profile_setup'),
    path('records/', views.attendance_records, name='records'),
]
