"""
CSV Import Service - Import Stripe data from CSV files
"""
import csv
import os
from datetime import datetime
from typing import List, Dict, Optional
from django.conf import settings
from django.db import transaction
from ..models import StripeAccount, Transaction


class CSVImportService:
    """
    Service to import Stripe transaction data from CSV files
    """

    def __init__(self, csv_directory: Optional[str] = None):
        """
        Initialize the CSV import service

        Args:
            csv_directory: Optional path to CSV directory
        """
        self.csv_directory = csv_directory or getattr(
            settings, 'STRIPE_CSV_DIRECTORY',
            '/opt/stripe-dashboard/complete_csv'
        )

    def import_from_csv(self, file_path: str, account: StripeAccount) -> Dict:
        """
        Import transactions from a CSV file

        Args:
            file_path: Path to the CSV file
            account: StripeAccount to associate transactions with

        Returns:
            Dictionary with import statistics
        """
        stats = {
            'total_rows': 0,
            'imported': 0,
            'skipped': 0,
            'errors': []
        }

        if not os.path.exists(file_path):
            stats['errors'].append(f"File not found: {file_path}")
            return stats

        # Try different encodings
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        csvfile = None
        
        for encoding in encodings:
            try:
                csvfile = open(file_path, 'r', encoding=encoding)
                # Try to read a sample
                sample = csvfile.read(1024)
                csvfile.seek(0)
                break
            except UnicodeDecodeError:
                if csvfile:
                    csvfile.close()
                continue
            except Exception as e:
                if csvfile:
                    csvfile.close()
                stats['errors'].append(f"Error opening file: {str(e)}")
                return stats
        
        if csvfile is None:
            stats['errors'].append("Could not decode file with any supported encoding")
            return stats

        try:
            # Use csv.Sniffer to detect dialect
            try:
                dialect = csv.Sniffer().sniff(sample)
            except csv.Error:
                dialect = csv.excel

            reader = csv.DictReader(csvfile, dialect=dialect)

            with transaction.atomic():
                for row in reader:
                    stats['total_rows'] += 1

                    try:
                        # Parse transaction data from CSV
                        transaction_data = self._parse_csv_row(row)

                        if not transaction_data:
                            stats['skipped'] += 1
                            continue

                        # Create or update transaction
                        trans, created = Transaction.objects.update_or_create(
                            stripe_id=transaction_data['stripe_id'],
                            defaults={
                                'account': account,
                                'amount': transaction_data['amount'],
                                'fee': transaction_data['fee'],
                                'currency': transaction_data['currency'],
                                'status': transaction_data['status'],
                                'type': transaction_data['type'],
                                'stripe_created': transaction_data['stripe_created'],
                                'customer_email': transaction_data.get('customer_email'),
                                'description': transaction_data.get('description'),
                                'stripe_metadata': transaction_data.get('metadata', {})
                            }
                        )

                        if created:
                            stats['imported'] += 1
                        else:
                            stats['skipped'] += 1

                    except Exception as e:
                        stats['errors'].append(f"Row {stats['total_rows']}: {str(e)}")

        except Exception as e:
            stats['errors'].append(f"Error reading CSV: {str(e)}")
        finally:
            if csvfile:
                csvfile.close()

        return stats

    def _parse_csv_row(self, row: Dict) -> Optional[Dict]:
        """
        Parse a CSV row into transaction data
        Supports multiple Stripe CSV formats:
        - Balance transactions (itemised activity, itemised payouts)
        - Payment intents (unified payments)
        - Balance summary

        Args:
            row: Dictionary representing a CSV row

        Returns:
            Dictionary with transaction data or None if invalid
        """
        try:
            # Skip summary rows (category field)
            if 'category' in row:
                return None
                
            # Different CSV formats might have different column names
            # Try to detect and map them
            # IMPORTANT: Check payout_id first since payout CSV also has balance_transaction_id

            # Format 1: Payout format (payout_id) - CHECK THIS FIRST
            if 'payout_id' in row and row.get('payout_id', '').strip() != '':
                # Use balance_transaction_id as the primary ID since that's unique per transaction
                stripe_id = row.get('balance_transaction_id', row.get('payout_id', ''))
                if not stripe_id or stripe_id.strip() == '':
                    return None
                
                # Amount (negative for payout)
                gross_str = row.get('gross', row.get('amount', '0'))
                amount = -abs(self._parse_amount(gross_str))  # Always negative
                
                # Fee
                fee_str = row.get('fee', '0')
                fee = self._parse_amount(fee_str)
                
                # Date - try multiple fields
                date_str = row.get('effective_at', row.get('created', row.get('arrival_date', row.get('payout_expected_arrival_date', ''))))
                stripe_created = self._parse_date(date_str)
                
                # Currency
                currency = row.get('currency', 'hkd').lower()
                
                # Description
                description = row.get('description', 'STRIPE PAYOUT')
                
                return {
                    'stripe_id': stripe_id,
                    'amount': amount,
                    'fee': fee,
                    'currency': currency,
                    'status': row.get('payout_status', row.get('status', 'paid')).lower(),
                    'type': 'payout',
                    'stripe_created': stripe_created,
                    'customer_email': None,
                    'description': description,
                    'stripe_metadata': {}
                }
            
            # Format 2: Balance transaction format (balance_transaction_id)
            elif 'balance_transaction_id' in row:
                stripe_id = row['balance_transaction_id']
                if not stripe_id or stripe_id.strip() == '':
                    return None
                
                # Gross amount (positive for charges, negative for refunds in original)
                gross_str = row.get('gross', '0')
                gross = self._parse_amount(gross_str)
                
                # Fee (always positive in CSV)
                fee_str = row.get('fee', '0')
                fee = self._parse_amount(fee_str)
                
                # Net amount
                net_str = row.get('net', '0')
                net = self._parse_amount(net_str)
                
                # Reporting category determines type
                reporting_cat = row.get('reporting_category', '').lower()
                if reporting_cat == 'payout':
                    trans_type = 'payout'
                    amount = gross  # Payout amount (negative)
                elif reporting_cat == 'refund':
                    trans_type = 'refund'
                    amount = gross  # Refund (negative)
                else:
                    trans_type = 'charge'
                    amount = gross  # Charge (positive)
                
                # Date
                date_str = row.get('created', row.get('available_on', ''))
                stripe_created = self._parse_date(date_str)
                
                # Currency
                currency = row.get('currency', 'hkd').lower()
                
                # Description
                description = row.get('description', '')
                
                return {
                    'stripe_id': stripe_id,
                    'amount': amount,
                    'fee': fee,
                    'currency': currency,
                    'status': 'succeeded',
                    'type': trans_type,
                    'stripe_created': stripe_created,
                    'customer_email': None,
                    'description': description if description else None,
                    'stripe_metadata': {}
                }
            
            # Format 3: Stripe standard export / Payment intent format
            elif 'id' in row or 'transaction_id' in row or 'Transaction ID' in row:
                stripe_id = row.get('id', row.get('transaction_id', row.get('Transaction ID', '')))
                
                if not stripe_id or stripe_id.strip() == '':
                    return None

                # Amount
                amount_str = row.get('amount', row.get('Amount', row.get('Net', '0')))
                amount = self._parse_amount(amount_str)

                # Fee
                fee_str = row.get('fee', row.get('Fee', '0'))
                fee = self._parse_amount(fee_str)

                # Currency
                currency = row.get('currency', row.get('Currency', 'usd')).lower()

                # Status
                status = row.get('status', row.get('Status', 'succeeded')).lower()
                if status not in ['succeeded', 'pending', 'failed', 'canceled', 'refunded']:
                    status = 'succeeded'

                # Type
                trans_type = row.get('type', row.get('Type', 'charge')).lower()
                if trans_type not in ['charge', 'payment', 'refund', 'payout', 'adjustment', 'fee', 'transfer', 'other']:
                    trans_type = 'charge'

                # Date
                date_str = row.get('created', row.get('Created (UTC)', row.get('Date', row.get('Created date (UTC)', ''))))
                stripe_created = self._parse_date(date_str)

                # Customer email
                customer_email = row.get('customer_email', row.get('Customer Email', ''))

                # Description
                description = row.get('description', row.get('Description', ''))

                return {
                    'stripe_id': stripe_id,
                    'amount': amount,
                    'fee': fee,
                    'currency': currency,
                    'status': status,
                    'type': trans_type,
                    'stripe_created': stripe_created,
                    'customer_email': customer_email if customer_email else None,
                    'description': description if description else None,
                    'stripe_metadata': {}
                }
            else:
                return None

        except Exception as e:
            print(f"Error parsing CSV row: {e}")
            print(f"Row data: {row}")
            return None

    def _parse_amount(self, amount_str: str) -> int:
        """
        Parse amount string to cents (integer)

        Args:
            amount_str: String representation of amount

        Returns:
            Amount in cents
        """
        try:
            # Remove currency symbols and spaces
            cleaned = amount_str.replace('$', '').replace(',', '').replace(' ', '').strip()

            if not cleaned or cleaned == '-':
                return 0

            # Convert to float then to cents
            amount_float = float(cleaned)
            return int(amount_float * 100)

        except (ValueError, AttributeError):
            return 0

    def _parse_date(self, date_str: str) -> datetime:
        """
        Parse date string to datetime with timezone awareness

        Args:
            date_str: String representation of date

        Returns:
            datetime object with UTC timezone
        """
        from django.utils import timezone as django_tz
        import pytz
        
        try:
            # Handle None or empty strings
            if not date_str or date_str.strip() == '':
                return django_tz.now()
            
            # Try different date formats
            date_formats = [
                '%Y-%m-%d %H:%M:%S',
                '%Y-%m-%d %H:%M',
                '%Y-%m-%d',
                '%m/%d/%Y %H:%M:%S',
                '%m/%d/%Y',
                '%d/%m/%Y',
                '%Y-%m-%dT%H:%M:%SZ',
                '%Y-%m-%dT%H:%M:%S.%fZ',
            ]

            parsed_date = None
            for fmt in date_formats:
                try:
                    parsed_date = datetime.strptime(date_str.strip(), fmt)
                    break
                except (ValueError, AttributeError):
                    continue

            if parsed_date is None:
                # If all formats fail, return current time
                print(f"Warning: Could not parse date '{date_str}', using current time")
                return django_tz.now()
            
            # Make timezone aware (assume UTC if not specified)
            if parsed_date.tzinfo is None:
                parsed_date = pytz.UTC.localize(parsed_date)
            
            return parsed_date

        except Exception as e:
            print(f"Exception in _parse_date for '{date_str}': {e}")
            return django_tz.now()

    def list_csv_files(self) -> List[str]:
        """
        List available CSV files in the directory

        Returns:
            List of CSV file paths
        """
        csv_files = []

        if not os.path.exists(self.csv_directory):
            return csv_files

        try:
            for filename in os.listdir(self.csv_directory):
                if filename.endswith('.csv'):
                    csv_files.append(os.path.join(self.csv_directory, filename))

            # Also check subdirectories
            for root, dirs, files in os.walk(self.csv_directory):
                for filename in files:
                    if filename.endswith('.csv'):
                        file_path = os.path.join(root, filename)
                        if file_path not in csv_files:
                            csv_files.append(file_path)

        except Exception as e:
            print(f"Error listing CSV files: {e}")

        return sorted(csv_files)
