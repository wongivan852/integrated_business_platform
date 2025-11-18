# forms.py - Django forms for customer management
from django import forms
from .models import Customer, Enrollment, Course, CustomerCommunicationPreference

class CustomerForm(forms.ModelForm):
    """Form for creating and editing customers with enhanced name fields and country selection"""
    
    class Meta:
        model = Customer
        fields = [
            # Essential name fields only (preferred_name removed)
            'first_name', 'middle_name', 'last_name', 'name_suffix', 'designation',
            
            # Contact information
            'email_primary', 'email_secondary',
            'phone_primary', 'phone_primary_country_code',
            'phone_secondary', 'phone_secondary_country_code', 
            'fax', 'fax_country_code',
            'whatsapp_number', 'whatsapp_country_code',
            'wechat_id',
            
            # Geographic and Address (simplified)
            'country_region', 'address_primary', 'address_secondary',
            
            # Professional (simplified)
            'company_primary', 'position_primary', 'company_secondary', 'position_secondary',
            'company_website',
            
            # Social media
            'linkedin_profile', 'facebook_profile', 'twitter_handle', 'instagram_handle', 
            'youtube_handle', 'youtube_channel_url',
            
            # Communication preferences
            'preferred_communication_method',
            
            # CRM fields
            'customer_type', 'status', 'preferred_learning_format', 'interests'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter first name (required)'
            }),
            'middle_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter middle name(s) (optional)'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter last name (required)'
            }),
            'name_suffix': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Other name, nickname, or alias (optional)'
            }),
            'designation': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Select professional or academic designation'
            }),
            'email_primary': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter primary email address'
            }),
            'email_secondary': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter secondary email address (optional)'
            }),
            'phone_primary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter phone number (without country code)'
            }),
            'phone_primary_country_code': forms.TextInput(attrs={
                'class': 'form-control country-code',
                'placeholder': '+1',
                'title': 'Auto-updated when country is selected, but you can manually change it'
            }),
            'phone_secondary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter secondary phone number (without country code)'
            }),
            'phone_secondary_country_code': forms.TextInput(attrs={
                'class': 'form-control country-code',
                'placeholder': '+1',
                'title': 'Can be different from primary phone country code'
            }),
            'fax': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter fax number (without country code)'
            }),
            'fax_country_code': forms.TextInput(attrs={
                'class': 'form-control country-code',
                'placeholder': '+1',
                'title': 'Auto-updated when country is selected, but you can manually change it'
            }),
            'whatsapp_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter WhatsApp number (without country code)'
            }),
            'whatsapp_country_code': forms.TextInput(attrs={
                'class': 'form-control country-code',
                'placeholder': '+1',
                'title': 'Auto-updated when country is selected, but you can manually change it'
            }),
            'country_region': forms.Select(attrs={
                'class': 'form-select',
                'id': 'id_country_region',
                'onchange': 'updateCountryCodes(this.value)'
            }),
            'wechat_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter WeChat ID'
            }),
            'customer_type': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'company_primary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter primary company'
            }),
            'position_primary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter primary position'
            }),
            'company_secondary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter secondary company (optional)'
            }),
            'position_secondary': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter secondary position (optional)'
            }),
            'company_website': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.example.com (include https:// or http://)'
            }),
            'address_primary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter primary address'
            }),
            'address_secondary': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Enter secondary address (optional)'
            }),
            'linkedin_profile': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.linkedin.com/in/username'
            }),
            'facebook_profile': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://www.facebook.com/username'
            }),
            'twitter_handle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Twitter/X handle (without @)'
            }),
            'instagram_handle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter Instagram handle (without @)'
            }),
            'youtube_handle': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter YouTube handle (without @)'
            }),
            'youtube_channel_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://youtube.com/@username or https://youtube.com/channel/ID'
            }),
            'preferred_learning_format': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Online, In-person, Hybrid'
            }),
            'interests': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Enter interests (comma-separated)'
            }),
            'preferred_communication_method': forms.Select(attrs={
                'class': 'form-select'
            }),
        }
        
        help_texts = {
            'linkedin_profile': 'Enter your LinkedIn username (e.g., john-doe) or full URL. The full URL will be added automatically.',
            'facebook_profile': 'Enter your Facebook username (e.g., greengoldtv) or full URL. The full URL will be added automatically.',
            'twitter_handle': 'Enter your Twitter/X handle without the @ symbol.',
            'instagram_handle': 'Enter your Instagram handle without the @ symbol.',
            'youtube_handle': 'Enter your YouTube handle without the @ symbol. Must be 3-30 characters, letters, numbers, dots, hyphens, and underscores only.',
            'youtube_channel_url': 'Full YouTube channel URL (e.g., https://youtube.com/@username). Will be auto-generated if you provide just the handle.',
        }


class CustomerCommunicationPreferenceForm(forms.ModelForm):
    """Form for managing customer communication preferences"""
    
    class Meta:
        model = CustomerCommunicationPreference
        fields = ['communication_type', 'priority', 'is_active', 'notes']
        widgets = {
            'communication_type': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Work hours only, Weekends preferred'
            })
        }


class EnrollmentForm(forms.ModelForm):
    """Form for course enrollment"""
    
    class Meta:
        model = Enrollment
        fields = ['customer', 'course', 'status', 'payment_status', 'notes']
        widgets = {
            'customer': forms.Select(attrs={'class': 'form-control'}),
            'course': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'payment_status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Additional notes about enrollment'
            })
        }


class MessageForm(forms.Form):
    """Form for sending messages to customers"""
    
    CHANNEL_CHOICES = [
        ('email_primary', 'Primary Email'),
        ('email_secondary', 'Secondary Email'),
        ('whatsapp', 'WhatsApp'),
        ('wechat', 'WeChat'),
    ]
    
    channel = forms.ChoiceField(
        choices=CHANNEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter message subject'
        })
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 6,
            'placeholder': 'Enter your message content'
        })
    )


class BulkMessageForm(forms.Form):
    """Form for sending bulk messages"""
    
    CHANNEL_CHOICES = [
        ('email_primary', 'Primary Email'),
        ('whatsapp', 'WhatsApp'),
        ('wechat', 'WeChat'),
    ]
    
    customer_type = forms.MultipleChoiceField(
        choices=Customer.CUSTOMER_TYPES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    status = forms.MultipleChoiceField(
        choices=Customer.STATUS_CHOICES,
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
        required=False
    )
    marketing_consent_only = forms.BooleanField(
        initial=True,
        required=False,
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )
    channel = forms.ChoiceField(
        choices=CHANNEL_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    subject = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter message subject'
        })
    )
    content = forms.CharField(
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 8,
            'placeholder': 'Enter your message content'
        })
    )
