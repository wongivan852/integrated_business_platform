"""
Phase 4 Views for Event Management - Customer Feedback & Equipment Management
"""
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from datetime import timedelta

from .models import (
    Event, EventEquipment, EventReview,
    CustomerFeedback, EquipmentDamageReport, DamagePhoto
)
from .forms import (
    CustomerFeedbackForm, EquipmentDamageReportForm,
    DamagePhotoForm, EquipmentReturnForm
)


# ========================================
# Phase 4: Customer Feedback Views
# ========================================

def customer_feedback_submit(request, token):
    """
    Public view for customers to submit feedback (no login required)
    """
    feedback = get_object_or_404(CustomerFeedback, feedback_token=token)

    # Check if already submitted
    if feedback.submitted:
        return render(request, 'event_management/feedback_already_submitted.html', {
            'feedback': feedback
        })

    if request.method == 'POST':
        form = CustomerFeedbackForm(request.POST, instance=feedback)
        if form.is_valid():
            feedback = form.save(commit=False)
            feedback.submitted = True
            feedback.submitted_at = timezone.now()
            feedback.save()

            # Send confirmation email (future enhancement with Celery)
            # from .tasks import send_feedback_confirmation_email
            # send_feedback_confirmation_email.delay(feedback.id)

            return redirect('event_management:feedback_thank_you', token=token)
    else:
        # Pre-fill customer information from event
        initial = {
            'customer_name': feedback.event.contact_person,
            'customer_email': feedback.event.contact_email,
            'customer_position': feedback.event.contact_position,
        }
        form = CustomerFeedbackForm(instance=feedback, initial=initial)

    context = {
        'form': form,
        'feedback': feedback,
        'event': feedback.event,
    }
    return render(request, 'event_management/customer_feedback_form.html', context)


def customer_feedback_thank_you(request, token):
    """Thank you page after feedback submission"""
    feedback = get_object_or_404(CustomerFeedback, feedback_token=token)

    context = {
        'feedback': feedback,
        'event': feedback.event,
    }
    return render(request, 'event_management/feedback_thank_you.html', context)


@login_required
def feedback_list(request):
    """Staff view: List all customer feedback"""
    feedbacks = CustomerFeedback.objects.select_related('event').order_by('-created_at')

    # Filter options
    status_filter = request.GET.get('status', 'all')
    if status_filter == 'submitted':
        feedbacks = feedbacks.filter(submitted=True)
    elif status_filter == 'pending':
        feedbacks = feedbacks.filter(submitted=False)

    # Statistics
    total_feedback = CustomerFeedback.objects.count()
    submitted_count = CustomerFeedback.objects.filter(submitted=True).count()
    pending_count = CustomerFeedback.objects.filter(submitted=False).count()

    # Submitted feedback for calculations
    submitted_feedbacks = CustomerFeedback.objects.filter(submitted=True)

    # Calculate average rating
    if submitted_feedbacks.exists():
        avg_rating = sum(f.average_rating for f in submitted_feedbacks) / submitted_feedbacks.count()
    else:
        avg_rating = 0

    # NPS calculations
    promoters = sum(1 for f in submitted_feedbacks if f.nps_category == 'promoter')
    passives = sum(1 for f in submitted_feedbacks if f.nps_category == 'passive')
    detractors = sum(1 for f in submitted_feedbacks if f.nps_category == 'detractor')

    if submitted_feedbacks.count() > 0:
        nps_score = ((promoters - detractors) / submitted_feedbacks.count()) * 100
    else:
        nps_score = 0

    context = {
        'feedbacks': feedbacks,
        'status_filter': status_filter,
        'total_feedback': total_feedback,
        'submitted_count': submitted_count,
        'pending_count': pending_count,
        'avg_rating': avg_rating,
        'nps_score': nps_score,
        'promoters': promoters,
        'passives': passives,
        'detractors': detractors,
    }
    return render(request, 'event_management/feedback_list.html', context)


