"""
Import BlenderCom + BlenderStudio Production Plan from CSV
"""
import csv
from datetime import datetime
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from project_management.models import Project, Task, ProjectMember, KanbanColumn
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Import BlenderCom + BlenderStudio Production Plan from CSV'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-path',
            type=str,
            default='/home/user/Downloads/BlenderCom + BlenderStudio Production Plan.csv',
            help='Path to CSV file'
        )

    def handle(self, *args, **options):
        csv_path = options['csv_path']

        self.stdout.write(self.style.WARNING(f'\nImporting from: {csv_path}'))

        # Email mapping for team members
        email_mapping = {
            'Yeung': 'yw.yeung@krystal.institute',
            'Sidne': 'sidne.lui@krystal.institute',
            'Jeff': 'jeff.koo@krystal.institute',
            'Cloudy': 'cloudy.poon@krystal.institute',
            'Adrian': 'adrian.chow@krystal.institute',
            'Tom': 'tom.sin@krystal.institute',
            'Eugene': 'eugene.choy@krystal.institute',
        }

        with transaction.atomic():
            # Get the project owner (use first admin or superuser)
            owner = User.objects.filter(is_superuser=True).first()
            if not owner:
                owner = User.objects.filter(is_staff=True).first()

            if not owner:
                self.stdout.write(self.style.ERROR('No admin user found. Please create one first.'))
                return

            # Create or get project
            project, created = Project.objects.get_or_create(
                project_code='BLENDER-2025',
                defaults={
                    'name': 'BlenderCom + BlenderStudio Production Plan',
                    'description': 'Production plan for BlenderCom and BlenderStudio platform development',
                    'start_date': '2025-02-20',
                    'end_date': '2025-10-28',
                    'status': 'active',
                    'priority': 'high',
                    'owner': owner,
                    'created_by': owner,
                    'default_view': 'gantt',
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'✓ Created project: {project.name}'))

                # Create Kanban columns
                columns = [
                    ('To Do', '#6c757d', 1),
                    ('In Progress', '#ffc107', 2),
                    ('Review', '#17a2b8', 3),
                    ('Done', '#28a745', 4),
                ]

                for name, color, pos in columns:
                    KanbanColumn.objects.create(
                        project=project,
                        name=name,
                        color=color,
                        position=pos
                    )
            else:
                self.stdout.write(self.style.WARNING(f'✓ Project already exists: {project.name}'))
                # Clear existing tasks for reimport
                Task.objects.filter(project=project).delete()
                self.stdout.write(self.style.WARNING('  Cleared existing tasks for reimport'))

            # Read CSV and store task data
            tasks_data = []
            with open(csv_path, 'r', encoding='utf-8-sig') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if row.get(' ID') and row.get(' ID').strip():
                        tasks_data.append(row)

            self.stdout.write(f'\nFound {len(tasks_data)} tasks in CSV')

            # First pass: Create all tasks
            task_mapping = {}  # Map CSV ID to Task object

            for row in tasks_data:
                task_id = row.get(' ID', '').strip()
                if not task_id:
                    continue

                name = row.get('Name', '').strip()
                duration_str = row.get('Duration', '0day').strip()
                start_str = row.get('Start', '').strip()
                finish_str = row.get('Finish', '').strip()
                resources = row.get('Resources', '').strip()

                # Parse duration
                duration = 1
                if 'day' in duration_str:
                    try:
                        duration = float(duration_str.replace('days?', '').replace('days', '').replace('day', '').strip())
                        duration = int(duration) if duration > 0 else 1
                    except:
                        duration = 1

                # Parse dates
                start_date = None
                end_date = None
                try:
                    if start_str:
                        start_date = datetime.strptime(start_str, '%m/%d/%Y').date()
                    if finish_str:
                        end_date = datetime.strptime(finish_str, '%m/%d/%Y').date()
                except:
                    pass

                # Determine status based on dates
                status = 'todo'
                today = datetime.now().date()
                if start_date and end_date:
                    if today > end_date:
                        status = 'completed'
                    elif today >= start_date:
                        status = 'in_progress'

                # Create task
                task = Task.objects.create(
                    project=project,
                    title=name[:300],  # Truncate to max length
                    task_code=f'BLENDER-T{task_id.zfill(3)}',
                    start_date=start_date,
                    end_date=end_date,
                    duration=duration,
                    status=status,
                    priority='medium',
                    progress=100 if status == 'completed' else 0,
                    created_by=owner,
                )

                # Assign resources (team members)
                if resources:
                    for resource_name in resources.split(','):
                        resource_name = resource_name.strip()
                        if resource_name in email_mapping:
                            email = email_mapping[resource_name]
                            try:
                                user = User.objects.get(email=email)

                                # Add user as project member if not already
                                ProjectMember.objects.get_or_create(
                                    project=project,
                                    user=user,
                                    defaults={'role': 'member'}
                                )

                                # Assign to task
                                task.assigned_to.add(user)
                            except User.DoesNotExist:
                                self.stdout.write(
                                    self.style.WARNING(f'  User not found: {email} ({resource_name})')
                                )

                task_mapping[task_id] = task
                self.stdout.write(f'  ✓ Created task {task_id}: {name[:50]}...')

            # Second pass: Set up task dependencies based on predecessors
            self.stdout.write('\nSetting up task dependencies...')
            for row in tasks_data:
                task_id = row.get(' ID', '').strip()
                predecessors = row.get('Predecessors', '').strip()

                if task_id and predecessors and task_id in task_mapping:
                    current_task = task_mapping[task_id]

                    # Parse predecessors (can be comma-separated)
                    for pred_id in predecessors.split(','):
                        pred_id = pred_id.strip()
                        if pred_id in task_mapping:
                            parent_task = task_mapping[pred_id]
                            # Set as parent task (simple hierarchy)
                            if not current_task.parent_task:
                                current_task.parent_task = parent_task
                                current_task.save()
                                self.stdout.write(f'  ✓ Task {task_id} → depends on → Task {pred_id}')
                                break  # Only set first predecessor as parent

            # Summary
            self.stdout.write(self.style.SUCCESS('\n' + '='*60))
            self.stdout.write(self.style.SUCCESS('Import Summary:'))
            self.stdout.write(self.style.SUCCESS(f'  Project: {project.name}'))
            self.stdout.write(self.style.SUCCESS(f'  Project Code: {project.project_code}'))
            self.stdout.write(self.style.SUCCESS(f'  Tasks Imported: {len(task_mapping)}'))
            self.stdout.write(self.style.SUCCESS(f'  Team Members: {ProjectMember.objects.filter(project=project).count()}'))
            self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
            self.stdout.write(
                self.style.SUCCESS(f'View project at: /project-management/{project.pk}/')
            )
