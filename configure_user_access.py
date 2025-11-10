"""
User Access Configuration Script
Configure app access for users based on email addresses and roles.

Usage:
    python configure_user_access.py

This script will:
1. Show current user access
2. Configure access based on user roles and departments
3. Create audit logs
4. Display summary of changes
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_platform.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from core.models import UserAppAccess, AppAccessAuditLog
from apps.app_integrations.registry import INTEGRATED_APPS

User = get_user_model()


# ============================================================================
# USER ACCESS CONFIGURATION
# ============================================================================

# Define access rules based on email patterns and roles
# Format: {'email': {'app_code': 'role', ...}}

USER_ACCESS_CONFIG = {
    # Platform Administrator - Full access to all apps
    'admin@krystal-platform.com': {
        'expense_claims': 'admin',
        'leave_system': 'admin',
        'asset_management': 'admin',
        'crm': 'admin',
        'quotations': 'admin',
        'stripe': 'admin',
        'event_management': 'admin',
        'project_management': 'admin',
        'attendance': 'admin',
    },

    # Ivan Wong - IT Manager - Full admin access
    'ivan.wong@krystal.institute': {
        'expense_claims': 'admin',
        'leave_system': 'admin',
        'asset_management': 'admin',
        'crm': 'admin',
        'quotations': 'admin',
        'stripe': 'admin',
        'event_management': 'admin',
        'project_management': 'admin',
        'attendance': 'admin',
    },

    # Test User - Basic employee access to core apps
    'test.user@krystal.institute': {
        'expense_claims': 'employee',
        'leave_system': 'employee',
        'event_management': 'employee',
        'project_management': 'employee',
        'attendance': 'employee',
    },
}

# Default access for all employees (if not specified above)
# Set to None to disable default access
DEFAULT_EMPLOYEE_ACCESS = {
    'expense_claims': 'employee',
    'leave_system': 'employee',
    'attendance': 'employee',
}

# Department-based access (optional)
# Format: {'department': {'app_code': 'role', ...}}
DEPARTMENT_ACCESS = {
    'IT': {
        'project_management': 'manager',
        'asset_management': 'manager',
    },
    'Finance': {
        'expense_claims': 'manager',
        'stripe': 'manager',
    },
    'HR': {
        'leave_system': 'manager',
        'attendance': 'manager',
    },
    'Sales': {
        'crm': 'manager',
        'quotations': 'manager',
    },
}


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def get_user_by_email(email):
    """Get user by email address."""
    try:
        return User.objects.get(email=email, is_active=True)
    except User.DoesNotExist:
        return None


def get_or_create_access(user, app_code, role, granted_by=None):
    """Get or create user app access."""
    access, created = UserAppAccess.objects.get_or_create(
        user=user,
        app_code=app_code,
        defaults={
            'role': role,
            'is_active': True,
            'granted_by': granted_by,
        }
    )

    if not created and access.role != role:
        # Update role if changed
        old_role = access.role
        access.role = role
        access.modified_by = granted_by
        access.save()
        return access, 'updated', old_role

    return access, 'created' if created else 'unchanged', None


def print_section(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(title)
    print("=" * 70)


# ============================================================================
# MAIN CONFIGURATION FUNCTION
# ============================================================================

def configure_user_access(dry_run=False):
    """
    Configure user access based on the configuration above.

    Args:
        dry_run: If True, only show what would be changed without making changes
    """
    print_section("USER ACCESS CONFIGURATION")

    if dry_run:
        print("🔍 DRY RUN MODE - No changes will be made")
    else:
        print("✅ LIVE MODE - Changes will be applied")

    # Get admin user for audit trail
    admin_user = User.objects.filter(is_superuser=True).first()

    changes_summary = {
        'created': 0,
        'updated': 0,
        'unchanged': 0,
        'errors': 0,
    }

    changes_detail = []

    # Process each user in configuration
    print_section("PROCESSING USER ACCESS CONFIGURATION")

    for email, access_config in USER_ACCESS_CONFIG.items():
        user = get_user_by_email(email)

        if not user:
            print(f"\n⚠️  User not found: {email}")
            changes_summary['errors'] += 1
            continue

        print(f"\n👤 User: {user.email} ({user.first_name} {user.last_name})")

        for app_code, role in access_config.items():
            if app_code not in INTEGRATED_APPS:
                print(f"   ⚠️  Unknown app: {app_code}")
                changes_summary['errors'] += 1
                continue

            if not dry_run:
                with transaction.atomic():
                    access, status, old_role = get_or_create_access(
                        user, app_code, role, admin_user
                    )
                    changes_summary[status] += 1

                    if status == 'created':
                        print(f"   ✅ Granted {role} access to {INTEGRATED_APPS[app_code]['name']}")
                        changes_detail.append({
                            'user': user.email,
                            'app': app_code,
                            'action': 'granted',
                            'role': role,
                        })
                    elif status == 'updated':
                        print(f"   🔄 Updated {app_code} access: {old_role} → {role}")
                        changes_detail.append({
                            'user': user.email,
                            'app': app_code,
                            'action': 'updated',
                            'old_role': old_role,
                            'new_role': role,
                        })
                    else:
                        print(f"   ℹ️  {app_code}: {role} (unchanged)")
            else:
                # Dry run - check what would change
                existing = UserAppAccess.objects.filter(
                    user=user, app_code=app_code, is_active=True
                ).first()

                if not existing:
                    print(f"   🔍 Would grant {role} access to {INTEGRATED_APPS[app_code]['name']}")
                    changes_summary['created'] += 1
                elif existing.role != role:
                    print(f"   🔍 Would update {app_code}: {existing.role} → {role}")
                    changes_summary['updated'] += 1
                else:
                    print(f"   ℹ️  {app_code}: {role} (unchanged)")
                    changes_summary['unchanged'] += 1

    # Process department-based access (optional)
    if DEPARTMENT_ACCESS:
        print_section("PROCESSING DEPARTMENT-BASED ACCESS")

        for user in User.objects.filter(is_active=True):
            department = getattr(user, 'department', None)

            if department and department in DEPARTMENT_ACCESS:
                print(f"\n👥 Department: {department} - User: {user.email}")

                for app_code, role in DEPARTMENT_ACCESS[department].items():
                    # Only apply if user doesn't have specific config
                    if user.email not in USER_ACCESS_CONFIG or \
                       app_code not in USER_ACCESS_CONFIG[user.email]:

                        if not dry_run:
                            with transaction.atomic():
                                access, status, old_role = get_or_create_access(
                                    user, app_code, role, admin_user
                                )
                                changes_summary[status] += 1

                                if status == 'created':
                                    print(f"   ✅ Granted {role} access to {app_code}")
                        else:
                            print(f"   🔍 Would grant {role} access to {app_code}")
                            changes_summary['created'] += 1

    # Process default employee access (optional)
    if DEFAULT_EMPLOYEE_ACCESS:
        print_section("PROCESSING DEFAULT EMPLOYEE ACCESS")

        for user in User.objects.filter(is_active=True, is_staff=False):
            # Skip users with specific configuration
            if user.email in USER_ACCESS_CONFIG:
                continue

            print(f"\n👤 Employee: {user.email}")

            for app_code, role in DEFAULT_EMPLOYEE_ACCESS.items():
                if not dry_run:
                    with transaction.atomic():
                        access, status, old_role = get_or_create_access(
                            user, app_code, role, admin_user
                        )
                        changes_summary[status] += 1

                        if status == 'created':
                            print(f"   ✅ Granted {role} access to {app_code}")
                else:
                    print(f"   🔍 Would grant {role} access to {app_code}")
                    changes_summary['created'] += 1

    # Print summary
    print_section("CONFIGURATION SUMMARY")

    if dry_run:
        print("\n🔍 DRY RUN - No actual changes were made\n")
    else:
        print("\n✅ CONFIGURATION COMPLETE\n")

    print(f"Access Grants Created:  {changes_summary['created']}")
    print(f"Access Grants Updated:  {changes_summary['updated']}")
    print(f"Access Grants Unchanged: {changes_summary['unchanged']}")
    print(f"Errors:                 {changes_summary['errors']}")
    print(f"Total Processed:        {sum(changes_summary.values())}")

    # Show current state
    print_section("CURRENT USER ACCESS STATE")

    for user in User.objects.filter(is_active=True).order_by('email'):
        print(f"\n👤 {user.email} ({user.first_name} {user.last_name})")

        access_list = UserAppAccess.objects.filter(user=user, is_active=True)
        if access_list.exists():
            for access in access_list:
                app_name = INTEGRATED_APPS.get(access.app_code, {}).get('name', access.app_code)
                print(f"   ✅ {app_name}: {access.role}")
        else:
            print(f"   ⚠️  No app access configured")

    return changes_summary, changes_detail


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

def show_usage():
    """Show usage examples."""
    print_section("USAGE INSTRUCTIONS")

    print("""