@login_required
def feedback_detail(request, pk):
    """Staff view: View detailed feedback"""
    feedback = get_object_or_404(
        CustomerFeedback.objects.select_related('event', 'reviewed_by'),
        pk=pk
    )

    context = {
        'feedback': feedback,
    }
    return render(request, 'event_management/feedback_detail.html', context)


@login_required
def feedback_review(request, pk):
    """Staff view: Mark feedback as reviewed and add internal notes"""
    feedback = get_object_or_404(CustomerFeedback, pk=pk)

    if request.method == 'POST':
        feedback.reviewed_by = request.user
        feedback.internal_notes = request.POST.get('internal_notes', '')
        feedback.follow_up_required = request.POST.get('follow_up_required') == 'on'
        feedback.follow_up_completed = request.POST.get('follow_up_completed') == 'on'
        feedback.save()

        messages.success(request, 'Feedback review saved successfully!')
        return redirect('event_management:feedback_detail', pk=pk)

    return redirect('event_management:feedback_detail', pk=pk)


@login_required
def feedback_create_for_event(request, event_pk):
    """Staff view: Create a feedback request for an event"""
    event = get_object_or_404(Event, pk=event_pk)

    # Check if feedback already exists
    if hasattr(event, 'customer_feedback'):
        messages.warning(request, 'Feedback request already exists for this event.')
        return redirect('event_management:event_detail', pk=event_pk)

    # Create feedback record with default ratings
    feedback = CustomerFeedback.objects.create(
        event=event,
        customer_name=event.contact_person,
        customer_email=event.contact_email,
        customer_position=event.contact_position,
        service_quality_rating=3,  # Default to neutral
        staff_professionalism_rating=3,
        timeliness_rating=3,
        technical_expertise_rating=3,
        communication_rating=3,
        likelihood_to_use_again=8,
    )
    feedback.feedback_sent_at = timezone.now()
    feedback.save()

    # Generate feedback URL
    feedback_url = request.build_absolute_uri(
        f'/events/feedback/{feedback.feedback_token}/'
    )

    messages.success(
        request,
        f'Feedback request created! Share this link with customer: {feedback_url}'
    )
    return redirect('event_management:event_detail', pk=event_pk)


# ========================================
# Phase 4: Equipment Damage Report Views
# ========================================

@login_required
def damage_report_list(request, event_pk):
    """List all damage reports for an event"""
    event = get_object_or_404(Event, pk=event_pk)
    equipment_items = event.equipment.all().prefetch_related('damage_reports__photos')

    # Statistics
    total_equipment = equipment_items.count()
    damaged_count = equipment_items.filter(status__in=['damaged', 'lost']).count()

    # Calculate total damage cost
    all_reports = EquipmentDamageReport.objects.filter(equipment__event=event)
    total_cost = sum(report.total_cost for report in all_reports)

    context = {
        'event': event,
        'equipment_items': equipment_items,
        'total_equipment': total_equipment,
        'damaged_count': damaged_count,
        'total_cost': total_cost,
        'all_reports': all_reports,
    }
    return render(request, 'event_management/damage_report_list.html', context)


@login_required
def damage_report_create(request, equipment_pk):
    """Create a damage report for equipment"""
    equipment = get_object_or_404(EventEquipment, pk=equipment_pk)

    if request.method == 'POST':
        form = EquipmentDamageReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.equipment = equipment
            report.discovered_by = request.user
            report.save()

            # Update equipment status to damaged
            equipment.status = 'damaged'
            equipment.damage_report = report.description
            equipment.save()

            messages.success(request, 'Damage report created successfully!')
            return redirect('event_management:damage_report_detail', pk=report.pk)
    else:
        form = EquipmentDamageReportForm()

    context = {
        'form': form,
        'equipment': equipment,
        'event': equipment.event,
    }
    return render(request, 'event_management/damage_report_form.html', context)


