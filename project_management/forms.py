"""
Forms for Project Management app
Now with bilingual support for English and Simplified Chinese
"""

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _, get_language
from django.utils import timezone

from .models import Project, Task, ProjectMember
from .bilingual_forms import BilingualFormMixin


class ProjectForm(BilingualFormMixin, forms.ModelForm):
    """
    Form for creating and editing projects
    Now with bilingual support - displays fields based on current language
    """

    class Meta:
        model = Project
        fields = [
            'name_en',
            'name_zh',
            'description_en',
            'description_zh',
            'project_code',
            'start_date',
            'end_date',
            'status',
            'priority',
            'budget',
            'default_view',
            'primary_language',
        ]
        widgets = {
            'name_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter project name (English)',
            }),
            'name_zh': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '输入项目名称（中文）',
            }),
            'description_en': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter project description (English)',
                'rows': 4,
            }),
            'description_zh': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '输入项目描述（中文）',
                'rows': 4,
            }),
            'project_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., PROJ-2025-001',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select',
            }),
            'budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
            }),
            'default_view': forms.Select(attrs={
                'class': 'form-select',
            }),
        }
        help_texts = {
            'project_code': _('Unique identifier for the project'),
            'budget': _('Total budget allocated for this project'),
            'default_view': _('Choose the default view when opening this project'),
        }

    def clean_project_code(self):
        """
        Validate that project code is unique
        """
        project_code = self.cleaned_data.get('project_code')

        # Check if another project with this code exists
        queryset = Project.objects.filter(project_code=project_code)

        # If editing, exclude current project
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise ValidationError(
                _('A project with this code already exists.')
            )

        return project_code

    def clean(self):
        """
        Validate date ranges and other cross-field validations
        """
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')

        # Validate end date is after start date
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError(
                    _('End date must be after start date.')
                )

        # Validate budget is positive
        budget = cleaned_data.get('budget')
        if budget is not None and budget < 0:
            raise ValidationError(
                _('Budget must be a positive number.')
            )

        return cleaned_data


class TaskForm(BilingualFormMixin, forms.ModelForm):
    """
    Form for creating and editing tasks
    Now with bilingual support - displays fields based on current language
    """

    class Meta:
        model = Task
        fields = [
            'title_en',
            'title_zh',
            'description_en',
            'description_zh',
            'parent_task',
            'status',
            'priority',
            'start_date',
            'end_date',
            'due_date',
            'duration',
            'progress',
            'is_milestone',
            'estimated_hours',
            'assigned_to',
            'primary_language',
        ]
        widgets = {
            'title_en': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task title (English)',
            }),
            'title_zh': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '输入任务标题（中文）',
            }),
            'description_en': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Enter task description (English)',
                'rows': 3,
            }),
            'description_zh': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': '输入任务描述（中文）',
                'rows': 3,
            }),
            'parent_task': forms.Select(attrs={
                'class': 'form-select',
            }),
            'status': forms.Select(attrs={
                'class': 'form-select',
            }),
            'priority': forms.Select(attrs={
                'class': 'form-select',
            }),
            'start_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'end_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'due_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date',
            }),
            'duration': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
            }),
            'progress': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
            }),
            'is_milestone': forms.CheckboxInput(attrs={
                'class': 'form-check-input',
            }),
            'estimated_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.5',
            }),
            'assigned_to': forms.SelectMultiple(attrs={
                'class': 'form-select',
                'size': '5',
            }),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Make duration and progress optional (they have defaults in the model)
        if 'duration' in self.fields:
            self.fields['duration'].required = False
        if 'progress' in self.fields:
            self.fields['progress'].required = False

        # Filter parent_task to only show tasks from same project
        if project:
            self.fields['parent_task'].queryset = Task.objects.filter(
                project=project
            ).exclude(pk=self.instance.pk if self.instance.pk else None)

            # Filter assigned_to to only show project members
            self.fields['assigned_to'].queryset = project.team_members.all()

    def clean(self):
        """
        Validate task data
        """
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        parent_task = cleaned_data.get('parent_task')

        # Validate end date is after start date
        if start_date and end_date:
            if end_date < start_date:
                raise ValidationError(
                    _('End date must be after start date.')
                )

        # Prevent circular parent relationships
        if parent_task and self.instance.pk:
            current_parent = parent_task
            while current_parent:
                if current_parent.pk == self.instance.pk:
                    raise ValidationError(
                        _('Task cannot be its own parent (circular dependency detected).')
                    )
                current_parent = current_parent.parent_task

        return cleaned_data


class ProjectMemberForm(forms.ModelForm):
    """
    Form for adding team members to a project
    """

    class Meta:
        model = ProjectMember
        fields = ['user', 'role']
        widgets = {
            'user': forms.Select(attrs={
                'class': 'form-select',
            }),
            'role': forms.Select(attrs={
                'class': 'form-select',
            }),
        }

    def __init__(self, *args, project=None, **kwargs):
        super().__init__(*args, **kwargs)

        # Filter out users who are already members and only show users with project_management access
        if project:
            existing_members = project.team_members.all()
            from django.contrib.auth import get_user_model
            from django.db.models import Q
            User = get_user_model()

            # Only show users who:
            # 1. Are NOT already members of this project
            # 2. Have 'project_management' in their apps_access field
            self.fields['user'].queryset = User.objects.filter(
                apps_access__contains='project_management'
            ).exclude(
                id__in=existing_members.values_list('id', flat=True)
            ).order_by('email')
