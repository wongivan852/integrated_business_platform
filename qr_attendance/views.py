"""
QR Code Attendance System Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Participant, QRAttendanceRecord, Venue


@login_required
def dashboard(request):
    """QR Attendance Dashboard with multi-venue support"""
    from .models import Venue

    # Get all active venues
    venues = Venue.objects.filter(is_active=True)

    # Calculate total occupancy across all venues
    total_occupancy = 0
    total_capacity = 0
    venue_stats = []

    for venue in venues:
        occupancy = venue.get_current_occupancy()
        total_occupancy += occupancy
        total_capacity += venue.max_capacity

        venue_stats.append({
            'venue': venue,
            'current_occupancy': occupancy,
            'max_capacity': venue.max_capacity,
            'available_capacity': venue.get_available_capacity(),
            'occupancy_percentage': venue.get_occupancy_percentage(),
            'is_at_capacity': venue.is_at_capacity(),
            'is_at_warning': venue.is_at_warning_level(),
        })

    # Overall stats
    overall_percentage = int((total_occupancy / total_capacity) * 100) if total_capacity > 0 else 0

    context = {
        'venues': venue_stats,
        'total_occupancy': total_occupancy,
        'total_capacity': total_capacity,
        'total_available': total_capacity - total_occupancy,
        'overall_percentage': overall_percentage,
        'venue_count': venues.count(),
    }
    return render(request, 'qr_attendance/dashboard.html', context)


@login_required
def scanner(request):
    """QR Code Scanner Interface with venue selection"""
    from .models import Venue

    # Get selected venue from query parameter or session
    venue_id = request.GET.get('venue') or request.session.get('selected_venue')

    venues = Venue.objects.filter(is_active=True)

    if venue_id:
        try:
            selected_venue = Venue.objects.get(id=venue_id, is_active=True)
            request.session['selected_venue'] = str(venue_id)
        except Venue.DoesNotExist:
            selected_venue = venues.first() if venues.exists() else None
    else:
        selected_venue = venues.first() if venues.exists() else None

    context = {
        'venue': selected_venue,
        'all_venues': venues,
        'selected_venue_id': str(selected_venue.id) if selected_venue else None,
    }
    return render(request, 'qr_attendance/scanner.html', context)


@login_required
def participant_list(request):
    """List all participants"""
    participants = Participant.objects.filter(is_active=True).order_by('-created_at')

    context = {
        'participants': participants,
    }
    return render(request, 'qr_attendance/participant_list.html', context)


@login_required
def participant_create(request):
    """Create new participant"""
    if request.method == 'POST':
        name = request.POST.get('name')
        email = request.POST.get('email')
        phone = request.POST.get('phone')
        participant_class = request.POST.get('participant_class', 'regular')

        participant = Participant.objects.create(
            name=name,
            email=email,
            phone=phone,
            participant_class=participant_class
        )

        messages.success(request, f'Participant {name} created successfully with QR code!')
        return redirect('qr_attendance:participant_detail', pk=participant.pk)

    return render(request, 'qr_attendance/participant_create.html')


@login_required
def participant_detail(request, pk):
    """View participant details and QR code"""
    participant = get_object_or_404(Participant, pk=pk)

    context = {
        'participant': participant,
    }
    return render(request, 'qr_attendance/participant_detail.html', context)


@login_required
def reports(request):
    """Attendance reports"""
    return render(request, 'qr_attendance/reports.html')


# Venue Management Views
@login_required
def venue_list(request):
    """List all venues"""
    venues = Venue.objects.all().order_by('name')

    context = {
        'venues': venues,
    }
    return render(request, 'qr_attendance/venue_list.html', context)


@login_required
def venue_create(request):
    """Create new venue"""
    if request.method == 'POST':
        name = request.POST.get('name')
        code = request.POST.get('code')
        location = request.POST.get('location', '')
        max_capacity = int(request.POST.get('max_capacity', 100))
        warning_threshold = int(request.POST.get('warning_threshold', 90))
        enable_capacity_limit = request.POST.get('enable_capacity_limit') == 'on'
        description = request.POST.get('description', '')

        venue = Venue.objects.create(
            name=name,
            code=code.upper(),
            location=location,
            max_capacity=max_capacity,
            warning_threshold=warning_threshold,
            enable_capacity_limit=enable_capacity_limit,
            description=description,
            created_by=request.user,
            is_active=True
        )

        messages.success(request, f'Venue "{name}" created successfully!')
        return redirect('qr_attendance:venue_list')

    return render(request, 'qr_attendance/venue_create.html')


@login_required
def venue_detail(request, pk):
    """View venue details and current occupancy"""
    venue = get_object_or_404(Venue, pk=pk)

    # Get currently checked-in participants at this venue
    checked_in_participants = venue.get_checked_in_participants()

    # Get recent activity at this venue
    recent_records = QRAttendanceRecord.objects.filter(
        venue=venue
    ).select_related('participant', 'scanned_by').order_by('-time_in')[:20]

    context = {
        'venue': venue,
        'checked_in_participants': checked_in_participants,
        'recent_records': recent_records,
    }
    return render(request, 'qr_attendance/venue_detail.html', context)


# API endpoints
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
from django.utils import timezone


@login_required
@require_POST
def scan_qr_code(request):
    """
    API endpoint to process QR code scan with venue tracking.
    Handles check-in and check-out logic for specific venues.
    """
    try:
        from .models import Venue, AuditLog

        data = json.loads(request.body)
        code = data.get('code', '').strip()
        venue_id = data.get('venue_id')

        if not code:
            return JsonResponse({'success': False, 'error': 'No code provided'})

        if not venue_id:
            return JsonResponse({'success': False, 'error': 'No venue selected'})

        # Find participant by unique_id
        try:
            participant = Participant.objects.get(unique_id=code, is_active=True)
        except Participant.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid participant code'})

        # Get venue
        try:
            venue = Venue.objects.get(id=venue_id, is_active=True)
        except Venue.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Invalid venue'})

        # Check if participant is currently checked in at THIS venue
        active_record = QRAttendanceRecord.objects.filter(
            participant=participant,
            venue=venue,
            checked_in=True
        ).first()

        if active_record:
            # Check out from this venue
            active_record.checkout()
            action = 'check_out'
            message = f'{participant.name} checked out from {venue.name}'

            # Log audit
            AuditLog.objects.create(
                action='scan_out',
                user=request.user,
                participant=participant,
                details=f'Checked out from {venue.name} at {timezone.now()}',
                ip_address=request.META.get('REMOTE_ADDR')
            )
        else:
            # Check if participant is checked in at a DIFFERENT venue
            other_venue_record = QRAttendanceRecord.objects.filter(
                participant=participant,
                checked_in=True
            ).exclude(venue=venue).first()

            if other_venue_record:
                # Auto check-out from other venue and check-in to new venue
                old_venue = other_venue_record.venue
                other_venue_record.checkout()

                AuditLog.objects.create(
                    action='scan_out',
                    user=request.user,
                    participant=participant,
                    details=f'Auto checked out from {old_venue.name} (moved to {venue.name})',
                    ip_address=request.META.get('REMOTE_ADDR')
                )

            # Check capacity before check-in
            if venue.enable_capacity_limit and venue.is_at_capacity():
                return JsonResponse({
                    'success': False,
                    'error': f'{venue.name} is at maximum capacity. Cannot check in.'
                })

            # Check in to new venue
            record = QRAttendanceRecord.objects.create(
                participant=participant,
                venue=venue,
                time_in=timezone.now(),
                scanned_by=request.user,
                checked_in=True
            )
            action = 'check_in'
            message = f'{participant.name} checked in to {venue.name}'

            # Log audit
            AuditLog.objects.create(
                action='scan_in',
                user=request.user,
                participant=participant,
                details=f'Checked in to {venue.name} at {timezone.now()}',
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return JsonResponse({
            'success': True,
            'action': action,
            'participant_name': participant.name,
            'venue_name': venue.name,
            'current_occupancy': venue.get_current_occupancy(),
            'available_capacity': venue.get_available_capacity(),
            'occupancy_percentage': venue.get_occupancy_percentage(),
            'message': message
        })

    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})
