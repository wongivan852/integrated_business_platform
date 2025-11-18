#!/usr/bin/env python3
"""
Django management command to help update forms and admin when custom fields are added
Usage: python manage.py update_customer_interface
"""

from django.core.management.base import BaseCommand
from django.apps import apps
import os


class Command(BaseCommand):
    help = 'Show instructions for updating Customer forms and admin interface after adding custom fields'

    def handle(self, *args, **options):
        from crm.models import Customer
        
        # Get all field names from the model
        model_fields = [f.name for f in Customer._meta.get_fields() 
                       if not f.many_to_many and not f.one_to_many and not f.name == 'id']
        
        self.stdout.write(self.style.SUCCESS('Current Customer Model Fields:'))
        for field in sorted(model_fields):
            field_obj = Customer._meta.get_field(field)
            self.stdout.write(f'  - {field}: {field_obj.__class__.__name__}')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('To update forms.py, add new fields to CustomerForm:'))
        self.stdout.write('''
class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = [
            # Basic Information
            'first_name', 'last_name', 'gender', 'date_of_birth',
            
            # Contact Information  
            'email_primary', 'email_secondary',
            'phone_primary', 'phone_secondary', 'whatsapp_number', 'fax',
            
            # Address Information
            'address_primary_line1', 'address_primary_line2', 'address_primary_city', 
            'address_primary_state', 'address_primary_postal_code',
            'address_secondary_line1', 'address_secondary_line2', 'address_secondary_city',
            'address_secondary_state', 'address_secondary_postal_code',
            'country', 'region',
            
            # Professional Information
            'company', 'position_primary', 'position_secondary', 'company_website',
            
            # Social Media
            'linkedin_profile', 'facebook_profile', 'twitter_profile', 
            'instagram_profile', 'wechat_id',
            
            # CRM Fields
            'customer_type', 'status', 'preferred_communication', 'notes',
            
            # ADD YOUR CUSTOM FIELDS HERE
        ]
        ''')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('To update admin.py, add new fields to CustomerAdmin fieldsets:'))
        self.stdout.write('''
    fieldsets = (
        ('Basic Information', {
            'fields': ('first_name', 'last_name', 'gender', 'date_of_birth')
        }),
        ('Contact Information', {
            'fields': (
                ('email_primary', 'email_secondary'),
                ('phone_primary', 'phone_secondary'),
                ('whatsapp_number', 'fax')
            )
        }),
        # ... existing fieldsets ...
        ('Custom Fields', {
            'fields': (
                # ADD YOUR CUSTOM FIELDS HERE
            ),
            'classes': ('collapse',)
        }),
    )
        ''')
        
        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS('To update CSV export, add new fields to export_customers_csv view in views.py'))
        
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('Remember to:'))
        self.stdout.write('1. Run migrations after adding fields')
        self.stdout.write('2. Update the CSV export headers and data rows')
        self.stdout.write('3. Test the form submission and admin interface')
        self.stdout.write('4. Consider adding validation for new fields')
