"""
App Registry Service

Provides centralized methods for app discovery, access control, and management.
"""

from django.db.models import Q
from django.core.cache import cache
from .models import ApplicationConfig, Department, DepartmentAppAccess, UserAppAccess, AppAccessLog


class AppRegistryService:
    """
    Service class for app registry operations.
    """

    CACHE_TIMEOUT = 300  # 5 minutes
    CACHE_KEY_ALL_APPS = 'app_registry:all_apps'
    CACHE_KEY_USER_APPS = 'app_registry:user_apps:{user_id}'
    CACHE_KEY_DEPT_APPS = 'app_registry:dept_apps:{dept_code}'

    @classmethod
    def get_all_apps(cls, active_only=True, category=None):
        """
        Get all registered applications.

        Args:
            active_only: Only return active apps
            category: Filter by category

        Returns:
            QuerySet of ApplicationConfig
        """
        cache_key = f"{cls.CACHE_KEY_ALL_APPS}:{active_only}:{category}"
        apps = cache.get(cache_key)

        if apps is None:
            queryset = ApplicationConfig.objects.all()

            if active_only:
                queryset = queryset.filter(is_active=True)

            if category:
                queryset = queryset.filter(category=category)

            apps = list(queryset.order_by('display_order', 'name'))
            cache.set(cache_key, apps, cls.CACHE_TIMEOUT)

        return apps

    @classmethod
    def get_apps_for_user(cls, user):
        """
        Get all apps a user can access.

        Args:
            user: Django User instance

        Returns:
            List of ApplicationConfig objects
        """
        # Superusers can access everything
        if user.is_superuser:
            return cls.get_all_apps(active_only=True)

        cache_key = cls.CACHE_KEY_USER_APPS.format(user_id=user.id)
        apps = cache.get(cache_key)

        if apps is None:
            # Get apps from user's individual access
            user_app_ids = UserAppAccess.objects.filter(
                user=user,
                is_enabled=True,
                access_level__in=['view', 'edit', 'admin']
            ).values_list('app_id', flat=True)

            # Get apps from user's department
            dept_code = getattr(user, 'department', None)
            dept_app_ids = []

            if dept_code:
                try:
                    dept = Department.objects.get(code=dept_code)
                    dept_app_ids = DepartmentAppAccess.objects.filter(
                        department=dept,
                        is_enabled=True
                    ).values_list('app_id', flat=True)
                except Department.DoesNotExist:
                    pass

            # Combine app IDs
            all_app_ids = set(user_app_ids) | set(dept_app_ids)

            # Get apps that don't require permission (public apps)
            public_app_ids = ApplicationConfig.objects.filter(
                is_active=True,
                requires_permission=False
            ).values_list('id', flat=True)

            all_app_ids |= set(public_app_ids)

            # Fetch apps
            apps = list(ApplicationConfig.objects.filter(
                id__in=all_app_ids,
                is_active=True
            ).order_by('display_order', 'name'))

            cache.set(cache_key, apps, cls.CACHE_TIMEOUT)

        return apps

    @classmethod
    def get_apps_for_department(cls, department_code):
        """
        Get all apps available to a department.

        Args:
            department_code: Department code

        Returns:
            List of ApplicationConfig objects
        """
        cache_key = cls.CACHE_KEY_DEPT_APPS.format(dept_code=department_code)
        apps = cache.get(cache_key)

        if apps is None:
            try:
                dept = Department.objects.get(code=department_code)
                app_ids = DepartmentAppAccess.objects.filter(
                    department=dept,
                    is_enabled=True
                ).values_list('app_id', flat=True)

                apps = list(ApplicationConfig.objects.filter(
                    id__in=app_ids,
                    is_active=True
                ).order_by('display_order', 'name'))

            except Department.DoesNotExist:
                apps = []

            cache.set(cache_key, apps, cls.CACHE_TIMEOUT)

        return apps

    @classmethod
    def is_app_accessible(cls, user, app_code):
        """
        Check if a user can access a specific app.

        Args:
            user: Django User instance
            app_code: Application code

        Returns:
            bool: True if user can access the app
        """
        try:
            app = ApplicationConfig.objects.get(code=app_code)
        except ApplicationConfig.DoesNotExist:
            return False

        # App must be active and not in maintenance
        if not app.is_active or app.maintenance_mode:
            return False

        # Superusers can access everything
        if user.is_superuser:
            return True

        # Staff can access everything (optional - remove if not desired)
        if user.is_staff:
            return True

        # App doesn't require permission
        if not app.requires_permission:
            return True

        # Check user's individual access
        user_access = UserAppAccess.objects.filter(
            user=user,
            app=app,
            is_enabled=True,
            access_level__in=['view', 'edit', 'admin']
        ).exists()

        if user_access:
            return True

        # Check department access
        dept_code = getattr(user, 'department', None)
        if dept_code:
            try:
                dept = Department.objects.get(code=dept_code)
                dept_access = DepartmentAppAccess.objects.filter(
                    department=dept,
                    app=app,
                    is_enabled=True
                ).exists()

                if dept_access:
                    return True
            except Department.DoesNotExist:
                pass

        return False

    @classmethod
    def get_access_level(cls, user, app_code):
        """
        Get user's access level for an app.

        Args:
            user: Django User instance
            app_code: Application code

        Returns:
            str: Access level ('none', 'view', 'edit', 'admin')
        """
        try:
            app = ApplicationConfig.objects.get(code=app_code)
        except ApplicationConfig.DoesNotExist:
            return 'none'

        # Superusers have admin access
        if user.is_superuser:
            return 'admin'

        # Check user's individual access
        try:
            user_access = UserAppAccess.objects.get(
                user=user,
                app=app,
                is_enabled=True
            )
            return user_access.access_level
        except UserAppAccess.DoesNotExist:
            pass

        # Check department access (defaults to 'view')
        dept_code = getattr(user, 'department', None)
        if dept_code:
            try:
                dept = Department.objects.get(code=dept_code)
                if DepartmentAppAccess.objects.filter(
                    department=dept,
                    app=app,
                    is_enabled=True
                ).exists():
                    return 'view'
            except Department.DoesNotExist:
                pass

        # App doesn't require permission
        if not app.requires_permission:
            return 'view'

        return 'none'

    @classmethod
    def grant_user_access(cls, user, app_code, access_level='view', granted_by=None, request=None):
        """
        Grant a user access to an app.

        Args:
            user: User to grant access to
            app_code: Application code
            access_level: Access level to grant
            granted_by: User granting access
            request: HTTP request for logging

        Returns:
            UserAppAccess instance
        """
        app = ApplicationConfig.objects.get(code=app_code)

        access, created = UserAppAccess.objects.update_or_create(
            user=user,
            app=app,
            defaults={
                'access_level': access_level,
                'is_enabled': True,
                'granted_by': granted_by,
            }
        )

        # Log the action
        AppAccessLog.log(
            user=user,
            app=app,
            action='access_granted' if created else 'access_modified',
            request=request,
            performed_by=granted_by,
            access_level=access_level,
            previous_level=None if created else access.access_level
        )

        # Clear cache
        cls.clear_user_cache(user.id)

        return access

    @classmethod
    def revoke_user_access(cls, user, app_code, revoked_by=None, request=None):
        """
        Revoke a user's access to an app.

        Args:
            user: User to revoke access from
            app_code: Application code
            revoked_by: User revoking access
            request: HTTP request for logging

        Returns:
            bool: True if access was revoked
        """
        try:
            app = ApplicationConfig.objects.get(code=app_code)
            access = UserAppAccess.objects.get(user=user, app=app)

            previous_level = access.access_level
            access.is_enabled = False
            access.access_level = 'none'
            access.save()

            # Log the action
            AppAccessLog.log(
                user=user,
                app=app,
                action='access_revoked',
                request=request,
                performed_by=revoked_by,
                previous_level=previous_level
            )

            # Clear cache
            cls.clear_user_cache(user.id)

            return True

        except (ApplicationConfig.DoesNotExist, UserAppAccess.DoesNotExist):
            return False

    @classmethod
    def clear_user_cache(cls, user_id):
        """Clear cached apps for a user."""
        cache_key = cls.CACHE_KEY_USER_APPS.format(user_id=user_id)
        cache.delete(cache_key)

    @classmethod
    def clear_department_cache(cls, dept_code):
        """Clear cached apps for a department."""
        cache_key = cls.CACHE_KEY_DEPT_APPS.format(dept_code=dept_code)
        cache.delete(cache_key)

    @classmethod
    def clear_all_cache(cls):
        """Clear all app registry caches."""
        # This is a simple implementation - in production, use cache versioning
        cache.delete_pattern(f"{cls.CACHE_KEY_ALL_APPS}:*")
        cache.delete_pattern(f"app_registry:*")

    @classmethod
    def register_app(cls, code, name, url_path, **kwargs):
        """
        Register a new application.

        Args:
            code: Unique app code
            name: Display name
            url_path: URL path for the app
            **kwargs: Additional ApplicationConfig fields

        Returns:
            ApplicationConfig instance
        """
        app, created = ApplicationConfig.objects.update_or_create(
            code=code,
            defaults={
                'name': name,
                'url_path': url_path,
                **kwargs
            }
        )

        # Clear cache
        cls.clear_all_cache()

        return app

    @classmethod
    def get_app_by_code(cls, app_code):
        """
        Get an app by its code.

        Args:
            app_code: Application code

        Returns:
            ApplicationConfig or None
        """
        try:
            return ApplicationConfig.objects.get(code=app_code)
        except ApplicationConfig.DoesNotExist:
            return None
