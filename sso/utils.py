"""SSO utility functions for token management."""
import jwt
import uuid
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from .models import SSOToken, SSOAuditLog


class SSOTokenManager:
    """Manager for SSO JWT tokens."""

    @staticmethod
    def get_secret_key():
        """Get SSO secret key from settings."""
        return getattr(settings, 'SSO_SECRET_KEY', settings.SECRET_KEY)

    @staticmethod
    def get_algorithm():
        """Get JWT algorithm from settings."""
        return getattr(settings, 'SSO_ALGORITHM', 'HS256')

    @staticmethod
    def get_token_lifetime():
        """Get access token lifetime in seconds."""
        return getattr(settings, 'SSO_TOKEN_LIFETIME', 3600)  # 1 hour default

    @staticmethod
    def get_refresh_lifetime():
        """Get refresh token lifetime in seconds."""
        return getattr(settings, 'SSO_REFRESH_LIFETIME', 86400)  # 24 hours default

    @classmethod
    def generate_token(cls, user, request=None):
        """
        Generate JWT access and refresh tokens for a user.

        Args:
            user: Django User instance
            request: HTTP request (for audit logging)

        Returns:
            dict: {
                'access': access_token,
                'refresh': refresh_token,
                'jti': token_id
            }
        """
        now = timezone.now()
        jti = str(uuid.uuid4())

        # Get user permissions
        try:
            profile = user.userprofile
            permissions = {
                'leave_system': profile.can_access_leave_system,
                'quotation_system': profile.can_access_quotation_system,
                'expense_system': profile.can_access_expense_system,
                'crm_system': profile.can_access_crm_system,
                'asset_management': profile.can_access_asset_management,
                'stripe_dashboard': profile.can_access_stripe_dashboard,
            }
        except:
            # Default permissions
            permissions = {
                'leave_system': True,
                'quotation_system': False,
                'expense_system': True,
                'crm_system': False,
                'asset_management': False,
                'stripe_dashboard': False,
            }

        # Access token payload
        access_payload = {
            'jti': jti,
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'employee_id': getattr(user, 'employee_id', ''),
            'job_title': '',  # CompanyUser doesn't have job_title field
            'is_staff': user.is_staff,
            'is_superuser': user.is_superuser,
            'is_active': user.is_active,
            'company': None,  # CompanyUser doesn't have company field
            'department': getattr(user, 'department', None),  # department is a string, not a FK
            'region': getattr(user, 'region', None),
            'permissions': permissions,
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(seconds=cls.get_token_lifetime())).timestamp()),
            'token_type': 'access',
        }

        # Refresh token payload (minimal data)
        refresh_payload = {
            'jti': jti + '_refresh',
            'user_id': user.id,
            'username': user.username,
            'iat': int(now.timestamp()),
            'exp': int((now + timedelta(seconds=cls.get_refresh_lifetime())).timestamp()),
            'token_type': 'refresh',
        }

        # Generate tokens
        access_token = jwt.encode(
            access_payload,
            cls.get_secret_key(),
            algorithm=cls.get_algorithm()
        )
        refresh_token = jwt.encode(
            refresh_payload,
            cls.get_secret_key(),
            algorithm=cls.get_algorithm()
        )

        # Store token in database
        ip_address = None
        user_agent = ''
        if request:
            ip_address = SSOAuditLog.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        SSOToken.objects.create(
            user=user,
            jti=jti,
            token=access_token,
            refresh_token=refresh_token,
            issued_at=now,
            expires_at=now + timedelta(seconds=cls.get_token_lifetime()),
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Log event
        if request:
            SSOAuditLog.log_event(
                'token_issued',
                user=user,
                request=request,
                token_id=jti
            )

        return {
            'access': access_token,
            'refresh': refresh_token,
            'jti': jti
        }

    @classmethod
    def validate_token(cls, token, request=None):
        """
        Validate a JWT token.

        Args:
            token: JWT token string
            request: HTTP request (for audit logging)

        Returns:
            dict: Decoded token payload if valid
            None: If token is invalid

        Raises:
            jwt.ExpiredSignatureError: If token is expired
            jwt.InvalidTokenError: If token is invalid
        """
        try:
            # Decode token
            payload = jwt.decode(
                token,
                cls.get_secret_key(),
                algorithms=[cls.get_algorithm()]
            )

            # Check token type
            if payload.get('token_type') != 'access':
                raise jwt.InvalidTokenError('Invalid token type')

            # Check if token is revoked
            jti = payload.get('jti')
            if jti:
                try:
                    sso_token = SSOToken.objects.get(jti=jti)
                    if not sso_token.is_valid():
                        if request:
                            SSOAuditLog.log_event(
                                'token_validated',
                                request=request,
                                token_id=jti,
                                status='revoked'
                            )
                        raise jwt.InvalidTokenError('Token has been revoked')

                    # Update last used
                    sso_token.last_used = timezone.now()
                    sso_token.save(update_fields=['last_used'])
                except SSOToken.DoesNotExist:
                    pass  # Token not in database, but payload is valid

            # Log successful validation
            if request:
                SSOAuditLog.log_event(
                    'token_validated',
                    user_id=payload.get('user_id'),
                    request=request,
                    token_id=jti,
                    status='success'
                )

            return payload

        except jwt.ExpiredSignatureError:
            if request:
                SSOAuditLog.log_event(
                    'token_validated',
                    request=request,
                    status='expired'
                )
            raise

        except jwt.InvalidTokenError as e:
            if request:
                SSOAuditLog.log_event(
                    'token_validated',
                    request=request,
                    status='invalid',
                    error=str(e)
                )
            raise

    @classmethod
    def refresh_token(cls, refresh_token, request=None):
        """
        Refresh an access token using a refresh token.

        Args:
            refresh_token: Refresh token string
            request: HTTP request (for audit logging)

        Returns:
            dict: New access token

        Raises:
            jwt.InvalidTokenError: If refresh token is invalid
        """
        try:
            # Decode refresh token
            payload = jwt.decode(
                refresh_token,
                cls.get_secret_key(),
                algorithms=[cls.get_algorithm()]
            )

            # Check token type
            if payload.get('token_type') != 'refresh':
                raise jwt.InvalidTokenError('Invalid token type')

            # Get user
            from django.contrib.auth import get_user_model
            User = get_user_model()
            user = User.objects.get(id=payload['user_id'])

            # Generate new access token (keep same jti base)
            result = cls.generate_token(user, request)

            # Log event
            if request:
                SSOAuditLog.log_event(
                    'token_refreshed',
                    user=user,
                    request=request
                )

            return result

        except Exception as e:
            if request:
                SSOAuditLog.log_event(
                    'token_refreshed',
                    request=request,
                    status='failed',
                    error=str(e)
                )
            raise

    @classmethod
    def revoke_token(cls, jti, reason="Manual revocation"):
        """Revoke a token by JTI."""
        try:
            token = SSOToken.objects.get(jti=jti)
            token.revoke(reason)
            SSOAuditLog.log_event(
                'token_revoked',
                user=token.user,
                token_id=jti,
                reason=reason
            )
            return True
        except SSOToken.DoesNotExist:
            return False

    @classmethod
    def revoke_user_tokens(cls, user, reason="User logout"):
        """Revoke all active tokens for a user."""
        SSOToken.revoke_user_tokens(user)
        SSOAuditLog.log_event(
            'token_revoked',
            user=user,
            reason=reason
        )


class SSOPermissionChecker:
    """Helper class to check SSO permissions."""

    APP_PERMISSION_MAP = {
        'leave_system': 'leave_system',
        'quotation_system': 'quotation_system',
        'expense_system': 'expense_system',
        'crm_system': 'crm_system',
        'asset_management': 'asset_management',
        'stripe_dashboard': 'stripe_dashboard',
        # URL path mappings
        'leave': 'leave_system',
        'quotations': 'quotation_system',
        'expenses': 'expense_system',
        'crm': 'crm_system',
        'assets': 'asset_management',
        'stripe': 'stripe_dashboard',
    }

    @classmethod
    def can_access_app(cls, token_payload, app_name):
        """
        Check if user can access an app based on token permissions.

        Args:
            token_payload: Decoded JWT payload
            app_name: App identifier

        Returns:
            bool: True if user can access the app
        """
        # Admin/staff can access everything
        if token_payload.get('is_superuser') or token_payload.get('is_staff'):
            return True

        # Get permission key
        permission_key = cls.APP_PERMISSION_MAP.get(app_name)
        if not permission_key:
            return False

        # Check permission in token
        permissions = token_payload.get('permissions', {})
        return permissions.get(permission_key, False)
