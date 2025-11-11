"""
Mixins for bilingual model support
"""
from django.db import models
from django.utils.translation import get_language, gettext_lazy as _


class BilingualFieldMixin:
    """
    Mixin to provide bilingual field access
    Automatically returns the correct language version based on current language
    """

    def get_bilingual_field(self, field_base_name):
        """
        Get the correct language version of a field

        Args:
            field_base_name: Base name of the field (e.g., 'name', 'description')

        Returns:
            Value in the current language, falling back to English
        """
        current_lang = get_language()

        # Map language codes to field suffixes
        lang_suffix = '_zh' if current_lang.startswith('zh') else '_en'

        # Try to get the field value in current language
        field_name = f"{field_base_name}{lang_suffix}"
        value = getattr(self, field_name, None)

        # Fallback to English if current language is empty
        if not value and lang_suffix == '_zh':
            value = getattr(self, f"{field_base_name}_en", None)

        # Fallback to Chinese if English is empty
        if not value and lang_suffix == '_en':
            value = getattr(self, f"{field_base_name}_zh", None)

        return value or ''

    @property
    def name(self):
        """Get name in current language"""
        if hasattr(self, 'name_en') or hasattr(self, 'name_zh'):
            return self.get_bilingual_field('name')
        return getattr(self, '_name', '')

    @property
    def description(self):
        """Get description in current language"""
        if hasattr(self, 'description_en') or hasattr(self, 'description_zh'):
            return self.get_bilingual_field('description')
        return getattr(self, '_description', '')

    @property
    def title(self):
        """Get title in current language"""
        if hasattr(self, 'title_en') or hasattr(self, 'title_zh'):
            return self.get_bilingual_field('title')
        return getattr(self, '_title', '')


class BilingualModel(models.Model, BilingualFieldMixin):
    """
    Abstract base model for bilingual content
    Provides common bilingual fields and methods
    """

    class Meta:
        abstract = True

    def __str__(self):
        """Return string representation in current language"""
        if hasattr(self, 'name_en') or hasattr(self, 'name_zh'):
            return self.name or str(self.pk)
        if hasattr(self, 'title_en') or hasattr(self, 'title_zh'):
            return self.title or str(self.pk)
        return super().__str__()

    def get_translated_field(self, field_name, language=None):
        """
        Get a specific field in a specific language

        Args:
            field_name: Base field name
            language: Language code ('en', 'zh', 'zh-hans'), None for current

        Returns:
            Field value in requested language
        """
        if language is None:
            language = get_language()

        suffix = '_zh' if language.startswith('zh') else '_en'
        return getattr(self, f"{field_name}{suffix}", '')

    def set_translated_field(self, field_name, value, language=None):
        """
        Set a specific field in a specific language

        Args:
            field_name: Base field name
            value: Value to set
            language: Language code, None for current
        """
        if language is None:
            language = get_language()

        suffix = '_zh' if language.startswith('zh') else '_en'
        setattr(self, f"{field_name}{suffix}", value)


class TimestampMixin(models.Model):
    """
    Mixin to add created/updated timestamp fields
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Updated At')
    )

    class Meta:
        abstract = True


class UserTrackingMixin(models.Model):
    """
    Mixin to track which user created/modified a record
    """
    created_by = models.ForeignKey(
        'authentication.CompanyUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_created',
        verbose_name=_('Created By')
    )
    updated_by = models.ForeignKey(
        'authentication.CompanyUser',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='%(class)s_updated',
        verbose_name=_('Updated By')
    )

    class Meta:
        abstract = True


class SoftDeleteMixin(models.Model):
    """
    Mixin to add soft delete functionality
    """
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_('Is Deleted')
    )
    deleted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Deleted At')
    )

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard=False):
        """
        Soft delete by default, pass hard=True for actual deletion
        """
        if hard:
            return super().delete(using=using, keep_parents=keep_parents)

        from django.utils import timezone
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=['is_deleted', 'deleted_at'])

    def restore(self):
        """Restore a soft-deleted object"""
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=['is_deleted', 'deleted_at'])