@login_required
def damage_report_detail(request, pk):
    """View detailed damage report with photos"""
    report = get_object_or_404(
        EquipmentDamageReport.objects.select_related(
            'equipment__event', 'discovered_by'
        ).prefetch_related('photos__uploaded_by'),
        pk=pk
    )

    context = {
        'report': report,
        'equipment': report.equipment,
        'event': report.equipment.event,
    }
    return render(request, 'event_management/damage_report_detail.html', context)


@login_required
def damage_report_edit(request, pk):
    """Edit an existing damage report"""
    report = get_object_or_404(EquipmentDamageReport, pk=pk)

    if request.method == 'POST':
        form = EquipmentDamageReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, 'Damage report updated successfully!')
            return redirect('event_management:damage_report_detail', pk=pk)
    else:
        form = EquipmentDamageReportForm(instance=report)

    context = {
        'form': form,
        'report': report,
        'equipment': report.equipment,
        'event': report.equipment.event,
    }
    return render(request, 'event_management/damage_report_form.html', context)


@login_required
def damage_photo_upload(request, report_pk):
    """Upload photos to a damage report"""
    report = get_object_or_404(EquipmentDamageReport, pk=report_pk)

    if request.method == 'POST':
        form = DamagePhotoForm(request.POST, request.FILES)
        if form.is_valid():
            photo = form.save(commit=False)
            photo.damage_report = report
            photo.uploaded_by = request.user
            photo.save()

            messages.success(request, 'Photo uploaded successfully!')
            return redirect('event_management:damage_report_detail', pk=report_pk)
    else:
        form = DamagePhotoForm()

    context = {
        'form': form,
        'report': report,
    }
    return render(request, 'event_management/damage_photo_upload.html', context)


@login_required
def damage_photo_delete(request, pk):
    """Delete a damage photo"""
    photo = get_object_or_404(DamagePhoto, pk=pk)
    report_pk = photo.damage_report.pk

    if request.method == 'POST':
        photo.photo.delete()  # Delete file from storage
        photo.delete()  # Delete database record
        messages.success(request, 'Photo deleted successfully!')

    return redirect('event_management:damage_report_detail', pk=report_pk)


# ========================================
# Phase 4: Equipment Return Views
# ========================================

@login_required
def equipment_return_process(request, pk):
    """Process equipment return"""
    equipment = get_object_or_404(EventEquipment, pk=pk)

    if request.method == 'POST':
        form = EquipmentReturnForm(request.POST, instance=equipment)
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.returned_by = request.user
            equipment.returned_date = timezone.now()
            equipment.save()

            # If equipment is damaged, redirect to create damage report
            if equipment.status == 'damaged' and equipment.damage_report:
                messages.info(
                    request,
                    'Equipment marked as damaged. Please create a detailed damage report.'
                )
                return redirect('event_management:damage_report_create', equipment_pk=pk)

            messages.success(request, f'{equipment.equipment_name} returned successfully!')
            return redirect('event_management:equipment_inventory', event_pk=equipment.event.pk)
    else:
        form = EquipmentReturnForm(instance=equipment)

    context = {
        'form': form,
        'equipment': equipment,
        'event': equipment.event,
    }
    return render(request, 'event_management/equipment_return_form.html', context)


@login_required
def equipment_inventory(request, event_pk):
    """Equipment inventory dashboard for an event"""
    event = get_object_or_404(Event, pk=event_pk)
    equipment_items = event.equipment.all().select_related('checked_out_by', 'returned_by')

    # Statistics
    total_items = equipment_items.count()
    checked_out = equipment_items.filter(status='checked_out').count()
    in_use = equipment_items.filter(status='in_use').count()
    returned = equipment_items.filter(status='returned').count()
    damaged = equipment_items.filter(status='damaged').count()
    lost = equipment_items.filter(status='lost').count()

    # Overdue equipment (checked out for more than planned event duration + 7 days)
    overdue_items = []
    for item in equipment_items.exclude(status='returned'):
        if item.days_out > (event.estimated_duration_days + 7):
            overdue_items.append(item)

    context = {
        'event': event,
        'equipment_items': equipment_items,
        'total_items': total_items,
        'checked_out': checked_out,
        'in_use': in_use,
        'returned': returned,
        'damaged': damaged,
        'lost': lost,
        'overdue_items': overdue_items,
    }
    return render(request, 'event_management/equipment_inventory.html', context)


