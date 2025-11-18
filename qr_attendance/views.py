"""
QR Code Attendance System Views
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .models import Participant, QRAttendanceRecord, VenueSettings


@login_required
def dashboard(request):
    """QR Attendance Dashboard"""
    venue = VenueSettings.get_settings()

    context = {
        'current_occupancy': venue.get_current_occupancy(),
        'max_capacity': venue.max_capacity,
        'available_capacity': venue.get_available_capacity(),
        'occupancy_percentage': venue.get_occupancy_percentage(),
        'is_at_capacity': venue.is_at_capacity(),
        'is_at_warning': venue.is_at_warning_level(),
    }
    return render(request, 'qr_attendance/dashboard.html', context)


@login_required
def scanner(request):
    """QR Code Scanner Interface"""
    venue = VenueSettings.get_settings()

    context = {
        'venue': venue,
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
