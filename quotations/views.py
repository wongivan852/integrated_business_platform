from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Quotation, Customer, Service, QuotationItem


@login_required
def dashboard(request):
    """Main dashboard view"""
    recent_quotations = Quotation.objects.filter(
        created_by=request.user
    ).order_by('-created_at')[:5]

    # Statistics
    total_quotations = Quotation.objects.filter(created_by=request.user).count()
    draft_quotations = Quotation.objects.filter(
        created_by=request.user,
        status='draft'
    ).count()
    sent_quotations = Quotation.objects.filter(
        created_by=request.user,
        status='sent'
    ).count()

    context = {
        'recent_quotations': recent_quotations,
        'total_quotations': total_quotations,
        'draft_quotations': draft_quotations,
        'sent_quotations': sent_quotations,
    }

    return render(request, 'quotations/dashboard.html', context)


@login_required
def quotation_list(request):
    """List all quotations"""
    quotations = Quotation.objects.filter(
        created_by=request.user
    ).order_by('-created_at')

    # Filter by status if provided
    status_filter = request.GET.get('status')
    if status_filter:
        quotations = quotations.filter(status=status_filter)

    context = {
        'quotations': quotations,
        'status_filter': status_filter,
        'status_choices': Quotation.STATUS_CHOICES,
    }

    return render(request, 'quotations/quotation_list.html', context)


@login_required
def customer_list(request):
    """List all customers"""
    customers = Customer.objects.filter(
        created_by=request.user
    ).order_by('name')

    context = {
        'customers': customers,
    }

    return render(request, 'quotations/customer_list.html', context)


@login_required
def service_list(request):
    """List all services"""
    services = Service.objects.filter(is_active=True).order_by('name')

    context = {
        'services': services,
    }

    return render(request, 'quotations/service_list.html', context)


# Placeholder views for future implementation
@login_required
def create_quotation(request):
    """Create new quotation"""
    context = {
        'page_title': 'Create New Quotation',
    }
    return render(request, 'quotations/under_construction.html', context)


@login_required
def edit_quotation(request, quotation_id):
    """Edit existing quotation"""
    context = {
        'page_title': 'Edit Quotation',
    }
    return render(request, 'quotations/under_construction.html', context)


@login_required
def create_customer(request):
    """Create new customer"""
    context = {
        'page_title': 'Add New Customer',
    }
    return render(request, 'quotations/under_construction.html', context)


@login_required
def create_service(request):
    """Create new service"""
    context = {
        'page_title': 'Add New Service',
    }
    return render(request, 'quotations/under_construction.html', context)
