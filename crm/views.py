# views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Prefetch
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib import messages
from django.shortcuts import render, redirect
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.utils.decorators import method_decorator
from .cache_utils import cache_result, cache_queryset_result, CacheManager
import csv
import datetime
from .models import Customer, Course, Enrollment, Conference, ConferenceRegistration, CommunicationLog
from .serializers import (
    CustomerSerializer, CourseSerializer, EnrollmentSerializer, 
    ConferenceSerializer, CommunicationLogSerializer
)
from .communication_services import CommunicationManager
from .forms import CustomerForm
from .utils import generate_customer_csv_response, validate_uat_access
from .csv_import_handler import CSVImportHandler
from .data_quality import DataQualityService

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['customer_type', 'status']
    search_fields = ['first_name', 'last_name', 'email_primary', 'company_primary']
    ordering_fields = ['created_at', 'last_name', 'first_name']
    ordering = ['-created_at']
    
    @cache_queryset_result(timeout=300, key_prefix='customer_viewset')
    def get_queryset(self):
        """Optimized queryset with prefetch for related data and caching"""
        return Customer.objects.select_related().prefetch_related(
            Prefetch('enrollment_set', queryset=Enrollment.objects.select_related('course')),
            Prefetch('communicationlog_set', queryset=CommunicationLog.objects.select_related()),
            Prefetch('youtube_messages', queryset=self._get_youtube_messages_queryset())
        ).only(
            'id', 'first_name', 'last_name', 'email_primary', 'customer_type', 
            'status', 'phone_primary', 'country_region', 'created_at', 'source'
        )
    
    def _get_youtube_messages_queryset(self):
        """Optimized YouTube messages queryset"""
        from .models import YouTubeMessage
        return YouTubeMessage.objects.select_related().only(
            'id', 'customer_id', 'status', 'subject', 'sent_at'
        )
    
    @action(detail=True, methods=['post'])
    @throttle_classes([UserRateThrottle])
    def send_message(self, request, pk=None):
        """Send message to customer via their preferred channel"""
        customer = self.get_object()
        channel = request.data.get('channel', 'email')  # Default to email
        subject = request.data.get('subject', '')
        content = request.data.get('content', '')
        
        comm_manager = CommunicationManager()
        success, message = comm_manager.send_message(customer, channel, subject, content)
        
        return Response({
            'status': 'success' if success else 'error',
            'message': message,
            'channel': channel
        })
    
    @action(detail=False, methods=['get'])
    @cache_result(timeout=300, key_prefix='customer_search')
    def search_by_contact(self, request):
        """Search customers by email, phone, or WhatsApp with enhanced caching"""
        contact = request.query_params.get('contact', '')
        if not contact:
            return Response({'error': 'Contact parameter required'}, status=400)
        
        # Optimized query with indexes
        customers = Customer.objects.filter(
            Q(email_primary__iexact=contact) |  # Exact match first (faster)
            Q(phone_primary__icontains=contact) |
            Q(whatsapp_number__icontains=contact) |
            Q(email_primary__icontains=contact)  # Partial match last
        ).select_related().only(
            'id', 'first_name', 'last_name', 'email_primary', 
            'phone_primary', 'whatsapp_number', 'customer_type', 'status'
        )[:20]  # Limit results for performance
        
        serializer = self.get_serializer(customers, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @throttle_classes([UserRateThrottle])
    def export_csv(self, request):
        """Export customer data to CSV"""
        # Apply any filtering from the viewset
        queryset = self.filter_queryset(self.get_queryset())
        return generate_customer_csv_response(queryset)
    
    @action(detail=False, methods=['post'])
    @throttle_classes([UserRateThrottle])
    def preview_csv_import(self, request):
        """Preview CSV import with field mapping analysis"""
        if 'csv_file' not in request.FILES:
            return Response({'error': 'No CSV file provided'}, status=400)
        
        csv_file = request.FILES['csv_file']
        try:
            csv_content = csv_file.read().decode('utf-8-sig')  # Handle BOM
        except UnicodeDecodeError:
            try:
                csv_content = csv_file.read().decode('latin-1')
            except UnicodeDecodeError:
                return Response({'error': 'Unable to decode CSV file. Please ensure it is UTF-8 or Latin-1 encoded.'}, status=400)
        
        import_handler = CSVImportHandler()
        preview_result = import_handler.preview_import(csv_content, max_rows=10)
        
        return Response(preview_result)
    
    @action(detail=False, methods=['post'])
    @throttle_classes([UserRateThrottle])
    def import_csv(self, request):
        """Import customers from CSV file"""
        if 'csv_file' not in request.FILES:
            return Response({'error': 'No CSV file provided'}, status=400)
        
        csv_file = request.FILES['csv_file']
        field_mapping = request.data.get('field_mapping')  # Optional custom mapping
        
        try:
            csv_content = csv_file.read().decode('utf-8-sig')  # Handle BOM
        except UnicodeDecodeError:
            try:
                csv_content = csv_file.read().decode('latin-1')
            except UnicodeDecodeError:
                return Response({'error': 'Unable to decode CSV file. Please ensure it is UTF-8 or Latin-1 encoded.'}, status=400)
        
        # Parse field mapping if provided as JSON string
        if field_mapping and isinstance(field_mapping, str):
            import json
            try:
                field_mapping = json.loads(field_mapping)
            except json.JSONDecodeError:
                return Response({'error': 'Invalid field mapping JSON'}, status=400)
        
        # Get default source from request
        default_source = request.data.get('default_source', 'csv_import')
        
        import_handler = CSVImportHandler()
        result = import_handler.import_csv(csv_content, field_mapping, default_source=default_source)
        
        if result['success']:
            return Response({
                'success': True,
                'message': f"Successfully imported {result['stats']['success']} customers",
                'stats': result['stats'],
                'warnings': result.get('warnings', [])
            })
        else:
            return Response({
                'success': False,
                'message': result.get('error', 'Import failed'),
                'errors': result.get('errors', []),
                'warnings': result.get('warnings', []),
                'stats': result.get('stats', {}),
                'field_mapping': result.get('field_mapping'),
                'missing_fields': result.get('missing_fields'),
                'headers': result.get('headers')
            }, status=400)
    
    @action(detail=False, methods=['get', 'post'])
    @throttle_classes([UserRateThrottle])
    def data_quality(self, request):
        """Data quality analysis and fixes"""
        service = DataQualityService()
        
        if request.method == 'GET':
            # Return data quality report
            report = service.get_data_quality_report()
            return Response(report)
        
        elif request.method == 'POST':
            # Run data quality fixes
            action = request.data.get('action', 'fix_all')
            
            if action == 'fix_all':
                results = service.fix_failed_records()
                return Response({
                    'success': True,
                    'message': f'Data quality fixes completed. {results["fixed"]} customers were fixed.',
                    'results': results
                })
            
            elif action == 'report_only':
                report = service.get_data_quality_report()
                return Response({
                    'success': True,
                    'message': 'Data quality report generated',
                    'report': report
                })
            
            else:
                return Response({
                    'error': 'Invalid action. Use "fix_all" or "report_only"'
                }, status=400)

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['course_type', 'is_active']
    search_fields = ['title', 'description']
    
    @cache_queryset_result(timeout=600, key_prefix='course_viewset')
    def get_queryset(self):
        """Optimized queryset with prefetch for enrollments and caching"""
        return Course.objects.prefetch_related(
            Prefetch('enrollment_set', queryset=Enrollment.objects.select_related('customer').only(
                'id', 'customer_id', 'course_id', 'status', 'enrollment_date'
            ))
        ).only(
            'id', 'title', 'course_type', 'is_active', 'start_date', 
            'end_date', 'price', 'max_participants'
        )
    
    @method_decorator(cache_page(settings.CACHE_TTL['course_list']))
    def list(self, request, *args, **kwargs):
        """Cached course list"""
        return super().list(request, *args, **kwargs)
    
    @action(detail=True, methods=['post'])
    def enroll_customer(self, request, pk=None):
        """Enroll a customer in this course"""
        course = self.get_object()
        customer_id = request.data.get('customer_id')
        
        try:
            customer = Customer.objects.get(id=customer_id)
            enrollment, created = Enrollment.objects.get_or_create(
                customer=customer,
                course=course,
                defaults={'status': 'registered'}
            )
            
            if created:
                return Response({'status': 'Customer enrolled successfully'})
            else:
                return Response({'status': 'Customer already enrolled'}, status=400)
                
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=404)

