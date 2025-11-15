"""
Gantt Chart Views for Project Management
Handles Gantt chart visualization, timeline calculations, and critical path analysis
"""

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.db.models import Q, F, Min, Max, Prefetch
from django.utils import timezone
from datetime import datetime, timedelta
import json

from ..models import (
    Project, Task, TaskDependency, ProjectBaseline, BaselineTask,
    TaskActivity, ProjectMember
)
from ..utils.permissions import check_project_access


# ============================================================================
# GANTT CHART VIEW
# ============================================================================

@login_required
def gantt_chart_view(request, pk):
    """
    Main Gantt chart view with timeline visualization
    """
    project = get_object_or_404(Project, pk=pk)

    # Check access permissions
    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        return render(request, 'project_management/no_access.html', {
            'project': project
        })

    # Get all tasks with dependencies and relationships
    tasks = Task.objects.filter(project=project).select_related(
        'parent_task',
        'created_by',
        'kanban_column'
    ).prefetch_related(
        'assigned_to',
        'predecessors__predecessor',
        'successors__successor',
        'subtasks'
    ).order_by('order', 'created_at')

    # Get baselines for comparison
    baselines = project.baselines.all()[:5]  # Last 5 baselines

    # Calculate project timeline stats
    timeline_stats = calculate_project_timeline(project, tasks)

    # Get critical path if tasks have dependencies
    critical_path = calculate_critical_path(tasks)

    # Calculate task variances if baseline selected
    selected_baseline_id = request.GET.get('baseline')
    baseline_comparison = None
    if selected_baseline_id:
        baseline_comparison = get_baseline_comparison(
            project,
            selected_baseline_id,
            tasks
        )

    # CRITICAL: Add boundary tasks to force timeline to span full year 2025
    # Convert tasks to list so we can append boundary tasks
    tasks_list = list(tasks)

    # Add is_boundary = False to regular tasks for template compatibility
    for task in tasks_list:
        task.is_boundary = False
        task.text = task.title  # Add text attribute for template compatibility

    # Create boundary task at start of year
    from datetime import date
    class BoundaryTask:
        """Minimal task object for timeline boundary"""
        def __init__(self, id, text, start_date, end_date):
            self.id = id
            self.pk = id
            self.text = text  # For template compatibility
            self.title = text  # Regular tasks use title
            self.task_code = f"BOUNDARY_{id}"
            self.title_cn = ""
            self.start_date = start_date
            self.end_date = end_date
            self.duration = 1
            self.progress = 0
            self.parent_task = None
            self.parent_task_id = None
            self.priority = "low"
            self.status = "pending"
            self.is_boundary = True  # Custom flag
            # Add missing attributes that might be accessed
            self.is_milestone = False
            self.process_owner = None
            self.definition_of_done = ""
            self.assigned_to = MockRelatedManager()  # Empty manager

    class MockRelatedManager:
        """Mock manager for assigned_to relationship"""
        def all(self):
            return []

    # Add boundary tasks for 2025
    start_boundary = BoundaryTask(
        id=999998,
        text="",
        start_date=date(2025, 1, 1),
        end_date=date(2025, 1, 2)
    )
    end_boundary = BoundaryTask(
        id=999999,
        text="",
        start_date=date(2025, 12, 31),
        end_date=date(2025, 12, 31)
    )

    tasks_list.append(start_boundary)
    tasks_list.append(end_boundary)

    context = {
        'project': project,
        'tasks': tasks_list,  # Use the list with boundary tasks
        'timeline_stats': timeline_stats,
        'critical_path': critical_path,
        'baselines': baselines,
        'selected_baseline_id': selected_baseline_id,
        'baseline_comparison': baseline_comparison,
        'can_edit': user_role in ['owner', 'admin', 'member'],
        'is_admin': user_role in ['owner', 'admin'],
        'view_mode': request.GET.get('mode', 'month'),  # day, week, month, year
        'show_critical_path': request.GET.get('show_critical', 'true') == 'true',
        'show_dependencies': request.GET.get('show_deps', 'true') == 'true',
        'show_progress': request.GET.get('show_progress', 'true') == 'true',
    }

    return render(request, 'project_management/project_gantt.html', context)


