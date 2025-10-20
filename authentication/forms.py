"""
Authentication forms for email-based login.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordChangeForm as DjangoPasswordChangeForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from .models import CompanyUser


# Approved email domains for internal staff registration
APPROVED_DOMAINS = [
    'krystal.institute',
    'krystal.technology',
    'cgge.media',
    'origincg.cn',
    'cgge.com.cn',
    'blendercom.cn',
    'dectedu.cn',
    'dectges.org',
    'blenderstudio.cn',
]


class EmailAuthenticationForm(AuthenticationForm):
    """
    Custom authentication form that uses email instead of username.
    """
    username = forms.EmailField(
        label=_('Email Address'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@company.com',
            'autofocus': True
        })
    )

    password = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Password'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Change the username field label to Email
        self.fields['username'].label = _('Email Address')


class CompanyUserCreationForm(UserCreationForm):
    """
    Form for creating new company users.
    """
    email = forms.EmailField(
        label=_('Email Address'),
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@company.com'
        })
    )

    first_name = forms.CharField(
        label=_('First Name'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'First Name'
        })
    )

    last_name = forms.CharField(
        label=_('Last Name'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Last Name'
        })
    )

    employee_id = forms.CharField(
        label=_('Employee ID'),
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'EMP001'
        })
    )

    region = forms.ChoiceField(
        label=_('Region'),
        choices=CompanyUser.REGION_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    department = forms.ChoiceField(
        label=_('Department'),
        choices=CompanyUser.DEPARTMENT_CHOICES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )

    class Meta:
        model = CompanyUser
        fields = (
            'email', 'first_name', 'last_name', 'employee_id',
            'region', 'department', 'password1', 'password2'
        )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove username field since we use email
        if 'username' in self.fields:
            del self.fields['username']

        # Style password fields
        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })
        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm Password'
        })

    def save(self, commit=True):
        """Save the user with email as username."""
        user = super().save(commit=False)
        user.username = user.email  # Set username to email for Django compatibility
        if commit:
            user.save()
        return user


class UserProfileForm(forms.ModelForm):
    """
    Form for updating user profile information.
    """

    class Meta:
        model = CompanyUser
        fields = [
            'first_name', 'last_name', 'phone', 'region', 'department'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'region': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make all fields required except phone
        for field_name, field in self.fields.items():
            if field_name != 'phone':
                field.required = True


class UserRegistrationForm(forms.ModelForm):
    """
    Simplified registration form for internal staff self-registration.
    Only requires email, name, and password. Superadmin approval required.
    """
    password1 = forms.CharField(
        label=_('Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter password (min 8 characters)'
        }),
        help_text=_('Password must be at least 8 characters long.')
    )
    password2 = forms.CharField(
        label=_('Confirm Password'),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm password'
        }),
        help_text=_('Enter the same password again for verification.')
    )

    class Meta:
        model = CompanyUser
        fields = ('email', 'first_name', 'last_name')
        widgets = {
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'your.name@company.com'
            }),
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'First Name'
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Last Name'
            }),
        }
        help_texts = {
            'email': _('Use your company email address. Approved domains: @krystal.institute, @cgge.media, etc.'),
        }

    def clean_email(self):
        """Validate email domain is in approved list"""
        email = self.cleaned_data.get('email', '').lower().strip()

        if not email:
            raise ValidationError(_('Email is required.'))

        # Check if email has @ symbol
        if '@' not in email:
            raise ValidationError(_('Please enter a valid email address.'))

        # Extract domain
        domain = email.split('@')[-1]

        # Check if email domain is approved
        if domain not in APPROVED_DOMAINS:
            approved_list = ', '.join(f'@{d}' for d in APPROVED_DOMAINS)
            raise ValidationError(
                _('Registration is only available for internal staff. '
                  'Your email domain (@%(domain)s) is not authorized. '
                  'Approved domains: %(domains)s'),
                params={'domain': domain, 'domains': approved_list}
            )

        # Check if email already exists
        if CompanyUser.objects.filter(email=email).exists():
            raise ValidationError(
                _('This email address is already registered. '
                  'If you forgot your password, please contact your administrator.')
            )

        return email

    def clean_password2(self):
        """Check that the two password entries match and meet requirements"""
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')

        if not password1:
            raise ValidationError(_('Please enter a password.'))

        if not password2:
            raise ValidationError(_('Please confirm your password.'))

        if password1 != password2:
            raise ValidationError(_('Passwords do not match.'))

        if len(password1) < 8:
            raise ValidationError(_('Password must be at least 8 characters long.'))

        return password2

    def save(self, commit=True):
        """Create user with is_approved=False (pending superadmin approval)"""
        user = super().save(commit=False)
        user.username = user.email  # Set username to email for Django compatibility
        user.set_password(self.cleaned_data['password1'])
        user.is_approved = False  # Requires superadmin approval
        user.is_active = False  # Inactive until approved

        # Auto-generate employee_id if not set
        if not user.employee_id:
            # Generate unique employee ID based on email
            import hashlib
            import time
            # Use first part of email + timestamp hash for uniqueness
            email_prefix = user.email.split('@')[0][:3].upper()
            timestamp_hash = hashlib.md5(f"{user.email}{time.time()}".encode()).hexdigest()[:6].upper()
            user.employee_id = f"NEW-{email_prefix}-{timestamp_hash}"

        # Set default values for required fields
        if not user.region:
            user.region = 'HK'  # Default to Hong Kong
        if not user.department:
            user.department = 'ADMIN'  # Default to Administration

        if commit:
            user.save()

        return user


class UserPasswordChangeForm(DjangoPasswordChangeForm):
    """Password change form for users with Bootstrap styling"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes and placeholders to fields
        self.fields['old_password'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Current Password'
        })
        self.fields['new_password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'New Password (min 8 characters)'
        })
        self.fields['new_password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Confirm New Password'
        })