class EnrollmentViewSet(viewsets.ModelViewSet):
    queryset = Enrollment.objects.all()
    serializer_class = EnrollmentSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['status', 'payment_status', 'customer', 'course']

class ConferenceViewSet(viewsets.ModelViewSet):
    queryset = Conference.objects.all()
    serializer_class = ConferenceSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['is_active']
    search_fields = ['name', 'description', 'venue']

class CommunicationLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = CommunicationLog.objects.all()
    serializer_class = CommunicationLogSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['customer', 'channel', 'is_outbound']
    ordering = ['-sent_at']


# Traditional Django views for admin interface
@login_required
def export_customers_csv(request):
    """Export all customer data to CSV - requires authentication"""
    return generate_customer_csv_response()


@cache_result(timeout=300, key_prefix='dashboard')
def test_dashboard(request):
    """Simple dashboard for testing with caching (no security)"""
    from .models import Course, Enrollment
    
    # Use cached stats where possible
    total_customers = cache.get('customer_stats_total')
    if total_customers is None:
        total_customers = Customer.objects.count()
        cache.set('customer_stats_total', total_customers, settings.CACHE_TTL['dashboard_stats'])
    
    active_customers = cache.get('customer_stats_active')
    if active_customers is None:
        active_customers = Customer.objects.filter(status='active').count()
        cache.set('customer_stats_active', active_customers, settings.CACHE_TTL['dashboard_stats'])
    
    context = {
        'total_customers': total_customers,
        'active_customers': active_customers,
        'recent_customers': Customer.objects.select_related().only(
            'id', 'first_name', 'last_name', 'email_primary', 'created_at'
        ).order_by('-created_at')[:5],
        'total_courses': Course.objects.filter(is_active=True).count() if hasattr(Course, 'objects') else 0,
        'total_enrollments': Enrollment.objects.count() if hasattr(Enrollment, 'objects') else 0,
    }
    return render(request, 'crm/dashboard.html', context)


