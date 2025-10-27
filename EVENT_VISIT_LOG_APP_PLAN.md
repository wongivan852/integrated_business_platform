# Event / Visit Log and Reminder App - Development Plan

**Project:** Integrated Business Platform Enhancement
**App Name:** Event/Visit Log and Reminder System
**Date:** October 27, 2025
**Version:** 1.0

---

## 1. EXECUTIVE SUMMARY

### Purpose
Develop a comprehensive Event/Visit Log and Reminder application to track customer visits, on-site installations, training sessions, and maintenance activities. This app will replace the dependency on the quotation system and provide a standalone workflow for managing customer engagements.

### Key Objectives
1. **Pre-Visit Planning** - Log event details, participants, and requirements before occurrence
2. **Prerequisites Management** - Track dependencies, equipment, and preparation tasks
3. **Cost Tracking** - Monitor execution costs (travel, accommodation, materials)
4. **Staff Reminders** - Automated notifications for code of conduct and ethics
5. **Performance Review** - Post-visit evaluation and feedback collection
6. **Inventory Management** - Stock-taking of equipment and materials

---

## 2. REQUIREMENTS ANALYSIS

### Based on Attached Documents

#### From Cost & Quotation Template:
- Customer information (Company, Contact, Address)
- Service dates and schedules
- Hardware configuration tracking
- Personnel assignment and daily rates
- Installation/Configuration services
- Training sessions
- Maintenance services
- Travel expenses (accommodation, transport, allowances)
- Approval workflow (Financial, Technical, Procurement, Business supervisors)

#### From Guangzhou Work Order (武汉诺澜科技):
- Service reference number (DECT-AI-20250222)
- Work completion checklist
- Training topics covered
- Post-installation testing
- Notes and recommendations
- Customer and engineer signatures

### Functional Requirements

#### 1. Pre-Event Logging
- Event type selection (Installation, Training, Maintenance, Sales Visit)
- Customer information
- Location details (delivery, installation, training addresses)
- Scheduled dates and times
- Assigned personnel
- Expected deliverables

#### 2. Prerequisites & Dependencies
- Checklist of required items
- Hardware/equipment preparation
- Software/tools required
- Documentation needed
- Travel arrangements
- Customer confirmation status

#### 3. Cost Tracking
- Personnel costs (daily rates by role)
- Travel expenses
  - Accommodation
  - Local transportation
  - Travel allowances
  - Other expenses
- Hardware/material costs
- Budget vs. actual tracking

#### 4. Automated Reminders
- Email/SMS notifications to staff
- Code of conduct guidelines
- Safety protocols
- Customer service ethics
- Pre-departure checklist
- Day-before reminders

#### 5. Post-Event Review
- Work completion checklist
- Time tracking (actual vs. estimated)
- Customer feedback form
- Issues encountered
- Recommendations for improvement
- Photo/document attachments

#### 6. Inventory Management
- Equipment check-out log
- Material usage tracking
- Equipment return verification
- Damage/loss reporting
- Stock level updates

---

## 3. DATABASE SCHEMA DESIGN

### Core Models

