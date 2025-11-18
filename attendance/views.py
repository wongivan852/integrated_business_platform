"""
Attendance system views.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Count, Sum
from datetime import datetime, timedelta
from .models import (
    Department,
    AttendanceProfile,
    AttendanceRecord,
    AttendanceAdjustment,
    ClientDevice,
    AttendanceSystemConfig
)


@login_required
def attendance_dashboard(request):
    """
    Main attendance dashboard showing overview and quick actions.
    """
    # Get or create attendance profile for current user
    try:
        profile = AttendanceProfile.objects.get(user=request.user)
    except AttendanceProfile.DoesNotExist:
        # Redirect to profile creation if user doesn't have attendance profile
        messages.warning(request, 'Please set up your attendance profile first.')
        return redirect('attendance:profile_setup')

    # Get today's attendance record
    today = timezone.now().date()
    today_record = AttendanceRecord.objects.filter(
        profile=profile,
        clock_in__date=today
    ).first()

    # Get current week's records
    week_start = today - timedelta(days=today.weekday())
    week_records = AttendanceRecord.objects.filter(
        profile=profile,
        clock_in__date__gte=week_start
    ).order_by('-clock_in')

    # Calculate total hours this week
    total_hours_week = week_records.aggregate(
        total=Sum('total_hours')
    )['total'] or 0

    # Get system config
    config = AttendanceSystemConfig.get_config()

    context = {
        'profile': profile,
        'today_record': today_record,
        'week_records': week_records,
        'total_hours_week': total_hours_week,
        'config': config,
        'is_clocked_in': today_record and not today_record.clock_out,
    }
    return render(request, 'attendance/dashboard.html', context)


@login_required
def profile_setup(request):
    """
    Set up or edit attendance profile.
    """
    # Check if profile already exists
    try:
        profile = AttendanceProfile.objects.get(user=request.user)
    except AttendanceProfile.DoesNotExist:
        profile = None

    if request.method == 'POST':
        # Handle profile creation/update
        employee_code = request.POST.get('employee_code')
        department_id = request.POST.get('department')
        work_schedule_start = request.POST.get('work_schedule_start')
        work_schedule_end = request.POST.get('work_schedule_end')

        if profile:
            # Update existing profile
            profile.employee_code = employee_code
            if department_id:
                profile.department_id = department_id
            profile.work_schedule_start = work_schedule_start or None
            profile.work_schedule_end = work_schedule_end or None
            profile.save()
            messages.success(request, 'Attendance profile updated successfully.')
        else:
            # Create new profile
            profile = AttendanceProfile.objects.create(
                user=request.user,
                employee_code=employee_code,
                department_id=department_id if department_id else None,
                work_schedule_start=work_schedule_start or None,
                work_schedule_end=work_schedule_end or None,
                attendance_role='employee',
                is_active=True
            )
            messages.success(request, 'Attendance profile created successfully.')

        return redirect('attendance:dashboard')

    departments = Department.objects.all().order_by('name')

    context = {
        'profile': profile,
        'departments': departments,
    }
    return render(request, 'attendance/profile_setup.html', context)


@login_required
def attendance_records(request):
    """
    View attendance history/records.
    """
    try:
        profile = AttendanceProfile.objects.get(user=request.user)
    except AttendanceProfile.DoesNotExist:
        messages.warning(request, 'Please set up your attendance profile first.')
        return redirect('attendance:profile_setup')

    # Get date range from query params
    date_from = request.GET.get('date_from')
    date_to = request.GET.get('date_to')

    records = AttendanceRecord.objects.filter(profile=profile).order_by('-clock_in')

    if date_from:
        records = records.filter(clock_in__date__gte=date_from)
    if date_to:
        records = records.filter(clock_in__date__lte=date_to)

    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': profile,
        'page_obj': page_obj,
        'date_from': date_from,
        'date_to': date_to,
    }
    return render(request, 'attendance/records.html', context)
