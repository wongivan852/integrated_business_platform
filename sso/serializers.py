"""SSO serializers for user data and permissions."""
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserPermissionsSerializer(serializers.Serializer):
    """Serialize user permissions for SSO token."""
    # Permissions are now stored in UserAppAccess model
    # and included in JWT token dynamically


class SSOUserSerializer(serializers.ModelSerializer):
    """Serialize user data for SSO token."""

    permissions = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'first_name',
            'last_name',
            'full_name',
            'employee_id',
            'region',
            'department',
            'is_staff',
            'is_superuser',
            'is_active',
            'permissions',
            'roles',
        ]
        read_only_fields = fields

    def get_permissions(self, obj):
        """Get user permissions from UserAppAccess model."""
        from core.models import UserAppAccess
        from apps.app_integrations.registry import INTEGRATED_APPS

        if obj.is_superuser:
            # Superuser has access to all apps
            return {app_key: True for app_key in INTEGRATED_APPS.keys()}

        # Get user's app access from database
        user_accesses = UserAppAccess.objects.filter(
            user=obj,
            is_active=True
        ).values('app_code', 'role')

        access_dict = {access['app_code']: access['role'] for access in user_accesses}

        return {
            app_key: access_dict.get(app_key, 'none') != 'none'
            for app_key in INTEGRATED_APPS.keys()
        }

    def get_roles(self, obj):
        """Get user roles per app from UserAppAccess model."""
        from core.models import UserAppAccess
        from apps.app_integrations.registry import INTEGRATED_APPS

        if obj.is_superuser:
            # Superuser has admin role for all apps
            return {app_key: 'admin' for app_key in INTEGRATED_APPS.keys()}

        # Get user's app access from database
        user_accesses = UserAppAccess.objects.filter(
            user=obj,
            is_active=True
        ).values('app_code', 'role')

        access_dict = {access['app_code']: access['role'] for access in user_accesses}

        return {
            app_key: access_dict.get(app_key, 'none')
            for app_key in INTEGRATED_APPS.keys()
        }


class TokenSerializer(serializers.Serializer):
    """Serialize token response."""

    access = serializers.CharField()
    refresh = serializers.CharField()
    user = SSOUserSerializer(read_only=True)


class TokenRefreshSerializer(serializers.Serializer):
    """Serialize token refresh request."""

    refresh = serializers.CharField()


class TokenValidateSerializer(serializers.Serializer):
    """Serialize token validation response."""

    valid = serializers.BooleanField()
    user = SSOUserSerializer(read_only=True)
    message = serializers.CharField(required=False)
