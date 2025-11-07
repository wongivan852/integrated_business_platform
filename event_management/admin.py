from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Event, EventPrerequisite, EventCost, EventReminder,
    EventWorkLog, EventReview, EventEquipment, EventApproval,
    CustomerFeedback, EquipmentDamageReport, DamagePhoto
)


class EventPrerequisiteInline(admin.TabularInline):
    """Inline display of prerequisites within Event admin"""
    model = EventPrerequisite
    extra = 1
    fields = ('category', 'description', 'status')


class EventCostInline(admin.TabularInline):
    """Inline display of costs within Event admin"""
    model = EventCost
    extra = 1
    fields = ('cost_type', 'description', 'estimated_amount', 'actual_amount')


class EventApprovalInline(admin.TabularInline):
    """Inline display of approvals within Event admin"""
    model = EventApproval
    extra = 0
    fields = ('approval_role', 'approver', 'status', 'comments')


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    """Admin configuration for Event model"""
    list_display = (
        'event_number', 'customer_company', 'event_type', 'status',
        'planned_start_date', 'planned_end_date', 'sales_responsible'
    )
    list_filter = ('event_type', 'status', 'planned_start_date')
    search_fields = ('event_number', 'customer_company', 'contact_person')
    filter_horizontal = ('assigned_staff',)
    inlines = [EventPrerequisiteInline, EventCostInline, EventApprovalInline]


@admin.register(EventPrerequisite)
class EventPrerequisiteAdmin(admin.ModelAdmin):
    """Admin configuration for EventPrerequisite model"""
    list_display = ('event', 'category', 'description', 'status')
    list_filter = ('category', 'status')
    search_fields = ('event__event_number', 'description')


@admin.register(EventCost)
class EventCostAdmin(admin.ModelAdmin):
    """Admin configuration for EventCost model"""
    list_display = ('event', 'cost_type', 'staff_member', 'estimated_amount', 'actual_amount')
    list_filter = ('cost_type',)
    search_fields = ('event__event_number', 'description')


@admin.register(EventReminder)
class EventReminderAdmin(admin.ModelAdmin):
    """Admin configuration for EventReminder model"""
    list_display = ('event', 'reminder_type', 'send_datetime', 'sent')
    list_filter = ('reminder_type', 'sent')
    search_fields = ('event__event_number', 'title', 'message')


@admin.register(EventWorkLog)
class EventWorkLogAdmin(admin.ModelAdmin):
    """Admin configuration for EventWorkLog model"""
    list_display = ('event', 'log_date', 'work_description')
    list_filter = ('log_date',)
    search_fields = ('event__event_number', 'work_description', 'tasks_completed')


@admin.register(EventReview)
class EventReviewAdmin(admin.ModelAdmin):
    """Admin configuration for EventReview model"""
    list_display = ('event', 'time_management_rating', 'technical_quality_rating', 'customer_satisfaction_rating')
    search_fields = ('event__event_number', 'what_went_well')


@admin.register(EventEquipment)
class EventEquipmentAdmin(admin.ModelAdmin):
    """Admin configuration for EventEquipment model"""
    list_display = ('event', 'equipment_name', 'quantity', 'status')
    list_filter = ('status',)
    search_fields = ('event__event_number', 'equipment_name')


@admin.register(EventApproval)
class EventApprovalAdmin(admin.ModelAdmin):
    """Admin configuration for EventApproval model"""
    list_display = ('event', 'approval_role', 'approver', 'status')
    list_filter = ('approval_role', 'status')
    search_fields = ('event__event_number', 'approver__username')


class DamagePhotoInline(admin.TabularInline):
    """Inline display of damage photos within EquipmentDamageReport admin"""
    model = DamagePhoto
    extra = 1
    fields = ('photo', 'caption', 'uploaded_by')
    readonly_fields = ('uploaded_at',)


