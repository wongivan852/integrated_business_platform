# admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse, path
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect
from django.contrib import messages
from django.template.response import TemplateResponse
from django.utils import timezone
from django.db import models
from django.db.models import Q, Count
from .models import (
    Customer, Course, Enrollment, Conference, ConferenceRegistration, 
    CommunicationLog, CustomerCommunicationPreference, YouTubeMessage
    # EmailTemplate, EmailCampaign, EmailLog, EmailSubscription  # Temporarily commented out
)
from .communication_services import CommunicationManager
from .csv_import_handler import CSVImportHandler

class CustomerCommunicationPreferenceInline(admin.TabularInline):
    model = CustomerCommunicationPreference
    extra = 1
    fields = ['communication_type', 'priority', 'is_active', 'notes']
    ordering = ['priority', 'communication_type']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = [
        'full_name', 'email_primary', 'customer_type', 'status', 
        'source', 'country_region', 'marketing_consent', 'created_at'
    ]
    list_filter = [
        'customer_type', 'status', 'source', 'country_region',
        'marketing_consent', 'created_at'
    ]
    search_fields = [
        'first_name', 'last_name', 'email_primary', 'email_secondary',
        'company_primary', 'company_secondary', 'phone_primary', 'phone_secondary'
    ]
    readonly_fields = ['id', 'created_at', 'updated_at']
    inlines = [CustomerCommunicationPreferenceInline]
    
    fieldsets = (
        ('Personal Information', {
            'fields': ('first_name', 'last_name', 'country_region')
        }),
        ('Email Addresses', {
            'fields': ('email_primary', 'email_secondary')
        }),
        ('Phone Numbers', {
            'fields': ('phone_primary', 'phone_secondary', 'fax')
        }),
        ('Messaging Apps', {
            'fields': ('whatsapp_number', 'wechat_id')
        }),
        ('Social Media', {
            'fields': ('linkedin_profile', 'facebook_profile', 'twitter_handle', 'instagram_handle', 'youtube_handle', 'youtube_channel_url'),
            'classes': ('collapse',)
        }),
        ('Professional Information', {
            'fields': (
                'customer_type', 'status',
                'company_primary', 'position_primary',
                'company_secondary', 'position_secondary',
                'company_website'
            )
        }),
        ('Addresses', {
            'fields': ('address_primary', 'address_secondary'),
            'classes': ('collapse',)
        }),
        ('Learning Preferences', {
            'fields': ('preferred_learning_format', 'interests', 'marketing_consent')
        }),
        ('Data Source Tracking', {
            'fields': ('source', 'referral_source'),
            'description': 'Track how customers found us for marketing analysis'
        }),
        ('System Information', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Full Name'

    actions = ['send_welcome_email', 'export_to_csv']
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('import-csv/', self.admin_site.admin_view(self.import_csv_view), name='crm_customer_import_csv'),
            path('diagnose-csv/', self.admin_site.admin_view(self.diagnose_csv_view), name='crm_customer_diagnose_csv'),
        ]
        return custom_urls + urls
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['import_csv_url'] = reverse('admin:crm_customer_import_csv')
        extra_context['diagnose_csv_url'] = reverse('admin:crm_customer_diagnose_csv')
        return super().changelist_view(request, extra_context)
    
    def import_csv_view(self, request):
        """Admin view for CSV import"""
        if request.method == 'POST':
            if 'preview' in request.POST:
                return self._handle_csv_preview(request)
            elif 'import' in request.POST:
                return self._handle_csv_import(request)
        
        context = {
            'title': 'Import Customers from CSV',
            'field_mappings': CSVImportHandler.FIELD_MAPPINGS,
            'mandatory_fields': CSVImportHandler.MANDATORY_FIELDS,
            'customer_types': Customer.CUSTOMER_TYPES,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        
        return TemplateResponse(request, 'admin/crm/customer/import_csv.html', context)
    
    def _handle_csv_preview(self, request):
        """Handle CSV preview request"""
        if 'csv_file' not in request.FILES:
            messages.error(request, 'Please select a CSV file.')
            return redirect('admin:crm_customer_import_csv')
        
        csv_file = request.FILES['csv_file']
        try:
            csv_content = csv_file.read().decode('utf-8-sig')
        except UnicodeDecodeError:
            try:
                csv_content = csv_file.read().decode('latin-1')
            except UnicodeDecodeError:
                messages.error(request, 'Unable to decode CSV file. Please ensure it is UTF-8 or Latin-1 encoded.')
                return redirect('admin:crm_customer_import_csv')
        
        import_handler = CSVImportHandler()
        preview_result = import_handler.preview_import(csv_content, max_rows=10)
        
        if 'error' in preview_result:
            messages.error(request, f"Preview error: {preview_result['error']}")
            return redirect('admin:crm_customer_import_csv')
        
        # Store CSV content in session for import
        request.session['csv_content'] = csv_content
        request.session['field_mapping'] = preview_result.get('field_mapping', {})
        request.session['default_source'] = request.POST.get('default_source', 'csv_import')
        
        context = {
            'title': 'CSV Import Preview',
            'preview_result': preview_result,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        
        return TemplateResponse(request, 'admin/crm/customer/import_csv_preview.html', context)
    
    def _handle_csv_import(self, request):
        """Handle actual CSV import"""
        csv_content = request.session.get('csv_content')
        field_mapping = request.session.get('field_mapping')
        default_source = request.session.get('default_source', 'csv_import')
        
        if not csv_content:
            messages.error(request, 'No CSV data found. Please upload and preview first.')
            return redirect('admin:crm_customer_import_csv')
        
        import_handler = CSVImportHandler()
        result = import_handler.import_csv(csv_content, field_mapping, default_source=default_source)
        
        if result['success']:
            messages.success(
                request, 
                f"Successfully imported {result['stats']['success']} customers. "
                f"Failed: {result['stats']['failed']}"
            )
            
            if result.get('warnings'):
                for warning in result['warnings']:
                    messages.warning(request, warning)
        else:
            messages.error(request, f"Import failed: {result.get('error', 'Unknown error')}")
            
            if result.get('errors'):
                for error in result['errors'][:5]:  # Show first 5 errors
                    messages.error(request, error)
        
        # Clear session data
        request.session.pop('csv_content', None)
        request.session.pop('field_mapping', None)
        request.session.pop('default_source', None)
        
        return redirect('admin:crm_customer_changelist')
    
    def diagnose_csv_view(self, request):
        """Diagnostic view for CSV files"""
        if request.method == 'POST' and 'csv_file' in request.FILES:
            csv_file = request.FILES['csv_file']
            try:
                csv_content = csv_file.read().decode('utf-8-sig')
            except UnicodeDecodeError:
                try:
                    csv_content = csv_file.read().decode('latin-1')
                except UnicodeDecodeError:
                    messages.error(request, 'Unable to decode CSV file. Please ensure it is UTF-8 or Latin-1 encoded.')
                    return redirect('admin:crm_customer_diagnose_csv')
            
            # Simple diagnostic without chardet dependency
            result = self._simple_csv_diagnostic(csv_content, csv_file.name)
            
            context = {
                'title': 'CSV File Diagnostic',
                'diagnostic_result': result,
                'file_name': csv_file.name,
                'opts': self.model._meta,
                'has_view_permission': self.has_view_permission(request),
            }
            
            return TemplateResponse(request, 'admin/crm/customer/diagnose_csv.html', context)
        
        context = {
            'title': 'CSV File Diagnostic',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        
        return TemplateResponse(request, 'admin/crm/customer/diagnose_csv.html', context)
    
    def _simple_csv_diagnostic(self, csv_content: str, filename: str) -> dict:
        """Simple CSV diagnostic without external dependencies"""
        import csv
        import io
        
        issues = []
        warnings = []
        info = []
        
        try:
            # Basic info
            info.append(f"File name: {filename}")
            info.append(f"Content length: {len(csv_content)} characters")
            info.append(f"Number of lines: {csv_content.count(chr(10)) + 1}")
            
            # Check for BOM
            if csv_content.startswith('\ufeff'):
                info.append("UTF-8 BOM detected")
                csv_content = csv_content[1:]  # Remove BOM
            
            # Detect delimiter
            delimiters = [',', ';', '\t', '|']
            delimiter_scores = {}
            
            for delimiter in delimiters:
                try:
                    sample = csv_content[:1000]
                    reader = csv.reader(io.StringIO(sample), delimiter=delimiter)
                    first_row = next(reader, [])
                    second_row = next(reader, [])
                    
                    if len(first_row) > 1 and len(second_row) > 1:
                        delimiter_scores[delimiter] = {
                            'name': {',': 'Comma', ';': 'Semicolon', '\t': 'Tab', '|': 'Pipe'}[delimiter],
                            'fields_row1': len(first_row),
                            'fields_row2': len(second_row),
                            'consistent': len(first_row) == len(second_row),
                            'count': sample.count(delimiter)
                        }
                except:
                    pass
            
            # Choose best delimiter
            if delimiter_scores:
                best_delimiter = max(delimiter_scores.keys(), 
                                   key=lambda d: (delimiter_scores[d]['consistent'], 
                                                delimiter_scores[d]['fields_row1']))
            else:
                best_delimiter = ','
                warnings.append("Could not detect delimiter clearly, using comma")
            
            # Analyze structure
            try:
                reader = csv.DictReader(io.StringIO(csv_content), delimiter=best_delimiter)
                headers = reader.fieldnames
                
                if not headers:
                    issues.append("No headers found in CSV file")
                    headers = []
                else:
                    info.append(f"Headers found: {len(headers)}")
                    
                    # Check for None headers
                    if None in headers:
                        issues.append("Some headers are None - possible delimiter issue")
                    
                    # Sample rows
                    sample_rows = []
                    for i, row in enumerate(reader):
                        if i >= 3:
                            break
                        sample_rows.append(dict(row))
                
                # Field mapping analysis
                field_mapping = {}
                unmapped_headers = []
                
                if headers:
                    handler = CSVImportHandler()
                    field_mapping, unmapped_headers = handler.analyze_headers(headers)
                    missing_mandatory = handler.validate_mandatory_fields(field_mapping)
                    
                    mapping_confidence = len(field_mapping) / len(headers) if headers else 0
                    info.append(f"Field mapping confidence: {mapping_confidence:.1%}")
                else:
                    missing_mandatory = ['first_name', 'last_name', 'email_primary']
                    sample_rows = []
                
                return {
                    'success': len(issues) == 0,
                    'issues': issues,
                    'warnings': warnings,
                    'info': info,
                    'delimiter_analysis': {
                        'available_delimiters': delimiter_scores,
                        'recommended_delimiter': best_delimiter
                    },
                    'structure_analysis': {
                        'headers': headers,
                        'header_count': len(headers) if headers else 0,
                        'sample_rows': sample_rows
                    },
                    'mapping_analysis': {
                        'field_mappings': field_mapping,
                        'unmapped_headers': unmapped_headers,
                        'missing_mandatory': missing_mandatory,
                        'mapping_confidence': mapping_confidence if 'mapping_confidence' in locals() else 0
                    },
                    'content_sample': csv_content[:1000] + '...' if len(csv_content) > 1000 else csv_content
                }
                
            except Exception as e:
                issues.append(f"Structure analysis failed: {str(e)}")
                return {
                    'success': False,
                    'issues': issues,
                    'warnings': warnings,
                    'info': info,
                    'content_sample': csv_content[:1000] + '...' if len(csv_content) > 1000 else csv_content
                }
                
        except Exception as e:
            return {
                'success': False,
                'issues': [f"Diagnostic failed: {str(e)}"],
                'warnings': [],
                'info': [],
                'content_sample': csv_content[:500] + '...' if len(csv_content) > 500 else csv_content
            }
    
    def send_welcome_email(self, request, queryset):
        comm_manager = CommunicationManager()
        success_count = 0
        
        for customer in queryset:
            if customer.email_primary and customer.marketing_consent:
                success, message = comm_manager.send_welcome_message(customer)
                if success:
                    success_count += 1
        
        self.message_user(request, f'Welcome emails sent to {success_count} customers.')
    send_welcome_email.short_description = "Send welcome email to selected customers"

@admin.register(CustomerCommunicationPreference)
class CustomerCommunicationPreferenceAdmin(admin.ModelAdmin):
    list_display = ['customer', 'communication_type', 'priority', 'is_active', 'created_at']
    list_filter = ['communication_type', 'priority', 'is_active']
    search_fields = ['customer__first_name', 'customer__last_name', 'customer__email_primary']
    readonly_fields = ['id', 'created_at', 'updated_at']

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'course_type', 'start_date', 'duration_hours', 'price', 'max_participants', 'is_active']
    list_filter = ['course_type', 'is_active', 'start_date']
    search_fields = ['title', 'description']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'start_date'

@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ['customer', 'course', 'status', 'payment_status', 'enrollment_date']
    list_filter = ['status', 'payment_status', 'enrollment_date']
    search_fields = ['customer__first_name', 'customer__last_name', 'course__title']
    readonly_fields = ['id']
    date_hierarchy = 'enrollment_date'

@admin.register(Conference)
class ConferenceAdmin(admin.ModelAdmin):
    list_display = ['name', 'venue', 'start_date', 'end_date', 'registration_fee', 'max_attendees', 'is_active']
    list_filter = ['is_active', 'start_date']
    search_fields = ['name', 'description', 'venue']
    readonly_fields = ['id', 'created_at']
    date_hierarchy = 'start_date'

@admin.register(ConferenceRegistration)
class ConferenceRegistrationAdmin(admin.ModelAdmin):
    list_display = ['customer', 'conference', 'registration_date']
    list_filter = ['registration_date']
    search_fields = ['customer__first_name', 'customer__last_name', 'conference__name']
    readonly_fields = ['id']
    date_hierarchy = 'registration_date'

@admin.register(CommunicationLog)
class CommunicationLogAdmin(admin.ModelAdmin):
    list_display = ['customer', 'channel', 'subject', 'sent_at', 'is_outbound']
    list_filter = ['channel', 'is_outbound', 'sent_at']
    search_fields = ['customer__first_name', 'customer__last_name', 'subject', 'content']
    readonly_fields = ['id', 'sent_at']
    date_hierarchy = 'sent_at'
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation of communication logs

# @admin.register(EmailTemplate)  # Temporarily commented out
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'template_type', 'status', 'usage_count', 'last_used', 'updated_at']
    list_filter = ['template_type', 'status', 'created_at']
    search_fields = ['name', 'subject', 'content_text']
    readonly_fields = ['id', 'usage_count', 'last_used', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Template Info', {
            'fields': ('name', 'template_type', 'status', 'created_by')
        }),
        ('Email Content', {
            'fields': ('subject', 'content_text', 'content_html')
        }),
        ('Template Variables', {
            'fields': ('available_variables',),
            'description': 'Available variables: {{first_name}}, {{last_name}}, {{email_primary}}, {{company_primary}}, etc.'
        }),
        ('Usage Statistics', {
            'fields': ('usage_count', 'last_used'),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['activate_templates', 'archive_templates', 'duplicate_template']
    
    def activate_templates(self, request, queryset):
        count = queryset.update(status='active')
        self.message_user(request, f'{count} templates activated.')
    activate_templates.short_description = "Activate selected templates"
    
    def archive_templates(self, request, queryset):
        count = queryset.update(status='archived')
        self.message_user(request, f'{count} templates archived.')
    archive_templates.short_description = "Archive selected templates"
    
    def duplicate_template(self, request, queryset):
        count = 0
        for template in queryset:
            template.pk = None
            template.name = f"{template.name} (Copy)"
            template.status = 'draft'
            template.usage_count = 0
            template.last_used = None
            template.save()
            count += 1
        self.message_user(request, f'{count} templates duplicated.')
    duplicate_template.short_description = "Duplicate selected templates"

# @admin.register(EmailCampaign)  # Temporarily commented out
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'status', 'target_audience', 'total_recipients', 
        'emails_sent', 'open_rate', 'click_rate', 'created_at'
    ]
    list_filter = ['status', 'target_audience', 'created_at']
    search_fields = ['name', 'description', 'subject']
    readonly_fields = [
        'id', 'total_recipients', 'emails_sent', 'emails_delivered', 
        'emails_opened', 'emails_clicked', 'emails_bounced', 'emails_failed',
        'sent_at', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Campaign Info', {
            'fields': ('name', 'description', 'status', 'created_by')
        }),
        ('Content', {
            'fields': ('template', 'subject', 'content_text', 'content_html')
        }),
        ('Targeting', {
            'fields': ('target_audience', 'custom_filter')
        }),
        ('Scheduling', {
            'fields': ('scheduled_at', 'sent_at')
        }),
        ('Metrics', {
            'fields': (
                'total_recipients', 'emails_sent', 'emails_delivered',
                'emails_opened', 'emails_clicked', 'emails_bounced', 'emails_failed'
            ),
            'classes': ('collapse',)
        }),
        ('System Info', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['send_campaigns', 'duplicate_campaigns']
    
    def send_campaigns(self, request, queryset):
        from .email_service import EnhancedEmailService
        
        email_service = EnhancedEmailService()
        sent_count = 0
        
        for campaign in queryset.filter(status__in=['draft', 'scheduled']):
            try:
                results = email_service.send_campaign(campaign)
                sent_count += 1
                self.message_user(
                    request, 
                    f'Campaign "{campaign.name}": {results["emails_sent"]} sent, {results["emails_failed"]} failed'
                )
            except Exception as e:
                self.message_user(
                    request, 
                    f'Campaign "{campaign.name}" failed: {str(e)}',
                    level=messages.ERROR
                )
        
        if sent_count > 0:
            self.message_user(request, f'{sent_count} campaigns processed.')
    send_campaigns.short_description = "Send selected campaigns"
    
    def duplicate_campaigns(self, request, queryset):
        count = 0
        for campaign in queryset:
            campaign.pk = None
            campaign.name = f"{campaign.name} (Copy)"
            campaign.status = 'draft'
            campaign.total_recipients = 0
            campaign.emails_sent = 0
            campaign.emails_delivered = 0
            campaign.emails_opened = 0
            campaign.emails_clicked = 0
            campaign.emails_bounced = 0
            campaign.emails_failed = 0
            campaign.scheduled_at = None
            campaign.sent_at = None
            campaign.save()
            count += 1
        self.message_user(request, f'{count} campaigns duplicated.')
    duplicate_campaigns.short_description = "Duplicate selected campaigns"

# @admin.register(EmailLog)  # Temporarily commented out
class EmailLogAdmin(admin.ModelAdmin):
    list_display = [
        'recipient_email', 'customer', 'campaign', 'status', 
        'queued_at', 'sent_at', 'opened_at'
    ]
    list_filter = ['status', 'queued_at', 'sent_at']
    search_fields = ['recipient_email', 'subject', 'customer__first_name', 'customer__last_name']
    readonly_fields = [
        'id', 'queued_at', 'sent_at', 'delivered_at', 'opened_at', 
        'clicked_at', 'bounced_at', 'failed_at'
    ]
    
    fieldsets = (
        ('Email Info', {
            'fields': ('customer', 'campaign', 'template', 'recipient_email', 'subject')
        }),
        ('Status', {
            'fields': ('status', 'external_message_id', 'error_message')
        }),
        ('Content', {
            'fields': ('content_text', 'content_html'),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('retry_count', 'max_retries', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': (
                'queued_at', 'sent_at', 'delivered_at', 'opened_at',
                'clicked_at', 'bounced_at', 'failed_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def has_add_permission(self, request):
        return False  # Prevent manual creation of email logs

# @admin.register(EmailSubscription)  # Temporarily commented out
class EmailSubscriptionAdmin(admin.ModelAdmin):
    list_display = [
        'customer', 'subscription_type', 'is_subscribed', 
        'subscribed_at', 'unsubscribed_at'
    ]
    list_filter = ['subscription_type', 'is_subscribed', 'subscribed_at']
    search_fields = ['customer__first_name', 'customer__last_name', 'customer__email_primary']
    readonly_fields = ['id', 'unsubscribe_token', 'subscribed_at', 'unsubscribed_at']
    
    fieldsets = (
        ('Subscription Info', {
            'fields': ('customer', 'subscription_type', 'is_subscribed')
        }),
        ('Unsubscribe Details', {
            'fields': ('unsubscribe_reason', 'unsubscribe_token'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('subscribed_at', 'unsubscribed_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['resubscribe_customers', 'unsubscribe_customers']
    
    def resubscribe_customers(self, request, queryset):
        count = 0
        for subscription in queryset:
            if not subscription.is_subscribed:
                subscription.is_subscribed = True
                subscription.unsubscribed_at = None
                subscription.unsubscribe_reason = ''
                subscription.save()
                count += 1
        self.message_user(request, f'{count} customers resubscribed.')
    resubscribe_customers.short_description = "Resubscribe selected customers"
    
    def unsubscribe_customers(self, request, queryset):
        count = 0
        for subscription in queryset:
            if subscription.is_subscribed:
                subscription.unsubscribe('Admin action')
                count += 1
        self.message_user(request, f'{count} customers unsubscribed.')
    unsubscribe_customers.short_description = "Unsubscribe selected customers"

@admin.register(YouTubeMessage)
class YouTubeMessageAdmin(admin.ModelAdmin):
    list_display = [
        'target_youtube_handle', 'customer', 'subject', 'message_type', 
        'status', 'priority_display', 'sent_at', 'response_received'
    ]
    list_filter = [
        'message_type', 'status', 'priority', 'response_received', 
        'created_at', 'sent_at'
    ]
    search_fields = [
        'target_youtube_handle', 'subject', 'content', 
        'customer__first_name', 'customer__last_name'
    ]
    readonly_fields = [
        'id', 'created_at', 'updated_at', 'sent_at', 'response_received_at',
        'opened_at', 'external_message_id'
    ]
    
    fieldsets = (
        ('Message Details', {
            'fields': ('customer', 'message_type', 'subject', 'content')
        }),
        ('Target Information', {
            'fields': ('target_youtube_handle', 'target_video_url')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'sent_by')
        }),
        ('Response Tracking', {
            'fields': ('response_received', 'response_content', 'response_received_at'),
            'classes': ('collapse',)
        }),
        ('Engagement Metrics', {
            'fields': ('message_opened', 'opened_at', 'click_count'),
            'classes': ('collapse',)
        }),
        ('Error Handling', {
            'fields': ('error_message', 'retry_count', 'max_retries'),
            'classes': ('collapse',)
        }),
        ('System Information', {
            'fields': ('external_message_id', 'platform_data'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('id', 'created_at', 'updated_at', 'sent_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['send_messages', 'retry_failed_messages', 'mark_as_read']
    
    def priority_display(self, obj):
        priority_map = {1: '🔴 High', 2: '🟡 Medium', 3: '🟢 Low'}
        return priority_map.get(obj.priority, f'{obj.priority}')
    priority_display.short_description = 'Priority'
    priority_display.admin_order_field = 'priority'
    
    def send_messages(self, request, queryset):
        from .youtube_service import youtube_service
        
        sent_count = 0
        failed_count = 0
        
        for message in queryset.filter(status__in=['draft', 'pending']):
            try:
                success, result_msg = youtube_service._send_message(message)
                if success:
                    message.mark_as_sent(
                        external_id=f"yt_{message.id}",
                        sent_by=request.user.get_full_name() or request.user.username
                    )
                    sent_count += 1
                else:
                    message.mark_as_failed(result_msg)
                    failed_count += 1
            except Exception as e:
                message.mark_as_failed(str(e))
                failed_count += 1
        
        if sent_count > 0:
            self.message_user(request, f'✅ {sent_count} messages sent successfully.')
        if failed_count > 0:
            self.message_user(
                request, 
                f'❌ {failed_count} messages failed to send.',
                level=messages.WARNING
            )
    send_messages.short_description = "Send selected messages"
    
    def retry_failed_messages(self, request, queryset):
        from .youtube_service import youtube_service
        
        retried_count = 0
        success_count = 0
        
        for message in queryset.filter(status='failed'):
            if message.retry_count < message.max_retries:
                try:
                    success, result_msg = youtube_service._send_message(message)
                    if success:
                        message.mark_as_sent(
                            external_id=f"yt_{message.id}",
                            sent_by=request.user.get_full_name() or request.user.username
                        )
                        success_count += 1
                    else:
                        message.mark_as_failed(result_msg)
                    retried_count += 1
                except Exception as e:
                    message.mark_as_failed(str(e))
                    retried_count += 1
        
        if retried_count > 0:
            self.message_user(
                request, 
                f'🔄 Retried {retried_count} messages. {success_count} succeeded.'
            )
        else:
            self.message_user(
                request, 
                'No messages available for retry (max retries reached).',
                level=messages.INFO
            )
    retry_failed_messages.short_description = "Retry failed messages"
    
    def mark_as_read(self, request, queryset):
        count = 0
        for message in queryset.filter(status__in=['sent', 'delivered']):
            if not message.message_opened:
                message.message_opened = True
                message.opened_at = timezone.now()
                message.save()
                count += 1
        
        self.message_user(request, f'👁️ Marked {count} messages as read.')
    mark_as_read.short_description = "Mark selected messages as read"
    
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('stats/', self.admin_site.admin_view(self.youtube_messaging_stats), 
                 name='crm_youtubemessage_stats'),
            path('send-bulk/', self.admin_site.admin_view(self.send_bulk_message), 
                 name='crm_youtubemessage_send_bulk'),
        ]
        return custom_urls + urls
    
    def youtube_messaging_stats(self, request):
        from .youtube_service import youtube_service
        
        stats = youtube_service.get_message_statistics()
        
        # Get top performers
        top_handles = YouTubeMessage.objects.values('target_youtube_handle').annotate(
            message_count=models.Count('id'),
            success_count=models.Count('id', filter=models.Q(status='sent'))
        ).order_by('-message_count')[:10]
        
        context = {
            'title': 'YouTube Messaging Statistics',
            'stats': stats,
            'top_handles': top_handles,
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        
        return TemplateResponse(request, 'admin/crm/youtubemessage/stats.html', context)
    
    def send_bulk_message(self, request):
        if request.method == 'POST':
            from .youtube_service import youtube_service
            
            handles = request.POST.get('handles', '').strip()
            subject = request.POST.get('subject', '').strip()
            content = request.POST.get('content', '').strip()
            message_type = request.POST.get('message_type', 'direct_message')
            priority = int(request.POST.get('priority', 3))
            
            if not all([handles, subject, content]):
                messages.error(request, 'All fields are required.')
                return redirect('admin:crm_youtubemessage_send_bulk')
            
            handle_list = [h.strip() for h in handles.split('\n') if h.strip()]
            sent_count = 0
            failed_count = 0
            
            for handle in handle_list:
                try:
                    success, msg, youtube_message = youtube_service.send_message_to_handle(
                        youtube_handle=handle,
                        subject=subject,
                        content=content,
                        message_type=message_type,
                        priority=priority
                    )
                    if success:
                        sent_count += 1
                    else:
                        failed_count += 1
                except Exception as e:
                    failed_count += 1
            
            messages.success(
                request, 
                f'Bulk message sent: {sent_count} succeeded, {failed_count} failed.'
            )
            return redirect('admin:crm_youtubemessage_changelist')
        
        context = {
            'title': 'Send Bulk YouTube Message',
            'opts': self.model._meta,
            'has_view_permission': self.has_view_permission(request),
        }
        
        return TemplateResponse(request, 'admin/crm/youtubemessage/send_bulk.html', context)
