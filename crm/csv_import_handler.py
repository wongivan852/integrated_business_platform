import csv
import io
import re
from typing import Dict, List, Tuple, Any, Optional
from django.db import transaction
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from .models import Customer
import logging

logger = logging.getLogger(__name__)

class CSVImportHandler:
    """
    Robust CSV import handler for customer data with flexible field mapping
    and comprehensive validation.
    """
    
    # Common field name variations for flexible mapping
    FIELD_MAPPINGS = {
        'first_name': [
            'first_name', 'firstname', 'first', 'given_name', 'givenname',
            'fname', 'f_name', 'forename', 'christian_name'
        ],
        'middle_name': [
            'middle_name', 'middlename', 'middle', 'middle_initial', 
            'mi', 'm_name', 'second_name'
        ],
        'last_name': [
            'last_name', 'lastname', 'last', 'surname', 'family_name',
            'familyname', 'lname', 'l_name', 'sur_name'
        ],
        'preferred_name': [
            'preferred_name', 'preferredname', 'nickname', 'nick_name',
            'display_name', 'displayname', 'known_as', 'goes_by'
        ],
        'title': [
            'title', 'salutation', 'prefix', 'honorific'
        ],
        'name_suffix': [
            'suffix', 'name_suffix', 'jr_sr', 'generation'
        ],
        'email_primary': [
            'email', 'email_primary', 'primary_email', 'email_address',
            'email1', 'main_email', 'work_email', 'business_email',
            'emails', 'email_addresses', 'contact_email', 'e_mail'
        ],
        'email_secondary': [
            'email_secondary', 'secondary_email', 'email2', 'personal_email',
            'alt_email', 'alternative_email', 'backup_email'
        ],
        'phone_primary': [
            'phone', 'phone_number', 'phone_primary', 'primary_phone',
            'phone1', 'mobile', 'cell', 'mobile_number', 'contact_number'
        ],
        'phone_secondary': [
            'phone_secondary', 'secondary_phone', 'phone2', 'home_phone',
            'work_phone', 'office_phone', 'landline'
        ],
        'company_primary': [
            'company', 'company_name', 'organization', 'employer',
            'company_primary', 'current_company', 'workplace'
        ],
        'position_primary': [
            'position', 'job_title', 'title_work', 'role', 'designation',
            'position_primary', 'current_position', 'job_role'
        ],
        'country_region': [
            'country', 'country_region', 'nationality', 'region'
        ],
        'customer_type': [
            'customer_type', 'type', 'category', 'classification'
        ],
        'source': [
            'source', 'data_source', 'lead_source', 'acquisition_source',
            'how_found', 'found_us', 'marketing_source', 'channel'
        ],
        'referral_source': [
            'referral_source', 'referral', 'referred_by', 'referrer'
        ]
    }
    
    # Mandatory fields that must be present or mappable
    MANDATORY_FIELDS = ['last_name', 'email_primary']  # first_name is now optional
    
    # Customer type mappings for flexible input
    CUSTOMER_TYPE_MAPPINGS = {
        'individual': ['individual', 'personal', 'person', 'learner', 'student'],
        'corporate': ['corporate', 'company', 'business', 'organization', 'org'],
        'student': ['student', 'pupil', 'learner', 'academic'],
        'instructor': ['instructor', 'teacher', 'trainer', 'educator', 'faculty']
    }
    
    # Source mappings for flexible input
    SOURCE_MAPPINGS = {
        'website': ['website', 'web', 'online', 'site'],
        'google_search': ['google', 'google_search', 'search', 'organic_search'],
        'social_media': ['social', 'social_media', 'social_network'],
        'facebook': ['facebook', 'fb'],
        'linkedin': ['linkedin', 'linked_in'],
        'instagram': ['instagram', 'ig'],
        'twitter': ['twitter', 'x', 'twitter_x'],
        'referral': ['referral', 'referred', 'recommendation'],
        'word_of_mouth': ['word_of_mouth', 'word_mouth', 'wom'],
        'email_marketing': ['email', 'email_marketing', 'newsletter'],
        'google_ads': ['google_ads', 'adwords', 'google_adwords'],
        'conference': ['conference', 'event', 'trade_show'],
        'csv_import': ['csv', 'import', 'bulk', 'upload'],
        'other': ['other', 'misc', 'miscellaneous'],
        'unknown': ['unknown', 'not_known', 'n/a', 'na', '']
    }
    
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_rows = 0
        
    def detect_delimiter(self, csv_content: str) -> str:
        """Auto-detect CSV delimiter with enhanced fallback"""
        # Try different sample sizes
        for sample_size in [1024, 2048, len(csv_content)]:
            sample = csv_content[:min(sample_size, len(csv_content))]
            
            # Try CSV sniffer first
            sniffer = csv.Sniffer()
            try:
                delimiter = sniffer.sniff(sample, delimiters=',;\t|').delimiter
                # Verify the delimiter actually works
                test_reader = csv.reader(io.StringIO(sample), delimiter=delimiter)
                first_row = next(test_reader, None)
                if first_row and len(first_row) > 1:
                    return delimiter
            except:
                pass
            
            # Fallback: count delimiters and test
            delimiters = [',', ';', '\t', '|', '~']
            delimiter_counts = {d: sample.count(d) for d in delimiters}
            
            # Sort by count and test each
            for delimiter, count in sorted(delimiter_counts.items(), key=lambda x: x[1], reverse=True):
                if count > 0:
                    try:
                        test_reader = csv.reader(io.StringIO(sample), delimiter=delimiter)
                        first_row = next(test_reader, None)
                        if first_row and len(first_row) > 1:
                            return delimiter
                    except:
                        continue
        
        # Final fallback
        return ','
    
    def analyze_headers(self, headers: List[str]) -> Dict[str, str]:
        """
        Analyze CSV headers and create field mapping
        Returns dict mapping CSV column names to model field names
        """
        field_mapping = {}
        unmapped_headers = []
        
        # Normalize headers for comparison
        normalized_headers = {h.lower().strip().replace(' ', '_'): h for h in headers}
        
        for model_field, variations in self.FIELD_MAPPINGS.items():
            mapped = False
            for variation in variations:
                if variation.lower() in normalized_headers:
                    field_mapping[normalized_headers[variation.lower()]] = model_field
                    mapped = True
                    break
            
            if not mapped and model_field in self.MANDATORY_FIELDS:
                # Try fuzzy matching for mandatory fields
                for header in normalized_headers.keys():
                    if any(part in header for part in variations):
                        field_mapping[normalized_headers[header]] = model_field
                        mapped = True
                        break
        
        # Identify unmapped headers for user review
        for header in headers:
            if header not in field_mapping:
                unmapped_headers.append(header)
        
        return field_mapping, unmapped_headers
    
    def validate_mandatory_fields(self, field_mapping: Dict[str, str]) -> List[str]:
        """Check if all mandatory fields are mapped"""
        missing_fields = []
        mapped_model_fields = set(field_mapping.values())
        
        for mandatory_field in self.MANDATORY_FIELDS:
            if mandatory_field not in mapped_model_fields:
                missing_fields.append(mandatory_field)
        
        return missing_fields
    
    def clean_name_field(self, value: str) -> str:
        """Clean and standardize name fields"""
        if not value:
            return ""
        
        # Remove extra whitespace and standardize
        cleaned = re.sub(r'\s+', ' ', str(value).strip())
        
        # Handle common formatting issues
        if cleaned.upper() == cleaned and len(cleaned) > 2:
            # Convert ALL CAPS to Title Case
            cleaned = cleaned.title()
        
        return cleaned
    
    def parse_full_name(self, full_name: str) -> Dict[str, str]:
        """
        Parse a full name into components when separate fields aren't available
        """
        if not full_name:
            return {'first_name': '', 'middle_name': '', 'last_name': ''}
        
        # Common titles and suffixes
        titles = ['mr', 'mrs', 'ms', 'dr', 'prof', 'professor', 'sir', 'madam']
        suffixes = ['jr', 'sr', 'ii', 'iii', 'iv', 'phd', 'md', 'esq']
        
        parts = full_name.strip().split()
        if not parts:
            return {'first_name': '', 'middle_name': '', 'last_name': ''}
        
        result = {'first_name': '', 'middle_name': '', 'last_name': '', 'title': '', 'name_suffix': ''}
        
        # Remove and store title if present
        if len(parts) > 1 and parts[0].lower().rstrip('.') in titles:
            result['title'] = parts.pop(0)
        
        # Remove and store suffix if present
        if len(parts) > 1 and parts[-1].lower().rstrip('.') in suffixes:
            result['name_suffix'] = parts.pop()
        
        # Assign remaining parts
        if len(parts) == 1:
            result['first_name'] = parts[0]
        elif len(parts) == 2:
            result['first_name'] = parts[0]
            result['last_name'] = parts[1]
        elif len(parts) >= 3:
            result['first_name'] = parts[0]
            result['middle_name'] = ' '.join(parts[1:-1])
            result['last_name'] = parts[-1]
        
        return result
    
    def normalize_customer_type(self, value: str) -> str:
        """Normalize customer type values"""
        if not value:
            return 'individual'  # Default
        
        value_lower = value.lower().strip()
        
        for standard_type, variations in self.CUSTOMER_TYPE_MAPPINGS.items():
            if value_lower in variations:
                return standard_type
        
        return 'individual'  # Default fallback
    
    def normalize_source(self, value: str) -> str:
        """Normalize source values"""
        if not value:
            return ''  # Let it be set automatically later
        
        value_lower = value.lower().strip()
        
        for standard_source, variations in self.SOURCE_MAPPINGS.items():
            if value_lower in variations:
                return standard_source
        
        # If no mapping found, return original value if it's valid
        # Check if it matches any of the model choices
        from .models import Customer
        valid_sources = [choice[0] for choice in Customer.SOURCE_CHOICES if choice[0]]
        
        if value_lower in valid_sources:
            return value_lower
        
        return 'other'  # Default fallback for unrecognized sources
    
    def normalize_email(self, email: str) -> str:
        """Clean and validate email, handling multiple email addresses"""
        if not email:
            return ""
        
        # Clean up the email string
        email = email.strip().lower()
        
        # Handle multiple emails separated by common delimiters
        possible_delimiters = [',', ';', '|', ' and ', ' & ', '\n', '\t']
        
        for delimiter in possible_delimiters:
            if delimiter in email:
                # Split and take the first valid email
                email_parts = [part.strip() for part in email.split(delimiter)]
                for part in email_parts:
                    if part:  # Skip empty parts
                        try:
                            validate_email(part)
                            return part  # Return first valid email
                        except ValidationError:
                            continue
                
                # If no valid email found, raise error with original string
                raise ValidationError(f"No valid email found in: {email}")
        
        # Single email - validate normally
        try:
            validate_email(email)
            return email
        except ValidationError:
            raise ValidationError(f"Invalid email format: {email}")
    
    def extract_multiple_emails(self, email_string: str) -> tuple:
        """Extract primary and secondary emails from a string containing multiple emails"""
        if not email_string:
            return "", ""
        
        # Clean up the email string
        email_string = email_string.strip().lower()
        
        # Handle multiple emails separated by common delimiters
        possible_delimiters = [',', ';', '|', ' and ', ' & ', '\n', '\t']
        
        valid_emails = []
        
        for delimiter in possible_delimiters:
            if delimiter in email_string:
                email_parts = [part.strip() for part in email_string.split(delimiter)]
                for part in email_parts:
                    if part:  # Skip empty parts
                        try:
                            validate_email(part)
                            valid_emails.append(part)
                        except ValidationError:
                            continue
                break
        else:
            # No delimiter found, try as single email
            try:
                validate_email(email_string)
                valid_emails.append(email_string)
            except ValidationError:
                pass
        
        # Return primary and secondary emails
        primary_email = valid_emails[0] if valid_emails else ""
        secondary_email = valid_emails[1] if len(valid_emails) > 1 else ""
        
        return primary_email, secondary_email
    
    def normalize_phone(self, phone: str) -> str:
        """Clean phone number"""
        if not phone:
            return ""
        
        # Remove common formatting
        phone = re.sub(r'[^\d+\-\(\)\s]', '', str(phone))
        phone = phone.strip()
        
        return phone
    
    def process_row(self, row_data: Dict[str, str], field_mapping: Dict[str, str], row_num: int, default_source: str = 'csv_import') -> Optional[Dict[str, Any]]:
        """
        Process a single CSV row and return cleaned data for Customer creation
        """
        try:
            customer_data = {}
            row_errors = []
            
            # Process mapped fields
            for csv_field, model_field in field_mapping.items():
                value = row_data.get(csv_field, '').strip()
                
                if model_field in ['first_name', 'middle_name', 'last_name', 'preferred_name']:
                    customer_data[model_field] = self.clean_name_field(value)
                elif model_field == 'email_primary':
                    try:
                        # Check if this looks like multiple emails
                        if any(delimiter in value for delimiter in [',', ';', '|', ' and ', ' & ']):
                            primary_email, secondary_email = self.extract_multiple_emails(value)
                            if primary_email:
                                customer_data['email_primary'] = primary_email
                                if secondary_email and 'email_secondary' not in customer_data:
                                    customer_data['email_secondary'] = secondary_email
                                self.warnings.append(f"Row {row_num}: Multiple emails found, using '{primary_email}' as primary" + 
                                                   (f" and '{secondary_email}' as secondary" if secondary_email else ""))
                            else:
                                row_errors.append(f"Row {row_num}: No valid email found in '{value}'")
                        else:
                            customer_data[model_field] = self.normalize_email(value)
                    except ValidationError as e:
                        row_errors.append(f"Row {row_num}: {str(e)}")
                elif model_field == 'email_secondary':
                    try:
                        customer_data[model_field] = self.normalize_email(value)
                    except ValidationError as e:
                        row_errors.append(f"Row {row_num}: {str(e)}")
                elif model_field in ['phone_primary', 'phone_secondary']:
                    customer_data[model_field] = self.normalize_phone(value)
                elif model_field == 'customer_type':
                    customer_data[model_field] = self.normalize_customer_type(value)
                elif model_field == 'source':
                    customer_data[model_field] = self.normalize_source(value)
                else:
                    customer_data[model_field] = value
            
            # Handle multiple emails in unmapped email columns
            if not customer_data.get('email_primary'):
                # Look for email fields that might contain multiple addresses
                email_fields = ['email', 'emails', 'email_address', 'email_addresses', 'contact_email']
                for field in email_fields:
                    if field in row_data and row_data[field].strip():
                        try:
                            primary_email, secondary_email = self.extract_multiple_emails(row_data[field])
                            if primary_email:
                                customer_data['email_primary'] = primary_email
                                if secondary_email:
                                    customer_data['email_secondary'] = secondary_email
                                    self.warnings.append(f"Row {row_num}: Found multiple emails in '{field}' column, using '{primary_email}' as primary and '{secondary_email}' as secondary")
                                else:
                                    self.warnings.append(f"Row {row_num}: Using email from '{field}' column: '{primary_email}'")
                                break
                        except Exception as e:
                            self.warnings.append(f"Row {row_num}: Could not process emails in '{field}' column: {str(e)}")
            
            # Handle case where full name is provided instead of separate fields
            if not customer_data.get('first_name') and not customer_data.get('last_name'):
                # Look for full name field
                full_name_fields = ['full_name', 'name', 'fullname', 'customer_name']
                full_name = None
                
                for field in full_name_fields:
                    if field in row_data and row_data[field].strip():
                        full_name = row_data[field].strip()
                        break
                
                if full_name:
                    name_parts = self.parse_full_name(full_name)
                    customer_data.update(name_parts)
            
            # Validate mandatory fields
            for field in self.MANDATORY_FIELDS:
                if not customer_data.get(field):
                    row_errors.append(f"Row {row_num}: Missing mandatory field '{field}'")
            
            # Set defaults
            if 'customer_type' not in customer_data:
                customer_data['customer_type'] = 'individual'
            
            if 'status' not in customer_data:
                customer_data['status'] = 'prospect'
            
            # Set source using the provided default if not specified in CSV
            if not customer_data.get('source'):
                customer_data['source'] = default_source
            
            if row_errors:
                self.errors.extend(row_errors)
                return None
            
            return customer_data
            
        except Exception as e:
            import traceback
            logger.error(f"Row {row_num} processing error: {str(e)}")
            logger.error(f"Traceback: {traceback.format_exc()}")
            self.errors.append(f"Row {row_num}: Unexpected error - {str(e)}")
            return None
    
    def import_csv(self, csv_content: str, field_mapping: Optional[Dict[str, str]] = None, default_source: str = 'csv_import') -> Dict[str, Any]:
        """
        Main import function
        """
        self.errors = []
        self.warnings = []
        self.success_count = 0
        self.total_rows = 0
        
        try:
            # Detect delimiter
            delimiter = self.detect_delimiter(csv_content)
            
            # Parse CSV
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file, delimiter=delimiter)
            
            headers = reader.fieldnames
            if not headers:
                return {
                    'success': False,
                    'error': 'No headers found in CSV file',
                    'errors': [],
                    'warnings': [],
                    'stats': {'total': 0, 'success': 0, 'failed': 0}
                }
            
            # Auto-detect field mapping if not provided
            if field_mapping is None:
                field_mapping, unmapped_headers = self.analyze_headers(headers)
                
                if unmapped_headers:
                    self.warnings.append(f"Unmapped columns: {', '.join(unmapped_headers)}")
            
            # Validate mandatory field mapping
            missing_fields = self.validate_mandatory_fields(field_mapping)
            if missing_fields:
                return {
                    'success': False,
                    'error': f'Missing mandatory fields: {", ".join(missing_fields)}',
                    'field_mapping': field_mapping,
                    'missing_fields': missing_fields,
                    'headers': headers
                }
            
            # Process rows
            customers_to_create = []
            seen_emails = set()  # Track emails within CSV to prevent duplicates
            
            with transaction.atomic():
                for row_num, row in enumerate(reader, start=2):  # Start at 2 (after header)
                    self.total_rows += 1
                    
                    customer_data = self.process_row(row, field_mapping, row_num, default_source)
                    if customer_data:
                        try:
                            email_primary = customer_data['email_primary']
                            
                            # Check for duplicates within the CSV itself
                            if email_primary in seen_emails:
                                self.warnings.append(
                                    f"Row {row_num}: Duplicate email {email_primary} found within CSV, skipping"
                                )
                                continue
                            
                            # Check for existing customer in database
                            existing = Customer.objects.filter(
                                email_primary=email_primary
                            ).first()
                            
                            if existing:
                                self.warnings.append(
                                    f"Row {row_num}: Customer with email {email_primary} already exists in database, skipping"
                                )
                                continue
                            
                            # Add email to seen set
                            seen_emails.add(email_primary)
                            
                            # Create customer
                            customer = Customer(**customer_data)
                            customer.full_clean()  # Validate
                            customers_to_create.append(customer)
                            
                        except ValidationError as e:
                            error_msg = f"Row {row_num}: Validation error - {str(e)}"
                            self.errors.append(error_msg)
                        except Exception as e:
                            error_msg = f"Row {row_num}: Error - {str(e)}"
                            self.errors.append(error_msg)
                
                # Bulk create if no errors
                if not self.errors and customers_to_create:
                    try:
                        Customer.objects.bulk_create(customers_to_create)
                        self.success_count = len(customers_to_create)
                    except Exception as bulk_error:
                        # If bulk create fails, try individual creates to identify problematic records
                        logger.error(f"Bulk create failed: {str(bulk_error)}")
                        
                        if "UNIQUE constraint failed" in str(bulk_error):
                            self.errors.append("Bulk import failed due to duplicate email addresses. Processing records individually...")
                            
                            # Process individual records to identify duplicates
                            for i, customer in enumerate(customers_to_create):
                                try:
                                    customer.save()
                                    self.success_count += 1
                                except Exception as individual_error:
                                    if "UNIQUE constraint failed" in str(individual_error):
                                        self.errors.append(f"Customer with email {customer.email_primary} could not be created: duplicate email address")
                                    else:
                                        self.errors.append(f"Customer with email {customer.email_primary} could not be created: {str(individual_error)}")
                        else:
                            self.errors.append(f"Bulk create failed: {str(bulk_error)}")
                            self.success_count = 0
        
        except Exception as e:
            logger.error(f"CSV processing error: {str(e)}")
            return {
                'success': False,
                'error': f'CSV processing error: {str(e)}',
                'error_type': type(e).__name__,
                'errors': self.errors,
                'warnings': self.warnings,
                'stats': {'total': self.total_rows, 'success': 0, 'failed': self.total_rows},
                'debug_info': {
                    'total_errors': len(self.errors),
                    'total_warnings': len(self.warnings),
                    'rows_processed': self.total_rows
                }
            }
        
        return {
            'success': len(self.errors) == 0,
            'errors': self.errors,
            'warnings': self.warnings,
            'stats': {
                'total': self.total_rows,
                'success': self.success_count,
                'failed': self.total_rows - self.success_count
            },
            'field_mapping': field_mapping
        }
    
    def preview_import(self, csv_content: str, max_rows: int = 5) -> Dict[str, Any]:
        """
        Preview CSV import with field mapping suggestions
        """
        try:
            delimiter = self.detect_delimiter(csv_content)
            logger.info(f"Detected delimiter: '{delimiter}'")
            
            csv_file = io.StringIO(csv_content)
            reader = csv.DictReader(csv_file, delimiter=delimiter)
            
            headers = reader.fieldnames
            if not headers:
                return {'error': 'No headers found in CSV file'}
            
            logger.info(f"CSV headers: {headers}")
            
            # Analyze headers
            field_mapping, unmapped_headers = self.analyze_headers(headers)
            missing_fields = self.validate_mandatory_fields(field_mapping)
            
            logger.info(f"Field mapping: {field_mapping}")
            logger.info(f"Unmapped headers: {unmapped_headers}")
            logger.info(f"Missing fields: {missing_fields}")
            
            # Get sample rows with error handling
            sample_rows = []
            row_errors = []
            
            for i, row in enumerate(reader):
                if i >= max_rows:
                    break
                try:
                    # Clean and validate sample row
                    cleaned_row = {}
                    for key, value in row.items():
                        if key is not None:  # Handle None keys from malformed CSV
                            cleaned_row[key] = str(value).strip() if value is not None else ''
                    sample_rows.append(cleaned_row)
                except Exception as row_error:
                    row_errors.append(f"Row {i+2}: {str(row_error)}")
            
            # Count total rows more safely
            try:
                total_rows = sum(1 for _ in csv.DictReader(io.StringIO(csv_content), delimiter=delimiter))
            except Exception as count_error:
                logger.warning(f"Could not count total rows: {count_error}")
                total_rows = len(sample_rows)
            
            result = {
                'headers': headers,
                'field_mapping': field_mapping,
                'unmapped_headers': unmapped_headers,
                'missing_fields': missing_fields,
                'sample_rows': sample_rows,
                'total_rows_detected': total_rows,
                'delimiter_detected': delimiter
            }
            
            if row_errors:
                result['row_errors'] = row_errors
            
            return result
            
        except Exception as e:
            logger.error(f"Preview error: {str(e)}")
            return {
                'error': f'Preview error: {str(e)}',
                'error_type': type(e).__name__,
                'csv_sample': csv_content[:500] + '...' if len(csv_content) > 500 else csv_content
            }