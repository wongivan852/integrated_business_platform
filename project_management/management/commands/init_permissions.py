"""
Django management command to initialize default roles and permissions.
Run with: python manage.py init_permissions
"""

from django.core.management.base import BaseCommand
from project_management.permissions_utils import initialize_default_roles_and_permissions


class Command(BaseCommand):
    help = 'Initialize default roles and permissions for the project management system'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.NOTICE('Initializing default roles and permissions...'))

        try:
            summary = initialize_default_roles_and_permissions()

            self.stdout.write(self.style.SUCCESS('\n✅ Successfully initialized permission system!'))
            self.stdout.write(self.style.SUCCESS(f'   - Created {summary["roles_created"]} roles'))
            self.stdout.write(self.style.SUCCESS(f'   - Created {summary["permissions_created"]} permissions'))

            self.stdout.write(self.style.NOTICE('\nDefault roles created:'))
            self.stdout.write('   - Administrator (admin): Full system access')
            self.stdout.write('   - Project Manager (project_manager): Manage projects and teams')
            self.stdout.write('   - Developer (developer): Work on tasks and projects')
            self.stdout.write('   - Viewer (viewer): Read-only access')

            self.stdout.write(self.style.NOTICE('\nPermission categories initialized:'))
            self.stdout.write('   - Project permissions (view, create, edit, delete, manage, export)')
            self.stdout.write('   - Task permissions (view, create, edit, delete, assign, comment)')
            self.stdout.write('   - Resource permissions (view, create, edit, delete)')
            self.stdout.write('   - Report permissions (view, create, export)')
            self.stdout.write('   - User & Role management (manage)')

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Error initializing permissions: {str(e)}'))
            raise e
