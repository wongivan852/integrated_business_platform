"""
Middleware for authentication-related checks.
"""

from django.shortcuts import redirect, render
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import get_language


class PasswordChangeRequiredMiddleware:
    """
    Middleware to enforce password change for users with password_change_required=True.
    Redirects to password change page after login if password change is required.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # List of URLs that should be accessible even when password change is required
        exempt_urls = [
            reverse('authentication:logout'),
            reverse('authentication:change_password'),
            reverse('authentication:change_password_required'),
        ]

        # Check if user is authenticated and has password_change_required flag
        if (
            request.user.is_authenticated
            and hasattr(request.user, 'password_change_required')
            and request.user.password_change_required
            and request.path not in exempt_urls
            and not request.path.startswith('/static/')
            and not request.path.startswith('/media/')
        ):
            # Show message only once per session
            if not request.session.get('password_change_message_shown', False):
                messages.warning(
                    request,
                    'For security reasons, you must change your password before continuing.'
                )
                request.session['password_change_message_shown'] = True

            # Redirect to the forced password change page (not the voluntary one)
            return redirect('authentication:change_password_required')

        response = self.get_response(request)
        return response


class MaintenanceModeMiddleware:
    """
    Middleware to check for maintenance mode and display maintenance message.
    Checks each app's maintenance status based on request path.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip for static/media files
        if request.path.startswith('/static/') or request.path.startswith('/media/'):
            return self.get_response(request)

        # Skip for admin and authentication URLs
        if request.path.startswith('/admin/') or request.path.startswith('/authentication/'):
            return self.get_response(request)

        # Get current app from request path
        app_name = self._get_app_name_from_path(request.path)

        if app_name:
            # Check if app is in maintenance mode
            from .models import ApplicationConfig

            try:
                app_config = ApplicationConfig.objects.get(name=app_name, is_maintenance=True)

                # Allow superusers to bypass if configured
                if app_config.allow_superuser_access and request.user.is_authenticated and request.user.is_superuser:
                    response = self.get_response(request)
                    return response

                # Get maintenance message based on language
                current_language = get_language()
                if current_language == 'zh-hans' and app_config.maintenance_message_cn:
                    message = app_config.maintenance_message_cn
                else:
                    message = app_config.maintenance_message or 'This application is currently under maintenance. Please check back later.'

                # Render maintenance page
                return render(request, 'authentication/maintenance.html', {
                    'app_name': app_config.display_name,
                    'maintenance_message': message,
                    'app_icon': app_config.icon,
                    'app_color': app_config.color,
                })

            except ApplicationConfig.DoesNotExist:
                # App not in maintenance mode or doesn't exist
                pass

        response = self.get_response(request)
        return response

    def _get_app_name_from_path(self, path):
        """Extract app name from URL path."""
        # Map URL patterns to app names
        app_mappings = {
            '/project-management/': 'project_management',
            '/leave-management/': 'leave_management',
            '/expense-reports/': 'expense_reports',
            '/dashboard/': 'dashboard',
        }

        for url_pattern, app_name in app_mappings.items():
            if path.startswith(url_pattern):
                return app_name

        return None