@admin.register(CustomerFeedback)
class CustomerFeedbackAdmin(admin.ModelAdmin):
    """Admin configuration for CustomerFeedback model"""
    list_display = (
        'event', 'customer_name', 'submitted', 'average_rating_display',
        'nps_category', 'follow_up_required'
    )
    list_filter = (
        'submitted', 'would_recommend', 'follow_up_required',
        'service_quality_rating', 'staff_professionalism_rating'
    )
    search_fields = ('event__event_number', 'customer_name', 'customer_email')
    readonly_fields = (
        'feedback_token', 'submitted_at', 'feedback_sent_at',
        'average_rating_display', 'nps_category_display'
    )

    fieldsets = (
        ('Event Information', {
            'fields': ('event', 'feedback_token', 'feedback_sent_at')
        }),
        ('Customer Information', {
            'fields': ('customer_name', 'customer_email', 'customer_position')
        }),
        ('Ratings', {
            'fields': (
                'service_quality_rating', 'staff_professionalism_rating',
                'timeliness_rating', 'technical_expertise_rating',
                'communication_rating', 'average_rating_display'
            )
        }),
        ('Feedback', {
            'fields': (
                'what_did_well', 'what_can_improve', 'additional_comments'
            )
        }),
        ('Net Promoter Score', {
            'fields': (
                'would_recommend', 'likelihood_to_use_again', 'nps_category_display'
            )
        }),
        ('Status', {
            'fields': ('submitted', 'submitted_at')
        }),
        ('Internal Notes', {
            'fields': (
                'reviewed_by', 'internal_notes',
                'follow_up_required', 'follow_up_completed'
            )
        }),
    )

    def average_rating_display(self, obj):
        """Display average rating with color coding"""
        if not obj.pk:
            return '-'
        avg = obj.average_rating
        color = 'green' if avg >= 4 else 'orange' if avg >= 3 else 'red'
        return format_html(
            '<span style="color: {}; font-weight: bold;">{:.1f}/5.0</span>',
            color, avg
        )
    average_rating_display.short_description = 'Avg Rating'

    def nps_category_display(self, obj):
        """Display NPS category with color coding"""
        if not obj.pk:
            return '-'
        category = obj.nps_category
        colors = {'promoter': 'green', 'passive': 'orange', 'detractor': 'red'}
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            colors.get(category, 'black'), category.title()
        )
    nps_category_display.short_description = 'NPS Category'


@admin.register(EquipmentDamageReport)
class EquipmentDamageReportAdmin(admin.ModelAdmin):
    """Admin configuration for EquipmentDamageReport model"""
    list_display = (
        'equipment', 'damage_type', 'severity', 'discovered_date',
        'repair_required', 'repair_completed', 'total_cost_display'
    )
    list_filter = (
        'damage_type', 'severity', 'repair_required', 'repair_completed',
        'preventable', 'insurance_claim_filed'
    )
    search_fields = (
        'equipment__equipment_name', 'equipment__event__event_number',
        'description', 'responsible_party'
    )
    readonly_fields = ('discovered_date', 'total_cost_display')
    inlines = [DamagePhotoInline]

    fieldsets = (
        ('Equipment & Damage Details', {
            'fields': (
                'equipment', 'damage_type', 'severity', 'description',
                'discovered_date', 'discovered_by', 'location'
            )
        }),
        ('Cause Analysis', {
            'fields': (
                'suspected_cause', 'preventable', 'prevention_notes'
            )
        }),
        ('Financial Impact', {
            'fields': (
                'estimated_repair_cost', 'actual_repair_cost',
                'replacement_cost', 'total_cost_display'
            )
        }),
        ('Repair Status', {
            'fields': (
                'repair_required', 'repair_completed', 'repair_completion_date'
            )
        }),
        ('Responsibility & Insurance', {
            'fields': (
                'responsible_party', 'insurance_claim_filed', 'insurance_claim_number'
            )
        }),
        ('Internal Notes', {
            'fields': ('internal_notes',)
        }),
    )

    def total_cost_display(self, obj):
        """Display total cost with currency"""
        if not obj.pk:
            return '-'
        cost = obj.total_cost
        if cost > 0:
            return format_html(
                '<span style="font-weight: bold;">¥{:,.2f}</span>',
                cost
            )
        return '¥0.00'
    total_cost_display.short_description = 'Total Cost'


@admin.register(DamagePhoto)
class DamagePhotoAdmin(admin.ModelAdmin):
    """Admin configuration for DamagePhoto model"""
    list_display = ('damage_report', 'caption', 'uploaded_by', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('damage_report__equipment__equipment_name', 'caption')
    readonly_fields = ('uploaded_at',)