def customer_dashboard(request):
    """Simple dashboard view for UAT testing (SECURED)"""
    # Validate UAT access
    is_valid, error_message = validate_uat_access(request)
    if not is_valid:
        return HttpResponseForbidden(error_message)
    
    from .models import Course, Enrollment
    context = {
        'total_customers': Customer.objects.count(),
        'active_customers': Customer.objects.filter(status='active').count(),
        'recent_customers': Customer.objects.order_by('-created_at')[:5],
        'total_courses': Course.objects.filter(is_active=True).count() if hasattr(Course, 'objects') else 0,
        'total_enrollments': Enrollment.objects.count() if hasattr(Enrollment, 'objects') else 0,
    }
    return render(request, 'crm/dashboard.html', context)


def public_customer_list(request):
    """Public customer list for UAT testing (SECURED)"""
    # Validate UAT access
    is_valid, error_message = validate_uat_access(request)
    if not is_valid:
        return HttpResponseForbidden(error_message)
    
    customers = Customer.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        customers = customers.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(email_primary__icontains=search_query) |
            Q(company_primary__icontains=search_query)
        )
    
    context = {
        'customers': customers[:50],  # Limit to 50 for UAT
        'search_query': search_query,
        'customer_types': Customer.CUSTOMER_TYPES,
        'statuses': Customer.STATUS_CHOICES,
    }
    return render(request, 'crm/customer_list.html', context)


def public_customer_create(request):
    """Public customer creation for UAT testing (SECURED)"""
    # Validate UAT access
    is_valid, error_message = validate_uat_access(request)
    if not is_valid:
        return HttpResponseForbidden(error_message)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer {customer.first_name} {customer.last_name} created successfully! Use the quick actions to continue.')
            # Redirect to customer detail view with customer ID (need to create this route)
            return redirect('crm:public_customer_list')
    else:
        form = CustomerForm()
    
    return render(request, 'crm/customer_form.html', {'form': form, 'title': 'Add New Customer'})


def test_customer_create(request):
    """Simple customer creation for testing (no security)"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer {customer.first_name} {customer.last_name} created successfully! Quick actions available below.')
            return redirect('crm:test_customer_create')
    else:
        form = CustomerForm()
    
    return render(request, 'crm/customer_form.html', {'form': form, 'title': 'Test Add Customer'})


def test_export_csv(request):
    """Test CSV export for development (no security)"""
    return generate_customer_csv_response()