# ============================================================================
# TIMELINE CALCULATIONS
# ============================================================================

def calculate_project_timeline(project, tasks):
    """
    Calculate project timeline statistics
    """
    if not tasks:
        return {
            'start_date': project.start_date,
            'end_date': project.end_date,
            'total_duration': (project.end_date - project.start_date).days,
            'tasks_with_dates': 0,
            'tasks_without_dates': 0,
            'total_tasks': 0,
            'completed_tasks': 0,
            'in_progress_tasks': 0,
            'not_started_tasks': 0,
            'overdue_tasks': 0,
            'average_progress': 0,
        }

    # Calculate date ranges
    tasks_with_dates = [t for t in tasks if t.start_date and t.end_date]

    if tasks_with_dates:
        min_date = min(t.start_date for t in tasks_with_dates)
        max_date = max(t.end_date for t in tasks_with_dates)
    else:
        min_date = project.start_date
        max_date = project.end_date

    # Status counts
    completed = sum(1 for t in tasks if t.status == 'completed')
    in_progress = sum(1 for t in tasks if t.status == 'in_progress')
    not_started = sum(1 for t in tasks if t.status == 'todo')
    overdue = sum(1 for t in tasks if t.is_overdue)

    # Progress calculation
    total_progress = sum(t.progress for t in tasks)
    average_progress = total_progress / len(tasks) if tasks else 0

    return {
        'start_date': min_date,
        'end_date': max_date,
        'total_duration': (max_date - min_date).days + 1,
        'tasks_with_dates': len(tasks_with_dates),
        'tasks_without_dates': len(tasks) - len(tasks_with_dates),
        'total_tasks': len(tasks),
        'completed_tasks': completed,
        'in_progress_tasks': in_progress,
        'not_started_tasks': not_started,
        'overdue_tasks': overdue,
        'average_progress': round(average_progress, 1),
        'completion_percentage': round((completed / len(tasks)) * 100, 1) if tasks else 0,
    }


def calculate_critical_path(tasks):
    """
    Calculate critical path using forward and backward pass
    Returns list of task IDs on critical path
    """
    if not tasks:
        return []

    # Build dependency graph
    task_dict = {t.id: t for t in tasks}
    dependencies = {}

    for task in tasks:
        deps = task.predecessors.all()
        dependencies[task.id] = [d.predecessor_id for d in deps]

    # Forward pass - calculate Early Start (ES) and Early Finish (EF)
    early_start = {}
    early_finish = {}

    for task in tasks:
        if not dependencies.get(task.id):
            # No predecessors - starts at project start or task start date
            early_start[task.id] = 0
        else:
            # ES = max(EF of all predecessors)
            pred_finishes = [early_finish.get(pred_id, 0) for pred_id in dependencies[task.id]]
            early_start[task.id] = max(pred_finishes) if pred_finishes else 0

        early_finish[task.id] = early_start[task.id] + (task.duration or 1)

    # Project completion time
    if not early_finish:
        return []

    project_duration = max(early_finish.values())

    # Backward pass - calculate Late Start (LS) and Late Finish (LF)
    late_start = {}
    late_finish = {}

    # Start from the end
    for task in reversed(list(tasks)):
        # Find successors
        successors = [t.id for t in tasks if task.id in dependencies.get(t.id, [])]

        if not successors:
            # No successors - LF = project duration
            late_finish[task.id] = project_duration
        else:
            # LF = min(LS of all successors)
            succ_starts = [late_start.get(succ_id, project_duration) for succ_id in successors]
            late_finish[task.id] = min(succ_starts) if succ_starts else project_duration

        late_start[task.id] = late_finish[task.id] - (task.duration or 1)

    # Calculate slack/float and identify critical path
    critical_path_ids = []

    for task in tasks:
        slack = late_start.get(task.id, 0) - early_start.get(task.id, 0)

        # Tasks with zero slack are on critical path
        if slack == 0:
            critical_path_ids.append(task.id)

    return critical_path_ids


# ============================================================================
# BASELINE COMPARISON
# ============================================================================

