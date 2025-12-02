"""SSO middleware for token injection, session management, and enforcement."""
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.http import JsonResponse
from django.conf import settings
from .utils import SSOTokenManager, SSOPermissionChecker
import jwt
import re
import logging

logger = logging.getLogger(__name__)


# Paths that don't require SSO authentication
SSO_EXEMPT_PATHS = [
    r'^/health/',           # Health check endpoints
    r'^/auth/',             # Authentication endpoints
    r'^/api/sso/',          # SSO API endpoints
    r'^/admin/',            # Django admin (uses session auth)
    r'^/static/',           # Static files
    r'^/media/',            # Media files
    r'^/favicon\.ico$',     # Favicon
    r'^/i18n/',             # Internationalization
    r'^/__debug__/',        # Django debug toolbar
]

# Compile regex patterns for performance
SSO_EXEMPT_PATTERNS = [re.compile(pattern) for pattern in SSO_EXEMPT_PATHS]


class SSOEnforcementMiddleware(MiddlewareMixin):
    """
    Middleware to enforce SSO authentication on all requests.

    This middleware:
    1. Checks if the request path requires SSO authentication
    2. Validates the SSO token (from session, cookie, or header)
    3. Redirects to login if no valid token is found
    4. Attaches user info to request for downstream use

    Configuration:
    - SSO_EXEMPT_PATHS: List of regex patterns for exempt paths
    - SSO_ENFORCE: Set to False to disable enforcement (default: True)
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.enforce = getattr(settings, 'SSO_ENFORCE', True)

    def __call__(self, request):
        # Skip if enforcement is disabled
        if not self.enforce:
            return self.get_response(request)

        # Skip exempt paths
        if self._is_exempt_path(request.path):
            return self.get_response(request)

        # Skip if user is already authenticated via Django session
        if request.user.is_authenticated:
            # Ensure SSO token exists in session
            self._ensure_sso_token(request)
            return self.get_response(request)

        # Try to validate SSO token
        token = self._get_token(request)

        if token:
            try:
                # Validate token
                payload = SSOTokenManager.validate_token(token, request)

                # Attach token payload to request
                request.sso_user = payload
                request.sso_token = token

                # Authenticate user via Django if not already
                if not request.user.is_authenticated:
                    self._authenticate_from_token(request, payload)

                return self.get_response(request)

            except jwt.ExpiredSignatureError:
                logger.debug(f"SSO token expired for path: {request.path}")
                return self._handle_invalid_token(request, 'Token expired')

            except jwt.InvalidTokenError as e:
                logger.debug(f"Invalid SSO token for path: {request.path}: {e}")
                return self._handle_invalid_token(request, str(e))

            except Exception as e:
                logger.error(f"SSO validation error: {e}")
                return self._handle_invalid_token(request, 'Validation error')

        # No token found - redirect to login
        return self._redirect_to_login(request)

    def _is_exempt_path(self, path):
        """Check if path is exempt from SSO enforcement."""
        for pattern in SSO_EXEMPT_PATTERNS:
            if pattern.match(path):
                return True
        return False

    def _get_token(self, request):
        """Get SSO token from various sources."""
        # 1. Check session
        token = request.session.get('sso_access_token')
        if token:
            return token

        # 2. Check cookie
        token = request.COOKIES.get('sso_token')
        if token:
            return token

        # 3. Check Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]

        # 4. Check query parameter (for redirects)
        token = request.GET.get('sso_token')
        if token:
            # Store in session for future requests
            request.session['sso_access_token'] = token
            return token

        return None

    def _ensure_sso_token(self, request):
        """Ensure authenticated user has SSO token in session."""
        if not request.session.get('sso_access_token'):
            try:
                # Generate new token for authenticated user
                tokens = SSOTokenManager.generate_token(request.user, request)
                request.session['sso_access_token'] = tokens['access']
                request.session['sso_refresh_token'] = tokens['refresh']
                request.session['sso_token_jti'] = tokens['jti']
                request.sso_token = tokens['access']
            except Exception as e:
                logger.error(f"Failed to generate SSO token: {e}")

    def _authenticate_from_token(self, request, payload):
        """Authenticate user from token payload."""
        try:
            from django.contrib.auth import get_user_model, login
            User = get_user_model()

            user = User.objects.get(id=payload['user_id'])
            if user.is_active:
                # Use Django's login to set session
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
        except Exception as e:
            logger.error(f"Failed to authenticate user from token: {e}")

    def _redirect_to_login(self, request):
        """Redirect to login page."""
        login_url = getattr(settings, 'LOGIN_URL', '/auth/login/')

        # For API requests, return JSON response
        if self._is_api_request(request):
            return JsonResponse({
                'error': 'Authentication required',
                'login_url': login_url
            }, status=401)

        # Build redirect URL with next parameter
        next_url = request.get_full_path()
        if next_url and next_url != login_url:
            return redirect(f"{login_url}?next={next_url}")

        return redirect(login_url)

    def _handle_invalid_token(self, request, reason):
        """Handle invalid or expired token."""
        # Clear invalid token from session
        if 'sso_access_token' in request.session:
            del request.session['sso_access_token']
        if 'sso_refresh_token' in request.session:
            del request.session['sso_refresh_token']

        # For API requests, return JSON response
        if self._is_api_request(request):
            return JsonResponse({
                'error': 'Invalid or expired token',
                'reason': reason
            }, status=401)

        # Redirect to login
        return self._redirect_to_login(request)

    def _is_api_request(self, request):
        """Check if request is an API request."""
        # Check Accept header
        accept = request.META.get('HTTP_ACCEPT', '')
        if 'application/json' in accept:
            return True

        # Check Content-Type
        content_type = request.META.get('CONTENT_TYPE', '')
        if 'application/json' in content_type:
            return True

        # Check path
        if request.path.startswith('/api/'):
            return True

        return False


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
