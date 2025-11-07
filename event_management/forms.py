"""
Django Forms for Event Management
"""
from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Event, EventPrerequisite, EventCost, EventReminder,
    EventWorkLog, EventReview, EventEquipment, EventApproval,
    CustomerFeedback, EquipmentDamageReport, DamagePhoto
)


class EventForm(forms.ModelForm):
    """Form for creating and editing events"""

    class Meta:
        model = Event
        fields = [
            'event_type', 'status',
            'customer_company', 'contact_person', 'contact_position',
            'contact_phone', 'contact_wechat', 'contact_email',
            'delivery_address', 'installation_address', 'training_address',
            'planned_start_date', 'planned_end_date',
            'estimated_duration_days',
            'sales_responsible', 'assigned_staff',
            'estimated_total_cost', 'actual_total_cost',
        ]
        widgets = {
            'event_type': forms.Select(attrs={'class': 'form-select'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'customer_company': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_person': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_position': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_wechat': forms.TextInput(attrs={'class': 'form-control'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'delivery_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'installation_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'training_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'planned_start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'planned_end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'estimated_duration_days': forms.NumberInput(attrs={'class': 'form-control'}),
            'sales_responsible': forms.Select(attrs={'class': 'form-select'}),
            'assigned_staff': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '5'}),
            'estimated_total_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'actual_total_cost': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('planned_start_date')
        end_date = cleaned_data.get('planned_end_date')

        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError('End date must be after start date.')

        return cleaned_data


class EventPrerequisiteForm(forms.ModelForm):
    """Form for managing event prerequisites"""

    class Meta:
        model = EventPrerequisite
        fields = ['category', 'description', 'status', 'responsible_person', 'due_date', 'notes']
        widgets = {
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'responsible_person': forms.Select(attrs={'class': 'form-select'}),
            'due_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class EventCostForm(forms.ModelForm):
    """Form for tracking event costs"""

    class Meta:
        model = EventCost
        fields = [
            'cost_type', 'description', 'staff_member',
            'daily_rate', 'days_count', 'estimated_amount', 'actual_amount',
            'currency', 'notes'
        ]
        widgets = {
            'cost_type': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'staff_member': forms.Select(attrs={'class': 'form-select'}),
            'daily_rate': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'days_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'estimated_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'readonly': 'readonly'}),
            'actual_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'currency': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def clean(self):
        cleaned_data = super().clean()
        daily_rate = cleaned_data.get('daily_rate')
        days_count = cleaned_data.get('days_count')

        if daily_rate and days_count:
            cleaned_data['estimated_amount'] = daily_rate * days_count

        return cleaned_data


class EventWorkLogForm(forms.ModelForm):
    """Form for daily work logs"""

    class Meta:
        model = EventWorkLog
        fields = [
            'log_date', 'start_time', 'end_time',
            'work_description', 'tasks_completed',
            'issues_encountered', 'notes_recommendations'
        ]
        widgets = {
            'log_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'work_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'tasks_completed': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'issues_encountered': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'notes_recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EventEquipmentForm(forms.ModelForm):
    """Form for equipment checkout and tracking"""

    class Meta:
        model = EventEquipment
        fields = [
            'equipment_name', 'equipment_serial', 'quantity', 'status',
            'checked_out_by', 'condition_notes'
        ]
        widgets = {
            'equipment_name': forms.TextInput(attrs={'class': 'form-control'}),
            'equipment_serial': forms.TextInput(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'checked_out_by': forms.Select(attrs={'class': 'form-select'}),
            'condition_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class EventReviewForm(forms.ModelForm):
    """Form for post-event review"""

    class Meta:
        model = EventReview
        fields = [
            'time_management_rating', 'technical_quality_rating',
            'customer_satisfaction_rating', 'cost_efficiency_rating',
            'what_went_well', 'areas_for_improvement',
            'lessons_learned', 'recommendations',
            'customer_feedback'
        ]
        widgets = {
            'time_management_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5'}),
            'technical_quality_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5'}),
            'customer_satisfaction_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5'}),
            'cost_efficiency_rating': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '5'}),
            'what_went_well': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'areas_for_improvement': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'lessons_learned': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'recommendations': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'customer_feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        ratings = [
            cleaned_data.get('time_management_rating'),
            cleaned_data.get('technical_quality_rating'),
            cleaned_data.get('customer_satisfaction_rating'),
            cleaned_data.get('cost_efficiency_rating'),
        ]

        for rating in ratings:
            if rating and (rating < 1 or rating > 5):
                raise ValidationError('Ratings must be between 1 and 5.')

        return cleaned_data


class EventApprovalForm(forms.ModelForm):
    """Form for approval workflow"""

    class Meta:
        model = EventApproval
        fields = ['status', 'comments']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'comments': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }


