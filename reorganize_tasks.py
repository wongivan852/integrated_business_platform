#!/usr/bin/env python
"""
Reorganize IAICC project tasks into proper WBS order
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_platform.settings')
django.setup()

from project_management.models import Task, Project

def reorganize_tasks():
    """Reorganize all tasks in IAICC project into proper WBS order"""

    # Get the IAICC project
    project = Project.objects.get(id=11)
    print(f"Reorganizing tasks for project: {project.name}\n")

    # Define the proper order structure
    order_counter = 10.0

    # Step 1: Organize WBS structure (1.0 through 12.0)
    wbs_codes = [
        'IAICC-WBS-1.0',  # Venue Management
        'IAICC-WBS-2.0',  # Guest Management
        'IAICC-WBS-3.0',  # Sponsorship & Partnerships
        'IAICC-WBS-4.0',  # Content & Programming
        'IAICC-WBS-5.0',  # Marketing & Communications
        'IAICC-WBS-6.0',  # Technical Infrastructure
        'IAICC-WBS-7.0',  # Event Materials
        'IAICC-WBS-8.0',  # Logistics & Operations
        'IAICC-WBS-9.0',  # Exhibition Area
        'IAICC-WBS-10.0', # Training & Rehearsal
        'IAICC-WBS-11.0', # Event Execution
        'IAICC-WBS-12.0', # Post-Event
    ]

    print("=== Organizing WBS Structure ===")
    for wbs_code in wbs_codes:
        try:
            wbs_task = Task.objects.get(project=project, task_code=wbs_code)
            wbs_task.order = order_counter
            wbs_task.parent_task = None
            wbs_task.indent_level = 0
            wbs_task.save()
            print(f"✓ {wbs_code} -> Order: {order_counter}")
            order_counter += 10

            # Get and order all children of this WBS
            children = Task.objects.filter(project=project, parent_task=wbs_task).exclude(
                task_code__startswith='T0'  # Exclude temporary tasks that might be misplaced
            ).order_by('task_code')

            for child in children:
                child.order = order_counter
                child.indent_level = 1
                child.save()
                print(f"  ├─ {child.task_code} -> Order: {order_counter}")
                order_counter += 10

        except Task.DoesNotExist:
            print(f"✗ {wbs_code} not found")
            continue

    # Step 2: Handle orphaned IAICC-XXX tasks (IAICC-001 to IAICC-029)
    # These need to be analyzed and potentially assigned to proper WBS categories
    print("\n=== Analyzing Orphaned Tasks (IAICC-001 to IAICC-029) ===")
    orphaned_tasks = Task.objects.filter(
        project=project,
        task_code__regex=r'^IAICC-\d{3}$',
        parent_task__isnull=True
    ).order_by('task_code')

    # Map tasks to appropriate WBS categories based on their titles
    task_mapping = {
        # Venue Management (1.0)
        'IAICC-001': 'IAICC-WBS-1.0',  # Venue Confirmation

        # Guest Management (2.0)
        'IAICC-006': 'IAICC-WBS-2.0',  # Flight Booking
        'IAICC-009': 'IAICC-WBS-2.0',  # Hotel Reservations

        # Sponsorship & Partnerships (3.0)
        'IAICC-002': 'IAICC-WBS-3.0',  # Sponsor Outreach
        'IAICC-003': 'IAICC-WBS-3.0',  # Partner Agreements
        'IAICC-004': 'IAICC-WBS-3.0',  # School Partnerships

        # Content & Programming (4.0)
        'IAICC-005': 'IAICC-WBS-4.0',  # Speaker Assets Collection
        'IAICC-007': 'IAICC-WBS-4.0',  # PPT Submission
        'IAICC-008': 'IAICC-WBS-4.0',  # Content Compliance Review
        'IAICC-014': 'IAICC-WBS-4.0',  # Training Content Development

        # Marketing & Communications (5.0)
        'IAICC-010': 'IAICC-WBS-5.0',  # Media Kit Preparation
        'IAICC-011': 'IAICC-WBS-5.0',  # Press Release 1
        'IAICC-012': 'IAICC-WBS-5.0',  # Website Updates

        # Technical Infrastructure (6.0)
        'IAICC-013': 'IAICC-WBS-6.0',  # Livestream Setup
        'IAICC-015': 'IAICC-WBS-6.0',  # Translation Equipment
        'IAICC-018': 'IAICC-WBS-6.0',  # Website UAT

        # Event Materials (7.0)
        'IAICC-016': 'IAICC-WBS-7.0',  # Materials Design
        'IAICC-017': 'IAICC-WBS-7.0',  # Materials Printing

        # Logistics & Operations (8.0)
        'IAICC-019': 'IAICC-WBS-8.0',  # Equipment Installation
        'IAICC-020': 'IAICC-WBS-8.0',  # Materials Installation

        # Training & Rehearsal (10.0)
        'IAICC-021': 'IAICC-WBS-10.0',  # First Rehearsal
        'IAICC-022': 'IAICC-WBS-10.0',  # Full Rehearsal
        'IAICC-023': 'IAICC-WBS-10.0',  # Staff Training
        'IAICC-024': 'IAICC-WBS-10.0',  # Pre-Conference Visits

        # Event Execution (11.0)
        'IAICC-025': 'IAICC-WBS-11.0',  # Main Event Day 1
        'IAICC-026': 'IAICC-WBS-11.0',  # Main Event Day 2
        'IAICC-027': 'IAICC-WBS-11.0',  # Event Documentation

        # Post-Event (12.0)
        'IAICC-028': 'IAICC-WBS-12.0',  # Final Payments
        'IAICC-029': 'IAICC-WBS-12.0',  # Post-Event Report
    }

    for task in orphaned_tasks:
        if task.task_code in task_mapping:
            parent_code = task_mapping[task.task_code]
            try:
                parent_task = Task.objects.get(project=project, task_code=parent_code)
                task.parent_task = parent_task
                task.order = order_counter
                task.indent_level = 1
                task.save()
                print(f"✓ {task.task_code} ({task.title[:40]}) -> Parent: {parent_code}, Order: {order_counter}")
                order_counter += 10
            except Task.DoesNotExist:
                print(f"✗ Parent {parent_code} not found for {task.task_code}")
        else:
            print(f"⚠ {task.task_code} ({task.title[:40]}) - No mapping defined")

    # Step 3: Fix misplaced T0xxx tasks
    print("\n=== Fixing Misplaced Tasks ===")

    # T0137 - Move in material to venue (should be under 8.0 Logistics)
    try:
        task = Task.objects.get(project=project, task_code='T0137')
        parent = Task.objects.get(project=project, task_code='IAICC-WBS-8.0')
        task.parent_task = parent
        task.order = order_counter
        task.indent_level = 1
        task.save()
        print(f"✓ T0137 moved to 8.0 Logistics, Order: {order_counter}")
        order_counter += 10
    except Task.DoesNotExist:
        pass

    # 8.4 - Insurance (should be under 8.0 Logistics)
    try:
        task = Task.objects.get(project=project, task_code='8.4')
        parent = Task.objects.get(project=project, task_code='IAICC-WBS-8.0')
        task.parent_task = parent
        task.order = order_counter
        task.indent_level = 1
        task.save()
        print(f"✓ 8.4 moved to 8.0 Logistics, Order: {order_counter}")
        order_counter += 10
    except Task.DoesNotExist:
        pass

    # T0140 - Related licence or approval (should be under 8.0 Logistics or 1.0 Venue)
    try:
        task = Task.objects.get(project=project, task_code='T0140')
        parent = Task.objects.get(project=project, task_code='IAICC-WBS-1.0')  # Permits belong to Venue
        task.parent_task = parent
        task.order = order_counter
        task.indent_level = 1
        task.save()
        print(f"✓ T0140 moved to 1.0 Venue Management, Order: {order_counter}")
        order_counter += 10
    except Task.DoesNotExist:
        pass

    # T0138, T0139 - Rehearsals (should be under 10.0 Training & Rehearsal)
    for task_code in ['T0138', 'T0139']:
        try:
            # Get all instances (there might be duplicates)
            tasks = Task.objects.filter(project=project, task_code=task_code)
            for task in tasks:
                parent = Task.objects.get(project=project, task_code='IAICC-WBS-10.0')
                task.parent_task = parent
                task.order = order_counter
                task.indent_level = 1
                task.save()
                print(f"✓ {task_code} moved to 10.0 Training & Rehearsal, Order: {order_counter}")
                order_counter += 10
        except Task.DoesNotExist:
            pass

    # Step 4: Organize Milestones
    print("\n=== Organizing Milestones ===")
    milestones = Task.objects.filter(
        project=project,
        task_code__regex=r'^M\d+$'
    ).order_by('task_code')

    for milestone in milestones:
        milestone.order = order_counter
        milestone.parent_task = None
        milestone.indent_level = 0
        milestone.save()
        print(f"✓ {milestone.task_code} -> Order: {order_counter}")
        order_counter += 10

    # Step 5: Organize Deliverables
    print("\n=== Organizing Deliverables ===")
    deliverables = Task.objects.filter(
        project=project,
        task_code__startswith='IAICC-DEL-'
    ).order_by('task_code')

    for deliverable in deliverables:
        deliverable.order = order_counter
        deliverable.parent_task = None
        deliverable.indent_level = 0
        deliverable.save()
        print(f"✓ {deliverable.task_code} -> Order: {order_counter}")
        order_counter += 10

    # Step 6: Organize Risks
    print("\n=== Organizing Risks ===")
    risks = Task.objects.filter(
        project=project,
        task_code__regex=r'^R\d+$'
    ).order_by('task_code')

    for risk in risks:
        risk.order = order_counter
        risk.parent_task = None
        risk.indent_level = 0
        risk.save()
        print(f"✓ {risk.task_code} -> Order: {order_counter}")
        order_counter += 10

    # Step 7: Organize Team Structure
    print("\n=== Organizing Team Structure ===")
    try:
        team = Task.objects.get(project=project, task_code='IAICC-TEAMS')
        team.order = order_counter
        team.parent_task = None
        team.indent_level = 0
        team.save()
        print(f"✓ IAICC-TEAMS -> Order: {order_counter}")
    except Task.DoesNotExist:
        pass

    print("\n✅ Task reorganization complete!")
    print(f"Total tasks processed: {Task.objects.filter(project=project).count()}")

if __name__ == '__main__':
    reorganize_tasks()
