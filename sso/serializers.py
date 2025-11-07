"""SSO serializers for user data and permissions."""
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserPermissionsSerializer(serializers.Serializer):
    """Serialize user permissions for SSO token."""

    can_access_leave_system = serializers.BooleanField()
    can_access_quotation_system = serializers.BooleanField()
    can_access_expense_system = serializers.BooleanField()
    can_access_crm_system = serializers.BooleanField()
    can_access_asset_management = serializers.BooleanField()
    can_access_stripe_dashboard = serializers.BooleanField()


class SSOUserSerializer(serializers.ModelSerializer):
    """Serialize user data for SSO token."""

    permissions = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    department_display = serializers.CharField(source='get_department_display', read_only=True)
    region_display = serializers.CharField(source='get_region_display', read_only=True)

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
            'department',
            'department_display',
            'region',
            'region_display',
            'is_staff',
            'is_superuser',
            'is_active',
            'apps_access',
            'permissions',
        ]
        read_only_fields = fields

    def get_permissions(self, obj):
        """Get user permissions from apps_access field."""
        # Map internal app names to permission keys
        apps_map = {
            'leave_system': 'can_access_leave_system',
            'quotation_system': 'can_access_quotation_system',
            'expense_system': 'can_access_expense_system',
            'crm_system': 'can_access_crm_system',
            'asset_management': 'can_access_asset_management',
            'stripe_dashboard': 'can_access_stripe_dashboard',
        }

        permissions = {}
        for app_key, perm_key in apps_map.items():
            permissions[perm_key] = obj.has_app_access(app_key) if hasattr(obj, 'has_app_access') else obj.is_superuser

        return permissions


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