class EventReminderForm(forms.ModelForm):
    """Form for creating and editing event reminders"""

    class Meta:
        model = EventReminder
        fields = [
            'reminder_type', 'title', 'message', 'recipients',
            'send_datetime', 'send_email', 'send_sms', 'send_wechat'
        ]
        widgets = {
            'reminder_type': forms.Select(attrs={'class': 'form-select'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter reminder title'}),
            'message': forms.Textarea(attrs={'class': 'form-control', 'rows': 6, 'placeholder': 'Enter reminder message'}),
            'recipients': forms.SelectMultiple(attrs={'class': 'form-select', 'size': '8'}),
            'send_datetime': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'send_email': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_send_email'}),
            'send_sms': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_send_sms'}),
            'send_wechat': forms.CheckboxInput(attrs={'class': 'form-check-input', 'id': 'id_send_wechat'}),
        }

    def clean_send_datetime(self):
        send_datetime = self.cleaned_data.get('send_datetime')
        if send_datetime:
            from django.utils import timezone
            if send_datetime < timezone.now():
                raise ValidationError('Send date/time cannot be in the past.')
        return send_datetime

    def clean(self):
        cleaned_data = super().clean()
        send_email = cleaned_data.get('send_email')
        send_sms = cleaned_data.get('send_sms')
        send_wechat = cleaned_data.get('send_wechat')

        # At least one notification channel must be selected
        if not (send_email or send_sms or send_wechat):
            raise ValidationError('Please select at least one notification channel.')

        return cleaned_data


class CustomerFeedbackForm(forms.ModelForm):
    """Public-facing form for customer feedback collection"""

    class Meta:
        model = CustomerFeedback
        fields = [
            'customer_name', 'customer_email', 'customer_position',
            'service_quality_rating', 'staff_professionalism_rating',
            'timeliness_rating', 'technical_expertise_rating', 'communication_rating',
            'what_did_well', 'what_can_improve', 'additional_comments',
            'would_recommend', 'likelihood_to_use_again'
        ]
        widgets = {
            'customer_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Name',
                'required': True
            }),
            'customer_email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.email@company.com',
                'required': True
            }),
            'customer_position': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your Position (Optional)'
            }),
            'service_quality_rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'staff_professionalism_rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'timeliness_rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'technical_expertise_rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'communication_rating': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'what_did_well': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please share what you liked about our service...'
            }),
            'what_can_improve': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Please share areas where we can improve...'
            }),
            'additional_comments': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Any other feedback you would like to share...'
            }),
            'would_recommend': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'likelihood_to_use_again': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }

    def clean(self):
        cleaned_data = super().clean()

        # Validate all ratings are provided
        rating_fields = [
            'service_quality_rating', 'staff_professionalism_rating',
            'timeliness_rating', 'technical_expertise_rating', 'communication_rating'
        ]

        for field in rating_fields:
            if not cleaned_data.get(field):
                raise ValidationError(f'Please provide a rating for {field.replace("_", " ")}.')

        return cleaned_data


class EquipmentDamageReportForm(forms.ModelForm):
    """Form for creating equipment damage reports"""

    class Meta:
        model = EquipmentDamageReport
        fields = [
            'damage_type', 'severity', 'description',
            'location', 'suspected_cause', 'preventable', 'prevention_notes',
            'estimated_repair_cost', 'actual_repair_cost', 'replacement_cost',
            'repair_required', 'repair_completed', 'repair_completion_date',
            'responsible_party', 'insurance_claim_filed', 'insurance_claim_number',
            'internal_notes'
        ]
        widgets = {
            'damage_type': forms.Select(attrs={'class': 'form-select'}),
            'severity': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the damage in detail...'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Where was the damage discovered?'
            }),
            'suspected_cause': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'What might have caused this damage?'
            }),
            'preventable': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'prevention_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'How could this have been prevented?'
            }),
            'estimated_repair_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'actual_repair_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'replacement_cost': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'repair_required': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'repair_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'repair_completion_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'responsible_party': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Who is responsible for the damage?'
            }),
            'insurance_claim_filed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'insurance_claim_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Insurance claim number'
            }),
            'internal_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Internal notes (not visible to customer)...'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        repair_completed = cleaned_data.get('repair_completed')
        repair_completion_date = cleaned_data.get('repair_completion_date')

        # If repair is completed, completion date is required
        if repair_completed and not repair_completion_date:
            raise ValidationError('Repair completion date is required when repair is marked as completed.')

        # If insurance claim is filed, claim number is required
        insurance_filed = cleaned_data.get('insurance_claim_filed')
        claim_number = cleaned_data.get('insurance_claim_number')
        if insurance_filed and not claim_number:
            raise ValidationError('Insurance claim number is required when a claim is filed.')

        return cleaned_data


class DamagePhotoForm(forms.ModelForm):
    """Form for uploading damage photos"""

    class Meta:
        model = DamagePhoto
        fields = ['photo', 'caption']
        widgets = {
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Brief description of what this photo shows...'
            }),
        }


class EquipmentReturnForm(forms.ModelForm):
    """Form for processing equipment returns"""

    class Meta:
        model = EventEquipment
        fields = ['status', 'condition_notes', 'damage_report']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'condition_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe the condition of the equipment upon return...'
            }),
            'damage_report': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe any damage (if applicable)...'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        damage_report = cleaned_data.get('damage_report')

        # If equipment is damaged or lost, damage report is required
        if status in ['damaged', 'lost'] and not damage_report:
            raise ValidationError('Damage report is required for damaged or lost equipment.')

        return cleaned_data