def get_baseline_comparison(project, baseline_id, current_tasks):
    """
    Compare current schedule with baseline
    """
    try:
        baseline = ProjectBaseline.objects.get(pk=baseline_id, project=project)
        baseline_tasks = baseline.tasks.all()

        # Build comparison data
        comparisons = []

        for current_task in current_tasks:
            # Find matching baseline task
            baseline_task = baseline_tasks.filter(task=current_task).first()

            if baseline_task:
                # Calculate variances
                start_variance = None
                end_variance = None
                duration_variance = None
                progress_variance = None

                if current_task.start_date and baseline_task.start_date:
                    start_variance = (current_task.start_date - baseline_task.start_date).days

                if current_task.end_date and baseline_task.end_date:
                    end_variance = (current_task.end_date - baseline_task.end_date).days

                duration_variance = current_task.duration - baseline_task.duration
                progress_variance = current_task.progress - baseline_task.progress

                comparisons.append({
                    'task': current_task,
                    'baseline_task': baseline_task,
                    'start_variance': start_variance,
                    'end_variance': end_variance,
                    'duration_variance': duration_variance,
                    'progress_variance': progress_variance,
                    'is_ahead': end_variance < 0 if end_variance is not None else False,
                    'is_behind': end_variance > 0 if end_variance is not None else False,
                })

        return {
            'baseline': baseline,
            'comparisons': comparisons,
            'total_ahead': sum(1 for c in comparisons if c['is_ahead']),
            'total_behind': sum(1 for c in comparisons if c['is_behind']),
            'total_on_track': sum(1 for c in comparisons if c['end_variance'] == 0),
        }

    except ProjectBaseline.DoesNotExist:
        return None


