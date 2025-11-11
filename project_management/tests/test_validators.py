"""
Tests for custom validators and bilingual functionality
"""
from django.test import TestCase
from django.core.exceptions import ValidationError
from django.utils import translation
from ..validators import (
    ChinesePhoneValidator,
    InternationalPhoneValidator,
    ChineseIDCardValidator,
    ChineseNameValidator,
    EnglishNameValidator,
    BilingualNameValidator,
    normalize_phone_number,
    format_phone_for_display,
    validate_date_format,
)


class ChinesePhoneValidatorTest(TestCase):
    """Test Chinese phone number validation"""

    def setUp(self):
        self.validator = ChinesePhoneValidator()

    def test_valid_chinese_mobile_numbers(self):
        """Test valid Chinese mobile numbers"""
        valid_numbers = [
            '13800138000',
            '13912345678',
            '15012345678',
            '17712345678',
            '19912345678',
            '138-0013-8000',  # With separators
            '139 1234 5678',  # With spaces
        ]

        for number in valid_numbers:
            with self.subTest(number=number):
                try:
                    self.validator(number)
                except ValidationError:
                    self.fail(f"Valid number {number} was rejected")

    def test_invalid_chinese_mobile_numbers(self):
        """Test invalid Chinese mobile numbers"""
        invalid_numbers = [
            '12345678901',  # Starts with 1, but second digit not in [3-9]
            '9876543210',   # Doesn't start with 1
            '138001380',    # Too short
            '13800138000123',  # Too long
            'abcdefghijk',  # Not numeric
            '+8613800138000',  # Has country code
        ]

        for number in invalid_numbers:
            with self.subTest(number=number):
                with self.assertRaises(ValidationError):
                    self.validator(number)


class InternationalPhoneValidatorTest(TestCase):
    """Test international phone number validation"""

    def setUp(self):
        self.validator = InternationalPhoneValidator()

    def test_valid_international_numbers(self):
        """Test valid international numbers"""
        valid_numbers = [
            '+15551234567',
            '+8613800138000',
            '+447700900123',
            '15551234567',  # Without +
        ]

        for number in valid_numbers:
            with self.subTest(number=number):
                try:
                    self.validator(number)
                except ValidationError:
                    self.fail(f"Valid number {number} was rejected")

    def test_invalid_international_numbers(self):
        """Test invalid international numbers"""
        invalid_numbers = [
            'abc',
            '123',  # Too short
            '+' + '1' * 16,  # Too long
            '+0123456789',  # Starts with 0
        ]

        for number in invalid_numbers:
            with self.subTest(number=number):
                with self.assertRaises(ValidationError):
                    self.validator(number)


class ChineseIDCardValidatorTest(TestCase):
    """Test Chinese ID card validation"""

    def setUp(self):
        self.validator = ChineseIDCardValidator()

    def test_valid_id_cards(self):
        """Test valid ID card numbers"""
        valid_ids = [
            '110101199003078515',  # Valid checksum
            '44030219900307061X',  # Valid with X
        ]

        for id_card in valid_ids:
            with self.subTest(id_card=id_card):
                try:
                    self.validator(id_card)
                except ValidationError:
                    self.fail(f"Valid ID {id_card} was rejected")

    def test_invalid_id_cards(self):
        """Test invalid ID card numbers"""
        invalid_ids = [
            '12345678901234567',  # Too short
            '1234567890123456789',  # Too long
            'abcdefghijklmnopqr',  # Not numeric
            '110101199003078516',  # Invalid checksum
        ]

        for id_card in invalid_ids:
            with self.subTest(id_card=id_card):
                with self.assertRaises(ValidationError):
                    self.validator(id_card)


