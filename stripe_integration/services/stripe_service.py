"""
Stripe Service - Django wrapper for Stripe Dashboard functionality
"""
import sys
import os
from typing import List, Dict, Optional
from decimal import Decimal
from datetime import datetime, timedelta
from django.conf import settings
from django.db.models import Sum, Count, Q
from ..models import StripeAccount, Transaction, StripeCustomer, StripeSubscription


class StripeService:
    """
    Service to interact with Stripe data and wrap Flask dashboard functionality
    """

    def __init__(self, account_id: Optional[int] = None):
        """
        Initialize the Stripe service

        Args:
            account_id: Optional specific Stripe account ID to work with
        """
        self.account_id = account_id
        self.flask_dashboard_path = getattr(settings, 'STRIPE_FLASK_DASHBOARD_PATH', '/opt/stripe-dashboard')

    def get_account_summary(self) -> List[Dict]:
        """
        Get summary of all Stripe accounts

        Returns:
            List of dictionaries containing account summaries
        """
        accounts = StripeAccount.objects.filter(is_active=True)

        summary = []
        for account in accounts:
            transaction_stats = Transaction.objects.filter(account=account).aggregate(
                total_count=Count('id'),
                total_amount=Sum('amount'),
                total_fees=Sum('fee')
            )

            summary.append({
                'account': account,
                'has_api_key': bool(account.api_key),
                'total_transactions': transaction_stats['total_count'] or 0,
                'total_amount': (transaction_stats['total_amount'] or 0) / 100,  # Convert to dollars
                'total_fees': (transaction_stats['total_fees'] or 0) / 100,
                'net_amount': ((transaction_stats['total_amount'] or 0) - (transaction_stats['total_fees'] or 0)) / 100
            })

        return summary

    def get_account_transactions(self, account_id: int, limit: int = 50, offset: int = 0) -> List[Transaction]:
        """
        Get transactions for a specific account

        Args:
            account_id: The Stripe account ID
            limit: Maximum number of transactions to return
            offset: Offset for pagination

        Returns:
            List of Transaction objects
        """
        return Transaction.objects.filter(
            account_id=account_id
        ).order_by('-stripe_created')[offset:offset + limit]

    def get_all_transactions(self, limit: int = 50, offset: int = 0) -> List[Transaction]:
        """
        Get all transactions across all accounts

        Args:
            limit: Maximum number of transactions to return
            offset: Offset for pagination

        Returns:
            List of Transaction objects
        """
        return Transaction.objects.all().order_by('-stripe_created')[offset:offset + limit]

    def get_transactions_by_date_range(self, start_date: datetime, end_date: datetime,
                                      account_id: Optional[int] = None) -> List[Transaction]:
        """
        Get transactions within a date range

        Args:
            start_date: Start date for the range
            end_date: End date for the range
            account_id: Optional account ID to filter by

        Returns:
            List of Transaction objects
        """
        query = Transaction.objects.filter(
            stripe_created__gte=start_date,
            stripe_created__lte=end_date
        )

        if account_id:
            query = query.filter(account_id=account_id)

        return query.order_by('-stripe_created')

    def get_monthly_statement(self, year: int, month: int, company: Optional[str] = None) -> Dict:
        """
        Generate monthly statement for transactions

        Args:
            year: Year for the statement
            month: Month for the statement
            company: Optional company filter

        Returns:
            Dictionary containing monthly statement data
        """
        # Start and end dates for the month
        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        # Get transactions for the month
        transactions = self.get_transactions_by_date_range(start_date, end_date)

        # Calculate summary
        total_charges = transactions.filter(type='charge').aggregate(
            count=Count('id'),
            amount=Sum('amount')
        )

        total_refunds = transactions.filter(type='refund').aggregate(
            count=Count('id'),
            amount=Sum('amount')
        )

        total_fees = transactions.aggregate(fees=Sum('fee'))

        return {
            'year': year,
            'month': month,
            'start_date': start_date,
            'end_date': end_date,
            'total_charges': (total_charges['amount'] or 0) / 100,
            'total_charges_count': total_charges['count'] or 0,
            'total_refunds': (total_refunds['amount'] or 0) / 100,
            'total_refunds_count': total_refunds['count'] or 0,
            'total_fees': (total_fees['fees'] or 0) / 100,
            'net_revenue': ((total_charges['amount'] or 0) - (total_refunds['amount'] or 0) - (total_fees['fees'] or 0)) / 100,
            'transactions': transactions
        }

    def get_dashboard_stats(self) -> Dict:
        """
        Get overall dashboard statistics

        Returns:
            Dictionary containing dashboard stats
        """
        # Last 30 days
        thirty_days_ago = datetime.now() - timedelta(days=30)

        recent_transactions = Transaction.objects.filter(
            stripe_created__gte=thirty_days_ago
        )

        all_transactions = Transaction.objects.all()

        recent_stats = recent_transactions.aggregate(
            count=Count('id'),
            total=Sum('amount'),
            fees=Sum('fee')
        )

        all_stats = all_transactions.aggregate(
            count=Count('id'),
            total=Sum('amount'),
            fees=Sum('fee')
        )

        active_customers = StripeCustomer.objects.filter(
            subscriptions__status='active'
        ).distinct().count()

        active_subscriptions = StripeSubscription.objects.filter(
            status='active'
        ).count()

        return {
            'recent_transactions_count': recent_stats['count'] or 0,
            'recent_total': (recent_stats['total'] or 0) / 100,
            'recent_fees': (recent_stats['fees'] or 0) / 100,
            'recent_net': ((recent_stats['total'] or 0) - (recent_stats['fees'] or 0)) / 100,
            'all_transactions_count': all_stats['count'] or 0,
            'all_total': (all_stats['total'] or 0) / 100,
            'all_fees': (all_stats['fees'] or 0) / 100,
            'all_net': ((all_stats['total'] or 0) - (all_stats['fees'] or 0)) / 100,
            'active_customers': active_customers,
            'active_subscriptions': active_subscriptions,
        }

    def use_flask_dashboard_service(self, service_name: str):
        """
        Import and use a service from the Flask dashboard

        Args:
            service_name: Name of the service to import

        Returns:
            The imported service class or None if not found
        """
        try:
            # Add Flask dashboard to Python path
            if self.flask_dashboard_path not in sys.path:
                sys.path.insert(0, self.flask_dashboard_path)

            # Import the service
            if service_name == 'csv_transaction':
                from app.services.csv_transaction_service import CSVTransactionService
                return CSVTransactionService
            elif service_name == 'complete_csv':
                from app.services.complete_csv_service import CompleteCsvService
                return CompleteCsvService
            elif service_name == 'customer_subscription':
                from app.services.customer_subscription_service import CustomerSubscriptionService
                return CustomerSubscriptionService
            else:
                return None
        except ImportError as e:
            print(f"Error importing Flask service {service_name}: {e}")
            return None
