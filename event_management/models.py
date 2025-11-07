"""
Event Management Models
Manages customer visits, installations, training, and maintenance events
"""

from django.db import models
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from authentication.models import CompanyUser
import uuid


class Event(models.Model):
    """Main Event/Visit model"""

    EVENT_TYPES = [
        ('installation', _('Hardware Installation & Configuration')),
        ('training', _('On-site Training')),
        ('maintenance', _('Maintenance Service')),
        ('sales_visit', _('Sales Visit')),
        ('consultation', _('Technical Consultation')),
    ]

    STATUS_CHOICES = [
        ('planned', _('Planned')),
        ('confirmed', _('Confirmed')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]

    # Basic Information
    event_number = models.CharField(
        _('Event Number'),
        max_length=50,
        unique=True,
        help_text=_('Unique event identifier (e.g., DECT-AI-20250222)')
    )
    event_type = models.CharField(
        _('Event Type'),
        max_length=20,
        choices=EVENT_TYPES
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned'
    )

    # Customer Information
    customer_company = models.CharField(_('Customer Company'), max_length=200)
    contact_person = models.CharField(_('Contact Person'), max_length=100)
    contact_position = models.CharField(_('Position'), max_length=100)
    contact_phone = models.CharField(_('Phone'), max_length=50)
    contact_wechat = models.CharField(_('WeChat ID'), max_length=100, blank=True)
    contact_email = models.EmailField(_('Email'))

    # Location Information
    delivery_address = models.TextField(_('Delivery Address'))
    installation_address = models.TextField(
        _('Installation/Maintenance Address'),
        blank=True,
        help_text=_('Leave blank if same as delivery address')
    )
    training_address = models.TextField(
        _('Training Address'),
        blank=True,
        help_text=_('Leave blank if same as delivery address')
    )

    # Schedule Information
    planned_start_date = models.DateField(_('Planned Start Date'))
    planned_end_date = models.DateField(_('Planned End Date'))
    actual_start_date = models.DateField(_('Actual Start Date'), null=True, blank=True)
    actual_end_date = models.DateField(_('Actual End Date'), null=True, blank=True)
    estimated_duration_days = models.IntegerField(_('Estimated Duration (Days)'))

    # Personnel
    sales_responsible = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        related_name='events_sales',
        null=True,
        verbose_name=_('Responsible Sales Personnel')
    )
    assigned_staff = models.ManyToManyField(
        CompanyUser,
        related_name='assigned_events',
        verbose_name=_('Assigned Staff'),
        blank=True
    )

    # Financial
    estimated_total_cost = models.DecimalField(
        _('Estimated Total Cost'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    actual_total_cost = models.DecimalField(
        _('Actual Total Cost'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    currency = models.CharField(_('Currency'), max_length=3, default='RMB')

    # Additional Information
    description = models.TextField(_('Description'), blank=True)
    notes = models.TextField(_('Internal Notes'), blank=True)

    # Metadata
    created_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        related_name='events_created',
        null=True,
        verbose_name=_('Created By')
    )
    created_at = models.DateTimeField(_('Created At'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Updated At'), auto_now=True)

    class Meta:
        ordering = ['-planned_start_date']
        verbose_name = _('Event/Visit')
        verbose_name_plural = _('Events/Visits')
        indexes = [
            models.Index(fields=['event_number']),
            models.Index(fields=['status']),
            models.Index(fields=['planned_start_date']),
        ]

    def __str__(self):
        return f"{self.event_number} - {self.customer_company}"

    def get_absolute_url(self):
        return reverse('event_management:event_detail', kwargs={'pk': self.pk})

    @property
    def is_upcoming(self):
        from django.utils import timezone
        return self.planned_start_date > timezone.now().date()

    @property
    def is_overdue(self):
        from django.utils import timezone
        return (self.status not in ['completed', 'cancelled'] and
                self.planned_end_date < timezone.now().date())

    @property
    def duration_days(self):
        if self.actual_start_date and self.actual_end_date:
            return (self.actual_end_date - self.actual_start_date).days + 1
        return self.estimated_duration_days


class EventPrerequisite(models.Model):
    """Prerequisites and checklist items for events"""

    CATEGORY_CHOICES = [
        ('hardware', _('Hardware/Equipment')),
        ('software', _('Software/Tools')),
        ('documentation', _('Documentation')),
        ('travel', _('Travel Arrangements')),
        ('customer', _('Customer Requirements')),
        ('other', _('Other')),
    ]

    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('blocked', _('Blocked')),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='prerequisites',
        verbose_name=_('Event')
    )
    category = models.CharField(_('Category'), max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField(_('Description'))
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    responsible_person = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Responsible Person')
    )
    due_date = models.DateField(_('Due Date'))
    completed_date = models.DateField(_('Completed Date'), null=True, blank=True)
    notes = models.TextField(_('Notes'), blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', 'status']
        verbose_name = _('Event Prerequisite')
        verbose_name_plural = _('Event Prerequisites')

    def __str__(self):
        return f"{self.event.event_number} - {self.get_category_display()}: {self.description[:50]}"

    @property
    def is_overdue(self):
        from django.utils import timezone
        return (self.status != 'completed' and
                self.due_date < timezone.now().date())


class EventCost(models.Model):
    """Cost tracking for events"""

    COST_TYPES = [
        ('personnel_installation', _('Personnel - Installation (¥1,500/day)')),
        ('personnel_configuration', _('Personnel - Configuration (¥4,000/day)')),
        ('personnel_training', _('Personnel - Training (¥3,000/day)')),
        ('personnel_maintenance', _('Personnel - Maintenance (¥4,000/day)')),
        ('accommodation', _('Accommodation')),
        ('transport', _('Transportation')),
        ('allowance', _('Travel Allowance')),
        ('hardware', _('Hardware/Materials')),
        ('other', _('Other Expenses')),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='costs',
        verbose_name=_('Event')
    )
    cost_type = models.CharField(_('Cost Type'), max_length=30, choices=COST_TYPES)
    description = models.CharField(_('Description'), max_length=200)

    # Personnel specific fields
    staff_member = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Staff Member')
    )
    daily_rate = models.DecimalField(
        _('Daily Rate'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text=_('Rate per day for personnel costs')
    )
    days_count = models.IntegerField(
        _('Number of Days'),
        null=True,
        blank=True
    )

    # General cost fields
    estimated_amount = models.DecimalField(
        _('Estimated Amount'),
        max_digits=10,
        decimal_places=2
    )
    actual_amount = models.DecimalField(
        _('Actual Amount'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    currency = models.CharField(_('Currency'), max_length=3, default='RMB')

    # Documentation
    receipt_attachment = models.FileField(
        _('Receipt'),
        upload_to='event_receipts/%Y/%m/',
        null=True,
        blank=True
    )
    notes = models.TextField(_('Notes'), blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['cost_type', '-created_at']
        verbose_name = _('Event Cost')
        verbose_name_plural = _('Event Costs')

    def __str__(self):
        return f"{self.event.event_number} - {self.get_cost_type_display()}: {self.estimated_amount}"

    @property
    def calculated_amount(self):
        """Auto-calculate amount for personnel costs"""
        if self.daily_rate and self.days_count:
            return self.daily_rate * self.days_count
        return self.estimated_amount

    @property
    def variance(self):
        """Calculate variance between estimated and actual"""
        if self.actual_amount:
            return self.actual_amount - self.estimated_amount
        return 0


class EventReminder(models.Model):
    """Automated reminders for events"""

    REMINDER_TYPES = [
        ('code_conduct', _('Code of Conduct')),
        ('safety', _('Safety Protocol')),
        ('customer_service', _('Customer Service Ethics')),
        ('checklist', _('Pre-Departure Checklist')),
        ('equipment', _('Equipment Checkout')),
        ('custom', _('Custom Reminder')),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='reminders',
        verbose_name=_('Event')
    )
    reminder_type = models.CharField(_('Reminder Type'), max_length=20, choices=REMINDER_TYPES)
    title = models.CharField(_('Title'), max_length=200)
    message = models.TextField(_('Message'))
    recipients = models.ManyToManyField(
        CompanyUser,
        related_name='event_reminders',
        verbose_name=_('Recipients')
    )

    send_datetime = models.DateTimeField(_('Send Date & Time'))
    sent = models.BooleanField(_('Sent'), default=False)
    sent_at = models.DateTimeField(_('Sent At'), null=True, blank=True)

    # Notification channels
    send_email = models.BooleanField(_('Send Email'), default=True)
    send_sms = models.BooleanField(_('Send SMS'), default=False)
    send_wechat = models.BooleanField(_('Send WeChat'), default=False)

    # Delivery status tracking
    email_sent = models.BooleanField(_('Email Sent'), default=False)
    sms_sent = models.BooleanField(_('SMS Sent'), default=False)
    wechat_sent = models.BooleanField(_('WeChat Sent'), default=False)

    # Error tracking
    email_error = models.TextField(_('Email Error'), blank=True)
    sms_error = models.TextField(_('SMS Error'), blank=True)
    wechat_error = models.TextField(_('WeChat Error'), blank=True)

    created_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        related_name='reminders_created',
        null=True,
        verbose_name=_('Created By')
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['send_datetime']
        verbose_name = _('Event Reminder')
        verbose_name_plural = _('Event Reminders')

    def __str__(self):
        return f"{self.event.event_number} - {self.title}"


class EventWorkLog(models.Model):
    """Daily work logs for events"""

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='work_logs',
        verbose_name=_('Event')
    )
    log_date = models.DateField(_('Log Date'))
    start_time = models.TimeField(_('Start Time'))
    end_time = models.TimeField(_('End Time'))

    work_description = models.TextField(_('Work Description'))
    staff_members = models.ManyToManyField(
        CompanyUser,
        related_name='work_logs',
        verbose_name=_('Staff Members')
    )

    # Work completion tracking
    tasks_completed = models.TextField(_('Tasks Completed'))
    issues_encountered = models.TextField(_('Issues Encountered'), blank=True)
    notes_recommendations = models.TextField(_('Notes and Recommendations'), blank=True)

    # Attachments
    photos = models.JSONField(
        _('Photos'),
        default=list,
        blank=True,
        help_text=_('List of photo file paths')
    )
    documents = models.JSONField(
        _('Documents'),
        default=list,
        blank=True,
        help_text=_('List of document file paths')
    )

    created_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        related_name='work_logs_created',
        null=True,
        verbose_name=_('Created By')
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-log_date', '-start_time']
        verbose_name = _('Event Work Log')
        verbose_name_plural = _('Event Work Logs')
        unique_together = ['event', 'log_date', 'start_time']

    def __str__(self):
        return f"{self.event.event_number} - {self.log_date}"

    @property
    def duration_hours(self):
        """Calculate work duration in hours"""
        from datetime import datetime, timedelta
        start = datetime.combine(self.log_date, self.start_time)
        end = datetime.combine(self.log_date, self.end_time)
        if end < start:
            end += timedelta(days=1)
        duration = end - start
        return duration.total_seconds() / 3600


class EventReview(models.Model):
    """Post-event review and evaluation"""

    RATING_CHOICES = [
        (1, _('1 - Poor')),
        (2, _('2 - Below Average')),
        (3, _('3 - Average')),
        (4, _('4 - Good')),
        (5, _('5 - Excellent')),
    ]

    event = models.OneToOneField(
        Event,
        on_delete=models.CASCADE,
        related_name='review',
        verbose_name=_('Event')
    )

    # Performance ratings
    time_management_rating = models.IntegerField(
        _('Time Management'),
        choices=RATING_CHOICES
    )
    technical_quality_rating = models.IntegerField(
        _('Technical Quality'),
        choices=RATING_CHOICES
    )
    customer_satisfaction_rating = models.IntegerField(
        _('Customer Satisfaction'),
        choices=RATING_CHOICES
    )
    cost_efficiency_rating = models.IntegerField(
        _('Cost Efficiency'),
        choices=RATING_CHOICES
    )

    # Feedback
    what_went_well = models.TextField(_('What Went Well'))
    areas_for_improvement = models.TextField(_('Areas for Improvement'))
    lessons_learned = models.TextField(_('Lessons Learned'))
    recommendations = models.TextField(_('Recommendations'))

    # Customer feedback
    customer_feedback = models.TextField(_('Customer Feedback'), blank=True)
    customer_signature = models.ImageField(
        _('Customer Signature'),
        upload_to='event_signatures/%Y/%m/',
        null=True,
        blank=True
    )
    customer_signed_date = models.DateField(_('Customer Signed Date'), null=True, blank=True)

    # Team feedback
    reviewed_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        related_name='reviews_conducted',
        null=True,
        verbose_name=_('Reviewed By')
    )
    review_date = models.DateField(_('Review Date'), auto_now_add=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Event Review')
        verbose_name_plural = _('Event Reviews')

    def __str__(self):
        return f"Review: {self.event.event_number}"

    @property
    def average_rating(self):
        """Calculate average rating across all categories"""
        ratings = [
            self.time_management_rating,
            self.technical_quality_rating,
            self.customer_satisfaction_rating,
            self.cost_efficiency_rating
        ]
        return sum(ratings) / len(ratings)


class EventEquipment(models.Model):
    """Equipment checkout and return tracking"""

    STATUS_CHOICES = [
        ('checked_out', _('Checked Out')),
        ('in_use', _('In Use')),
        ('returned', _('Returned')),
        ('damaged', _('Damaged')),
        ('lost', _('Lost')),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='equipment',
        verbose_name=_('Event')
    )
    equipment_name = models.CharField(_('Equipment Name'), max_length=200)
    equipment_serial = models.CharField(_('Serial Number'), max_length=100, blank=True)
    quantity = models.IntegerField(_('Quantity'), default=1)

    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='checked_out'
    )

    checked_out_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        related_name='equipment_checked_out',
        null=True,
        verbose_name=_('Checked Out By')
    )
    checked_out_date = models.DateTimeField(_('Checked Out Date'), auto_now_add=True)

    returned_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        related_name='equipment_returned',
        null=True,
        blank=True,
        verbose_name=_('Returned By')
    )
    returned_date = models.DateTimeField(_('Returned Date'), null=True, blank=True)

    condition_notes = models.TextField(_('Condition Notes'), blank=True)
    damage_report = models.TextField(_('Damage Report'), blank=True)

    class Meta:
        ordering = ['-checked_out_date']
        verbose_name = _('Event Equipment')
        verbose_name_plural = _('Event Equipment')

    def __str__(self):
        return f"{self.event.event_number} - {self.equipment_name} (x{self.quantity})"

    @property
    def is_returned(self):
        return self.status == 'returned'

    @property
    def days_out(self):
        """Calculate how many days equipment has been checked out"""
        from django.utils import timezone
        end_date = self.returned_date or timezone.now()
        delta = end_date - self.checked_out_date
        return delta.days


class EventApproval(models.Model):
    """Multi-level approval workflow for events"""

    APPROVAL_ROLES = [
        ('financial', _('Financial Supervisor')),
        ('technical', _('Technical Supervisor')),
        ('procurement', _('Procurement Personnel')),
        ('business', _('Business Supervisor')),
    ]

    STATUS_CHOICES = [
        ('pending', _('Pending Review')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]

    event = models.ForeignKey(
        Event,
        on_delete=models.CASCADE,
        related_name='approvals',
        verbose_name=_('Event')
    )
    approval_role = models.CharField(_('Approval Role'), max_length=20, choices=APPROVAL_ROLES)
    approver = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        related_name='event_approvals',
        null=True,
        blank=True,
        verbose_name=_('Approver')
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    comments = models.TextField(_('Comments'), blank=True)
    approved_date = models.DateTimeField(_('Approval Date'), null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        verbose_name = _('Event Approval')
        verbose_name_plural = _('Event Approvals')
        unique_together = ['event', 'approval_role']

    def __str__(self):
        return f"{self.event.event_number} - {self.get_approval_role_display()}: {self.status}"


class CustomerFeedback(models.Model):
    """Customer feedback collected post-event"""

    RATING_CHOICES = [
        (1, _('1 - Very Dissatisfied')),
        (2, _('2 - Dissatisfied')),
        (3, _('3 - Neutral')),
        (4, _('4 - Satisfied')),
        (5, _('5 - Very Satisfied')),
    ]

    # Unique identifier for external access
    feedback_token = models.UUIDField(
        _('Feedback Token'),
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    event = models.OneToOneField(
        Event,
        on_delete=models.CASCADE,
        related_name='customer_feedback',
        verbose_name=_('Event')
    )

    # Customer information
    customer_name = models.CharField(_('Customer Name'), max_length=100)
    customer_email = models.EmailField(_('Customer Email'))
    customer_position = models.CharField(_('Position'), max_length=100, blank=True)

    # Ratings
    service_quality_rating = models.IntegerField(
        _('Service Quality'),
        choices=RATING_CHOICES,
        help_text=_('How would you rate the overall service quality?')
    )
    staff_professionalism_rating = models.IntegerField(
        _('Staff Professionalism'),
        choices=RATING_CHOICES,
        help_text=_('How professional were our staff members?')
    )
    timeliness_rating = models.IntegerField(
        _('Timeliness'),
        choices=RATING_CHOICES,
        help_text=_('How satisfied were you with our punctuality and time management?')
    )
    technical_expertise_rating = models.IntegerField(
        _('Technical Expertise'),
        choices=RATING_CHOICES,
        help_text=_('How would you rate our technical knowledge and expertise?')
    )
    communication_rating = models.IntegerField(
        _('Communication'),
        choices=RATING_CHOICES,
        help_text=_('How clear and effective was our communication?')
    )

    # Open-ended feedback
    what_did_well = models.TextField(
        _('What did we do well?'),
        blank=True,
        help_text=_('Please share what you liked about our service')
    )
    what_can_improve = models.TextField(
        _('What can we improve?'),
        blank=True,
        help_text=_('Please share areas where we can do better')
    )
    additional_comments = models.TextField(
        _('Additional Comments'),
        blank=True,
        help_text=_('Any other feedback you would like to share')
    )

    # Net Promoter Score
    would_recommend = models.BooleanField(
        _('Would you recommend us?'),
        default=True,
        help_text=_('Would you recommend our services to others?')
    )
    likelihood_to_use_again = models.IntegerField(
        _('Likelihood to Use Again (1-10)'),
        choices=[(i, str(i)) for i in range(1, 11)],
        default=10,
        help_text=_('How likely are you to use our services again? (1=Not likely, 10=Very likely)')
    )

    # Status
    submitted = models.BooleanField(_('Submitted'), default=False)
    submitted_at = models.DateTimeField(_('Submitted At'), null=True, blank=True)
    feedback_sent_at = models.DateTimeField(_('Feedback Request Sent At'), null=True, blank=True)

    # Internal tracking
    reviewed_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        related_name='customer_feedbacks_reviewed',
        null=True,
        blank=True,
        verbose_name=_('Reviewed By')
    )
    internal_notes = models.TextField(_('Internal Notes'), blank=True)
    follow_up_required = models.BooleanField(_('Follow-up Required'), default=False)
    follow_up_completed = models.BooleanField(_('Follow-up Completed'), default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Customer Feedback')
        verbose_name_plural = _('Customer Feedback')
        ordering = ['-created_at']

    def __str__(self):
        return f"Feedback: {self.event.event_number} - {self.customer_name}"

    @property
    def average_rating(self):
        """Calculate average rating across all categories"""
        ratings = [
            self.service_quality_rating,
            self.staff_professionalism_rating,
            self.timeliness_rating,
            self.technical_expertise_rating,
            self.communication_rating,
        ]
        return sum(ratings) / len(ratings)

    @property
    def is_positive(self):
        """Determine if feedback is overall positive (avg >= 4)"""
        return self.average_rating >= 4.0

    @property
    def nps_category(self):
        """Categorize NPS score (Detractor, Passive, Promoter)"""
        score = self.likelihood_to_use_again
        if score <= 6:
            return 'detractor'
        elif score <= 8:
            return 'passive'
        else:
            return 'promoter'

    def get_feedback_url(self):
        """Get the public URL for feedback submission"""
        from django.urls import reverse
        return reverse('event_management:customer_feedback_submit', kwargs={'token': self.feedback_token})


class EquipmentDamageReport(models.Model):
    """Detailed damage reports for equipment"""

    SEVERITY_CHOICES = [
        ('minor', _('Minor - Cosmetic damage only')),
        ('moderate', _('Moderate - Affects functionality')),
        ('severe', _('Severe - Equipment unusable')),
        ('total_loss', _('Total Loss - Beyond repair')),
    ]

    DAMAGE_TYPE_CHOICES = [
        ('physical', _('Physical Damage')),
        ('water', _('Water Damage')),
        ('electrical', _('Electrical Failure')),
        ('wear_tear', _('Normal Wear and Tear')),
        ('missing', _('Missing Components')),
        ('other', _('Other')),
    ]

    equipment = models.ForeignKey(
        EventEquipment,
        on_delete=models.CASCADE,
        related_name='damage_reports',
        verbose_name=_('Equipment')
    )

    # Damage details
    damage_type = models.CharField(_('Damage Type'), max_length=20, choices=DAMAGE_TYPE_CHOICES)
    severity = models.CharField(_('Severity'), max_length=20, choices=SEVERITY_CHOICES)
    description = models.TextField(_('Damage Description'))

    # When and where
    discovered_date = models.DateTimeField(_('Discovered Date'), auto_now_add=True)
    discovered_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        related_name='damage_reports_discovered',
        null=True,
        verbose_name=_('Discovered By')
    )
    location = models.CharField(
        _('Location'),
        max_length=200,
        blank=True,
        help_text=_('Where was the damage discovered?')
    )

    # Cause analysis
    suspected_cause = models.TextField(
        _('Suspected Cause'),
        blank=True,
        help_text=_('What might have caused this damage?')
    )
    preventable = models.BooleanField(
        _('Preventable'),
        default=False,
        help_text=_('Could this damage have been prevented?')
    )
    prevention_notes = models.TextField(
        _('Prevention Notes'),
        blank=True,
        help_text=_('How could this have been prevented?')
    )

    # Financial impact
    estimated_repair_cost = models.DecimalField(
        _('Estimated Repair Cost'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    actual_repair_cost = models.DecimalField(
        _('Actual Repair Cost'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    replacement_cost = models.DecimalField(
        _('Replacement Cost'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    # Status tracking
    repair_required = models.BooleanField(_('Repair Required'), default=True)
    repair_completed = models.BooleanField(_('Repair Completed'), default=False)
    repair_completion_date = models.DateField(_('Repair Completion Date'), null=True, blank=True)

    # Responsibility
    responsible_party = models.CharField(
        _('Responsible Party'),
        max_length=200,
        blank=True,
        help_text=_('Who is responsible for the damage?')
    )
    insurance_claim_filed = models.BooleanField(_('Insurance Claim Filed'), default=False)
    insurance_claim_number = models.CharField(_('Insurance Claim Number'), max_length=100, blank=True)

    # Internal notes
    internal_notes = models.TextField(_('Internal Notes'), blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Equipment Damage Report')
        verbose_name_plural = _('Equipment Damage Reports')
        ordering = ['-discovered_date']

    def __str__(self):
        return f"{self.equipment.equipment_name} - {self.get_severity_display()}"

    @property
    def total_cost(self):
        """Calculate total cost (repair or replacement)"""
        if self.actual_repair_cost:
            return self.actual_repair_cost
        elif self.estimated_repair_cost:
            return self.estimated_repair_cost
        elif self.replacement_cost:
            return self.replacement_cost
        return 0


class DamagePhoto(models.Model):
    """Photos documenting equipment damage"""

    damage_report = models.ForeignKey(
        EquipmentDamageReport,
        on_delete=models.CASCADE,
        related_name='photos',
        verbose_name=_('Damage Report')
    )

    photo = models.ImageField(
        _('Photo'),
        upload_to='damage_photos/%Y/%m/%d/',
        help_text=_('Photo of the damage')
    )
    caption = models.CharField(
        _('Caption'),
        max_length=200,
        blank=True,
        help_text=_('Brief description of what this photo shows')
    )

    uploaded_by = models.ForeignKey(
        CompanyUser,
        on_delete=models.SET_NULL,
        related_name='damage_photos_uploaded',
        null=True,
        verbose_name=_('Uploaded By')
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _('Damage Photo')
        verbose_name_plural = _('Damage Photos')
        ordering = ['uploaded_at']

    def __str__(self):
        return f"Photo for {self.damage_report.equipment.equipment_name}"
