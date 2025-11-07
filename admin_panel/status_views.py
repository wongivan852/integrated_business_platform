"""
App Status Dashboard Views
Monitor development status and function-level progress for all business applications
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.db import transaction
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.db.models import Q, Count, Avg

from core.models import AppStatus, AppFunction, AppStatusHistory


def is_admin(user):
    """Check if user is admin/superuser"""
    return user.is_superuser or user.is_staff


@login_required
@user_passes_test(is_admin)
def app_status_dashboard(request):
    """Main app status dashboard with overview"""

    # Get all apps with their function counts
    apps = AppStatus.objects.filter(is_active=True).prefetch_related('functions')

    # Calculate statistics
    total_apps = apps.count()
    apps_in_production = apps.filter(status='production').count()
    apps_in_uat = apps.filter(status='uat').count()
    apps_in_softlaunch = apps.filter(status='softlaunch').count()
    apps_developing = apps.filter(status='developing').count()

    # Function statistics
    total_functions = AppFunction.objects.count()
    functions_in_production = AppFunction.objects.filter(status='production').count()
    functions_developing = AppFunction.objects.filter(status='developing').count()
    functions_blocked = AppFunction.objects.filter(is_blocked=True).count()

    # Calculate average completion
    avg_completion = apps.aggregate(Avg('completion_percentage'))['completion_percentage__avg'] or 0

    # Recent status changes
    recent_changes = AppStatusHistory.objects.select_related('app', 'changed_by').order_by('-created_at')[:10]

    # Apps by status
    apps_by_status = {
        'developing': apps.filter(status='developing'),
        'prototype': apps.filter(status='prototype'),
        'uat': apps.filter(status='uat'),
        'softlaunch': apps.filter(status='softlaunch'),
        'production': apps.filter(status='production'),
    }

    context = {
        'apps': apps,
        'total_apps': total_apps,
        'apps_in_production': apps_in_production,
        'apps_in_uat': apps_in_uat,
        'apps_in_softlaunch': apps_in_softlaunch,
        'apps_developing': apps_developing,
        'total_functions': total_functions,
        'functions_in_production': functions_in_production,
        'functions_developing': functions_developing,
        'functions_blocked': functions_blocked,
        'avg_completion': int(avg_completion),
        'recent_changes': recent_changes,
        'apps_by_status': apps_by_status,
    }
    return render(request, 'admin_panel/app_status_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def app_status_detail(request, app_code):
    """Detailed view of an app's status and functions"""
    app = get_object_or_404(AppStatus, app_code=app_code)

    # Get all functions grouped by status
    functions = app.functions.all().select_related('assigned_to')

    functions_by_status = {
        'planned': functions.filter(status='planned'),
        'developing': functions.filter(status='developing'),
        'completed': functions.filter(status='completed'),
        'uat': functions.filter(status='uat'),
        'softlaunch': functions.filter(status='softlaunch'),
        'production': functions.filter(status='production'),
        'blocked': functions.filter(status='blocked'),
    }

    # Status history
    status_history = app.status_history.select_related('changed_by').order_by('-created_at')[:20]

    # Blocked functions
    blocked_functions = functions.filter(is_blocked=True)

    # Functions with dependencies
    functions_with_deps = functions.filter(depends_on__isnull=False).distinct()

    context = {
        'app': app,
        'functions': functions,
        'functions_by_status': functions_by_status,
        'status_history': status_history,
        'blocked_functions': blocked_functions,
        'functions_with_deps': functions_with_deps,
    }
    return render(request, 'admin_panel/app_status_detail.html', context)


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def update_app_status(request, app_code):
    """Update application status"""
    app = get_object_or_404(AppStatus, app_code=app_code)

    new_status = request.POST.get('status')
    notes = request.POST.get('notes', '')

    if new_status not in dict(AppStatus.STATUS_CHOICES).keys():
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)

    old_status = app.status

    if old_status != new_status:
        # Record status change
        AppStatusHistory.objects.create(
            app=app,
            old_status=old_status,
            new_status=new_status,
            changed_by=request.user,
            notes=notes
        )

        # Update app status
        app.status = new_status

        # Update relevant date fields
        from django.utils import timezone
        today = timezone.now().date()

        if new_status == 'prototype' and not app.prototype_date:
            app.prototype_date = today
        elif new_status == 'uat' and not app.uat_date:
            app.uat_date = today
        elif new_status == 'softlaunch' and not app.softlaunch_date:
            app.softlaunch_date = today
        elif new_status == 'production' and not app.production_date:
            app.production_date = today

        app.save()

        messages.success(request, f"App status updated to {new_status}")
        return JsonResponse({
            'success': True,
            'status': new_status,
            'status_display': app.get_status_display(),
            'status_color': app.get_status_color()
        })

    return JsonResponse({'success': False, 'error': 'Status unchanged'})


