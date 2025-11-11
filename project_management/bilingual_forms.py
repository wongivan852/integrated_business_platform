"""
Bilingual forms with language-aware validation
"""
from django import forms
from django.utils.translation import get_language, gettext_lazy as _
from django.core.exceptions import ValidationError
from .validators import (
    chinese_phone_validator,
    intl_phone_validator,
    chinese_name_validator,
    english_name_validator,
    bilingual_name_validator,
    normalize_phone_number,
    format_phone_for_display,
)


class BilingualFormMixin:
    """
    Mixin for forms that need language-aware validation
    """

    def __init__(self, *args, **kwargs):
        self.current_lang = kwargs.pop('language', None) or get_language()
        super().__init__(*args, **kwargs)
        self.configure_for_language()

    def configure_for_language(self):
        """
        Configure form fields based on current language
        Override this method to customize field behavior per language
        """
        is_chinese = self.current_lang.startswith('zh')

        # Update field labels and help text based on language
        for field_name, field in self.fields.items():
            if is_chinese:
                # Use Chinese-specific validators and formats
                if field_name.endswith('_phone'):
                    field.validators = [chinese_phone_validator]
                    field.help_text = _('Format: 138-0013-8000')
                elif field_name.endswith('_name'):
                    if hasattr(field, 'chinese_validation') and field.chinese_validation:
                        field.validators = [chinese_name_validator]
            else:
                # Use English/International validators
                if field_name.endswith('_phone'):
                    field.validators = [intl_phone_validator]
                    field.help_text = _('Format: +1-555-123-4567')
                elif field_name.endswith('_name'):
                    if hasattr(field, 'english_validation') and field.english_validation:
                        field.validators = [english_name_validator]

    def get_language_field(self, base_field_name):
        """
        Get the language-specific field name

        Args:
            base_field_name: Base name like 'name' or 'description'

        Returns:
            Language-specific field name like 'name_en' or 'name_zh'
        """
        suffix = '_zh' if self.current_lang.startswith('zh') else '_en'
        return f"{base_field_name}{suffix}"


class BilingualModelForm(BilingualFormMixin, forms.ModelForm):
    """
    ModelForm with bilingual support
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set initial values for bilingual fields
        if self.instance and self.instance.pk:
            self.populate_bilingual_fields()

    def populate_bilingual_fields(self):
        """Populate form with bilingual field values"""
        # Override in subclass if needed
        pass

    def save(self, commit=True):
        """Save with language context"""
        instance = super().save(commit=False)

        # Store the language context
        if hasattr(instance, 'last_edit_language'):
            instance.last_edit_language = self.current_lang

        if commit:
            instance.save()

        return instance


class ContactInformationForm(BilingualFormMixin, forms.Form):
    """
    Example form for contact information with bilingual validation
    """
    name = forms.CharField(
        max_length=100,
        label=_('Name'),
        validators=[bilingual_name_validator]
    )

    phone = forms.CharField(
        max_length=20,
        label=_('Phone Number'),
        help_text=_('Enter phone number in local format')
    )

    email = forms.EmailField(
        label=_('Email'),
        required=False
    )

    address = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        label=_('Address'),
        required=False,
        help_text=_('Enter address in your preferred format')
    )

    def clean_phone(self):
        """Normalize and validate phone number"""
        phone = self.cleaned_data.get('phone')
        if not phone:
            return phone

        # Determine country code based on language
        country_code = '86' if self.current_lang.startswith('zh') else None

        try:
            # Normalize to E.164 format
            normalized = normalize_phone_number(phone, country_code)
            return normalized
        except Exception:
            raise ValidationError(_('Invalid phone number format'))

    def clean_name(self):
        """Validate name based on language context"""
        name = self.cleaned_data.get('name')
        if not name:
            return name

        is_chinese = self.current_lang.startswith('zh')

        # Check if name contains Chinese characters
        has_chinese = any('\u4e00' <= char <= '\u9fa5' for char in name)

        # Warn if language mismatch
        if is_chinese and not has_chinese:
            # Allow English names in Chinese context, but validate format
            english_name_validator(name)
        elif not is_chinese and has_chinese:
            # Allow Chinese names in English context
            chinese_name_validator(name)

        return name


class BilingualProjectForm(BilingualModelForm):
    """
    Example bilingual project form
    """
    # Bilingual name fields
    name_en = forms.CharField(
        max_length=200,
        label=_('Project Name (English)'),
        required=False
    )
    name_zh = forms.CharField(
        max_length=200,
        label=_('Project Name (Chinese)'),
        required=False
    )

    # Bilingual description fields
    description_en = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label=_('Description (English)'),
        required=False
    )
    description_zh = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4}),
        label=_('Description (Chinese)'),
        required=False
    )

    # Language-neutral fields
    project_code = forms.CharField(
        max_length=50,
        label=_('Project Code'),
        help_text=_('Unique identifier (language-neutral)')
    )

    start_date = forms.DateField(
        label=_('Start Date'),
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    end_date = forms.DateField(
        label=_('End Date'),
        widget=forms.DateInput(attrs={'type': 'date'})
    )

    budget = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        label=_('Budget'),
        required=False
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Show/hide fields based on current language
        is_chinese = self.current_lang.startswith('zh')

        if is_chinese:
            # In Chinese mode, prioritize Chinese fields
            self.fields['name_zh'].required = True
            self.fields['name_en'].widget = forms.HiddenInput()
            self.fields['description_zh'].required = True
            self.fields['description_en'].widget = forms.HiddenInput()
        else:
            # In English mode, prioritize English fields
            self.fields['name_en'].required = True
            self.fields['name_zh'].widget = forms.HiddenInput()
            self.fields['description_en'].required = True
            self.fields['description_zh'].widget = forms.HiddenInput()

    def clean(self):
        """Validate that at least one language version is provided"""
        cleaned_data = super().clean()

        # Check that at least one name is provided
        name_en = cleaned_data.get('name_en')
        name_zh = cleaned_data.get('name_zh')

        if not name_en and not name_zh:
            raise ValidationError(
                _('Please provide project name in at least one language')
            )

        # Auto-fill the other language field if only one is provided
        # (In production, you might want to use translation API)
        if name_en and not name_zh:
            cleaned_data['name_zh'] = name_en  # Placeholder
        elif name_zh and not name_en:
            cleaned_data['name_en'] = name_zh  # Placeholder

        return cleaned_data

    class Meta:
        model = None  # Set this in actual implementation
        fields = [
            'name_en', 'name_zh',
            'description_en', 'description_zh',
            'project_code', 'start_date', 'end_date', 'budget'
        ]


class LanguageSwitchForm(forms.Form):
    """
    Form for language switching
    """
    language = forms.ChoiceField(
        choices=[
            ('en', 'English'),
            ('zh-hans', '简体中文'),
        ],
        label=_('Language'),
        widget=forms.RadioSelect
    )

    next = forms.CharField(
        widget=forms.HiddenInput(),
        required=False
    )
