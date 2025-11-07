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

        try:
            with open(file_path, 'r', encoding='utf-8') as csvfile:
                # Try to detect the CSV format
                sample = csvfile.read(1024)
                csvfile.seek(0)

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

        return stats

    def _parse_csv_row(self, row: Dict) -> Optional[Dict]:
        """
        Parse a CSV row into transaction data

        Args:
            row: Dictionary representing a CSV row

        Returns:
            Dictionary with transaction data or None if invalid
        """
        try:
            # Different CSV formats might have different column names
            # Try to detect and map them

            # Stripe standard export format
            if 'id' in row:
                stripe_id = row['id']
            elif 'transaction_id' in row:
                stripe_id = row['transaction_id']
            elif 'Transaction ID' in row:
                stripe_id = row['Transaction ID']
            else:
                return None

            if not stripe_id:
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
            date_str = row.get('created', row.get('Created (UTC)', row.get('Date', '')))
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
                'metadata': {}
            }

        except Exception as e:
            print(f"Error parsing CSV row: {e}")
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
        Parse date string to datetime

        Args:
            date_str: String representation of date

        Returns:
            datetime object
        """
        try:
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

            for fmt in date_formats:
                try:
                    return datetime.strptime(date_str, fmt)
                except ValueError:
                    continue

            # If all formats fail, return current time
            return datetime.now()

        except Exception:
            return datetime.now()

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
