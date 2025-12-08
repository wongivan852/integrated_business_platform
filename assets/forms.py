from django import forms
from .models import Asset


class AssetForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['name', 'description', 'category', 'serial_number', 'model_number', 
                  'manufacturer', 'purchase_date', 'purchase_value', 'current_value', 
                  'current_location', 'responsible_person', 'primary_user', 'condition', 
                  'status', 'notes', 'photo', 'document']
        widgets = {
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.txt'
            }),
            'description': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'photo': 'Upload an image file (JPG, PNG, etc.) for this asset',
            'document': 'Upload PDF, Word, Excel or other document files',
        }


class AssetCreateForm(forms.ModelForm):
    class Meta:
        model = Asset
        fields = ['asset_id', 'name', 'description', 'category', 'serial_number', 
                  'model_number', 'manufacturer', 'purchase_date', 'purchase_value', 
                  'current_value', 'current_location', 'responsible_person', 'primary_user', 
                  'condition', 'photo', 'document']
        widgets = {
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.doc,.docx,.xls,.xlsx,.txt'
            }),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
        help_texts = {
            'photo': 'Upload an image file (JPG, PNG, etc.) for this asset',
            'document': 'Upload PDF, Word, Excel or other document files',
        }
