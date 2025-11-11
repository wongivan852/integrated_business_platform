## Comprehensive Bilingual Implementation Guide

# Complete Bilingual Django Application Guide

This guide documents the comprehensive bilingual implementation for the Project Management application, supporting both English and Simplified Chinese with cultural-aware validation.

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Database Schema Design](#database-schema-design)
3. [Validators](#validators)
4. [Forms](#forms)
5. [Models](#models)
6. [Serializers](#serializers)
7. [Views](#views)
8. [Templates](#templates)
9. [Testing](#testing)
10. [Cultural Considerations](#cultural-considerations)
11. [Best Practices](#best-practices)

---

## Architecture Overview

### Bilingual Data Storage Pattern

We use **separate field storage** for bilingual content:

```python
# Example Model
class Project(BilingualModel):
    # Bilingual fields - separate columns
    name_en = models.CharField(max_length=200)
    name_zh = models.CharField(max_length=200)
    description_en = models.TextField()
    description_zh = models.TextField()

    # Language-neutral fields
    project_code = models.CharField(max_length=50, unique=True)
    budget = models.DecimalField(max_digits=12, decimal_places=2)
    start_date = models.DateField()
```

**Advantages:**
- Simple queries and indexing
- No JOIN operations needed
- Easy backup and migration
- Clear data structure

**Trade-offs:**
- More columns in database
- Data duplication for language-neutral content
- Need to manage synchronization

---

## Database Schema Design

### 1. Bilingual Fields Pattern

```python
# models.py
from .mixins import BilingualModel

class Product(BilingualModel):
    # Bilingual fields
    name_en = models.CharField(max_length=200, verbose_name="Name (English)")
    name_zh = models.CharField(max_length=200, verbose_name="名称(中文)")

    description_en = models.TextField(verbose_name="Description (English)")
    description_zh = models.TextField(verbose_name="描述(中文)")

    # Language-neutral fields
    sku = models.CharField(max_length=50, unique=True, db_index=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    # Access via property (from BilingualModel mixin)
    @property
    def name(self):
        return self.get_bilingual_field('name')

    @property
    def description(self):
        return self.get_bilingual_field('description')
```

### 2. Foreign Key Translations

```python
class Category(BilingualModel):
    name_en = models.CharField(max_length=100)
    name_zh = models.CharField(max_length=100)

    class Meta:
        unique_together = [('name_en', 'name_zh')]

class Product(models.Model):
    category = models.ForeignKey(Category, on_delete=models.PROTECT)
    # Category name will be accessed via category.name property
```

### 3. Migration Strategy

```python
# migrations/0001_add_bilingual_fields.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('project_management', '0001_initial'),
    ]

    operations = [
        # Add new bilingual fields
        migrations.AddField(
            model_name='project',
            name='name_en',
            field=models.CharField(max_length=200, default=''),
        ),
        migrations.AddField(
            model_name='project',
            name='name_zh',
            field=models.CharField(max_length=200, default=''),
        ),
        # Copy data from old field
        migrations.RunPython(copy_existing_data),
        # Remove old field after verification
        migrations.RemoveField(
            model_name='project',
            name='name',
        ),
    ]

def copy_existing_data(apps, schema_editor):
    Project = apps.get_model('project_management', 'Project')
    for project in Project.objects.all():
        project.name_en = project.name  # Assuming existing data is English
        project.name_zh = project.name  # Placeholder
        project.save(update_fields=['name_en', 'name_zh'])
```

---

## Validators

### Custom Validators

#### 1. Chinese Phone Number Validator

```python
from .validators import ChinesePhoneValidator

class Employee(models.Model):
    phone = models.CharField(
        max_length=20,
        validators=[ChinesePhoneValidator()]
    )
```

**Validates:**
- Format: `1[3-9]xxxxxxxxx` (11 digits)
- Example: `138-0013-8000`, `13800138000`

#### 2. International Phone Validator

```python
from .validators import InternationalPhoneValidator

class Contact(models.Model):
    phone = models.CharField(
        max_length=20,
        validators=[InternationalPhoneValidator()]
    )
```

**Validates:**
- E.164 format: `+[country code][number]`
- Example: `+1-555-123-4567`, `+8613800138000`

#### 3. Chinese ID Card Validator

```python
from .validators import ChineseIDCardValidator

class Employee(models.Model):
    id_card = models.CharField(
        max_length=18,
        validators=[ChineseIDCardValidator()]
    )
```

**Validates:**
- 18-digit ID with checksum
- Example: `110101199003078515`

#### 4. Name Validators

```python
from .validators import (
    ChineseNameValidator,
    EnglishNameValidator,
    BilingualNameValidator
)

# Use bilingual validator for flexibility
class Person(models.Model):
    name = models.CharField(
        max_length=100,
        validators=[BilingualNameValidator()]
    )
```

### Phone Number Normalization

```python
from .validators import normalize_phone_number, format_phone_for_display

# In your form or view
phone = '138-0013-8000'
normalized = normalize_phone_number(phone, country_code='86')
# Result: '+8613800138000'

# For display
display_phone = format_phone_for_display(normalized, language='zh')
# Result: '138-0013-8000'
```

---

## Forms

### Bilingual Form Implementation

```python
from .bilingual_forms import BilingualModelForm

class ProjectForm(BilingualModelForm):
    class Meta:
        model = Project
        fields = [
            'name_en', 'name_zh',
            'description_en', 'description_zh',
            'project_code', 'start_date', 'budget'
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configure based on language
        if self.current_lang.startswith('zh'):
            # Prioritize Chinese fields
            self.fields['name_zh'].required = True
            self.fields['name_en'].required = False
            self.fields['name_en'].widget = forms.HiddenInput()
        else:
            # Prioritize English fields
            self.fields['name_en'].required = True
            self.fields['name_zh'].required = False
            self.fields['name_zh'].widget = forms.HiddenInput()
```

### Usage in Views

```python
from django.views.generic import CreateView
from django.utils.translation import get_language

class ProjectCreateView(CreateView):
    model = Project
    form_class = ProjectForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['language'] = get_language()  # Pass current language
        return kwargs
```

---

## Models

### Using Bilingual Model Mixin

```python
from .mixins import BilingualModel, TimestampMixin

class Project(BilingualModel, TimestampMixin):
    """Project with bilingual support"""

    # Bilingual fields
    name_en = models.CharField(max_length=200)
    name_zh = models.CharField(max_length=200)
    description_en = models.TextField(blank=True)
    description_zh = models.TextField(blank=True)

    # Language-neutral fields
    project_code = models.CharField(max_length=50, unique=True)
    start_date = models.DateField()
    end_date = models.DateField()
    budget = models.DecimalField(max_digits=12, decimal_places=2)

    # Inherited from TimestampMixin:
    # - created_at
    # - updated_at

    def __str__(self):
        # BilingualModel provides smart __str__
        return self.name  # Returns name in current language

    class Meta:
        verbose_name = _('Project')
        verbose_name_plural = _('Projects')
```

### Querying Bilingual Models

```python
from django.utils.translation import get_language, override

# Query in current language
projects = Project.objects.all()
for project in projects:
    print(project.name)  # Returns name in current language

# Query in specific language
with override('zh-hans'):
    for project in projects:
        print(project.name)  # Returns Chinese name

# Raw field access
project = Project.objects.first()
print(project.name_en)  # Always English
print(project.name_zh)  # Always Chinese

# Search in specific language
Project.objects.filter(name_en__icontains='test')
Project.objects.filter(name_zh__icontains='测试')
```

---

## Serializers

### Bilingual API Serializers

```python
from .bilingual_serializers import BilingualSerializerMixin
from rest_framework import serializers

class ProjectSerializer(BilingualSerializerMixin, serializers.ModelSerializer):
    # Read-only fields in current language
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)

    # Write fields for both languages
    name_en = serializers.CharField(write_only=True, required=False)
    name_zh = serializers.CharField(write_only=True, required=False)
    description_en = serializers.CharField(write_only=True, required=False)
    description_zh = serializers.CharField(write_only=True, required=False)

    class Meta:
        model = Project
        fields = [
            'id', 'project_code',
            'name', 'description',  # Auto language-switching
            'name_en', 'name_zh',
            'description_en', 'description_zh',
            'start_date', 'end_date', 'budget'
        ]
        bilingual_fields = ['name', 'description']
```

### API View with Language Context

```python
from rest_framework import viewsets
from rest_framework.decorators import action

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Add language from query param or header
        context['language'] = self.request.query_params.get(
            'lang',
            self.request.META.get('HTTP_ACCEPT_LANGUAGE', 'en').split(',')[0]
        )
        return context
```

---

## Views

### Language Detection and Storage

```python
# views.py
from django.utils.translation import get_language, activate
from django.views.generic import TemplateView

class LanguageAwareView(TemplateView):
    def dispatch(self, request, *args, **kwargs):
        # Detect language from various sources
        lang = (
            request.GET.get('lang') or  # Query parameter
            request.session.get('django_language') or  # Session
            get_language()  # Django default
        )

        # Activate language
        activate(lang)

        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_language'] = get_language()
        return context
```

### Language Switching View

```python
from django.views.generic import View
from django.http import HttpResponseRedirect
from django.utils.translation import activate

class SetLanguageView(View):
    """Custom language switching view"""

    def post(self, request):
        language = request.POST.get('language', 'en')
        next_url = request.POST.get('next', '/')

        # Validate language
        from django.conf import settings
        if language in dict(settings.LANGUAGES):
            # Store in session
            request.session['django_language'] = language

            # Activate for current request
            activate(language)

            # Store in user profile if authenticated
            if request.user.is_authenticated:
                request.user.preferred_language = language
                request.user.save(update_fields=['preferred_language'])

        return HttpResponseRedirect(next_url)
```

---

## Templates

### Template Internationalization

```django
{% load i18n %}

{# Language switcher #}
<div class="language-switcher">
  <form method="post" action="{% url 'set_language' %}">
    {% csrf_token %}
    <input name="next" type="hidden" value="{{ request.get_full_path }}" />

    <button type="submit" name="language" value="en"
            class="{% if LANGUAGE_CODE == 'en' %}active{% endif %}">
      English
    </button>

    <button type="submit" name="language" value="zh-hans"
            class="{% if LANGUAGE_CODE == 'zh-hans' %}active{% endif %}">
      简体中文
    </button>
  </form>
</div>

{# Display bilingual content #}
<h1>{{ project.name }}</h1>  {# Auto language-switching #}
<p>{{ project.description }}</p>

{# Translated static text #}
<label>{% trans "Project Code" %}:</label>
<span>{{ project.project_code }}</span>

{# Formatted dates based on language #}
{% if LANGUAGE_CODE == 'zh-hans' %}
  {{ project.start_date|date:"Y年n月j日" }}
{% else %}
  {{ project.start_date|date:"M d, Y" }}
{% endif %}

{# Phone number display #}
<div class="phone">
  {% if LANGUAGE_CODE == 'zh-hans' %}
    {{ contact.phone|format_phone_zh }}
  {% else %}
    {{ contact.phone|format_phone_intl }}
  {% endif %}
</div>
```

### Custom Template Tags

```python
# templatetags/bilingual_filters.py
from django import template
from project_management.validators import format_phone_for_display

register = template.Library()

@register.filter
def format_phone(value, language='en'):
    """Format phone number for display"""
    return format_phone_for_display(value, language)

@register.filter
def bilingual_field(obj, field_name):
    """Get bilingual field in current language"""
    if hasattr(obj, 'get_bilingual_field'):
        return obj.get_bilingual_field(field_name)
    return ''
```

---

## Testing

### Test Structure

```python
# tests/test_bilingual.py
from django.test import TestCase, override_settings
from django.utils.translation import override
from ..models import Project

class BilingualModelTest(TestCase):
    def setUp(self):
        self.project = Project.objects.create(
            name_en='Test Project',
            name_zh='测试项目',
            project_code='TEST001',
        )

    def test_language_switching(self):
        """Test automatic language switching"""
        with override('en'):
            self.assertEqual(self.project.name, 'Test Project')

        with override('zh-hans'):
            self.assertEqual(self.project.name, '测试项目')

    def test_fallback_to_english(self):
        """Test fallback when Chinese not provided"""
        project = Project.objects.create(
            name_en='English Only',
            name_zh='',
            project_code='TEST002',
        )

        with override('zh-hans'):
            self.assertEqual(project.name, 'English Only')
```

### Validator Tests

```python
# tests/test_validators.py
class ValidatorTest(TestCase):
    def test_chinese_phone_validation(self):
        """Test Chinese phone validator"""
        from ..validators import ChinesePhoneValidator

        validator = ChinesePhoneValidator()

        # Valid
        validator('13800138000')  # Should not raise

        # Invalid
        with self.assertRaises(ValidationError):
            validator('12345678901')
```

### Form Tests

```python
class BilingualFormTest(TestCase):
    def test_form_with_language_context(self):
        """Test form respects language context"""
        with override('zh-hans'):
            form = ProjectForm(language='zh-hans')
            self.assertTrue(form.fields['name_zh'].required)
            self.assertFalse(form.fields['name_en'].required)
```

---

## Cultural Considerations

### 1. Name Order

**English**: First Name + Last Name
```python
full_name = f"{first_name} {last_name}"  # John Smith
```

**Chinese**: Last Name + First Name (姓 + 名)
```python
full_name = f"{last_name}{first_name}"  # 张三 (Zhang San)
```

### 2. Phone Format

**English/US**: `+1-555-123-4567`
**Chinese**: `138-0013-8000` or `+86 138 0013 8000`

### 3. Date Format

**English (US)**: `MM/DD/YYYY` → `12/25/2024`
**English (UK/ISO)**: `DD/MM/YYYY` or `YYYY-MM-DD`
**Chinese**: `YYYY年MM月DD日` → `2024年12月25日`

```python
# In templates
{% if LANGUAGE_CODE == 'zh-hans' %}
  {{ date|date:"Y年n月j日" }}
{% else %}
  {{ date|date:"M d, Y" }}
{% endif %}
```

### 4. Address Format

**English**: Street → City → State → Country
```
123 Main Street
New York, NY 10001
USA
```

**Chinese**: Country → Province → City → District → Street
```
中国
北京市
朝阳区
建国路123号
```

### 5. Currency Display

**English**: `$1,234.56`
**Chinese**: `¥1,234.56` or `1234.56元`

```python
from babel.numbers import format_currency
from django.utils.translation import get_language

def format_price(amount):
    lang = get_language()
    if lang.startswith('zh'):
        return format_currency(amount, 'CNY', locale='zh_CN')
    return format_currency(amount, 'USD', locale='en_US')
```

---

## Best Practices

### 1. Always Store Dates as Datetime Objects

```python
# Good
start_date = models.DateField()

# Bad - storing formatted string
start_date_str = models.CharField(max_length=50)  # Don't do this
```

### 2. Normalize Phone Numbers on Save

```python
from .validators import normalize_phone_number

class Contact(models.Model):
    phone = models.CharField(max_length=20)

    def save(self, *args, **kwargs):
        if self.phone:
            self.phone = normalize_phone_number(self.phone)
        super().save(*args, **kwargs)
```

### 3. Provide Both Language Versions in Forms

```python
# Show both fields in admin/forms for content entry
class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['name_en', 'name_zh', 'description_en', 'description_zh']
```

### 4. Use Language Context in Tests

```python
from django.utils.translation import override

def test_with_language():
    with override('zh-hans'):
        # Test Chinese version
        pass

    with override('en'):
        # Test English version
        pass
```

### 5. Implement Fallbacks

```python
@property
def name(self):
    """Get name with fallback"""
    lang = get_language()
    if lang.startswith('zh'):
        return self.name_zh or self.name_en
    return self.name_en or self.name_zh
```

---

## Quick Reference Commands

```bash
# Create messages for translation
python manage.py makemessages -l zh_Hans

# Compile messages
python manage.py compilemessages

# Run tests
python manage.py test project_management.tests

# Create migration for bilingual fields
python manage.py makemigrations project_management

# Apply migrations
python manage.py migrate
```

---

## Example: Complete Bilingual Model

```python
from django.db import models
from django.utils.translation import gettext_lazy as _
from .mixins import BilingualModel, TimestampMixin
from .validators import normalize_phone_number

class Employee(BilingualModel, TimestampMixin):
    """Employee with full bilingual support"""

    # Bilingual fields
    name_en = models.CharField(max_length=100, verbose_name="Name (English)")
    name_zh = models.CharField(max_length=100, verbose_name="姓名(中文)")

    position_en = models.CharField(max_length=100)
    position_zh = models.CharField(max_length=100)

    # Language-neutral fields
    employee_id = models.CharField(max_length=20, unique=True)
    email = models.EmailField()
    phone = models.CharField(max_length=20)

    # Chinese-specific field
    id_card = models.CharField(
        max_length=18,
        blank=True,
        validators=[ChineseIDCardValidator()]
    )

    # Metadata
    hire_date = models.DateField()
    salary = models.DecimalField(max_digits=10, decimal_places=2)

    def save(self, *args, **kwargs):
        # Normalize phone on save
        if self.phone:
            self.phone = normalize_phone_number(self.phone)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name  # BilingualModel handles language switching

    class Meta:
        verbose_name = _('Employee')
        verbose_name_plural = _('Employees')
        ordering = ['employee_id']
```

---

## Conclusion

This implementation provides:

- ✅ Separate field storage for bilingual content
- ✅ Cultural-aware validation (phone, ID, names, dates)
- ✅ Automatic language switching
- ✅ Consistent data normalization
- ✅ Comprehensive testing
- ✅ Easy-to-use APIs and forms
- ✅ Template support with proper formatting

The system is production-ready and handles the complexities of bilingual data management while maintaining data integrity and user experience.
