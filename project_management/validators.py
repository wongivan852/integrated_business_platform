"""
Custom validators for bilingual project management
Handles cultural-aware validation for Chinese and English inputs
"""
import re
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.core.validators import RegexValidator


class ChinesePhoneValidator:
    """
    Validates Chinese mobile phone numbers
    Format: 1[3-9]xxxxxxxxx (11 digits starting with 1[3-9])
    """
    message = _('Enter a valid Chinese phone number (e.g., 138-0013-8000)')
    code = 'invalid_chinese_phone'
    regex = re.compile(r'^1[3-9]\d{9}$')

    def __call__(self, value):
        # Remove common separators
        cleaned = re.sub(r'[-\s()]', '', str(value))

        if not self.regex.match(cleaned):
            raise ValidationError(self.message, code=self.code)


class InternationalPhoneValidator:
    """
    Validates international phone numbers in E.164 format
    Format: +[country code][number] (max 15 digits)
    """
    message = _('Enter a valid international phone number (e.g., +1-555-123-4567)')
    code = 'invalid_intl_phone'
    regex = re.compile(r'^\+?[1-9]\d{1,14}$')

    def __call__(self, value):
        # Remove common separators
        cleaned = re.sub(r'[-\s()]', '', str(value))

        if not self.regex.match(cleaned):
            raise ValidationError(self.message, code=self.code)


class ChineseIDCardValidator:
    """
    Validates Chinese ID card numbers (居民身份证)
    Format: 18 digits with checksum validation
    """
    message = _('Enter a valid Chinese ID card number (18 digits)')
    code = 'invalid_chinese_id'

    # Checksum weights and check codes
    WEIGHTS = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    CHECK_CODES = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']

    def __call__(self, value):
        value = str(value).upper()

        # Check length
        if len(value) != 18:
            raise ValidationError(self.message, code=self.code)

        # Check if first 17 digits are numeric
        if not value[:17].isdigit():
            raise ValidationError(self.message, code=self.code)

        # Validate checksum
        checksum = sum(int(value[i]) * self.WEIGHTS[i] for i in range(17)) % 11

        if value[17] != self.CHECK_CODES[checksum]:
            raise ValidationError(
                _('Invalid ID card checksum'),
                code='invalid_id_checksum'
            )


class ChineseNameValidator:
    """
    Validates Chinese names
    Typically 2-4 Chinese characters
    """
    message = _('Enter a valid Chinese name (2-4 Chinese characters)')
    code = 'invalid_chinese_name'
    regex = re.compile(r'^[\u4e00-\u9fa5]{2,4}$')

    def __call__(self, value):
        if not self.regex.match(str(value)):
            raise ValidationError(self.message, code=self.code)


class EnglishNameValidator:
    """
    Validates English names
    Letters, spaces, hyphens, and apostrophes allowed
    """
    message = _('Enter a valid English name')
    code = 'invalid_english_name'
    regex = re.compile(r"^[A-Za-z]+([\s'-][A-Za-z]+)*$")

    def __call__(self, value):
        if not self.regex.match(str(value)):
            raise ValidationError(self.message, code=self.code)


class BilingualNameValidator:
    """
    Validates names in both Chinese and English
    Accepts either format
    """
    def __call__(self, value):
        chinese_regex = re.compile(r'^[\u4e00-\u9fa5]{2,4}$')
        english_regex = re.compile(r"^[A-Za-z]+([\s'-][A-Za-z]+)*$")

        if not (chinese_regex.match(str(value)) or english_regex.match(str(value))):
            raise ValidationError(
                _('Enter a valid name in Chinese (2-4 characters) or English'),
                code='invalid_name'
            )


def normalize_phone_number(phone, country_code=None):
    """
    Normalize phone number to E.164 format

    Args:
        phone: Phone number string
        country_code: Country code (e.g., '86' for China, '1' for US)

    Returns:
        Normalized phone number in E.164 format
    """
    # Remove all non-digit characters
    digits = re.sub(r'\D', '', str(phone))

    # If already has country code (starts with +), return as is
    if phone.startswith('+'):
        return digits

    # Add country code if provided
    if country_code:
        # Remove leading 0 if present (common in some countries)
        if digits.startswith('0'):
            digits = digits[1:]
        return f"+{country_code}{digits}"

    # Chinese mobile number detection (starts with 1[3-9])
    if re.match(r'^1[3-9]\d{9}$', digits):
        return f"+86{digits}"

    # US number detection (10 digits)
    if len(digits) == 10:
        return f"+1{digits}"

    return f"+{digits}"


def format_phone_for_display(phone, language='en'):
    """
    Format phone number for display based on language/culture

    Args:
        phone: Phone number (preferably in E.164 format)
        language: 'en' or 'zh'

    Returns:
        Formatted phone number string
    """
    # Remove + and get digits
    digits = re.sub(r'\D', '', str(phone))

    # Chinese mobile format: 138-0013-8000
    if language == 'zh' and digits.startswith('86') and len(digits) == 13:
        number = digits[2:]  # Remove country code
        return f"{number[:3]}-{number[3:7]}-{number[7:]}"

    # US format: +1-555-123-4567
    if language == 'en' and digits.startswith('1') and len(digits) == 11:
        return f"+1-{digits[1:4]}-{digits[4:7]}-{digits[7:]}"

    # Generic format
    if phone.startswith('+'):
        return phone
    return f"+{digits}"


def validate_date_format(date_str, language='en'):
    """
    Validate date string format based on language

    Args:
        date_str: Date string
        language: 'en' or 'zh'

    Returns:
        bool: True if valid format
    """
    if language == 'zh':
        # Chinese format: YYYY-MM-DD or YYYY年MM月DD日
        patterns = [
            r'^\d{4}-\d{2}-\d{2}$',
            r'^\d{4}年\d{1,2}月\d{1,2}日$',
        ]
    else:
        # English formats: MM/DD/YYYY, DD/MM/YYYY, YYYY-MM-DD
        patterns = [
            r'^\d{1,2}/\d{1,2}/\d{4}$',
            r'^\d{4}-\d{2}-\d{2}$',
        ]

    return any(re.match(pattern, date_str) for pattern in patterns)


# Convenient validator instances
chinese_phone_validator = ChinesePhoneValidator()
intl_phone_validator = InternationalPhoneValidator()
chinese_id_validator = ChineseIDCardValidator()
chinese_name_validator = ChineseNameValidator()
english_name_validator = EnglishNameValidator()
bilingual_name_validator = BilingualNameValidator()
