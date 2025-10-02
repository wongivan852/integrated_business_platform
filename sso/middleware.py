"""SSO middleware for token injection and session management."""
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
from .utils import SSOTokenManager
import logging

logger = logging.getLogger(__name__)


class SSOTokenInjectionMiddleware(MiddlewareMixin):
    """
    Middleware to inject SSO tokens into requests to secondary apps.

    This middleware:
    1. Detects requests to secondary apps
    2. Generates/retrieves SSO token for authenticated user
    3. Injects token into request (URL parameter or header)
    4. Tracks sessions across apps
    """

    def process_request(self, request):
        """Process incoming requests."""
        # Only process authenticated users
        if not request.user.is_authenticated:
            return None

        # Check if request is to a secondary app
        if not self._is_secondary_app_request(request):
            return None

        # Generate or retrieve SSO token
        try:
            # Check if user already has an active token in session
            sso_token = request.session.get('sso_access_token')

            if not sso_token or not self._is_token_valid(sso_token):
                # Generate new token
                tokens = SSOTokenManager.generate_token(request.user, request)
                sso_token = tokens['access']

                # Store in session
                request.session['sso_access_token'] = sso_token
                request.session['sso_refresh_token'] = tokens['refresh']
                request.session['sso_token_jti'] = tokens['jti']

            # Inject token into request
            request.sso_token = sso_token

        except Exception as e:
            logger.error(f"SSO token generation failed: {str(e)}")
            # Continue without SSO - app should fall back to local auth

        return None

    def process_response(self, request, response):
        """Process outgoing responses."""
        # Update session activity timestamp
        if hasattr(request, 'sso_token') and request.user.is_authenticated:
            request.session.modified = True

        return response

    def _is_secondary_app_request(self, request):
        """Check if request is to a secondary app."""
        # Check if path starts with /apps/
        return request.path.startswith('/apps/')

    def _is_token_valid(self, token):
        """Check if token is still valid."""
        try:
            SSOTokenManager.validate_token(token)
            return True
        except:
            return False
