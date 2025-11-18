# utils.py - Utility functions for the CRM application
from django.http import HttpResponse
from .models import Customer
import csv
import datetime


def generate_customer_csv_response(queryset=None):
    """
    Generate a CSV response for customer data.
    
    Args:
        queryset: Optional Customer queryset. If None, exports all customers.
        
    Returns:
        HttpResponse with CSV content
    """
    if queryset is None:
        queryset = Customer.objects.all()
    
    response = HttpResponse(content_type='text/csv')
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    response['Content-Disposition'] = f'attachment; filename="customers_export_{timestamp}.csv"'
    
    writer = csv.writer(response)
    
    # CSV Headers - simplified for internal customer data management
    headers = [
        'ID', 'First Name', 'Middle Name', 'Last Name', 'Preferred Name', 'Other Names',
        'Primary Email', 'Secondary Email',
        'Primary Phone', 'Primary Phone Country Code', 'Secondary Phone', 'Secondary Phone Country Code',
        'WhatsApp Number', 'WhatsApp Country Code', 'Fax', 'Fax Country Code', 'WeChat ID',
        'Primary Company', 'Primary Position', 'Secondary Company', 'Secondary Position', 'Company Website',
        'Primary Address', 'Secondary Address', 'Country/Region',
        'LinkedIn Profile', 'Facebook Profile', 'Twitter Handle', 'Instagram Handle',
        'Customer Type', 'Status', 'Preferred Learning Format', 'Preferred Communication Method',
        'Interests',
        'Created At', 'Updated At'
    ]
    writer.writerow(headers)
    
    # Export customer data - simplified for internal management
    for customer in queryset:
        row = [
            customer.id,
            customer.first_name,
            customer.middle_name or '',
            customer.last_name,
            customer.preferred_name or '',
            customer.other_names or '',
            customer.email_primary,
            customer.email_secondary or '',
            customer.phone_primary or '',
            customer.phone_primary_country_code or '',
            customer.phone_secondary or '',
            customer.phone_secondary_country_code or '',
            customer.whatsapp_number or '',
            customer.whatsapp_country_code or '',
            customer.fax or '',
            customer.fax_country_code or '',
            customer.wechat_id or '',
            customer.company_primary or '',
            customer.position_primary or '',
            customer.company_secondary or '',
            customer.position_secondary or '',
            customer.company_website or '',
            customer.address_primary or '',
            customer.address_secondary or '',
            customer.get_country_region_display() if customer.country_region else '',
            customer.linkedin_profile or '',
            customer.facebook_profile or '',
            customer.twitter_handle or '',
            customer.instagram_handle or '',
            customer.get_customer_type_display(),
            customer.get_status_display(),
            customer.preferred_learning_format or '',
            customer.get_preferred_communication_method_display(),
            customer.interests or '',
            customer.created_at.strftime('%Y-%m-%d %H:%M:%S') if customer.created_at else '',
            customer.updated_at.strftime('%Y-%m-%d %H:%M:%S') if customer.updated_at else ''
        ]
        writer.writerow(row)
    
    return response


def validate_uat_access(request):
    """
    Validate UAT access token for public views.
    
    Args:
        request: Django request object
        
    Returns:
        tuple: (is_valid, error_message)
    """
    from django.conf import settings
    
    # Check if public UAT views are enabled
    if not settings.ENABLE_PUBLIC_UAT_VIEWS:
        return False, "UAT views are disabled. Please use secure login."
    
    # Check for UAT access token
    access_token = request.GET.get('token') or request.POST.get('token')
    if access_token != settings.UAT_ACCESS_TOKEN:
        return False, "Invalid access token. Contact administrator for UAT access."
    
    return True, None


def get_customer_display_data(customer):
    """
    Get formatted display data for a customer.
    
    Args:
        customer: Customer instance
        
    Returns:
        dict: Formatted customer data
    """
    return {
        'id': str(customer.id),
        'full_name': customer.full_name,
        'display_name': customer.display_name,
        'email': customer.email_primary,
        'phone': customer.phone_primary,
        'company': customer.company_primary,
        'status': customer.get_status_display(),
        'customer_type': customer.get_customer_type_display(),
        'created_at': customer.created_at.strftime('%Y-%m-%d') if customer.created_at else '',
        'country_code': customer.get_country_code(),
    }


def sanitize_customer_data(data):
    """
    Sanitize customer data for safe display.
    
    Args:
        data: Dictionary of customer data
        
    Returns:
        dict: Sanitized data
    """
    import html
    
    sanitized = {}
    for key, value in data.items():
        if isinstance(value, str):
            # HTML escape to prevent XSS
            sanitized[key] = html.escape(value)
        else:
            sanitized[key] = value
    
    return sanitized