This script configures user access to apps based on email addresses.

1. CUSTOMIZE THE CONFIGURATION:
   Edit USER_ACCESS_CONFIG in this file to set access for specific users.

   Example:
   USER_ACCESS_CONFIG = {
       'john.doe@company.com': {
           'expense_claims': 'employee',
           'leave_system': 'employee',
       },
       'jane.manager@company.com': {
           'expense_claims': 'manager',
           'leave_system': 'manager',
           'stripe': 'admin',
       },
   }

2. ROLE LEVELS:
   - 'none': No access (explicitly deny)
   - 'employee': Basic employee access
   - 'manager': Manager-level access
   - 'admin': Full administrative access

3. RUN DRY RUN FIRST (recommended):
   python configure_user_access.py --dry-run

   This shows what changes would be made without actually making them.

4. APPLY CHANGES:
   python configure_user_access.py

   This will apply the configuration and update the database.

5. DEPARTMENT-BASED ACCESS:
   You can also configure access by department in DEPARTMENT_ACCESS.
   This applies to all users in that department (unless overridden).

6. DEFAULT ACCESS:
   Set DEFAULT_EMPLOYEE_ACCESS to grant basic access to all employees.
   Set to None to disable default access.
""")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

if __name__ == '__main__':
    import sys

    # Check for dry-run flag
    dry_run = '--dry-run' in sys.argv or '-d' in sys.argv

    # Check for help flag
    if '--help' in sys.argv or '-h' in sys.argv:
        show_usage()
        sys.exit(0)

    try:
        changes_summary, changes_detail = configure_user_access(dry_run=dry_run)

        if not dry_run:
            print("\n✅ Configuration applied successfully!")
            print("\nYou can now:")
            print("1. Log in to http://localhost:8000/admin-panel/")
            print("2. View the access matrix and audit logs")
            print("3. Test user logins to verify access")
        else:
            print("\n🔍 Dry run complete!")
            print("\nTo apply these changes, run:")
            print("python configure_user_access.py")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
