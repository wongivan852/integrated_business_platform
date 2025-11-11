"""
Bilingual API serializers for REST API
"""
from rest_framework import serializers
from django.utils.translation import get_language
from .validators import normalize_phone_number, format_phone_for_display


class BilingualSerializerMixin:
    """
    Mixin for serializers that handle bilingual content
    Automatically returns fields in the correct language
    """

    def to_representation(self, instance):
        """
        Override to return language-specific fields
        """
        representation = super().to_representation(instance)
        current_lang = self.context.get('language') or get_language()

        # Get bilingual fields configuration
        bilingual_fields = getattr(self.Meta, 'bilingual_fields', [])

        for field_base_name in bilingual_fields:
            # Get the language-specific field value
            if hasattr(instance, 'get_bilingual_field'):
                value = instance.get_bilingual_field(field_base_name)
            else:
                # Manual field selection
                suffix = '_zh' if current_lang.startswith('zh') else '_en'
                field_name = f"{field_base_name}{suffix}"
                value = getattr(instance, field_name, '')

            # Add to representation
            representation[field_base_name] = value

            # Optionally include both languages
            if getattr(self.Meta, 'include_all_languages', False):
                representation[f"{field_base_name}_en"] = getattr(instance, f"{field_base_name}_en", '')
                representation[f"{field_base_name}_zh"] = getattr(instance, f"{field_base_name}_zh", '')

        return representation


class PhoneNumberField(serializers.CharField):
    """
    Custom field for phone numbers with automatic normalization
    """

    def __init__(self, country_code=None, **kwargs):
        self.country_code = country_code
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        """Normalize phone number on input"""
        value = super().to_internal_value(data)
        try:
            return normalize_phone_number(value, self.country_code)
        except Exception:
            raise serializers.ValidationError('Invalid phone number format')

    def to_representation(self, value):
        """Format phone number for display"""
        if not value:
            return value

        language = self.context.get('language') or get_language()
        lang_code = 'zh' if language.startswith('zh') else 'en'

        return format_phone_for_display(value, lang_code)


class BilingualProjectSerializer(BilingualSerializerMixin, serializers.Serializer):
    """
    Example serializer for bilingual project data
    """
    id = serializers.IntegerField(read_only=True)
    project_code = serializers.CharField(max_length=50)

    # Bilingual fields - will be handled by mixin
    name = serializers.CharField(read_only=True)
    description = serializers.CharField(read_only=True)

    # Individual language fields for writing
    name_en = serializers.CharField(max_length=200, required=False, write_only=True)
    name_zh = serializers.CharField(max_length=200, required=False, write_only=True)
    description_en = serializers.CharField(required=False, write_only=True)
    description_zh = serializers.CharField(required=False, write_only=True)

    # Language-neutral fields
    start_date = serializers.DateField()
    end_date = serializers.DateField()
    budget = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    status = serializers.CharField(max_length=20)
    priority = serializers.CharField(max_length=20)

    # Status and priority display names (translated)
    status_display = serializers.SerializerMethodField()
    priority_display = serializers.SerializerMethodField()

    class Meta:
        bilingual_fields = ['name', 'description']
        include_all_languages = False  # Set to True to include both languages in response

    def get_status_display(self, obj):
        """Get translated status display"""
        if hasattr(obj, 'get_status_display'):
            return obj.get_status_display()
        return obj.status

    def get_priority_display(self, obj):
        """Get translated priority display"""
        if hasattr(obj, 'get_priority_display'):
            return obj.get_priority_display()
        return obj.priority

    def validate(self, data):
        """Validate that at least one language version is provided"""
        name_en = data.get('name_en')
        name_zh = data.get('name_zh')

        if not name_en and not name_zh:
            raise serializers.ValidationError({
                'name': 'At least one language version of the name is required'
            })

        return data


class BilingualContactSerializer(BilingualSerializerMixin, serializers.Serializer):
    """
    Serializer for contact information with phone normalization
    """
    id = serializers.IntegerField(read_only=True)

    name = serializers.CharField(max_length=100)
    phone = PhoneNumberField()
    email = serializers.EmailField(required=False)
    address = serializers.CharField(required=False)

    # Language context
    preferred_language = serializers.ChoiceField(
        choices=[('en', 'English'), ('zh', 'Chinese')],
        default='en'
    )

    def create(self, validated_data):
        """Create with language context"""
        # In real implementation, save to database
        return validated_data

    def update(self, instance, validated_data):
        """Update with language context"""
        # In real implementation, update database
        for key, value in validated_data.items():
            setattr(instance, key, value)
        return instance


class LanguageContextMixin:
    """
    Mixin to add language context to serializer
    """

    def get_language(self):
        """Get language from context or request"""
        # Try context first
        if 'language' in self.context:
            return self.context['language']

        # Try from request
        request = self.context.get('request')
        if request:
            # Check query parameter
            lang = request.query_params.get('lang') or request.query_params.get('language')
            if lang:
                return lang

            # Check header
            lang = request.META.get('HTTP_ACCEPT_LANGUAGE', '').split(',')[0].split('-')[0]
            if lang:
                return lang

        # Default to current Django language
        return get_language()


class BilingualListSerializer(BilingualSerializerMixin, LanguageContextMixin, serializers.ListSerializer):
    """
    List serializer with bilingual support
    """

    def to_representation(self, data):
        """Add language context to child serializers"""
        language = self.get_language()

        # Set language context for all child serializers
        for item in data:
            self.child.context['language'] = language

        return super().to_representation(data)
