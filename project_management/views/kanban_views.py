"""
Kanban Column management views and API endpoints
"""

from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext_lazy as _

from ..models import Project, KanbanColumn
from .project_views import check_project_access


# ============================================================================
# API: Create Kanban Column
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_column_create(request, project_pk):
    """
    API endpoint to create a new Kanban column
    """
    project = get_object_or_404(Project, pk=project_pk)

    # Check access - requires admin or owner
    has_access, user_role = check_project_access(request.user, project, required_role='admin')
    if not has_access:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        import json
        data = json.loads(request.body)

        name = data.get('name', '').strip()
        if not name:
            return JsonResponse({'error': 'Name is required'}, status=400)

        color = data.get('color', '#6c757d')
        wip_limit = data.get('wip_limit')

        # Get max position
        max_position = project.kanban_columns.count()

        # Create column
        column = KanbanColumn.objects.create(
            project=project,
            name=name,
            color=color,
            position=max_position + 1,
            wip_limit=wip_limit if wip_limit else None
        )

        return JsonResponse({
            'success': True,
            'column': {
                'id': column.pk,
                'name': column.name,
                'color': column.color,
                'position': column.position,
                'wip_limit': column.wip_limit,
                'task_count': 0
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# API: Update Kanban Column
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_column_update(request, project_pk, column_id):
    """
    API endpoint to update a Kanban column
    """
    project = get_object_or_404(Project, pk=project_pk)
    column = get_object_or_404(KanbanColumn, pk=column_id, project=project)

    # Check access - requires admin or owner
    has_access, user_role = check_project_access(request.user, project, required_role='admin')
    if not has_access:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        import json
        data = json.loads(request.body)

        if 'name' in data:
            column.name = data['name'].strip()
        if 'color' in data:
            column.color = data['color']
        if 'wip_limit' in data:
            column.wip_limit = data['wip_limit'] if data['wip_limit'] else None

        column.save()

        return JsonResponse({
            'success': True,
            'column': {
                'id': column.pk,
                'name': column.name,
                'color': column.color,
                'wip_limit': column.wip_limit,
                'task_count': column.task_count
            }
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# API: Delete Kanban Column
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_column_delete(request, project_pk, column_id):
    """
    API endpoint to delete a Kanban column
    """
    project = get_object_or_404(Project, pk=project_pk)
    column = get_object_or_404(KanbanColumn, pk=column_id, project=project)

    # Check access - requires admin or owner
    has_access, user_role = check_project_access(request.user, project, required_role='admin')
    if not has_access:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        # Check if column has tasks
        task_count = column.tasks.count()
        if task_count > 0:
            return JsonResponse({
                'error': f'Cannot delete column with {task_count} tasks. Move or delete tasks first.',
                'task_count': task_count
            }, status=400)

        column.delete()

        return JsonResponse({
            'success': True,
            'message': 'Column deleted successfully'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# ============================================================================
# API: Reorder Kanban Columns
# ============================================================================

@login_required
@require_http_methods(["POST"])
def api_column_reorder(request, project_pk):
    """
    API endpoint to reorder Kanban columns
    """
    project = get_object_or_404(Project, pk=project_pk)

    # Check access - requires admin or owner
    has_access, user_role = check_project_access(request.user, project, required_role='admin')
    if not has_access:
        return JsonResponse({'error': 'Permission denied'}, status=403)

    try:
        import json
        data = json.loads(request.body)

        column_order = data.get('column_order', [])

        # Update positions
        for index, column_id in enumerate(column_order, start=1):
            try:
                column = project.kanban_columns.get(pk=column_id)
                column.position = index
                column.save(update_fields=['position'])
            except KanbanColumn.DoesNotExist:
                continue

        return JsonResponse({
            'success': True,
            'message': 'Columns reordered successfully'
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
