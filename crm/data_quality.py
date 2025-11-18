"""
Data Quality Service for CRM System
Handles data validation, cleanup, and quality improvement
"""
import re
import logging
from typing import List, Optional, Dict, Any
from django.db import transaction, models
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Customer

logger = logging.getLogger('crm.data_quality')

class DataQualityService:
    """
    Service for improving and validating data quality in the CRM system
    """
    
    # Domain to country mapping for email-based country detection
    DOMAIN_COUNTRY_MAP = {
        # Major country-specific domains
        'gmail.com': None,  # Global service
        'outlook.com': None,  # Global service
        'hotmail.com': None,  # Global service
        'yahoo.com': None,  # Global service
        'qq.com': 'CN',
        '163.com': 'CN',
        '126.com': 'CN',
        'sina.com': 'CN',
        'sohu.com': 'CN',
        'yahoo.co.jp': 'JP',
        'yahoo.co.uk': 'GB',
        'yahoo.ca': 'CA',
        'yahoo.com.au': 'AU',
        'yandex.ru': 'RU',
        'mail.ru': 'RU',
        'rambler.ru': 'RU',
        't-online.de': 'DE',
        'web.de': 'DE',
        'gmx.de': 'DE',
        'orange.fr': 'FR',
        'laposte.net': 'FR',
        'wanadoo.fr': 'FR',
        'libero.it': 'IT',
        'tiscali.it': 'IT',
        'virgilio.it': 'IT',
        'uol.com.br': 'BR',
        'globo.com': 'BR',
        'terra.com.br': 'BR',
    }
    
    # Common email format issues and their fixes
    EMAIL_CORRECTIONS = {
        r'(\w+)\s+at\s+(\w+\.\w+)': r'\1@\2',  # "user at domain.com" -> "user@domain.com"
        r'(\w+)\[dot\](\w+)': r'\1.\2',  # "user[dot]domain" -> "user.domain"
        r'(\w+)\(at\)(\w+\.\w+)': r'\1@\2',  # "user(at)domain.com" -> "user@domain.com"
        r'(\w+)_at_(\w+\.\w+)': r'\1@\2',  # "user_at_domain.com" -> "user@domain.com"
        r'\.com\.': '.com',  # Remove duplicate .com
        r'\.co\.uk\.': '.co.uk',  # Fix UK domains
        r'@+': '@',  # Remove duplicate @ symbols
        r'\.+': '.',  # Remove duplicate dots
    }
    
    def __init__(self):
        self.validation_results = {
            'processed': 0,
            'fixed': 0,
            'failed': 0,
            'errors': []
        }
    
    def clean_email_address(self, email: str) -> Optional[str]:
        """
        Clean and validate email addresses with common fixes
        """
        if not email or not isinstance(email, str):
            return None
        
        # Basic cleanup
        email = email.strip().lower()
        
        # Remove spaces around @
        email = re.sub(r'\s*@\s*', '@', email)
        
        # Apply common corrections
        for pattern, replacement in self.EMAIL_CORRECTIONS.items():
            email = re.sub(pattern, replacement, email, flags=re.IGNORECASE)
        
        # Validate the cleaned email
        try:
            validate_email(email)
            return email
        except ValidationError:
            return None
    
    def detect_country_from_email(self, email: str) -> Optional[str]:
        """
        Attempt to detect country from email domain
        """
        if not email or '@' not in email:
            return None
        
        try:
            domain = email.split('@')[1].lower()
            
            # Check direct domain mapping
            if domain in self.DOMAIN_COUNTRY_MAP:
                return self.DOMAIN_COUNTRY_MAP[domain]
            
            # Check for country code TLDs
            if domain.endswith('.cn'):
                return 'CN'
            elif domain.endswith('.jp'):
                return 'JP'
            elif domain.endswith('.uk') or domain.endswith('.co.uk'):
                return 'GB'
            elif domain.endswith('.de'):
                return 'DE'
            elif domain.endswith('.fr'):
                return 'FR'
            elif domain.endswith('.it'):
                return 'IT'
            elif domain.endswith('.es'):
                return 'ES'
            elif domain.endswith('.nl'):
                return 'NL'
            elif domain.endswith('.au'):
                return 'AU'
            elif domain.endswith('.ca'):
                return 'CA'
            elif domain.endswith('.in'):
                return 'IN'
            elif domain.endswith('.br'):
                return 'BR'
            elif domain.endswith('.ru'):
                return 'RU'
            elif domain.endswith('.za'):
                return 'ZA'
            elif domain.endswith('.sg'):
                return 'SG'
            elif domain.endswith('.hk'):
                return 'HK'
            elif domain.endswith('.tw'):
                return 'TW'
            elif domain.endswith('.kr'):
                return 'KR'
            elif domain.endswith('.th'):
                return 'TH'
            elif domain.endswith('.my'):
                return 'MY'
            elif domain.endswith('.ph'):
                return 'PH'
            elif domain.endswith('.id'):
                return 'ID'
            elif domain.endswith('.vn'):
                return 'VN'
            
        except Exception as e:
            logger.debug(f"Error detecting country from email {email}: {str(e)}")
        
        return None
    
    def fix_failed_records(self) -> Dict[str, Any]:
        """
        Attempt to fix failed import records by improving email validation
        and filling missing data
        """
        results = {
            'processed': 0,
            'fixed': 0,
            'updated': 0,
            'still_invalid': 0,
            'errors': []
        }
        
        try:
            # Find customers with problematic emails or missing data
            problematic_customers = Customer.objects.filter(
                models.Q(email_primary__isnull=True) |
                models.Q(email_primary__exact='') |
                models.Q(country_region__isnull=True) |
                models.Q(country_region__exact='') |
                models.Q(email_primary__contains=' ') |  # Emails with spaces
                models.Q(email_primary__contains='[') |  # Malformed emails
                models.Q(email_primary__contains='(') |
                models.Q(email_primary__regex=r'.*\s+at\s+.*')  # "user at domain" format
            )
            
            results['processed'] = problematic_customers.count()
            logger.info(f"Found {results['processed']} customers with data quality issues")
            
            with transaction.atomic():
                for customer in problematic_customers:
                    fixed_customer = False
                    
                    # Fix email if problematic
                    if customer.email_primary:
                        cleaned_email = self.clean_email_address(customer.email_primary)
                        if cleaned_email and cleaned_email != customer.email_primary:
                            customer.email_primary = cleaned_email
                            fixed_customer = True
                            logger.info(f"Fixed email for customer {customer.id}: {cleaned_email}")
                    
                    # Try to fill missing country from email
                    if not customer.country_region and customer.email_primary:
                        detected_country = self.detect_country_from_email(customer.email_primary)
                        if detected_country:
                            customer.country_region = detected_country
                            fixed_customer = True
                            logger.info(f"Detected country {detected_country} for customer {customer.id}")
                    
                    # Save if any fixes were made
                    if fixed_customer:
                        try:
                            customer.save()
                            results['fixed'] += 1
                        except Exception as e:
                            results['errors'].append(f"Failed to save customer {customer.id}: {str(e)}")
                            results['still_invalid'] += 1
            
            logger.info(f"Data quality fix completed: {results['fixed']} customers fixed")
            
        except Exception as e:
            error_msg = f"Data quality fix failed: {str(e)}"
            logger.error(error_msg)
            results['errors'].append(error_msg)
        
        return results
    
    def validate_and_enhance_customer_data(self, customer_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and enhance customer data before import/save
        """
        enhanced_data = customer_data.copy()
        
        # Clean email
        if 'email_primary' in enhanced_data and enhanced_data['email_primary']:
            cleaned_email = self.clean_email_address(enhanced_data['email_primary'])
            if cleaned_email:
                enhanced_data['email_primary'] = cleaned_email
            else:
                enhanced_data['email_primary'] = None  # Mark as invalid
        
        # Detect country from email if missing
        if (not enhanced_data.get('country_region') and 
            enhanced_data.get('email_primary')):
            detected_country = self.detect_country_from_email(enhanced_data['email_primary'])
            if detected_country:
                enhanced_data['country_region'] = detected_country
        
        # Clean phone numbers (basic cleanup)
        for phone_field in ['phone_primary', 'phone_secondary', 'whatsapp_number']:
            if phone_field in enhanced_data and enhanced_data[phone_field]:
                phone = enhanced_data[phone_field]
                # Remove common separators and spaces
                cleaned_phone = re.sub(r'[\s\-\(\)]+', '', str(phone))
                if cleaned_phone != phone:
                    enhanced_data[phone_field] = cleaned_phone
        
        # Clean names (remove extra spaces, proper case)
        for name_field in ['first_name', 'last_name', 'preferred_name']:
            if name_field in enhanced_data and enhanced_data[name_field]:
                name = str(enhanced_data[name_field]).strip()
                # Remove multiple spaces
                name = re.sub(r'\s+', ' ', name)
                # Proper case (careful with names like McDonald)
                if name.lower() != name and name.upper() != name:
                    pass  # Already properly cased
                else:
                    name = name.title()
                enhanced_data[name_field] = name
        
        return enhanced_data
    
    def get_data_quality_report(self) -> Dict[str, Any]:
        """
        Generate a comprehensive data quality report
        """
        from django.db import models
        
        report = {
            'timestamp': timezone.now().isoformat(),
            'total_customers': Customer.objects.count(),
            'issues': {},
            'quality_scores': {}
        }
        
        # Email issues
        report['issues']['invalid_emails'] = Customer.objects.filter(
            models.Q(email_primary__isnull=True) |
            models.Q(email_primary__exact='') |
            models.Q(email_primary__contains=' ') |
            models.Q(email_primary__regex=r'.*[^\w@\.\-].*')  # Invalid characters
        ).count()
        
        # Missing country data
        report['issues']['missing_countries'] = Customer.objects.filter(
            models.Q(country_region__isnull=True) |
            models.Q(country_region__exact='')
        ).count()
        
        # Missing names
        report['issues']['missing_first_names'] = Customer.objects.filter(
            models.Q(first_name__isnull=True) |
            models.Q(first_name__exact='')
        ).count()
        
        report['issues']['missing_last_names'] = Customer.objects.filter(
            models.Q(last_name__isnull=True) |
            models.Q(last_name__exact='')
        ).count()
        
        # Missing phone numbers
        report['issues']['missing_phones'] = Customer.objects.filter(
            models.Q(phone_primary__isnull=True) |
            models.Q(phone_primary__exact='')
        ).count()
        
        # Calculate quality scores
        total = report['total_customers']
        if total > 0:
            report['quality_scores']['email_completeness'] = round(
                ((total - report['issues']['invalid_emails']) / total) * 100, 2
            )
            report['quality_scores']['country_completeness'] = round(
                ((total - report['issues']['missing_countries']) / total) * 100, 2
            )
            report['quality_scores']['name_completeness'] = round(
                ((total - report['issues']['missing_first_names'] - report['issues']['missing_last_names']) / (total * 2)) * 100, 2
            )
            report['quality_scores']['phone_completeness'] = round(
                ((total - report['issues']['missing_phones']) / total) * 100, 2
            )
            
            # Overall quality score (weighted average)
            report['quality_scores']['overall'] = round(
                (report['quality_scores']['email_completeness'] * 0.4 +
                 report['quality_scores']['country_completeness'] * 0.2 +
                 report['quality_scores']['name_completeness'] * 0.3 +
                 report['quality_scores']['phone_completeness'] * 0.1), 2
            )
        
        return report


# Django management command integration
def run_data_quality_fixes():
    """
    Function to be called from management command or API endpoint
    """
    service = DataQualityService()
    return service.fix_failed_records()