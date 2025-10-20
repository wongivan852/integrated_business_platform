"""
Attendance Integration App Configuration
"""
from django.apps import AppConfig


class AttendanceIntegrationConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'attendance_integration'
    verbose_name = 'Attendance Integration'

    def ready(self):
        """Import signals when app is ready"""
        import attendance_integration.signals  # noqa