@login_required
@user_passes_test(is_admin)
@require_http_methods(["POST"])
def update_function_status(request, function_id):
    """Update function status"""
    function = get_object_or_404(AppFunction, id=function_id)

    new_status = request.POST.get('status')

    if new_status not in dict(AppFunction.STATUS_CHOICES).keys():
        return JsonResponse({'success': False, 'error': 'Invalid status'}, status=400)

    function.status = new_status

    # Update completed date if moving to completed
    if new_status in ['completed', 'uat', 'softlaunch', 'production'] and not function.completed_at:
        from django.utils import timezone
        function.completed_at = timezone.now().date()

    function.save()

    # This will trigger app.update_completion() via the save method

    return JsonResponse({
        'success': True,
        'status': new_status,
        'status_display': function.get_status_display(),
        'status_color': function.get_status_color(),
        'app_completion': function.app.completion_percentage
    })


@login_required
@user_passes_test(is_admin)
def function_status_board(request):
    """Kanban-style board view of all functions"""

    # Filter options
    app_filter = request.GET.get('app', '')
    priority_filter = request.GET.get('priority', '')

    functions = AppFunction.objects.select_related('app', 'assigned_to')

    if app_filter:
        functions = functions.filter(app__app_code=app_filter)

    if priority_filter:
        functions = functions.filter(priority=priority_filter)

    # Group by status for kanban board
    kanban_columns = {
        'planned': functions.filter(status='planned'),
        'developing': functions.filter(status='developing'),
        'completed': functions.filter(status='completed'),
        'uat': functions.filter(status='uat'),
        'softlaunch': functions.filter(status='softlaunch'),
        'production': functions.filter(status='production'),
        'blocked': functions.filter(status='blocked'),
    }

    # Get all apps for filter
    apps = AppStatus.objects.filter(is_active=True)

    context = {
        'kanban_columns': kanban_columns,
        'apps': apps,
        'app_filter': app_filter,
        'priority_filter': priority_filter,
    }
    return render(request, 'admin_panel/function_status_board.html', context)


@login_required
@user_passes_test(is_admin)
def timeline_view(request):
    """Timeline view showing app progress"""
    apps = AppStatus.objects.filter(is_active=True).order_by('target_launch_date', 'app_name')

    # Group by status
    timeline_groups = {
        'overdue': [],
        'upcoming': [],
        'on_track': [],
        'completed': [],
    }

    from django.utils import timezone
    today = timezone.now().date()

    for app in apps:
        if app.status == 'production':
            timeline_groups['completed'].append(app)
        elif app.target_launch_date:
            days_until = (app.target_launch_date - today).days
            if days_until < 0:
                timeline_groups['overdue'].append(app)
            elif days_until <= 30:
                timeline_groups['upcoming'].append(app)
            else:
                timeline_groups['on_track'].append(app)
        else:
            timeline_groups['on_track'].append(app)

    context = {
        'timeline_groups': timeline_groups,
        'today': today,
    }
    return render(request, 'admin_panel/app_timeline.html', context)


@login_required
@user_passes_test(is_admin)
def blocked_functions_report(request):
    """Report of all blocked functions"""
    blocked_functions = AppFunction.objects.filter(
        is_blocked=True
    ).select_related('app', 'assigned_to').order_by('priority', 'app__app_name')

    # Group by app
    blocked_by_app = {}
    for func in blocked_functions:
        app_name = func.app.app_name
        if app_name not in blocked_by_app:
            blocked_by_app[app_name] = []
        blocked_by_app[app_name].append(func)

    context = {
        'blocked_functions': blocked_functions,
        'blocked_by_app': blocked_by_app,
        'total_blocked': blocked_functions.count(),
    }
    return render(request, 'admin_panel/blocked_functions_report.html', context)