#### 3.1 Event Model
```python
class Event(models.Model):
    EVENT_TYPES = [
        ('installation', 'Hardware Installation & Configuration'),
        ('training', 'On-site Training'),
        ('maintenance', 'Maintenance Service'),
        ('sales_visit', 'Sales Visit'),
        ('consultation', 'Technical Consultation'),
    ]

    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    # Basic Information
    event_number = models.CharField(max_length=50, unique=True)  # e.g., DECT-AI-20250222
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planned')

    # Customer Information
    customer_company = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=100)
    contact_position = models.CharField(max_length=100)
    contact_phone = models.CharField(max_length=50)
    contact_wechat = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField()

    # Location Information
    delivery_address = models.TextField()
    installation_address = models.TextField(blank=True)
    training_address = models.TextField(blank=True)

    # Schedule Information
    planned_start_date = models.DateField()
    planned_end_date = models.DateField()
    actual_start_date = models.DateField(null=True, blank=True)
    actual_end_date = models.DateField(null=True, blank=True)
    estimated_duration_days = models.IntegerField()

    # Personnel
    sales_responsible = models.ForeignKey(CompanyUser, on_delete=models.SET_NULL,
                                         related_name='events_sales', null=True)
    assigned_staff = models.ManyToManyField(CompanyUser, related_name='assigned_events')

    # Links to other systems
    related_quotation = models.ForeignKey('quotations.Quotation', null=True,
                                         blank=True, on_delete=models.SET_NULL)

    # Financial
    estimated_total_cost = models.DecimalField(max_digits=10, decimal_places=2)
    actual_total_cost = models.DecimalField(max_digits=10, decimal_places=2,
                                            null=True, blank=True)

    # Metadata
    created_by = models.ForeignKey(CompanyUser, on_delete=models.SET_NULL,
                                  related_name='events_created', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

#### 3.2 EventPrerequisite Model
```python
class EventPrerequisite(models.Model):
    CATEGORY_CHOICES = [
        ('hardware', 'Hardware/Equipment'),
        ('software', 'Software/Tools'),
        ('documentation', 'Documentation'),
        ('travel', 'Travel Arrangements'),
        ('customer', 'Customer Requirements'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('blocked', 'Blocked'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                             related_name='prerequisites')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    responsible_person = models.ForeignKey(CompanyUser, on_delete=models.SET_NULL,
                                          null=True)
    due_date = models.DateField()
    completed_date = models.DateField(null=True, blank=True)
    notes = models.TextField(blank=True)
```

#### 3.3 EventCost Model
```python
class EventCost(models.Model):
    COST_TYPES = [
        ('personnel', 'Personnel Cost'),
        ('accommodation', 'Accommodation'),
        ('transport', 'Transportation'),
        ('allowance', 'Travel Allowance'),
        ('hardware', 'Hardware/Materials'),
        ('other', 'Other Expenses'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='costs')
    cost_type = models.CharField(max_length=20, choices=COST_TYPES)
    description = models.CharField(max_length=200)

    # Personnel specific
    staff_member = models.ForeignKey(CompanyUser, on_delete=models.SET_NULL,
                                    null=True, blank=True)
    daily_rate = models.DecimalField(max_digits=10, decimal_places=2,
                                     null=True, blank=True)
    days_count = models.IntegerField(null=True, blank=True)

    # General cost
    estimated_amount = models.DecimalField(max_digits=10, decimal_places=2)
    actual_amount = models.DecimalField(max_digits=10, decimal_places=2,
                                       null=True, blank=True)
    currency = models.CharField(max_length=3, default='RMB')

    # Documentation
    receipt_attachment = models.FileField(upload_to='event_receipts/',
                                         null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 3.4 EventReminder Model
```python
class EventReminder(models.Model):
    REMINDER_TYPES = [
        ('code_conduct', 'Code of Conduct'),
        ('safety', 'Safety Protocol'),
        ('customer_service', 'Customer Service Ethics'),
        ('checklist', 'Pre-Departure Checklist'),
        ('custom', 'Custom Reminder'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                             related_name='reminders')
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    recipients = models.ManyToManyField(CompanyUser, related_name='event_reminders')

    send_datetime = models.DateTimeField()
    sent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(null=True, blank=True)

    created_by = models.ForeignKey(CompanyUser, on_delete=models.SET_NULL,
                                  related_name='reminders_created', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 3.5 EventWorkLog Model
```python
class EventWorkLog(models.Model):
    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                             related_name='work_logs')
    log_date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()

    work_description = models.TextField()
    staff_members = models.ManyToManyField(CompanyUser,
                                          related_name='work_logs')

    # Work completion tracking
    tasks_completed = models.TextField()
    issues_encountered = models.TextField(blank=True)
    notes_recommendations = models.TextField(blank=True)

    # Attachments
    photos = models.JSONField(default=list)  # Store file paths
    documents = models.JSONField(default=list)

    created_by = models.ForeignKey(CompanyUser, on_delete=models.SET_NULL,
                                  related_name='work_logs_created', null=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

#### 3.6 EventReview Model
```python
class EventReview(models.Model):
    RATING_CHOICES = [(i, str(i)) for i in range(1, 6)]

    event = models.OneToOneField(Event, on_delete=models.CASCADE,
                                related_name='review')

    # Performance ratings
    time_management_rating = models.IntegerField(choices=RATING_CHOICES)
    technical_quality_rating = models.IntegerField(choices=RATING_CHOICES)
    customer_satisfaction_rating = models.IntegerField(choices=RATING_CHOICES)
    cost_efficiency_rating = models.IntegerField(choices=RATING_CHOICES)

    # Feedback
    what_went_well = models.TextField()
    areas_for_improvement = models.TextField()
    lessons_learned = models.TextField()
    recommendations = models.TextField()

    # Customer feedback
    customer_feedback = models.TextField(blank=True)
    customer_signature = models.ImageField(upload_to='event_signatures/',
                                          null=True, blank=True)
    customer_signed_date = models.DateField(null=True, blank=True)

    # Team feedback
    reviewed_by = models.ForeignKey(CompanyUser, on_delete=models.SET_NULL,
                                   related_name='reviews_conducted', null=True)
    review_date = models.DateField(auto_now_add=True)
```

#### 3.7 EventEquipment Model
```python
class EventEquipment(models.Model):
    STATUS_CHOICES = [
        ('checked_out', 'Checked Out'),
        ('in_use', 'In Use'),
        ('returned', 'Returned'),
        ('damaged', 'Damaged'),
        ('lost', 'Lost'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                             related_name='equipment')
    equipment_name = models.CharField(max_length=200)
    equipment_serial = models.CharField(max_length=100, blank=True)
    quantity = models.IntegerField()

    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                             default='checked_out')

    checked_out_by = models.ForeignKey(CompanyUser, on_delete=models.SET_NULL,
                                      related_name='equipment_checked_out',
                                      null=True)
    checked_out_date = models.DateTimeField(auto_now_add=True)

    returned_by = models.ForeignKey(CompanyUser, on_delete=models.SET_NULL,
                                   related_name='equipment_returned',
                                   null=True, blank=True)
    returned_date = models.DateTimeField(null=True, blank=True)

    condition_notes = models.TextField(blank=True)
    damage_report = models.TextField(blank=True)
```

#### 3.8 EventApproval Model
```python
class EventApproval(models.Model):
    APPROVAL_ROLES = [
        ('financial', 'Financial Supervisor'),
        ('technical', 'Technical Supervisor'),
        ('procurement', 'Procurement Personnel'),
        ('business', 'Business Supervisor'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE,
                             related_name='approvals')
    approval_role = models.CharField(max_length=20, choices=APPROVAL_ROLES)
    approver = models.ForeignKey(CompanyUser, on_delete=models.SET_NULL,
                                related_name='event_approvals', null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES,
                             default='pending')

    comments = models.TextField(blank=True)
    approved_date = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
```

---

## 4. APP STRUCTURE

### Directory Layout
```
integrated_business_platform/
├── event_management/              # New Django app
│   ├── __init__.py
│   ├── admin.py                   # Django admin configuration
│   ├── apps.py                    # App configuration
│   ├── models.py                  # All models defined above
│   ├── views.py                   # View functions/classes
│   ├── urls.py                    # URL routing
│   ├── forms.py                   # Form definitions
│   ├── signals.py                 # Signal handlers for reminders
│   ├── tasks.py                   # Celery tasks for scheduled jobs
│   ├── utils.py                   # Utility functions
│   ├── serializers.py             # API serializers
│   ├── migrations/                # Database migrations
│   ├── templates/
│   │   └── event_management/
│   │       ├── event_list.html
│   │       ├── event_detail.html
│   │       ├── event_form.html
│   │       ├── event_calendar.html
│   │       ├── prerequisite_list.html
│   │       ├── cost_tracking.html
│   │       ├── work_log_form.html
│   │       ├── review_form.html
│   │       ├── equipment_checkout.html
│   │       └── dashboard.html
│   ├── static/
│   │   └── event_management/
│   │       ├── css/
│   │       ├── js/
│   │       └── img/
│   └── tests/                     # Unit tests
│       ├── test_models.py
│       ├── test_views.py
│       └── test_forms.py
```

---

## 5. KEY FEATURES IMPLEMENTATION

### 5.1 Event Dashboard
- Overview of upcoming events
- Events requiring attention (missing prerequisites)
- Budget status across all events
- Staff availability calendar
- Quick statistics (events this month, total costs, pending approvals)

### 5.2 Event Creation Wizard
**Step 1:** Basic Information
- Event type, customer details, dates

**Step 2:** Personnel Assignment
- Select assigned staff with roles
- Estimate daily rates and duration

**Step 3:** Prerequisites Setup
- Add checklist items across categories
- Assign responsibilities and due dates

**Step 4:** Cost Estimation
- Personnel costs auto-calculated
- Add travel and material costs
- Set budget limits

**Step 5:** Reminder Configuration
- Set automated reminder schedule
- Customize reminder content
- Select recipients

**Step 6:** Review & Submit
- Summary of all information
- Submit for approval workflow

### 5.3 Pre-Event Checklist
- Prerequisites dashboard for assigned staff
- Mark items as complete with notes
- Upload supporting documents
- Alert system for overdue items
- Equipment checkout interface

### 5.4 During-Event Tracking
- Mobile-friendly work log entry
- Real-time photo uploads
- Time tracking (check-in/check-out)
- Issue reporting
- Customer communication log

### 5.5 Post-Event Review
- Automated review form generation
- Performance rating system
- Customer feedback collection
- Equipment return verification
- Cost reconciliation (estimated vs. actual)
- Generate completion report

### 5.6 Reporting & Analytics
- Events by type/status/customer
- Cost analysis (budget vs. actual)
- Staff utilization reports
- Customer satisfaction trends
- Equipment usage statistics
- Monthly/quarterly summaries

---

## 6. INTEGRATION POINTS

### 6.1 With Authentication System
- Use existing CompanyUser model
- Role-based access control (Sales, Technical, Finance, Admin)
- Permission-based feature access

### 6.2 With Cost Quotation System
- Link events to quotations (optional)
- Import hardware configuration from quotations
- Sync customer information

### 6.3 With Expense Claims
- Auto-create expense claims from event costs
- Link receipts to expense items
- Streamline reimbursement process

### 6.4 With Asset Management (if exists)
- Track equipment checkout/return
- Update inventory levels
- Equipment maintenance scheduling

### 6.5 Notification System
- Email notifications for reminders
- SMS alerts for urgent items
- Dashboard notifications
- Mobile push notifications (future)

---

## 7. USER ROLES & PERMISSIONS

### 7.1 Sales Personnel
- Create events
- Edit own events
- View all events
- Submit for approval

### 7.2 Technical Staff
- View assigned events
- Update prerequisites
- Submit work logs
- Mark tasks complete
- Checkout/return equipment

### 7.3 Financial Supervisor
- View all events and costs
- Approve financial aspects
- Generate cost reports
- Monitor budgets

### 7.4 Operations Manager
- View all events
- Assign personnel
- Approve all events
- Access all reports

### 7.5 System Administrator
- Full access
- User management
- System configuration
- Data export/import

---

## 8. IMPLEMENTATION PHASES

### Phase 1: Foundation (Weeks 1-2)
**Deliverables:**
- Database models created and migrated
- Basic CRUD operations for Events
- Admin panel configured
- User authentication integrated

**Tasks:**
1. Create event_management Django app
2. Define all models in models.py
3. Create and run migrations
4. Set up admin.py for data entry
5. Configure URLs and basic views

### Phase 2: Core Features (Weeks 3-4)
**Deliverables:**
- Event creation wizard
- Prerequisites management
- Cost tracking system
- Basic reporting

**Tasks:**
1. Build event creation form with wizard
2. Implement prerequisite CRUD operations
3. Create cost tracking interface
4. Develop event detail page
5. Build event list with filters

### Phase 3: Reminders & Workflow (Weeks 5-6)
**Deliverables:**
- Automated reminder system
- Approval workflow
- Email notifications
- Work log functionality

**Tasks:**
1. Set up Celery for scheduled tasks
2. Implement reminder creation and sending
3. Build approval workflow system
4. Create work log forms and views
5. Integrate email notification system

### Phase 4: Review & Inventory (Weeks 7-8)
**Deliverables:**
- Post-event review system
- Equipment checkout/return
- Performance ratings
- Customer feedback forms

**Tasks:**
1. Build review form with ratings
2. Implement equipment management
3. Create inventory tracking
4. Add signature capture for customers
5. Generate completion reports

### Phase 5: Reporting & Polish (Weeks 9-10)
**Deliverables:**
- Comprehensive dashboards
- Analytics reports
- Export functionality
- Mobile optimization
- User documentation

**Tasks:**
1. Create event dashboard with charts
2. Build report generation system
3. Implement data export (PDF, Excel)
4. Optimize for mobile devices
5. Write user guides and help documentation
6. Conduct UAT (User Acceptance Testing)

---

## 9. TECHNICAL SPECIFICATIONS

### 9.1 Technology Stack
- **Backend:** Django 4.2+ (existing platform)
- **Database:** SQLite3 (development), PostgreSQL (production recommended)
- **Frontend:** Bootstrap 5, jQuery
- **Charts:** Chart.js or similar
- **Notifications:** Django Email Backend, Celery
- **File Storage:** Django default (configurable to S3)
- **Forms:** Django Forms with Crispy Forms

### 9.2 API Endpoints (REST API - Optional)
```
GET    /api/events/                    # List events
POST   /api/events/                    # Create event
GET    /api/events/{id}/               # Event details
PUT    /api/events/{id}/               # Update event
DELETE /api/events/{id}/               # Delete event

GET    /api/events/{id}/prerequisites/ # List prerequisites
POST   /api/events/{id}/prerequisites/ # Add prerequisite
PUT    /api/prerequisites/{id}/        # Update prerequisite
DELETE /api/prerequisites/{id}/        # Delete prerequisite

GET    /api/events/{id}/costs/         # List costs
POST   /api/events/{id}/costs/         # Add cost
PUT    /api/costs/{id}/                # Update cost

GET    /api/events/{id}/work-logs/     # List work logs
POST   /api/events/{id}/work-logs/     # Create work log

GET    /api/events/{id}/review/        # Get review
POST   /api/events/{id}/review/        # Submit review

GET    /api/events/{id}/equipment/     # List equipment
POST   /api/events/{id}/equipment/     # Checkout equipment
PUT    /api/equipment/{id}/return/     # Return equipment
```

### 9.3 Security Considerations
- CSRF protection enabled
- SQL injection prevention (Django ORM)
- XSS protection in templates
- File upload validation
- Permission-based access control
- Audit trail for sensitive operations
- Data encryption for sensitive fields

---

## 10. DATA MIGRATION STRATEGY

### From Existing Systems:
1. **Customer Data** - Import from quotation system
2. **Staff Data** - Use existing CompanyUser records
3. **Historical Events** - Manual entry or bulk import from spreadsheets

### Migration Script Template:
```python
# management/commands/import_events.py
from django.core.management.base import BaseCommand
from event_management.models import Event
import csv

class Command(BaseCommand):
    def handle(self, *args, **options):
        with open('historical_events.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                Event.objects.create(
                    event_number=row['event_number'],
                    # ... map CSV columns to model fields
                )
```

---

## 11. TESTING STRATEGY

### 11.1 Unit Tests
- Model validation tests
- Form validation tests
- View permission tests
- Utility function tests

### 11.2 Integration Tests
- Event creation workflow
- Approval process flow
- Reminder sending system
- Cost calculation accuracy

### 11.3 User Acceptance Testing
- Sales team creates and manages events
- Technical team logs work and checks equipment
- Finance team reviews costs and approves
- Management accesses reports

---

## 12. DEPLOYMENT PLAN

### 12.1 Development Environment
- Local development with SQLite
- Git version control
- Feature branch workflow

### 12.2 Staging Environment
- Test server deployment
- PostgreSQL database
- Full data migration test
- UAT with select users

### 12.3 Production Deployment
- Backup existing database
- Deploy new code
- Run migrations
- Import historical data
- Monitor for 48 hours
- Training sessions for users

---

## 13. MAINTENANCE & SUPPORT

### 13.1 Regular Maintenance
- Weekly database backups
- Monthly security updates
- Quarterly feature reviews
- Annual system audit

### 13.2 Support Structure
- Help documentation
- Video tutorials
- Email support
- Bug reporting system
- Feature request tracking

---

## 14. SUCCESS METRICS

### Key Performance Indicators:
1. **Event Completion Rate** - % of events completed on time
2. **Budget Accuracy** - Average variance between estimated and actual costs
3. **User Adoption** - % of events logged in system vs. manual tracking
4. **Customer Satisfaction** - Average rating from customer feedback
5. **Equipment Return Rate** - % of equipment returned on time
6. **Prerequisite Completion** - % of prerequisites completed before event
7. **Review Completion** - % of events with completed reviews

---

## 15. BUDGET ESTIMATE

### Development Costs:
- **Phase 1:** 80 hours × rate
- **Phase 2:** 100 hours × rate
- **Phase 3:** 80 hours × rate
- **Phase 4:** 80 hours × rate
- **Phase 5:** 60 hours × rate
- **Total:** ~400 hours

### Infrastructure Costs:
- Server hosting (if separate)
- Email service (SendGrid/AWS SES)
- SMS service (Twilio) - optional
- Storage (AWS S3) - optional

---

## 16. RISKS & MITIGATION

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|---------------------|
| User resistance to new system | High | Medium | Comprehensive training, gradual rollout |
| Data migration issues | High | Medium | Thorough testing, backup plans |
| Integration complexities | Medium | High | Well-defined APIs, incremental integration |
| Performance with large data | Medium | Low | Database optimization, indexing |
| Security vulnerabilities | High | Low | Security audit, regular updates |

---

## 17. NEXT STEPS

### Immediate Actions:
1. **Review & Approval** - Stakeholder review of this plan
2. **Resource Allocation** - Assign development team
3. **Timeline Confirmation** - Confirm start and end dates
4. **Budget Approval** - Secure funding
5. **Kickoff Meeting** - Align all stakeholders

### Development Start:
1. Set up development environment
2. Create Git repository
3. Initialize Django app structure
4. Begin Phase 1 implementation

---

## 18. CONTACT & APPROVAL

**Prepared By:** Claude AI Development Assistant
**Date:** October 27, 2025
**Version:** 1.0

**Approval Required From:**
- [ ] Business Supervisor - Strategy & Requirements
- [ ] Technical Supervisor - Architecture & Feasibility
- [ ] Financial Supervisor - Budget & Resources
- [ ] Operations Manager - Process & Workflow

---

## APPENDIX A: Sample Code Structure

### models.py (Excerpt)
```python
from django.db import models
from authentication.models import CompanyUser

class Event(models.Model):
    # ... (as defined in section 3.1)

    class Meta:
        ordering = ['-planned_start_date']
        verbose_name = 'Event/Visit'
        verbose_name_plural = 'Events/Visits'

    def __str__(self):
        return f"{self.event_number} - {self.customer_company}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('event_detail', kwargs={'pk': self.pk})

    @property
    def is_upcoming(self):
        from django.utils import timezone
        return self.planned_start_date > timezone.now().date()

    @property
    def total_estimated_personnel_cost(self):
        return sum(cost.estimated_amount for cost in
                  self.costs.filter(cost_type='personnel'))
```

### views.py (Excerpt)
```python
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from .models import Event
from .forms import EventForm

class EventListView(LoginRequiredMixin, ListView):
    model = Event
    template_name = 'event_management/event_list.html'
    context_object_name = 'events'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

class EventCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Event
    form_class = EventForm
    template_name = 'event_management/event_form.html'
    permission_required = 'event_management.add_event'

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
```

### urls.py
```python
from django.urls import path
from . import views

app_name = 'event_management'

urlpatterns = [
    path('', views.EventListView.as_view(), name='event_list'),
    path('create/', views.EventCreateView.as_view(), name='event_create'),
    path('<int:pk>/', views.EventDetailView.as_view(), name='event_detail'),
    path('<int:pk>/edit/', views.EventUpdateView.as_view(), name='event_update'),
    path('<int:pk>/review/', views.EventReviewView.as_view(), name='event_review'),
    # ... more URLs
]
```

---

## APPENDIX B: Database Relationships Diagram

```
Event (Central Entity)
├── EventPrerequisite (Many) - Prerequisites for event
├── EventCost (Many) - All costs associated
├── EventReminder (Many) - Scheduled reminders
├── EventWorkLog (Many) - Daily work logs
├── EventReview (One) - Post-event review
├── EventEquipment (Many) - Equipment tracking
├── EventApproval (Many) - Approval workflow
├── CompanyUser (Many-to-Many) - Assigned staff
├── CompanyUser (ForeignKey) - Sales responsible
└── Quotation (Optional ForeignKey) - Related quote
```

---

**End of Development Plan**

This comprehensive plan provides a complete roadmap for developing the Event/Visit Log and Reminder app. The next step is to review this plan with stakeholders and begin implementation according to the phased timeline.