class NameValidatorTest(TestCase):
    """Test name validators"""

    def test_chinese_name_validator(self):
        """Test Chinese name validation"""
        validator = ChineseNameValidator()

        # Valid Chinese names
        valid_names = ['张三', '李四', '王小明', '欧阳锋']
        for name in valid_names:
            with self.subTest(name=name):
                try:
                    validator(name)
                except ValidationError:
                    self.fail(f"Valid name {name} was rejected")

        # Invalid Chinese names
        invalid_names = ['A', 'John', 'Zhang San', '张', '张三李四王']
        for name in invalid_names:
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    validator(name)

    def test_english_name_validator(self):
        """Test English name validation"""
        validator = EnglishNameValidator()

        # Valid English names
        valid_names = ['John', 'Mary Smith', "O'Connor", 'Jean-Pierre', 'Mary-Jane']
        for name in valid_names:
            with self.subTest(name=name):
                try:
                    validator(name)
                except ValidationError:
                    self.fail(f"Valid name {name} was rejected")

        # Invalid English names
        invalid_names = ['123', 'John@Smith', '张三', '']
        for name in invalid_names:
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    validator(name)

    def test_bilingual_name_validator(self):
        """Test bilingual name validation"""
        validator = BilingualNameValidator()

        # Valid names (both languages)
        valid_names = ['张三', '李四', 'John', 'Mary Smith', "O'Connor"]
        for name in valid_names:
            with self.subTest(name=name):
                try:
                    validator(name)
                except ValidationError:
                    self.fail(f"Valid name {name} was rejected")

        # Invalid names
        invalid_names = ['123', '', 'John@Smith']
        for name in invalid_names:
            with self.subTest(name=name):
                with self.assertRaises(ValidationError):
                    validator(name)


class PhoneNormalizationTest(TestCase):
    """Test phone number normalization"""

    def test_normalize_chinese_mobile(self):
        """Test Chinese mobile normalization"""
        self.assertEqual(
            normalize_phone_number('13800138000'),
            '+8613800138000'
        )
        self.assertEqual(
            normalize_phone_number('138-0013-8000'),
            '+8613800138000'
        )

    def test_normalize_us_number(self):
        """Test US number normalization"""
        self.assertEqual(
            normalize_phone_number('5551234567', '1'),
            '+15551234567'
        )

    def test_normalize_with_country_code(self):
        """Test normalization with explicit country code"""
        self.assertEqual(
            normalize_phone_number('1234567890', '86'),
            '+861234567890'
        )

    def test_format_for_display(self):
        """Test phone formatting for display"""
        # Chinese format
        self.assertEqual(
            format_phone_for_display('+8613800138000', 'zh'),
            '138-0013-8000'
        )

        # US format
        self.assertEqual(
            format_phone_for_display('+15551234567', 'en'),
            '+1-555-123-4567'
        )


class DateFormatValidationTest(TestCase):
    """Test date format validation"""

    def test_chinese_date_formats(self):
        """Test Chinese date format validation"""
        valid_formats = [
            '2024-01-15',
            '2024年01月15日',
            '2024年1月15日',
        ]

        for date_str in valid_formats:
            with self.subTest(date_str=date_str):
                self.assertTrue(
                    validate_date_format(date_str, 'zh'),
                    f"Valid Chinese date {date_str} was rejected"
                )

    def test_english_date_formats(self):
        """Test English date format validation"""
        valid_formats = [
            '01/15/2024',
            '2024-01-15',
            '1/15/2024',
        ]

        for date_str in valid_formats:
            with self.subTest(date_str=date_str):
                self.assertTrue(
                    validate_date_format(date_str, 'en'),
                    f"Valid English date {date_str} was rejected"
                )


class LanguageContextTest(TestCase):
    """Test language-aware functionality"""

    def test_validator_with_language_context(self):
        """Test validators respect language context"""
        # Test with Chinese context
        with translation.override('zh-hans'):
            phone = '13800138000'
            normalized = normalize_phone_number(phone)
            self.assertTrue(normalized.startswith('+86'))

        # Test with English context
        with translation.override('en'):
            phone = '5551234567'
            # Note: Auto-detection might treat this as US number
            normalized = normalize_phone_number(phone)
            self.assertTrue(normalized.startswith('+'))
