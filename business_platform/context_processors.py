"""
Context processors for making global variables available in templates.
"""

from django.conf import settings


def app_context(request):
    """
    Make app version and other global settings available in all templates.
    """
    return {
        'APP_VERSION': getattr(settings, 'APP_VERSION', '1.0.0'),
        'APP_VERSION_DATE': getattr(settings, 'APP_VERSION_DATE', ''),
    }
