"""
Authentication forms for email-based login.
"""

from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.utils.translation import gettext_lazy as _
from .models import CompanyUser


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