# ============================================================================
# TASK DEPENDENCY API ENDPOINTS
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_add_dependency(request, project_pk):
    """
    Add a task dependency
    """
    project = get_object_or_404(Project, pk=project_pk)

    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    try:
        data = json.loads(request.body)

        predecessor_id = data.get('predecessor_id')
        successor_id = data.get('successor_id')
        dependency_type = data.get('dependency_type', 'FS')
        lag_days = data.get('lag_days', 0)

        # Validate
        if not predecessor_id or not successor_id:
            return JsonResponse({'error': 'Both predecessor and successor required'}, status=400)

        if predecessor_id == successor_id:
            return JsonResponse({'error': 'Task cannot depend on itself'}, status=400)

        predecessor = get_object_or_404(Task, pk=predecessor_id, project=project)
        successor = get_object_or_404(Task, pk=successor_id, project=project)

        # Check for circular dependency
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Attempting to add dependency: {predecessor.task_code} ({predecessor.id}) -> {successor.task_code} ({successor.id})")

        if would_create_circular_dependency(predecessor, successor):
            logger.warning(f"Circular dependency detected when trying to add {predecessor.task_code} -> {successor.task_code}")
            return JsonResponse({
                'error': f'This would create a circular dependency. {successor.task_code} already depends on {predecessor.task_code} (directly or indirectly)'
            }, status=400)

        # Create dependency
        dependency = TaskDependency.objects.create(
            predecessor=predecessor,
            successor=successor,
            dependency_type=dependency_type,
            lag_days=lag_days
        )

        # Log activity
        TaskActivity.objects.create(
            task=successor,
            user=request.user,
            action='dependency_added',
            details={
                'predecessor': predecessor.task_code,
                'dependency_type': dependency_type,
                'lag_days': lag_days
            }
        )

        return JsonResponse({
            'success': True,
            'dependency': {
                'id': dependency.pk,
                'predecessor': predecessor.task_code,
                'successor': successor.task_code,
                'type': dependency_type,
                'lag_days': lag_days
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def api_remove_dependency(request, project_pk, dependency_id):
    """
    Remove a task dependency
    """
    project = get_object_or_404(Project, pk=project_pk)

    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    try:
        dependency = get_object_or_404(
            TaskDependency,
            pk=dependency_id,
            predecessor__project=project
        )

        # Log activity before deleting
        TaskActivity.objects.create(
            task=dependency.successor,
            user=request.user,
            action='dependency_removed',
            details={
                'predecessor': dependency.predecessor.task_code,
                'dependency_type': dependency.dependency_type
            }
        )

        dependency.delete()

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_remove_dependency_by_tasks(request, project_pk):
    """
    Remove a task dependency by predecessor and successor task IDs
    This is used when deleting from the lightbox UI
    """
    project = get_object_or_404(Project, pk=project_pk)

    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    try:
        data = json.loads(request.body)
        predecessor_id = data.get('predecessor_id')
        successor_id = data.get('successor_id')

        if not predecessor_id or not successor_id:
            return JsonResponse({'error': 'Both predecessor_id and successor_id required'}, status=400)

        # Find the dependency
        dependency = TaskDependency.objects.filter(
            predecessor_id=predecessor_id,
            successor_id=successor_id,
            predecessor__project=project
        ).first()

        if not dependency:
            # Dependency doesn't exist - this is OK, just return success
            return JsonResponse({'success': True, 'message': 'Dependency not found (may have already been deleted)'})

        # Log activity before deleting
        try:
            TaskActivity.objects.create(
                task=dependency.successor,
                user=request.user,
                action='dependency_removed',
                details={
                    'predecessor': dependency.predecessor.task_code,
                    'dependency_type': dependency.dependency_type
                }
            )
        except Exception:
            pass  # Don't fail if activity logging fails

        dependency.delete()

        return JsonResponse({'success': True, 'message': 'Dependency removed successfully'})

    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error removing dependency: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)


def would_create_circular_dependency(predecessor, successor):
    """
    Check if creating this dependency would create a circular dependency.
    We're trying to create: predecessor -> successor
    This would be circular if there's already a path: successor -> ... -> predecessor
    """
    import logging
    logger = logging.getLogger(__name__)

    # BFS to check if predecessor is reachable from successor
    visited = set()
    queue = [successor]
    path = []

    while queue:
        current = queue.pop(0)

        if current.id in visited:
            continue

        visited.add(current.id)
        path.append(current.task_code)

        # Check if we've reached the predecessor
        if current.id == predecessor.id:
            logger.info(f"Circular dependency path found: {' -> '.join(path)}")
            return True

        # Add all successors of current task
        for dep in current.successors.all():
            queue.append(dep.successor)

    return False


# ============================================================================
# TASK UPDATE API ENDPOINTS FOR GANTT
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_update_task_dates(request, project_pk, task_id):
    """
    Update task start/end dates from Gantt drag
    """
    project = get_object_or_404(Project, pk=project_pk)
    task = get_object_or_404(Task, pk=task_id, project=project)

    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    try:
        data = json.loads(request.body)

        start_date_str = data.get('start_date')
        end_date_str = data.get('end_date')

        old_start = task.start_date
        old_end = task.end_date

        if start_date_str:
            task.start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        if end_date_str:
            task.end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()

        # Recalculate duration
        if task.start_date and task.end_date:
            task.duration = (task.end_date - task.start_date).days + 1

        task.save(update_fields=['start_date', 'end_date', 'duration'])

        # Log activity
        TaskActivity.objects.create(
            task=task,
            user=request.user,
            action='updated',
            details={
                'field': 'dates',
                'old_start': str(old_start) if old_start else None,
                'new_start': str(task.start_date) if task.start_date else None,
                'old_end': str(old_end) if old_end else None,
                'new_end': str(task.end_date) if task.end_date else None,
            }
        )

        return JsonResponse({
            'success': True,
            'task': {
                'id': task.pk,
                'start_date': str(task.start_date) if task.start_date else None,
                'end_date': str(task.end_date) if task.end_date else None,
                'duration': task.duration
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_update_task_progress(request, project_pk, task_id):
    """
    Update task progress percentage
    """
    project = get_object_or_404(Project, pk=project_pk)
    task = get_object_or_404(Task, pk=task_id, project=project)

    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    try:
        data = json.loads(request.body)
        progress = data.get('progress')
        title = data.get('title', data.get('text'))  # Accept both 'title' and 'text'
        title_cn = data.get('title_cn', '')
        process_owner_id = data.get('process_owner_id')
        definition_of_done = data.get('definition_of_done', '')

        # Log what we received
        import logging
        logger = logging.getLogger(__name__)
        logger.info(f"Update task {task_id}: progress={progress}, title={title}, title_cn={title_cn}, "
                   f"process_owner_id={process_owner_id}, definition_of_done={definition_of_done[:50] if definition_of_done else ''}")

        if progress is None:
            return JsonResponse({'error': 'Progress value required'}, status=400)

        progress = int(progress)
        if progress < 0 or progress > 100:
            return JsonResponse({'error': 'Progress must be between 0 and 100'}, status=400)

        old_progress = task.progress
        old_title = task.title
        old_title_cn = task.title_cn
        task.progress = progress

        # Update title if provided
        if title and title.strip():
            task.title = title.strip()

        task.title_cn = title_cn
        task.definition_of_done = definition_of_done

        # Handle process owner
        if process_owner_id and process_owner_id != '':
            from django.contrib.auth import get_user_model
            User = get_user_model()
            try:
                process_owner = User.objects.get(pk=int(process_owner_id))
                task.process_owner = process_owner
            except (User.DoesNotExist, ValueError):
                logger.warning(f"Invalid process_owner_id: {process_owner_id}")
                task.process_owner = None
        else:
            task.process_owner = None

        # Auto-update status based on progress
        if progress == 100 and task.status != 'completed':
            task.status = 'completed'
        elif progress > 0 and task.status == 'todo':
            task.status = 'in_progress'

        task.save(update_fields=['title', 'progress', 'status', 'title_cn', 'process_owner', 'definition_of_done'])

        # Log activity
        try:
            TaskActivity.objects.create(
                task=task,
                user=request.user,
                action='updated',
                details={
                    'field': 'progress',
                    'old_value': old_progress,
                    'new_value': progress
                }
            )
        except Exception as activity_error:
            logger.warning(f"Failed to create TaskActivity: {activity_error}")

        logger.info(f"Task {task_id} updated successfully: title_cn='{task.title_cn}'")

        return JsonResponse({
            'success': True,
            'progress': progress,
            'status': task.status,
            'title_cn': task.title_cn,
            'process_owner_id': task.process_owner.pk if task.process_owner else None,
            'definition_of_done': task.definition_of_done
        })

    except json.JSONDecodeError as e:
        return JsonResponse({'success': False, 'error': f'Invalid JSON: {str(e)}'}, status=400)
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error updating task {task_id}: {error_details}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# ============================================================================
# BASELINE MANAGEMENT
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_create_baseline(request, project_pk):
    """
    Create a new project baseline
    """
    project = get_object_or_404(Project, pk=project_pk)

    has_access, user_role = check_project_access(request.user, project, required_role='admin')
    if not has_access:
        return JsonResponse({'error': 'Permission denied - Admin required'}, status=403)

    try:
        data = json.loads(request.body)

        name = data.get('name', f"Baseline {timezone.now().strftime('%Y-%m-%d %H:%M')}")
        description = data.get('description', '')

        # Create baseline
        baseline = ProjectBaseline.objects.create(
            project=project,
            name=name,
            description=description,
            created_by=request.user
        )

        # Snapshot all tasks
        tasks = project.tasks.filter(start_date__isnull=False, end_date__isnull=False)

        for task in tasks:
            BaselineTask.objects.create(
                baseline=baseline,
                task=task,
                task_code=task.task_code,
                title=task.title,
                start_date=task.start_date,
                end_date=task.end_date,
                duration=task.duration,
                progress=task.progress
            )

        return JsonResponse({
            'success': True,
            'baseline': {
                'id': baseline.pk,
                'name': baseline.name,
                'description': baseline.description,
                'created_at': baseline.created_at.isoformat(),
                'task_count': baseline.tasks.count()
            }
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_http_methods(["DELETE"])
def api_delete_baseline(request, project_pk, baseline_id):
    """
    Delete a project baseline
    """
    project = get_object_or_404(Project, pk=project_pk)

    has_access, user_role = check_project_access(request.user, project, required_role='admin')
    if not has_access:
        return JsonResponse({'error': 'Permission denied - Admin required'}, status=403)

    try:
        baseline = get_object_or_404(ProjectBaseline, pk=baseline_id, project=project)
        baseline.delete()

        return JsonResponse({'success': True})

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# TASK CREATION AND DELETION FROM GANTT
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_create_task(request, project_pk):
    """
    Create a new task from Gantt chart
    """
    project = get_object_or_404(Project, pk=project_pk)

    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    try:
        data = json.loads(request.body)

        title = data.get('text', 'New Task')
        start_date_str = data.get('start_date')
        duration = data.get('duration', 1)
        parent_id = data.get('parent')

        # Parse start date
        start_date = None
        if start_date_str:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()

        # Calculate end date
        end_date = None
        if start_date:
            end_date = start_date + timedelta(days=int(duration) - 1)

        # Get parent task if specified
        parent_task = None
        if parent_id and parent_id != 0:
            try:
                parent_task = Task.objects.get(pk=parent_id, project=project)
            except Task.DoesNotExist:
                pass

        # Generate task code
        task_count = project.tasks.count() + 1
        task_code = f"T{task_count:04d}"

        # Create the task
        task = Task.objects.create(
            project=project,
            title=title,
            task_code=task_code,
            start_date=start_date,
            end_date=end_date,
            duration=int(duration),
            parent_task=parent_task,
            created_by=request.user,
            status='todo',
            priority='medium'
        )

        # Log activity
        TaskActivity.objects.create(
            task=task,
            user=request.user,
            action='created',
            details={'source': 'gantt_chart'}
        )

        return JsonResponse({
            'success': True,
            'task': {
                'id': task.pk,
                'text': task.title,
                'task_code': task.task_code,
                'start_date': str(task.start_date) if task.start_date else None,
                'duration': task.duration,
                'parent': parent_task.pk if parent_task else 0,
                'progress': task.progress / 100,
                'status': task.status
            }
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error creating task: {error_details}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_check_task_deletion(request, project_pk, task_id):
    """
    Check what will be affected when deleting a task
    Returns information about subtasks and dependencies
    """
    project = get_object_or_404(Project, pk=project_pk)
    task = get_object_or_404(Task, pk=task_id, project=project)

    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    # Count subtasks (will be cascade deleted)
    subtasks = Task.objects.filter(parent_task=task)
    subtask_count = subtasks.count()

    # Get all subtasks recursively
    def get_all_subtasks(parent):
        all_subtasks = []
        direct_subtasks = Task.objects.filter(parent_task=parent)
        for subtask in direct_subtasks:
            all_subtasks.append(subtask)
            all_subtasks.extend(get_all_subtasks(subtask))
        return all_subtasks

    all_subtasks = get_all_subtasks(task)
    total_subtask_count = len(all_subtasks)

    # Check dependencies
    predecessors = TaskDependency.objects.filter(successor=task)
    successors = TaskDependency.objects.filter(predecessor=task)

    predecessor_tasks = [
        {'code': dep.predecessor.task_code, 'title': dep.predecessor.title}
        for dep in predecessors
    ]

    successor_tasks = [
        {'code': dep.successor.task_code, 'title': dep.successor.title}
        for dep in successors
    ]

    return JsonResponse({
        'success': True,
        'task_code': task.task_code,
        'task_title': task.title,
        'subtask_count': total_subtask_count,
        'subtasks': [{'code': st.task_code, 'title': st.title} for st in all_subtasks[:10]],  # First 10
        'has_more_subtasks': total_subtask_count > 10,
        'predecessor_count': len(predecessor_tasks),
        'predecessors': predecessor_tasks,
        'successor_count': len(successor_tasks),
        'successors': successor_tasks
    })


@login_required
@require_http_methods(["POST"])
def api_delete_task(request, project_pk, task_id):
    """
    Delete a task from Gantt chart with enhanced checking and logging
    """
    project = get_object_or_404(Project, pk=project_pk)
    task = get_object_or_404(Task, pk=task_id, project=project)

    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    try:
        import logging
        logger = logging.getLogger(__name__)

        task_code = task.task_code
        task_title = task.title

        # Count what will be deleted
        def get_all_subtasks(parent):
            all_subtasks = []
            direct_subtasks = Task.objects.filter(parent_task=parent)
            for subtask in direct_subtasks:
                all_subtasks.append(subtask)
                all_subtasks.extend(get_all_subtasks(subtask))
            return all_subtasks

        all_subtasks = get_all_subtasks(task)
        subtask_count = len(all_subtasks)

        # Get dependency counts
        predecessor_count = TaskDependency.objects.filter(successor=task).count()
        successor_count = TaskDependency.objects.filter(predecessor=task).count()

        logger.info(f"Deleting task {task_code} ({task_title}) - "
                   f"{subtask_count} subtasks, {predecessor_count} predecessors, {successor_count} successors")

        # Create activity log before deletion
        try:
            TaskActivity.objects.create(
                task=task,
                user=request.user,
                activity_type='status_changed',
                description=f'Deleted task {task_code}: {task_title}' +
                           (f' (including {subtask_count} subtasks)' if subtask_count > 0 else ''),
                project=project
            )
        except Exception as log_error:
            logger.warning(f"Failed to create activity log: {log_error}")

        # Perform deletion
        task.delete()

        logger.info(f"Successfully deleted task {task_code}")

        return JsonResponse({
            'success': True,
            'message': f'Task {task_code} deleted successfully',
            'details': {
                'task_code': task_code,
                'subtasks_deleted': subtask_count,
                'dependencies_removed': predecessor_count + successor_count
            }
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        logger = logging.getLogger(__name__)
        logger.error(f"Error deleting task {task_id}: {error_details}")

        return JsonResponse({
            'success': False,
            'error': f'Failed to delete task: {str(e)}',
            'details': str(e)
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_reorder_task(request, project_pk, task_id):
    """
    Update task order and hierarchy
    """
    project = get_object_or_404(Project, pk=project_pk)
    task = get_object_or_404(Task, pk=task_id, project=project)

    has_access, user_role = check_project_access(request.user, project)
    if not has_access:
        return JsonResponse({'success': False, 'error': 'Permission denied'}, status=403)

    try:
        data = json.loads(request.body)

        parent_id = data.get('parent')
        target_id = data.get('target')  # Task to place before/after
        position = data.get('position', 'after')  # 'before' or 'after'

        # Update parent
        if parent_id == 0 or parent_id is None:
            task.parent_task = None
        else:
            try:
                parent_task = Task.objects.get(pk=parent_id, project=project)
                task.parent_task = parent_task
            except Task.DoesNotExist:
                return JsonResponse({'success': False, 'error': 'Parent task not found'}, status=404)

        # Update order
        if target_id:
            try:
                # Handle special dhtmlxGantt identifiers like 'next:459'
                actual_target_id = target_id
                if isinstance(target_id, str):
                    if target_id.startswith('next:'):
                        # Extract the task ID after 'next:'
                        actual_target_id = int(target_id.split(':')[1])
                        position = 'after'  # 'next:' always means after
                    elif target_id.startswith('prev:'):
                        # Extract the task ID after 'prev:'
                        actual_target_id = int(target_id.split(':')[1])
                        position = 'before'  # 'prev:' always means before
                    else:
                        # Try to convert to int
                        actual_target_id = int(target_id)

                target_task = Task.objects.get(pk=actual_target_id, project=project)
                if position == 'before':
                    task.order = target_task.order - 0.5
                else:
                    task.order = target_task.order + 0.5
            except (Task.DoesNotExist, ValueError, IndexError):
                # If target task doesn't exist or ID is invalid, keep current order
                pass

        task.save(update_fields=['parent_task', 'order'])

        # Re-normalize orders
        normalize_task_orders(project)

        # Log activity
        TaskActivity.objects.create(
            task=task,
            user=request.user,
            action='reordered',
            details={
                'parent': parent_id,
                'position': position
            }
        )

        return JsonResponse({
            'success': True,
            'task': {
                'id': task.pk,
                'parent': task.parent_task.pk if task.parent_task else 0,
                'order': task.order
            }
        })

    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error reordering task: {error_details}")
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def normalize_task_orders(project):
    """
    Normalize task orders to ensure they're sequential integers
    """
    tasks = Task.objects.filter(project=project).order_by('order', 'created_at')

    for index, task in enumerate(tasks):
        task.order = (index + 1) * 10
        task.save(update_fields=['order'])
