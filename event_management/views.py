"""
Views for Event Management App - Phase 1 Basic Implementation
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q, Count, Sum
from django.utils import timezone
from datetime import timedelta
import uuid

from .models import (
    Event, EventPrerequisite, EventCost, EventReminder,
    EventWorkLog, EventReview, EventEquipment, EventApproval,
    CustomerFeedback, EquipmentDamageReport, DamagePhoto
)
from .forms import (
    EventReminderForm, CustomerFeedbackForm, EquipmentDamageReportForm,
    DamagePhotoForm, EquipmentReturnForm
)


@login_required
def event_dashboard(request):
    """
    Dashboard showing event statistics and upcoming events
    """
    # Get current user's events
    user_events = Event.objects.filter(
        Q(sales_responsible=request.user) | Q(assigned_staff=request.user)
    ).distinct()

    # Statistics
    total_events = user_events.count()
    upcoming_events = user_events.filter(
        status__in=['planned', 'confirmed'],
        planned_start_date__gte=timezone.now().date()
    ).count()
    in_progress_events = user_events.filter(status='in_progress').count()
    completed_events = user_events.filter(status='completed').count()

    # Recent events
    recent_events = user_events.order_by('-created_at')[:5]

    # Pending approvals (if user is an approver)
    pending_approvals = EventApproval.objects.filter(
        approver=request.user,
        status='pending'
    ).select_related('event')[:5]

    # Upcoming reminders
    upcoming_reminders = EventReminder.objects.filter(
        recipient=request.user,
        is_sent=False,
        scheduled_time__gte=timezone.now(),
        scheduled_time__lte=timezone.now() + timedelta(days=7)
    ).select_related('event').order_by('scheduled_time')[:5]

    context = {
        'total_events': total_events,
        'upcoming_events': upcoming_events,
        'in_progress_events': in_progress_events,
        'completed_events': completed_events,
        'recent_events': recent_events,
        'pending_approvals': pending_approvals,
        'upcoming_reminders': upcoming_reminders,
    }

    return render(request, 'event_management/dashboard.html', context)


@login_required
def event_list(request):
    """
    List all events with filtering and search
    """
    events = Event.objects.all().select_related(
        'sales_responsible', 'created_by'
    ).prefetch_related('assigned_staff')

    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        events = events.filter(
            Q(event_number__icontains=search_query) |
            Q(customer_company__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(location_city__icontains=search_query)
        )

    # Filter by event type
    event_type = request.GET.get('event_type', '')
    if event_type:
        events = events.filter(event_type=event_type)

    # Filter by status
    status = request.GET.get('status', '')
    if status:
        events = events.filter(status=status)

    # Order by planned start date (newest first)
    events = events.order_by('-planned_start_date')

    context = {
        'events': events,
        'search_query': search_query,
        'event_type': event_type,
        'status': status,
        'event_type_choices': Event.EVENT_TYPES,
        'status_choices': Event.STATUS_CHOICES,
    }

    return render(request, 'event_management/event_list.html', context)


@login_required
def event_detail(request, pk):
    """
    Detailed view of a single event with all related information
    """
    event = get_object_or_404(
        Event.objects.select_related(
            'sales_responsible', 'created_by'
        ).prefetch_related('assigned_staff'),
        pk=pk
    )

    # Get related objects
    prerequisites = event.prerequisites.all().order_by('category', 'id')
    costs = event.costs.all().select_related('staff_member').order_by('-expense_date')
    work_logs = event.work_logs.all().select_related('staff_member').order_by('-log_date')
    equipment = event.equipment.all().select_related('checked_out_by').order_by('-checkout_date')
    approvals = event.approvals.all().select_related('approver').order_by('approval_role')

    try:
        review = event.review
    except EventReview.DoesNotExist:
        review = None

    # Calculate completion percentage for prerequisites
    total_prerequisites = prerequisites.count()
    completed_prerequisites = prerequisites.filter(is_completed=True).count()
    prerequisite_completion = (completed_prerequisites / total_prerequisites * 100) if total_prerequisites > 0 else 0

    context = {
        'event': event,
        'prerequisites': prerequisites,
        'costs': costs,
        'work_logs': work_logs,
        'equipment': equipment,
        'approvals': approvals,
        'review': review,
        'prerequisite_completion': prerequisite_completion,
    }

    return render(request, 'event_management/event_detail.html', context)


@login_required
def event_create(request):
    """
    Create a new event
    """
    if request.method == 'POST':
        try:
            # Generate event number
            event_number = f"EVT-{timezone.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

            # Create event
            event = Event.objects.create(
                event_number=event_number,
                event_type=request.POST.get('event_type'),
                status=request.POST.get('status', 'planned'),
                customer_company=request.POST.get('customer_company'),
                contact_person=request.POST.get('contact_person'),
                contact_position=request.POST.get('contact_position'),
                contact_phone=request.POST.get('contact_phone'),
                contact_wechat=request.POST.get('contact_wechat', ''),
                contact_email=request.POST.get('contact_email'),
                delivery_address=request.POST.get('delivery_address'),
                installation_address=request.POST.get('installation_address', ''),
                training_address=request.POST.get('training_address', ''),
                planned_start_date=request.POST.get('planned_start_date'),
                planned_end_date=request.POST.get('planned_end_date'),
                estimated_duration_days=request.POST.get('estimated_duration_days'),
                sales_responsible=request.user,
                estimated_total_cost=request.POST.get('estimated_total_cost', 0),
                actual_total_cost=request.POST.get('actual_total_cost', 0),
            )

            messages.success(request, f'Event {event.event_number} created successfully!')
            return redirect('event_management:event_detail', pk=event.pk)

        except Exception as e:
            messages.error(request, f'Error creating event: {str(e)}')
            return redirect('event_management:event_create')

    context = {
        'event_type_choices': Event.EVENT_TYPES,
        'status_choices': Event.STATUS_CHOICES,
    }

    return render(request, 'event_management/event_form.html', context)


@login_required
def event_edit(request, pk):
    """
    Edit an existing event (placeholder for Phase 2)
    """
    event = get_object_or_404(Event, pk=pk)

    if request.method == 'POST':
        messages.info(request, 'Event editing will be implemented in Phase 2.')
        return redirect('event_management:event_detail', pk=pk)

    context = {
        'event': event,
        'event_type_choices': Event.EVENT_TYPES,
        'status_choices': Event.STATUS_CHOICES,
    }

    return render(request, 'event_management/event_form.html', context)


@login_required
def event_prerequisites(request, event_pk):
    """
    View and manage event prerequisites
    """
    event = get_object_or_404(Event, pk=event_pk)
    prerequisites = event.prerequisites.all().order_by('category', 'id')

    context = {
        'event': event,
        'prerequisites': prerequisites,
    }

    return render(request, 'event_management/event_prerequisites.html', context)


@login_required
def event_costs(request, event_pk):
    """
    View and manage event costs
    """
    event = get_object_or_404(Event, pk=event_pk)
    costs = event.costs.all().select_related('staff_member').order_by('-expense_date')

    # Calculate totals
    total_estimated = costs.aggregate(Sum('estimated_amount'))['estimated_amount__sum'] or 0
    total_actual = costs.aggregate(Sum('actual_amount'))['actual_amount__sum'] or 0

    context = {
        'event': event,
        'costs': costs,
        'total_estimated': total_estimated,
        'total_actual': total_actual,
    }

    return render(request, 'event_management/event_costs.html', context)


@login_required
def event_worklogs(request, event_pk):
    """
    View event work logs
    """
    event = get_object_or_404(Event, pk=event_pk)
    work_logs = event.work_logs.all().select_related('staff_member').order_by('-log_date')

    context = {
        'event': event,
        'work_logs': work_logs,
    }

    return render(request, 'event_management/event_worklogs.html', context)


@login_required
def event_equipment(request, event_pk):
    """
    View and manage event equipment
    """
    event = get_object_or_404(Event, pk=event_pk)
    equipment = event.equipment.all().select_related('checked_out_by').order_by('-checkout_date')

    # Separate checked out and returned equipment
    checked_out = equipment.filter(is_returned=False)
    returned = equipment.filter(is_returned=True)

    context = {
        'event': event,
        'checked_out': checked_out,
        'returned': returned,
    }

    return render(request, 'event_management/event_equipment.html', context)


@login_required
def event_approvals(request, event_pk):
    """
    View event approvals
    """
    event = get_object_or_404(Event, pk=event_pk)
    approvals = event.approvals.all().select_related('approver').order_by('approval_role')

    context = {
        'event': event,
        'approvals': approvals,
    }

    return render(request, 'event_management/event_approvals.html', context)


@login_required
def approval_review(request, pk):
    """
    Review and approve/reject an approval request
    """
    approval = get_object_or_404(EventApproval, pk=pk)

    # Check if current user is the approver
    if approval.approver != request.user:
        messages.error(request, 'You are not authorized to review this approval.')
        return redirect('event_management:event_detail', pk=approval.event.pk)

    if request.method == 'POST':
        action = request.POST.get('action')
        comments = request.POST.get('comments', '')

        if action == 'approve':
            approval.status = 'approved'
            approval.approved_at = timezone.now()
            approval.comments = comments
            approval.save()
            messages.success(request, f'Approval for {approval.event.event_number} has been approved.')
        elif action == 'reject':
            approval.status = 'rejected'
            approval.approved_at = timezone.now()
            approval.comments = comments
            approval.save()
            messages.warning(request, f'Approval for {approval.event.event_number} has been rejected.')

        return redirect('event_management:event_detail', pk=approval.event.pk)

    context = {
        'approval': approval,
    }

    return render(request, 'event_management/approval_review.html', context)


@login_required
def event_review_create(request, event_pk):
    """
    Create a review for a completed event
    """
    event = get_object_or_404(Event, pk=event_pk)

    # Check if review already exists
    try:
        existing_review = event.review
        messages.info(request, 'A review already exists for this event.')
        return redirect('event_management:event_detail', pk=event_pk)
    except EventReview.DoesNotExist:
        pass

    if request.method == 'POST':
        messages.info(request, 'Event review creation will be fully implemented in Phase 4.')
        return redirect('event_management:event_detail', pk=event_pk)

    context = {
        'event': event,
    }

    return render(request, 'event_management/event_review_form.html', context)


# ============================================================================
# REMINDER MANAGEMENT VIEWS
# ============================================================================

@login_required
def reminder_list(request, event_pk):
    """List all reminders for an event"""
    event = get_object_or_404(Event, pk=event_pk)
    reminders = event.reminders.all().prefetch_related('recipients')

    # Calculate statistics
    now = timezone.now()
    pending_count = reminders.filter(sent=False, send_datetime__gte=now).count()
    sent_count = reminders.filter(sent=True).count()
    overdue_count = reminders.filter(sent=False, send_datetime__lt=now).count()

    context = {
        'event': event,
        'reminders': reminders,
        'pending_count': pending_count,
        'sent_count': sent_count,
        'overdue_count': overdue_count,
        'now': now,
    }

    return render(request, 'event_management/reminder_list.html', context)


@login_required
def reminder_create(request, event_pk):
    """Create a new reminder for an event"""
    event = get_object_or_404(Event, pk=event_pk)

    if request.method == 'POST':
        form = EventReminderForm(request.POST)
        if form.is_valid():
            reminder = form.save(commit=False)
            reminder.event = event
            reminder.created_by = request.user
            reminder.save()
            form.save_m2m()  # Save the many-to-many relationships (recipients)

            # Trigger auto-creation of reminder task
            from .tasks import auto_create_event_reminders
            # Note: This is already created, so we just schedule the existing reminder
            # The check_and_send_reminders task will pick it up

            messages.success(request, f'Reminder "{reminder.title}" created successfully!')
            return redirect('event_management:reminder_list', event_pk=event.pk)
    else:
        # Set default values
        initial = {
            'send_email': True,
            'send_sms': False,
            'send_wechat': False,
        }
        form = EventReminderForm(initial=initial)

    context = {
        'event': event,
        'form': form,
        'reminder': None,
    }

    return render(request, 'event_management/reminder_form.html', context)


@login_required
def reminder_edit(request, pk):
    """Edit an existing reminder"""
    reminder = get_object_or_404(EventReminder, pk=pk)

    # Don't allow editing sent reminders
    if reminder.sent:
        messages.warning(request, 'Cannot edit a reminder that has already been sent.')
        return redirect('event_management:reminder_list', event_pk=reminder.event.pk)

    if request.method == 'POST':
        form = EventReminderForm(request.POST, instance=reminder)
        if form.is_valid():
            form.save()
            messages.success(request, f'Reminder "{reminder.title}" updated successfully!')
            return redirect('event_management:reminder_list', event_pk=reminder.event.pk)
    else:
        form = EventReminderForm(instance=reminder)

    context = {
        'event': reminder.event,
        'form': form,
        'reminder': reminder,
    }

    return render(request, 'event_management/reminder_form.html', context)


@login_required
def reminder_detail(request, pk):
    """View reminder details"""
    reminder = get_object_or_404(
        EventReminder.objects.select_related('event', 'created_by').prefetch_related('recipients'),
        pk=pk
    )

    context = {
        'reminder': reminder,
        'event': reminder.event,
    }

    return render(request, 'event_management/reminder_detail.html', context)


@login_required
def reminder_delete(request, pk):
    """Delete a reminder"""
    reminder = get_object_or_404(EventReminder, pk=pk)
    event_pk = reminder.event.pk

    # Don't allow deleting sent reminders
    if reminder.sent:
        messages.warning(request, 'Cannot delete a reminder that has already been sent.')
        return redirect('event_management:reminder_list', event_pk=event_pk)

    if request.method == 'POST':
        title = reminder.title
        reminder.delete()
        messages.success(request, f'Reminder "{title}" deleted successfully!')
        return redirect('event_management:reminder_list', event_pk=event_pk)

    context = {
        'reminder': reminder,
        'event': reminder.event,
    }

    return render(request, 'event_management/reminder_confirm_delete.html', context)


@login_required
def reminder_send_now(request, pk):
    """Send a reminder immediately (AJAX endpoint)"""
    from django.http import JsonResponse
    from .tasks import send_reminder_email, send_reminder_sms, send_reminder_wechat

    if request.method != 'POST':
        return JsonResponse({'status': 'error', 'message': 'POST method required'}, status=405)

    reminder = get_object_or_404(EventReminder, pk=pk)

    # Don't allow re-sending
    if reminder.sent:
        return JsonResponse({'status': 'error', 'message': 'Reminder already sent'})

    # Queue the tasks
    try:
        if reminder.send_email:
            send_reminder_email.delay(reminder.id)

        if reminder.send_sms:
            send_reminder_sms.delay(reminder.id)

        if reminder.send_wechat:
            send_reminder_wechat.delay(reminder.id)

        return JsonResponse({'status': 'success', 'message': 'Reminder is being sent'})
    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)})


# Import Phase 4 views
from .views_phase4 import (
    customer_feedback_submit, customer_feedback_thank_you,
    feedback_list, feedback_detail, feedback_review, feedback_create_for_event,
    damage_report_list, damage_report_create, damage_report_detail, damage_report_edit,
    damage_photo_upload, damage_photo_delete,
    equipment_return_process, equipment_inventory,
    analytics_dashboard
)