# ========================================
# Phase 4: Analytics Dashboard
# ========================================

@login_required
def analytics_dashboard(request):
    """Performance analytics dashboard"""
    # Date range filter
    days = int(request.GET.get('days', 90))
    start_date = timezone.now().date() - timedelta(days=days)

    # Event statistics
    events = Event.objects.filter(created_at__gte=start_date)
    total_events = events.count()
    completed_events = events.filter(status='completed').count()

    # Customer feedback statistics
    feedbacks = CustomerFeedback.objects.filter(
        submitted=True,
        submitted_at__gte=start_date
    )

    feedback_response_rate = 0
    if completed_events > 0:
        feedback_response_rate = (feedbacks.count() / completed_events) * 100

    # Average ratings
    if feedbacks.exists():
        avg_service_quality = sum(f.service_quality_rating for f in feedbacks) / feedbacks.count()
        avg_staff_professionalism = sum(f.staff_professionalism_rating for f in feedbacks) / feedbacks.count()
        avg_timeliness = sum(f.timeliness_rating for f in feedbacks) / feedbacks.count()
        avg_technical_expertise = sum(f.technical_expertise_rating for f in feedbacks) / feedbacks.count()
        avg_communication = sum(f.communication_rating for f in feedbacks) / feedbacks.count()
        overall_avg = sum(f.average_rating for f in feedbacks) / feedbacks.count()
    else:
        avg_service_quality = avg_staff_professionalism = avg_timeliness = 0
        avg_technical_expertise = avg_communication = overall_avg = 0

    # NPS Score
    promoters = sum(1 for f in feedbacks if f.nps_category == 'promoter')
    passives = sum(1 for f in feedbacks if f.nps_category == 'passive')
    detractors = sum(1 for f in feedbacks if f.nps_category == 'detractor')

    if feedbacks.count() > 0:
        nps_score = ((promoters - detractors) / feedbacks.count()) * 100
    else:
        nps_score = 0

    # Equipment damage statistics
    damage_reports = EquipmentDamageReport.objects.filter(
        discovered_date__gte=start_date
    )
    total_damage_cost = sum(report.total_cost for report in damage_reports)
    preventable_damage = damage_reports.filter(preventable=True).count()

    # Event reviews
    reviews = EventReview.objects.filter(
        review_date__gte=start_date
    )
    if reviews.exists():
        avg_review_rating = sum(r.average_rating for r in reviews) / reviews.count()
    else:
        avg_review_rating = 0

    # Prepare data for charts (for Chart.js)
    rating_labels = ['Service Quality', 'Staff Professionalism', 'Timeliness', 'Technical Expertise', 'Communication']
    rating_data = [
        avg_service_quality,
        avg_staff_professionalism,
        avg_timeliness,
        avg_technical_expertise,
        avg_communication
    ]

    context = {
        'days': days,
        'start_date': start_date,
        'total_events': total_events,
        'completed_events': completed_events,
        'feedback_response_rate': feedback_response_rate,
        'avg_service_quality': avg_service_quality,
        'avg_staff_professionalism': avg_staff_professionalism,
        'avg_timeliness': avg_timeliness,
        'avg_technical_expertise': avg_technical_expertise,
        'avg_communication': avg_communication,
        'overall_avg': overall_avg,
        'nps_score': nps_score,
        'promoters': promoters,
        'passives': passives,
        'detractors': detractors,
        'total_feedbacks': feedbacks.count(),
        'damage_reports_count': damage_reports.count(),
        'total_damage_cost': total_damage_cost,
        'preventable_damage': preventable_damage,
        'avg_review_rating': avg_review_rating,
        'rating_labels': rating_labels,
        'rating_data': rating_data,
    }
    return render(request, 'event_management/analytics_dashboard.html', context)
