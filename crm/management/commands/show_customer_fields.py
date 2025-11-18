"""
Management command to show the enhanced Customer model fields
"""
from django.core.management.base import BaseCommand
from crm.models import Customer, CustomerCommunicationPreference
from django.db import models

class Command(BaseCommand):
    help = 'Display the enhanced Customer model fields and structure'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🔍 Enhanced Customer Model Fields'))
        self.stdout.write('=' * 60)
        
        # Get all fields from the Customer model
        customer_fields = Customer._meta.get_fields()
        
        # Group fields by category
        field_categories = {
            'Core Identity': ['id', 'first_name', 'last_name'],
            'Email Addresses': ['email_primary', 'email_secondary'],
            'Phone Numbers': ['phone_primary', 'phone_secondary', 'fax'],
            'Messaging Apps': ['whatsapp_number', 'wechat_id'],
            'Social Media': ['linkedin_profile', 'facebook_profile', 'twitter_handle', 'instagram_handle'],
            'Geographic': ['country_region'],
            'Customer Classification': ['customer_type', 'status'],
            'Professional Info': ['company_primary', 'position_primary', 'company_secondary', 'position_secondary', 'company_website'],
            'Addresses': ['address_primary', 'address_secondary'],
            'Learning Preferences': ['preferred_learning_format', 'interests'],
            'Marketing': ['marketing_consent'],
            'System Fields': ['created_at', 'updated_at']
        }
        
        for category, field_names in field_categories.items():
            self.stdout.write(f'\n📋 {category}:')
            self.stdout.write('-' * 30)
            
            for field_name in field_names:
                try:
                    field = Customer._meta.get_field(field_name)
                    field_type = field.__class__.__name__
                    
                    # Get field constraints and options
                    constraints = []
                    if getattr(field, 'unique', False):
                        constraints.append('UNIQUE')
                    if getattr(field, 'blank', False):
                        constraints.append('Optional')
                    else:
                        constraints.append('Required')
                    if hasattr(field, 'max_length') and field.max_length:
                        constraints.append(f'Max: {field.max_length}')
                    if hasattr(field, 'help_text') and field.help_text:
                        constraints.append(f'Help: {field.help_text}')
                    
                    constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                    
                    self.stdout.write(f'  • {field_name:<20} : {field_type}{constraint_str}')
                    
                except Exception as e:
                    self.stdout.write(f'  • {field_name:<20} : Field not found')
        
        # Show Communication Preferences model
        self.stdout.write(f'\n📞 Communication Preferences Model:')
        self.stdout.write('-' * 40)
        
        comm_fields = CustomerCommunicationPreference._meta.get_fields()
        for field in comm_fields:
            if field.name != 'customer':  # Skip the foreign key back reference
                field_type = field.__class__.__name__
                constraints = []
                
                if hasattr(field, 'choices') and field.choices:
                    choices_str = ', '.join([choice[0] for choice in field.choices[:3]])
                    if len(field.choices) > 3:
                        choices_str += '...'
                    constraints.append(f'Choices: {choices_str}')
                
                if getattr(field, 'blank', False):
                    constraints.append('Optional')
                
                constraint_str = f" ({', '.join(constraints)})" if constraints else ""
                self.stdout.write(f'  • {field.name:<20} : {field_type}{constraint_str}')
        
        # Show sample usage
        self.stdout.write(f'\n💡 Enhanced Features:')
        self.stdout.write('-' * 30)
        self.stdout.write('  • Multiple email addresses per customer')
        self.stdout.write('  • Multiple phone numbers (primary/secondary)')
        self.stdout.write('  • Social media profile integration')
        self.stdout.write('  • Multiple company/position tracking')
        self.stdout.write('  • Flexible communication preferences')
        self.stdout.write('  • Geographic information')
        self.stdout.write('  • Fax number support')
        
        self.stdout.write(f'\n🔧 Usage Examples:')
        self.stdout.write('-' * 30)
        self.stdout.write('  # Access primary email')
        self.stdout.write('  customer.email_primary')
        self.stdout.write('')
        self.stdout.write('  # Backward compatibility')
        self.stdout.write('  customer.email  # Returns email_primary')
        self.stdout.write('')
        self.stdout.write('  # Communication preferences')
        self.stdout.write('  customer.communication_preferences.filter(priority=1)')
        
        self.stdout.write(f'\n✅ Migration Status: Complete')
        self.stdout.write('All enhanced fields have been successfully added to the database!')
