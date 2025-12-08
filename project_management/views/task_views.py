"""
Task CRUD views and API endpoints for Project Management app
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from ..models import Project, Task, KanbanColumn, TaskActivity
from ..forms import TaskForm
from .project_views import check_project_access


# ============================================================================
# Task List View
# ============================================================================

@login_required
def task_list(request, project_pk):
    """
    List all tasks for a project
    """
    project = get_object_or_404(Project, pk=project_pk)

    # Check access
    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have permission to view this project."))
        return redirect('project_management:project_list')

    tasks = project.tasks.select_related(
        'parent_task', 'kanban_column'
    ).prefetch_related('assigned_to').order_by('order', '-created_at')

    # Apply filters
    status_filter = request.GET.get('status')
    if status_filter:
        tasks = tasks.filter(status=status_filter)

    priority_filter = request.GET.get('priority')
    if priority_filter:
        tasks = tasks.filter(priority=priority_filter)

    search_query = request.GET.get('q')
    if search_query:
        tasks = tasks.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(task_code__icontains=search_query)
        )

    context = {
        'project': project,
        'tasks': tasks,
        'user_role': user_role,
        'status_filter': status_filter,
        'priority_filter': priority_filter,
        'search_query': search_query,
        'can_edit': user_role in ['owner', 'admin', 'member'],
    }

    return render(request, 'project_management/task_list.html', context)


# ============================================================================
# Task Create View
# ============================================================================

@login_required
def task_create(request, project_pk):
    """
    Create a new task
    """
    project = get_object_or_404(Project, pk=project_pk)

    # Check access - requires member or higher
    has_access, user_role = check_project_access(request.user, project, required_role='member')
    if not has_access:
        messages.error(request, _("You don't have permission to create tasks in this project."))
        return redirect('project_management:project_detail', pk=project.pk)

    if request.method == 'POST':
        form = TaskForm(request.POST, project=project)
        if form.is_valid():
            task = form.save(commit=False)
            task.project = project
            task.created_by = request.user

            # Generate task code if not provided
            if not task.task_code:
                task_count = project.tasks.count() + 1
                task.task_code = f"{project.project_code}-T{task_count:03d}"

            # Set default kanban column if not set
            if not task.kanban_column and project.default_view == 'kanban':
                first_column = project.kanban_columns.order_by('position').first()
                if first_column:
                    task.kanban_column = first_column

            task.save()
            form.save_m2m()  # Save many-to-many relationships

            # Log activity
            TaskActivity.objects.create(
                task=task,
                user=request.user,
                action='created',
                details={'task_title': task.title}
            )

            messages.success(request, _('Task "{}" created successfully!').format(task.title))

            # Check if user clicked "Save & Add Another"
            if 'save_and_add' in request.POST:
                # Redirect back to task creation page
                return redirect('project_management:task_create', project_pk=project.pk)

            # Redirect based on where user came from
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('project_management:task_detail', project_pk=project.pk, pk=task.pk)
        else:
            # Log validation errors for debugging
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Task form validation failed: {form.errors}")
            messages.error(request, _('Please correct the errors below.'))
    else:
        # Pre-populate column from query param
        initial_data = {}
        column_id = request.GET.get('column')
        if column_id:
            try:
                column = project.kanban_columns.get(pk=column_id)
                initial_data['kanban_column'] = column
            except KanbanColumn.DoesNotExist:
                pass

        form = TaskForm(project=project, initial=initial_data)

    context = {
        'form': form,
        'project': project,
        'action': 'Create',
    }

    return render(request, 'project_management/task_form.html', context)


# ============================================================================
# Task Detail View
# ============================================================================

@login_required
def task_detail(request, project_pk, pk):
    """
    Display detailed view of a single task
    """
    project = get_object_or_404(Project, pk=project_pk)
    task = get_object_or_404(Task, pk=pk, project=project)

    # Check access
    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        messages.error(request, _("You don't have permission to view this task."))
        return redirect('project_management:project_list')

    # Handle comment submission
    if request.method == 'POST' and 'comment' in request.POST:
        comment_text = request.POST.get('comment', '').strip()
        if comment_text:
            from ..models import TaskComment, TaskActivity

            # Create comment
            TaskComment.objects.create(
                task=task,
                author=request.user,
                text=comment_text
            )

            # Log activity
            TaskActivity.objects.create(
                task=task,
                user=request.user,
                action='commented',
                details={'comment': comment_text[:100]}  # First 100 chars
            )

            messages.success(request, _('Comment added successfully!'))
            return redirect('project_management:task_detail', project_pk=project.pk, pk=task.pk)
        else:
            messages.error(request, _('Comment cannot be empty.'))

    # Get related data
    from ..models import TaskComment, TaskAttachment, TaskChecklist

    comments = task.comments.select_related('author').order_by('-created_at')
    attachments = task.attachments.select_related('uploaded_by').order_by('-uploaded_at')
    checklists = task.checklists.prefetch_related('items').order_by('position')
    activities = task.activities.select_related('user').order_by('-timestamp')[:20]
    
    # Check for missing files
    missing_files = [att for att in attachments if not att.file_exists()]
    if missing_files:
        messages.warning(
            request, 
            f'{len(missing_files)} file(s) are missing from this task. '
            f'They may have been lost when converting tasks to subtasks. '
            f'<a href="{project.get_absolute_url()}/files/" class="alert-link">View File Pool</a> to manage files.',
            extra_tags='safe'
        )

    context = {
        'project': project,
        'task': task,
        'user_role': user_role,
        'comments': comments,
        'attachments': attachments,
        'checklists': checklists,
        'activities': activities,
        'can_edit': user_role in ['owner', 'admin', 'member'],
        'missing_files_count': len(missing_files),
    }

    return render(request, 'project_management/task_detail.html', context)


# ============================================================================
# Task Edit View
# ============================================================================

@login_required
def task_edit(request, project_pk, pk):
    """
    Edit an existing task
    """
    project = get_object_or_404(Project, pk=project_pk)
    task = get_object_or_404(Task, pk=pk, project=project)

    # Check access - requires member or higher
    has_access, user_role = check_project_access(request.user, project, required_role='member')
    if not has_access:
        messages.error(request, _("You don't have permission to edit tasks in this project."))
        return redirect('project_management:task_detail', project_pk=project.pk, pk=task.pk)

    if request.method == 'POST':
        form = TaskForm(request.POST, instance=task, project=project)
        if form.is_valid():
            task = form.save()

            # Log activity
            TaskActivity.objects.create(
                task=task,
                user=request.user,
                action='updated',
                details={'task_title': task.title}
            )

            messages.success(request, _('Task "{}" updated successfully!').format(task.title))
            return redirect('project_management:task_detail', project_pk=project.pk, pk=task.pk)
    else:
        form = TaskForm(instance=task, project=project)

    context = {
        'form': form,
        'project': project,
        'task': task,
        'action': 'Edit',
    }

    return render(request, 'project_management/task_form.html', context)


# ============================================================================
# Task Delete View
# ============================================================================

@login_required
def task_delete(request, project_pk, pk):
    """
    Delete a task
    """
    project = get_object_or_404(Project, pk=project_pk)
    task = get_object_or_404(Task, pk=pk, project=project)

    # Check access - requires member or higher
    has_access, user_role = check_project_access(request.user, project, required_role='member')
    if not has_access:
        messages.error(request, _("You don't have permission to delete tasks in this project."))
        return redirect('project_management:task_detail', project_pk=project.pk, pk=task.pk)

    if request.method == 'POST':
        task_title = task.title
        task.delete()
        messages.success(request, _('Task "{}" deleted successfully.').format(task_title))

        # Redirect to previous page or kanban board
        next_url = request.POST.get('next',
            request.META.get('HTTP_REFERER',
                f'/projects/{project.pk}/kanban/'))
        return redirect(next_url)

    context = {
        'project': project,
        'task': task,
    }

    return render(request, 'project_management/task_confirm_delete.html', context)


# ============================================================================
# API: Update Task Position (for drag & drop)
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_task_move(request, project_pk, pk):
    """
    API endpoint to move a task to a different column/position
    """
    project = get_object_or_404(Project, pk=project_pk)
    task = get_object_or_404(Task, pk=pk, project=project)

    # Check access
    has_access, user_role = check_project_access(request.user, project, required_role='member')
    if not has_access:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        import json
        data = json.loads(request.body)

        column_id = data.get('column_id')
        position = data.get('position', 0)

        # Validate column belongs to project
        if column_id:
            column = get_object_or_404(KanbanColumn, pk=column_id, project=project)

            # Check WIP limit
            if column.wip_limit and column.is_over_wip_limit and task.kanban_column_id != column_id:
                return JsonResponse({
                    'error': f'Column "{column.name}" has reached its WIP limit of {column.wip_limit}',
                    'wip_limit_exceeded': True
                }, status=400)

            old_column = task.kanban_column
            task.kanban_column = column
            task.kanban_position = position
            task.save(update_fields=['kanban_column', 'kanban_position'])

            # Log activity
            if old_column != column:
                TaskActivity.objects.create(
                    task=task,
                    user=request.user,
                    action='moved',
                    details={
                        'from_column': old_column.name if old_column else None,
                        'to_column': column.name
                    }
                )
        else:
            task.kanban_position = position
            task.save(update_fields=['kanban_position'])

        return JsonResponse({
            'success': True,
            'task_id': task.pk,
            'column_id': column_id,
            'position': position
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# API: Quick Task Create (for Kanban board)
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_task_quick_create(request, project_pk):
    """
    API endpoint to quickly create a task from Kanban board
    """
    project = get_object_or_404(Project, pk=project_pk)

    # Check access
    has_access, user_role = check_project_access(request.user, project, required_role='member')
    if not has_access:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        import json
        data = json.loads(request.body)

        title = data.get('title', '').strip()
        if not title:
            return JsonResponse({'error': 'Title is required'}, status=400)

        column_id = data.get('column_id')

        # Generate task code
        task_count = project.tasks.count() + 1
        task_code = f"{project.project_code}-T{task_count:03d}"

        # Create task
        task = Task.objects.create(
            project=project,
            title=title,
            task_code=task_code,
            created_by=request.user,
            status='todo',
            priority='medium'
        )

        # Set column if provided
        if column_id:
            try:
                column = project.kanban_columns.get(pk=column_id)
                task.kanban_column = column
                task.save(update_fields=['kanban_column'])
            except KanbanColumn.DoesNotExist:
                pass

        # Log activity
        TaskActivity.objects.create(
            task=task,
            user=request.user,
            action='created',
            details={'task_title': task.title}
        )

        return JsonResponse({
            'success': True,
            'task': {
                'id': task.pk,
                'title': task.title,
                'task_code': task.task_code,
                'status': task.status,
                'priority': task.priority,
                'url': f'/projects/{project.pk}/tasks/{task.pk}/'
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# API: Update Task Field (inline editing)
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_task_update_field(request, project_pk, pk):
    """
    API endpoint to update a single field of a task
    """
    project = get_object_or_404(Project, pk=project_pk)
    task = get_object_or_404(Task, pk=pk, project=project)

    # Check access
    has_access, user_role = check_project_access(request.user, project, required_role='member')
    if not has_access:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        import json
        data = json.loads(request.body)

        field = data.get('field')
        value = data.get('value')

        allowed_fields = ['title', 'description', 'status', 'priority', 'progress', 'due_date']

        if field not in allowed_fields:
            return JsonResponse({'error': 'Invalid field'}, status=400)

        # Update field
        setattr(task, field, value)
        task.save(update_fields=[field])

        # Log activity
        TaskActivity.objects.create(
            task=task,
            user=request.user,
            action='updated',
            details={
                'field': field,
                'value': value
            }
        )

        return JsonResponse({
            'success': True,
            'field': field,
            'value': value
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# =============================================================================
# Task Attachment Views
# =============================================================================

@login_required
@require_http_methods(["POST"])
def task_upload_attachment(request, project_pk, task_pk):
    """
    Upload file attachment to a task
    """
    from ..models import TaskAttachment, TaskActivity
    import os
    
    project = get_object_or_404(Project, pk=project_pk)
    task = get_object_or_404(Task, pk=task_pk, project=project)
    
    # Check access - members and above can upload
    has_access, user_role = check_project_access(request.user, project, required_role='member')
    if not has_access:
        messages.error(request, 'You do not have permission to upload files.')
        return redirect('project_management:task_detail', project_pk=project_pk, pk=task_pk)
    
    if 'file' not in request.FILES:
        if request.content_type == 'multipart/form-data':
            return JsonResponse({'success': False, 'error': 'No file was uploaded.'}, status=400)
        messages.error(request, 'No file was uploaded.')
        return redirect('project_management:task_detail', project_pk=project_pk, pk=task_pk)
    
    uploaded_file = request.FILES['file']
    
    # Validate file size (max 10MB)
    max_size = 10 * 1024 * 1024  # 10MB
    if uploaded_file.size > max_size:
        error_msg = f'File size exceeds 10MB limit. Your file is {round(uploaded_file.size / (1024 * 1024), 2)}MB.'
        if request.content_type == 'multipart/form-data':
            return JsonResponse({'success': False, 'error': error_msg}, status=400)
        messages.error(request, error_msg)
        return redirect('project_management:task_detail', project_pk=project_pk, pk=task_pk)
    
    # Get file extension and type
    file_ext = os.path.splitext(uploaded_file.name)[1].lower()
    file_type = uploaded_file.content_type
    
    # Create attachment
    attachment = TaskAttachment.objects.create(
        task=task,
        file=uploaded_file,
        filename=uploaded_file.name,
        file_size=uploaded_file.size,
        file_type=file_type,
        uploaded_by=request.user,
        description=request.POST.get('description', '')
    )
    
    # Log activity
    TaskActivity.objects.create(
        task=task,
        user=request.user,
        action='file_uploaded',
        details={
            'filename': uploaded_file.name,
            'file_size': uploaded_file.size,
            'file_type': file_type
        }
    )
    
    # Return JSON response for AJAX requests
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.content_type == 'multipart/form-data':
        return JsonResponse({
            'success': True,
            'message': f'File "{uploaded_file.name}" uploaded successfully!',
            'filename': uploaded_file.name,
            'file_size': uploaded_file.size,
        })

    messages.success(request, f'File "{uploaded_file.name}" uploaded successfully!')
    return redirect('project_management:task_detail', project_pk=project_pk, pk=task_pk)


@login_required
@require_http_methods(["POST"])
def task_delete_attachment(request, project_pk, task_pk, attachment_pk):
    """
    Delete file attachment from a task
    """
    from ..models import TaskAttachment, TaskActivity
    import os
    
    project = get_object_or_404(Project, pk=project_pk)
    task = get_object_or_404(Task, pk=task_pk, project=project)
    attachment = get_object_or_404(TaskAttachment, pk=attachment_pk, task=task)
    
    # Check access - only uploader, admins, or owners can delete
    has_access, user_role = check_project_access(request.user, project)
    can_delete = (
        attachment.uploaded_by == request.user or
        user_role in ['owner', 'admin']
    )
    
    if not can_delete:
        messages.error(request, 'You do not have permission to delete this file.')
        return redirect('project_management:task_detail', project_pk=project_pk, pk=task_pk)
    
    filename = attachment.filename
    
    # Delete the physical file
    if attachment.file:
        try:
            if os.path.isfile(attachment.file.path):
                os.remove(attachment.file.path)
        except Exception as e:
            print(f"Error deleting file: {e}")
    
    # Delete the database record
    attachment.delete()
    
    # Log activity
    TaskActivity.objects.create(
        task=task,
        user=request.user,
        action='file_deleted',
        details={
            'filename': filename
        }
    )
    
    messages.success(request, f'File "{filename}" deleted successfully!')
    return redirect('project_management:task_detail', project_pk=project_pk, pk=task_pk)
