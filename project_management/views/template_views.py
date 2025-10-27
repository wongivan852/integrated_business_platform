"""
Project Template Views
Handles template creation, browsing, and project instantiation from templates
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db import transaction, models
from django.utils import timezone
from datetime import timedelta
import json

from ..models import (
    ProjectTemplate, TemplateTask, TemplateDependency,
    Project, Task, TaskDependency, ProjectMember
)
from ..utils.permissions import check_project_access


@login_required
def template_list(request):
    """
    Display list of available project templates
    Supports filtering and search
    """
    # Get all templates (public + user's private)
    templates = ProjectTemplate.objects.filter(
        is_public=True
    ) | ProjectTemplate.objects.filter(
        created_by=request.user
    )
    templates = templates.distinct().order_by('-created_at')

    # Apply filters
    category = request.GET.get('category')
    if category:
        templates = templates.filter(category=category)

    search = request.GET.get('search')
    if search:
        templates = templates.filter(name__icontains=search) | \
                   templates.filter(description__icontains=search)

    # Get categories for filter dropdown
    categories = ProjectTemplate.CATEGORY_CHOICES

    # Calculate statistics for each template
    template_data = []
    for template in templates:
        task_count = template.template_tasks.count()
        usage_count = Project.objects.filter(created_from_template=template).count()
        template_data.append({
            'template': template,
            'task_count': task_count,
            'usage_count': usage_count,
            'is_owner': template.created_by == request.user
        })

    context = {
        'template_data': template_data,
        'categories': categories,
        'filters': {
            'category': category,
            'search': search,
        }
    }

    return render(request, 'project_management/template_list.html', context)


@login_required
def template_detail(request, template_id):
    """
    Display detailed view of a template with task structure
    """
    template = get_object_or_404(ProjectTemplate, pk=template_id)

    # Check access (public templates or owner)
    if not template.is_public and template.created_by != request.user:
        messages.error(request, 'You do not have permission to view this template.')
        return redirect('project_management:template_list')

    # Get template tasks ordered by sequence
    template_tasks = template.template_tasks.all().order_by('sequence_number')

    # Get dependencies
    dependencies = TemplateDependency.objects.filter(
        task__template=template
    ).select_related('task', 'depends_on')

    # Build dependency map
    dependency_map = {}
    for dep in dependencies:
        if dep.task.id not in dependency_map:
            dependency_map[dep.task.id] = []
        dependency_map[dep.task.id].append({
            'depends_on': dep.depends_on,
            'dependency_type': dep.get_dependency_type_display()
        })

    # Calculate total estimated hours
    total_hours = sum([task.estimated_hours for task in template_tasks])

    # Usage statistics
    usage_count = Project.objects.filter(created_from_template=template).count()
    recent_uses = Project.objects.filter(
        created_from_template=template
    ).order_by('-created_at')[:5]

    context = {
        'template': template,
        'template_tasks': template_tasks,
        'dependency_map': dependency_map,
        'total_hours': total_hours,
        'usage_count': usage_count,
        'recent_uses': recent_uses,
        'is_owner': template.created_by == request.user,
    }

    return render(request, 'project_management/template_detail.html', context)


@login_required
def template_create(request):
    """
    Create a new project template from scratch
    """
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        category = request.POST.get('category')
        default_duration_days = request.POST.get('default_duration_days')
        estimated_budget = request.POST.get('estimated_budget')
        is_public = request.POST.get('is_public') == 'on'

        # Validation
        if not name:
            messages.error(request, 'Template name is required.')
            return redirect('project_management:template_create')

        # Create template
        template = ProjectTemplate.objects.create(
            name=name,
            description=description,
            category=category,
            created_by=request.user,
            default_duration_days=int(default_duration_days) if default_duration_days else 30,
            estimated_budget=float(estimated_budget) if estimated_budget else None,
            is_public=is_public
        )

        messages.success(request, f'Template "{template.name}" created successfully!')
        return redirect('project_management:template_detail', template_id=template.id)

    # GET request - show form
    categories = ProjectTemplate.CATEGORY_CHOICES

    context = {
        'categories': categories,
    }

    return render(request, 'project_management/template_form.html', context)


@login_required
def template_edit(request, template_id):
    """
    Edit an existing template
    """
    template = get_object_or_404(ProjectTemplate, pk=template_id)

    # Check ownership
    if template.created_by != request.user:
        messages.error(request, 'You do not have permission to edit this template.')
        return redirect('project_management:template_detail', template_id=template.id)

    if request.method == 'POST':
        template.name = request.POST.get('name')
        template.description = request.POST.get('description')
        template.category = request.POST.get('category')
        template.default_duration_days = int(request.POST.get('default_duration_days', 30))
        estimated_budget = request.POST.get('estimated_budget')
        template.estimated_budget = float(estimated_budget) if estimated_budget else None
        template.is_public = request.POST.get('is_public') == 'on'
        template.save()

        messages.success(request, 'Template updated successfully!')
        return redirect('project_management:template_detail', template_id=template.id)

    # GET request - show form
    categories = ProjectTemplate.CATEGORY_CHOICES

    context = {
        'template': template,
        'categories': categories,
        'is_edit': True,
    }

    return render(request, 'project_management/template_form.html', context)


@login_required
def template_delete(request, template_id):
    """
    Delete a template
    """
    template = get_object_or_404(ProjectTemplate, pk=template_id)

    # Check ownership
    if template.created_by != request.user:
        messages.error(request, 'You do not have permission to delete this template.')
        return redirect('project_management:template_detail', template_id=template.id)

    if request.method == 'POST':
        template_name = template.name
        template.delete()
        messages.success(request, f'Template "{template_name}" deleted successfully!')
        return redirect('project_management:template_list')

    # GET request - show confirmation
    context = {
        'template': template,
    }

    return render(request, 'project_management/template_confirm_delete.html', context)


@login_required
def project_from_template(request, template_id):
    """
    Create a new project from a template
    """
    template = get_object_or_404(ProjectTemplate, pk=template_id)

    # Check access
    if not template.is_public and template.created_by != request.user:
        messages.error(request, 'You do not have permission to use this template.')
        return redirect('project_management:template_list')

    if request.method == 'POST':
        # Get form data
        project_name = request.POST.get('project_name')
        project_description = request.POST.get('project_description')
        project_code = request.POST.get('project_code')
        start_date_str = request.POST.get('start_date')
        duration_days = int(request.POST.get('duration_days', template.default_duration_days))
        budget = request.POST.get('budget')

        # Validation
        if not project_name:
            messages.error(request, 'Project name is required.')
            return redirect('project_management:project_from_template', template_id=template.id)

        # Parse start date
        if start_date_str:
            start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        else:
            start_date = timezone.now().date()

        end_date = start_date + timedelta(days=duration_days)

        # Create project from template
        try:
            with transaction.atomic():
                # Create project
                project = Project.objects.create(
                    name=project_name,
                    description=project_description or template.description,
                    project_code=project_code,
                    owner=request.user,
                    start_date=start_date,
                    end_date=end_date,
                    budget=float(budget) if budget else template.estimated_budget,
                    status='planning',
                    created_from_template=template
                )

                # Add creator as owner
                ProjectMember.objects.create(
                    project=project,
                    user=request.user,
                    role='owner'
                )

                # Create tasks from template
                task_map = {}  # Map template task IDs to new task IDs
                template_tasks = template.template_tasks.all().order_by('sequence_number')

                for template_task in template_tasks:
                    # Calculate task dates based on sequence
                    task_start = start_date + timedelta(days=(template_task.sequence_number * 2))
                    task_duration = max(1, int(template_task.estimated_hours / 8))  # Convert hours to days
                    task_end = task_start + timedelta(days=task_duration)

                    # Create task
                    task = Task.objects.create(
                        project=project,
                        name=template_task.name,
                        description=template_task.description,
                        start_date=task_start,
                        due_date=task_end,
                        estimated_hours=template_task.estimated_hours,
                        status='todo'
                    )

                    task_map[template_task.id] = task

                # Create dependencies
                dependencies = TemplateDependency.objects.filter(
                    task__template=template
                )

                for dep in dependencies:
                    if dep.task.id in task_map and dep.depends_on.id in task_map:
                        TaskDependency.objects.create(
                            task=task_map[dep.task.id],
                            depends_on=task_map[dep.depends_on.id],
                            dependency_type=dep.dependency_type
                        )

                messages.success(
                    request,
                    f'Project "{project.name}" created successfully with {len(task_map)} tasks!'
                )
                return redirect('project_management:project_detail', pk=project.id)

        except Exception as e:
            messages.error(request, f'Error creating project: {str(e)}')
            return redirect('project_management:project_from_template', template_id=template.id)

    # GET request - show form
    # Get template tasks for preview
    template_tasks = template.template_tasks.all().order_by('sequence_number')[:5]
    total_tasks = template.template_tasks.count()

    context = {
        'template': template,
        'template_tasks': template_tasks,
        'total_tasks': total_tasks,
        'today': timezone.now().date(),
    }

    return render(request, 'project_management/project_from_template.html', context)


@login_required
@require_http_methods(["POST"])
def api_save_as_template(request, project_pk):
    """
    Save an existing project as a template
    """
    project = get_object_or_404(Project, pk=project_pk)

    # Check permission
    has_access, user_role = check_project_access(request.user, project)
    if not has_access or user_role not in ['owner', 'manager']:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to save this project as a template.'
        }, status=403)

    try:
        data = json.loads(request.body)
        template_name = data.get('template_name')
        template_description = data.get('template_description', '')
        category = data.get('category', 'other')
        is_public = data.get('is_public', False)

        if not template_name:
            return JsonResponse({
                'success': False,
                'error': 'Template name is required.'
            }, status=400)

        with transaction.atomic():
            # Calculate project duration
            if project.start_date and project.end_date:
                duration = (project.end_date - project.start_date).days
            else:
                duration = 30

            # Create template
            template = ProjectTemplate.objects.create(
                name=template_name,
                description=template_description,
                category=category,
                created_by=request.user,
                default_duration_days=duration,
                estimated_budget=project.budget,
                is_public=is_public
            )

            # Copy tasks
            tasks = project.tasks.all().order_by('task_code')
            task_map = {}

            for idx, task in enumerate(tasks):
                template_task = TemplateTask.objects.create(
                    template=template,
                    name=task.name,
                    description=task.description,
                    estimated_hours=task.estimated_hours or 8.0,
                    assignee_role='member',  # Default role
                    sequence_number=idx
                )
                task_map[task.id] = template_task

            # Copy dependencies
            dependencies = TaskDependency.objects.filter(task__project=project)
            for dep in dependencies:
                if dep.task.id in task_map and dep.depends_on.id in task_map:
                    TemplateDependency.objects.create(
                        task=task_map[dep.task.id],
                        depends_on=task_map[dep.depends_on.id],
                        dependency_type=dep.dependency_type
                    )

            return JsonResponse({
                'success': True,
                'template_id': template.id,
                'message': f'Template "{template.name}" created with {len(task_map)} tasks!'
            })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_add_template_task(request, template_id):
    """
    Add a task to a template
    """
    template = get_object_or_404(ProjectTemplate, pk=template_id)

    # Check ownership
    if template.created_by != request.user:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to modify this template.'
        }, status=403)

    try:
        data = json.loads(request.body)
        task_name = data.get('name')
        task_description = data.get('description', '')
        estimated_hours = float(data.get('estimated_hours', 8.0))
        assignee_role = data.get('assignee_role', 'member')

        if not task_name:
            return JsonResponse({
                'success': False,
                'error': 'Task name is required.'
            }, status=400)

        # Get next sequence number
        max_seq = template.template_tasks.aggregate(
            models.Max('sequence_number')
        )['sequence_number__max'] or 0

        # Create task
        template_task = TemplateTask.objects.create(
            template=template,
            name=task_name,
            description=task_description,
            estimated_hours=estimated_hours,
            assignee_role=assignee_role,
            sequence_number=max_seq + 1
        )

        return JsonResponse({
            'success': True,
            'task_id': template_task.id,
            'message': 'Task added successfully!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_remove_template_task(request, template_id, task_id):
    """
    Remove a task from a template
    """
    template = get_object_or_404(ProjectTemplate, pk=template_id)
    template_task = get_object_or_404(TemplateTask, pk=task_id, template=template)

    # Check ownership
    if template.created_by != request.user:
        return JsonResponse({
            'success': False,
            'error': 'You do not have permission to modify this template.'
        }, status=403)

    try:
        task_name = template_task.name
        template_task.delete()

        return JsonResponse({
            'success': True,
            'message': f'Task "{task_name}" removed successfully!'
        })

    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
