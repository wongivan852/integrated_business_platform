"""SSO serializers for user data and permissions."""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from authentication.models import UserProfile

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
    company_name = serializers.CharField(source='company.name', read_only=True, allow_null=True)
    department_name = serializers.CharField(source='department.name', read_only=True, allow_null=True)

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
            'job_title',
            'is_staff',
            'is_superuser',
            'is_active',
            'company_name',
            'department_name',
            'permissions',
        ]
        read_only_fields = fields

    def get_permissions(self, obj):
        """Get user permissions from UserProfile."""
        try:
            profile = obj.userprofile
            return {
                'can_access_leave_system': profile.can_access_leave_system,
                'can_access_quotation_system': profile.can_access_quotation_system,
                'can_access_expense_system': profile.can_access_expense_system,
                'can_access_crm_system': profile.can_access_crm_system,
                'can_access_asset_management': profile.can_access_asset_management,
                'can_access_stripe_dashboard': profile.can_access_stripe_dashboard,
            }
        except UserProfile.DoesNotExist:
            # Return default permissions if profile doesn't exist
            return {
                'can_access_leave_system': True,
                'can_access_quotation_system': False,
                'can_access_expense_system': True,
                'can_access_crm_system': False,
                'can_access_asset_management': False,
                'can_access_stripe_dashboard': False,
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
