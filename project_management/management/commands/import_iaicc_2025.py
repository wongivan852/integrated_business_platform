"""
Import IAICC 2025 Conference Project Plan from CSV files
Comprehensive import including Gantt chart, WBS, milestones, deliverables, budget, risks, and team resources
"""
import csv
import os
from datetime import datetime
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from project_management.models import (
    Project, Task, ProjectMember, KanbanColumn,
    TaskLabel, TaskLabelAssignment, TaskComment,
    ProjectCost
)
from django.db import transaction

User = get_user_model()


class Command(BaseCommand):
    help = 'Import IAICC 2025 Conference Project Plan from CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-dir',
            type=str,
            default='/home/user/Downloads/iaicc-2025-csv-export',
            help='Directory containing CSV files'
        )

    def handle(self, *args, **options):
        csv_dir = options['csv_dir']

        self.stdout.write(self.style.WARNING(f'\n{"="*70}'))
        self.stdout.write(self.style.WARNING('IAICC 2025 Project Import'))
        self.stdout.write(self.style.WARNING(f'{"="*70}\n'))
        self.stdout.write(f'CSV Directory: {csv_dir}\n')

        # File paths
        files = {
            'gantt': os.path.join(csv_dir, '01_gantt_chart_tasks.csv'),
            'wbs': os.path.join(csv_dir, '02_wbs.csv'),
            'deliverables': os.path.join(csv_dir, '03_deliverables.csv'),
            'milestones': os.path.join(csv_dir, '04_milestones.csv'),
            'budget': os.path.join(csv_dir, '05_budget.csv'),
            'revenue': os.path.join(csv_dir, '06_revenue.csv'),
            'risks': os.path.join(csv_dir, '07_risks.csv'),
            'teams': os.path.join(csv_dir, '08_teams_resources.csv'),
            'hours': os.path.join(csv_dir, '09_resource_hour_estimates.csv'),
        }

        # Verify all files exist
        for name, path in files.items():
            if not os.path.exists(path):
                self.stdout.write(self.style.ERROR(f'✗ Missing file: {name} at {path}'))
                return
            self.stdout.write(self.style.SUCCESS(f'✓ Found: {name}'))

        with transaction.atomic():
            # Get the project owner (use first admin or superuser)
            owner = User.objects.filter(is_superuser=True).first()
            if not owner:
                owner = User.objects.filter(is_staff=True).first()

            if not owner:
                self.stdout.write(self.style.ERROR('\n✗ No admin user found. Please create one first.'))
                return

            self.stdout.write(f'\nProject Owner: {owner.get_full_name()} ({owner.email})\n')

            # Create or get project
            project, created = Project.objects.get_or_create(
                project_code='IAICC-2025',
                defaults={
                    'name': 'IAICC 2025 - International AI and Creativity Conference',
                    'description': '''International AI and Creativity Conference
December 13-14, 2025
Greater Bay Area, China

A comprehensive project plan for organizing and executing a major international conference on AI and Creativity, including:
- Venue management and logistics
- Speaker and guest coordination
- Marketing and PR campaigns
- Technical infrastructure setup
- Team coordination and resource management
- Budget and financial oversight
''',
                    'start_date': '2024-11-01',
                    'end_date': '2025-12-30',
                    'status': 'active',
                    'priority': 'critical',
                    'owner': owner,
                    'created_by': owner,
                    'default_view': 'gantt',
                    'budget': Decimal('1460000'),  # Max budget estimate in CNY
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
                self.stdout.write('  ✓ Created Kanban columns')
            else:
                self.stdout.write(self.style.WARNING(f'✓ Project already exists: {project.name}'))
                # Clear existing tasks for reimport
                Task.objects.filter(project=project).delete()
                TaskLabel.objects.filter(project=project).delete()
                ProjectCost.objects.filter(project=project).delete()
                Resource.objects.filter(project=project).delete()
                self.stdout.write(self.style.WARNING('  Cleared existing data for reimport'))

            # Import data
            self.stdout.write('\n' + '='*70)
            self.stdout.write('IMPORTING DATA')
            self.stdout.write('='*70 + '\n')

            # 1. Import Task Labels (for categories, risks, etc.)
            self.import_task_labels(project)

            # 2. Import Gantt Chart Tasks
            task_mapping = self.import_gantt_tasks(project, owner, files['gantt'])

            # 3. Import WBS structure and additional tasks
            self.import_wbs_tasks(project, owner, files['wbs'], task_mapping)

            # 4. Import Milestones as special tasks
            self.import_milestones(project, owner, files['milestones'])

            # 5. Import Deliverables as tasks
            self.import_deliverables(project, owner, files['deliverables'])

            # 6. Import Budget & Revenue as Project Costs
            self.import_financial_data(project, owner, files['budget'], files['revenue'])

            # 7. Import Risks as task comments/labels
            self.import_risks(project, owner, files['risks'])

            # 8. Import Teams and Resources
            self.import_team_resources(project, owner, files['teams'])

            # Final Summary
            self.print_summary(project)

    def import_task_labels(self, project):
        """Create task labels for categorization"""
        self.stdout.write('\n[1] Creating Task Labels...')

        labels = [
            ('Critical Path', '#dc3545', 'Tasks on the critical path'),
            ('Phase 1', '#007bff', 'Planning & Setup'),
            ('Phase 2', '#28a745', 'Speaker & Content'),
            ('Phase 3', '#ffc107', 'Marketing & PR'),
            ('Phase 4', '#17a2b8', 'Operations Setup'),
            ('Phase 5', '#6f42c1', 'Final Preparations'),
            ('Phase 6', '#fd7e14', 'Event Execution'),
            ('Phase 7', '#6c757d', 'Wrap-up'),
            ('Risk', '#dc3545', 'Risk item'),
            ('Milestone', '#28a745', 'Project milestone'),
            ('Deliverable', '#17a2b8', 'Project deliverable'),
        ]

        count = 0
        for name, color, desc in labels:
            label, created = TaskLabel.objects.get_or_create(
                project=project,
                name=name,
                defaults={'color': color, 'description': desc}
            )
            if created:
                count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {count} task labels'))

    def import_gantt_tasks(self, project, owner, csv_path):
        """Import Gantt chart tasks"""
        self.stdout.write('\n[2] Importing Gantt Chart Tasks...')

        task_mapping = {}
        phase_mapping = {}

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                phase = row['Phase']
                task_name = row['Task Name']
                start_date_str = row['Start Date']
                end_date_str = row['End Date']
                progress = int(row['Progress %'])
                owner_name = row['Owner']
                is_critical = row['Critical Path'].lower() == 'true'

                # Parse dates (format: Nov 4, Dec 12, etc.)
                start_date = self.parse_date(start_date_str)
                end_date = self.parse_date(end_date_str)

                # Determine status
                status = self.determine_status(start_date, end_date, progress)

                # Generate task code
                task_code = f"IAICC-{len(task_mapping) + 1:03d}"

                # Create task
                task = Task.objects.create(
                    project=project,
                    title=task_name,
                    task_code=task_code,
                    start_date=start_date,
                    end_date=end_date,
                    progress=progress,
                    status=status,
                    priority='critical' if is_critical else 'high',
                    created_by=owner,
                )

                # Add phase label
                phase_num = phase.split(':')[0].strip()
                label = TaskLabel.objects.filter(project=project, name=phase_num).first()
                if label:
                    TaskLabelAssignment.objects.create(task=task, label=label)

                # Add critical path label
                if is_critical:
                    critical_label = TaskLabel.objects.filter(project=project, name='Critical Path').first()
                    if critical_label:
                        TaskLabelAssignment.objects.create(task=task, label=critical_label)

                # Add owner as comment
                TaskComment.objects.create(
                    task=task,
                    author=owner,
                    text=f"Task Owner: {owner_name}"
                )

                task_mapping[task_name] = task
                phase_mapping.setdefault(phase, []).append(task)

        self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {len(task_mapping)} Gantt tasks'))
        return task_mapping

    def import_wbs_tasks(self, project, owner, csv_path, task_mapping):
        """Import WBS structure"""
        self.stdout.write('\n[3] Importing WBS Structure...')

        wbs_count = 0
        parent_tasks = {}

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                parent_code = row['Parent Code']
                parent_name = row['Parent Name']
                wbs_code = row['WBS Code']
                task_name = row['Task Name']
                task_owner = row['Owner']
                deadline_str = row['Deadline']

                # Create parent task if doesn't exist
                if parent_code not in parent_tasks:
                    parent_task = Task.objects.create(
                        project=project,
                        title=f"{parent_code} {parent_name}",
                        task_code=f"IAICC-WBS-{parent_code}",
                        status='in_progress',
                        priority='high',
                        created_by=owner,
                    )
                    parent_tasks[parent_code] = parent_task

                # Check if task already exists in task_mapping
                if task_name not in task_mapping:
                    # Parse deadline
                    end_date = self.parse_date(deadline_str)

                    # Create WBS task
                    task = Task.objects.create(
                        project=project,
                        title=task_name,
                        task_code=wbs_code,
                        parent_task=parent_tasks[parent_code],
                        end_date=end_date,
                        status='todo',
                        priority='medium',
                        created_by=owner,
                        indent_level=1,
                    )

                    # Add owner comment
                    TaskComment.objects.create(
                        task=task,
                        author=owner,
                        text=f"Task Owner: {task_owner}"
                    )

                    task_mapping[task_name] = task
                    wbs_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Created {len(parent_tasks)} parent tasks and {wbs_count} WBS sub-tasks'))

    def import_milestones(self, project, owner, csv_path):
        """Import milestones as special tasks"""
        self.stdout.write('\n[4] Importing Milestones...')

        milestone_label = TaskLabel.objects.filter(project=project, name='Milestone').first()
        count = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                milestone_id = row['Milestone ID']
                date_str = row['Date']
                title = row['Title']
                status = row['Status']
                deliverables = row['Deliverables']
                dependencies = row['Dependencies']
                risks = row['Risks']

                # Parse date
                milestone_date = self.parse_date(date_str)

                # Create milestone task
                task = Task.objects.create(
                    project=project,
                    title=f"🏁 {title}",
                    task_code=milestone_id,
                    start_date=milestone_date,
                    end_date=milestone_date,
                    is_milestone=True,
                    status=self.map_milestone_status(status),
                    priority='critical',
                    created_by=owner,
                    description=f"""**Deliverables:**
{deliverables}

**Dependencies:**
{dependencies}

**Key Risks:**
{risks}
"""
                )

                # Add milestone label
                if milestone_label:
                    TaskLabelAssignment.objects.create(task=task, label=milestone_label)

                count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {count} milestones'))

    def import_deliverables(self, project, owner, csv_path):
        """Import deliverables as tasks"""
        self.stdout.write('\n[5] Importing Deliverables...')

        deliverable_label = TaskLabel.objects.filter(project=project, name='Deliverable').first()
        count = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                category = row['Category']
                deliverable_name = row['Deliverable']
                quantity = row['Quantity']
                deadline_str = row['Deadline']
                task_owner = row['Owner']

                # Parse deadline
                due_date = self.parse_date(deadline_str)

                # Create deliverable task
                task = Task.objects.create(
                    project=project,
                    title=f"📦 {deliverable_name}",
                    task_code=f"IAICC-DEL-{count + 1:03d}",
                    due_date=due_date,
                    status='todo',
                    priority='medium',
                    created_by=owner,
                    description=f"**Category:** {category}\n**Quantity:** {quantity}\n**Owner:** {task_owner}"
                )

                # Add deliverable label
                if deliverable_label:
                    TaskLabelAssignment.objects.create(task=task, label=deliverable_label)

                count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {count} deliverables'))

    def import_financial_data(self, project, owner, budget_csv, revenue_csv):
        """Import budget and revenue data"""
        self.stdout.write('\n[6] Importing Financial Data...')

        # Category mapping
        category_mapping = {
            'Venue & Facilities': 'equipment',
            'Speaker & Guest Management': 'travel',
            'Marketing & PR': 'other',
            'Event Materials & Production': 'materials',
            'Catering & Hospitality': 'other',
            'Technology & Digital': 'software',
            'Insurance & Contingency': 'overhead',
            'Exhibition & Sponsorship': 'other',
        }

        # Import budget items
        budget_count = 0
        with open(budget_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                category_name = row['Category']
                estimated = row['Estimated Budget']
                priority = row['Priority']
                items = row['Items']

                # Parse budget range (e.g., "¥200,000 - ¥300,000")
                amount = self.parse_budget_amount(estimated)

                ProjectCost.objects.create(
                    project=project,
                    category=category_mapping.get(category_name, 'other'),
                    amount=amount,
                    description=f"**{category_name}** ({priority} priority)\n\n{items}",
                    date=datetime.now().date(),
                    vendor='',
                    created_by=owner,
                )
                budget_count += 1

        # Import revenue items (as negative costs/income)
        revenue_count = 0
        with open(revenue_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                source = row['Revenue Source']
                units = row['Units']
                price = row['Price']
                estimated = row['Estimated Revenue']

                # Parse revenue amount (stored as negative for income)
                amount = self.parse_budget_amount(estimated) * -1  # Negative for revenue

                ProjectCost.objects.create(
                    project=project,
                    category='other',
                    amount=amount,
                    description=f"**Revenue: {source}**\nUnits: {units}\nPrice: {price}",
                    date=datetime.now().date(),
                    vendor='',
                    created_by=owner,
                )
                revenue_count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {budget_count} budget items and {revenue_count} revenue items'))

    def import_risks(self, project, owner, csv_path):
        """Import risks and create risk tracking tasks"""
        self.stdout.write('\n[7] Importing Risk Management...')

        risk_label = TaskLabel.objects.filter(project=project, name='Risk').first()
        count = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                risk_id = row['Risk ID']
                category = row['Category']
                description = row['Risk Description']
                probability = row['Probability']
                impact = row['Impact']
                score = row['Score']
                mitigation = row['Mitigation']
                contingency = row['Contingency']
                risk_owner = row['Owner']

                # Determine priority based on score
                score_int = int(score)
                if score_int >= 16:
                    priority = 'critical'
                elif score_int >= 10:
                    priority = 'high'
                elif score_int >= 5:
                    priority = 'medium'
                else:
                    priority = 'low'

                # Create risk task
                task = Task.objects.create(
                    project=project,
                    title=f"⚠️ [{risk_id}] {description}",
                    task_code=risk_id,
                    status='in_progress',
                    priority=priority,
                    created_by=owner,
                    description=f"""**Category:** {category}
**Probability:** {probability}
**Impact:** {impact}
**Risk Score:** {score}

**Mitigation Strategies:**
{mitigation}

**Contingency Plan:**
{contingency}

**Risk Owner:** {risk_owner}
"""
                )

                # Add risk label
                if risk_label:
                    TaskLabelAssignment.objects.create(task=task, label=risk_label)

                count += 1

        self.stdout.write(self.style.SUCCESS(f'  ✓ Imported {count} risk items'))

    def import_team_resources(self, project, owner, csv_path):
        """Import team resources as project documentation"""
        self.stdout.write('\n[8] Importing Team Resources...')

        teams = {}
        total_members = 0

        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                team_name = row['Team Name']
                team_lead = row['Team Lead']
                team_size = row['Team Size']
                role = row['Role']
                name = row['Name']
                allocation = row['Allocation']

                if team_name not in teams:
                    teams[team_name] = {
                        'lead': team_lead,
                        'size': team_size,
                        'members': []
                    }

                teams[team_name]['members'].append({
                    'role': role,
                    'name': name,
                    'allocation': allocation
                })
                total_members += 1

        # Create a task for team documentation
        team_doc = "# IAICC 2025 Team Structure\n\n"
        team_doc += f"Total Teams: {len(teams)}\n"
        team_doc += f"Total Members: {total_members}\n\n"

        for team_name, team_info in teams.items():
            team_doc += f"## {team_name}\n"
            team_doc += f"- **Lead:** {team_info['lead']}\n"
            team_doc += f"- **Size:** {team_info['size']}\n\n"
            team_doc += "**Team Members:**\n"
            for member in team_info['members']:
                team_doc += f"- {member['name']} - {member['role']} ({member['allocation']})\n"
            team_doc += "\n"

        # Create a documentation task
        Task.objects.create(
            project=project,
            title="📋 Team Structure & Resource Allocation",
            task_code="IAICC-TEAMS",
            description=team_doc,
            status='in_progress',
            priority='high',
            created_by=owner,
        )

        self.stdout.write(self.style.SUCCESS(f'  ✓ Documented {len(teams)} teams with {total_members} members'))

    def parse_date(self, date_str):
        """Parse various date formats"""
        if not date_str or date_str.strip() == '':
            return None

        date_str = date_str.strip()

        # Try different date formats
        formats = [
            '%b %d',  # Nov 4
            '%B %d, %Y',  # November 4, 2025
            '%m/%d/%Y',  # 11/04/2025
            '%Y-%m-%d',  # 2025-11-04
        ]

        for fmt in formats:
            try:
                parsed = datetime.strptime(date_str, fmt)
                # If no year specified, assume 2025
                if parsed.year == 1900:
                    parsed = parsed.replace(year=2025)
                return parsed.date()
            except ValueError:
                continue

        # If all else fails, return None
        return None

    def parse_budget_amount(self, budget_str):
        """Parse budget amount from string like '¥200,000 - ¥300,000'"""
        # Take the average of the range
        budget_str = budget_str.replace('¥', '').replace(',', '')

        if ' - ' in budget_str:
            parts = budget_str.split(' - ')
            try:
                low = Decimal(parts[0].strip())
                high = Decimal(parts[1].strip())
                return (low + high) / 2
            except:
                return Decimal('0')
        else:
            try:
                return Decimal(budget_str.strip())
            except:
                return Decimal('0')

    def determine_status(self, start_date, end_date, progress):
        """Determine task status based on dates and progress"""
        if progress == 100:
            return 'completed'

        if not start_date:
            return 'todo'

        today = datetime.now().date()

        if today < start_date:
            return 'todo'
        elif start_date <= today <= (end_date or start_date):
            return 'in_progress'
        elif end_date and today > end_date:
            return 'in_progress'  # Should be completed but isn't

        return 'todo'

    def map_milestone_status(self, status):
        """Map milestone status to task status"""
        mapping = {
            'completed': 'completed',
            'on-track': 'in_progress',
            'at-risk': 'in_progress',
            'upcoming': 'todo',
        }
        return mapping.get(status, 'todo')

    def print_summary(self, project):
        """Print import summary"""
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('IMPORT COMPLETE'))
        self.stdout.write('='*70)

        task_count = Task.objects.filter(project=project).count()
        milestone_count = Task.objects.filter(project=project, is_milestone=True).count()
        label_count = TaskLabel.objects.filter(project=project).count()
        cost_count = ProjectCost.objects.filter(project=project).count()
        member_count = ProjectMember.objects.filter(project=project).count()

        self.stdout.write(f'\n  Project: {project.name}')
        self.stdout.write(f'  Project Code: {project.project_code}')
        self.stdout.write(f'  Status: {project.get_status_display()}')
        self.stdout.write(f'  Priority: {project.get_priority_display()}')
        self.stdout.write(f'  Duration: {project.start_date} to {project.end_date}')
        self.stdout.write(f'  Budget: ¥{project.budget:,.2f}')
        self.stdout.write(f'\n  Tasks: {task_count}')
        self.stdout.write(f'  Milestones: {milestone_count}')
        self.stdout.write(f'  Labels: {label_count}')
        self.stdout.write(f'  Financial Items: {cost_count}')
        self.stdout.write(f'  Project Members: {member_count}')

        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS(f'\n✓ View project in browser:'))
        self.stdout.write(self.style.SUCCESS(f'  http://localhost:8000/project-management/projects/{project.pk}/'))
        self.stdout.write('='*70 + '\n')
