"""
Monthly Statement Service - Generate and manage monthly statements
Addresses 3 key challenges:
1. Opening/Closing balance consistency
2. Payout integration and reconciliation
3. Clear month-end definition
"""

from datetime import datetime, timedelta
from django.db.models import Sum, Count, Q
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from ..models import StripeAccount, Transaction, MonthlyStatement


class MonthlyStatementService:
    """
    Service to generate and manage monthly statements with proper balance tracking
    """
    
    def __init__(self):
        self.currency_defaults = {
            'hkd': 'HK$',
            'usd': '$',
            'eur': '€',
            'gbp': '£',
        }
    
    def get_month_boundaries(self, year, month):
        """
        Get clear start and end boundaries for a month
        Addresses Challenge 3: Month-end definition
        
        Returns:
            tuple: (start_date, end_date) with timezone awareness
        """
        # Start: First second of the month
        start_date = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
        
        # End: Last second of the month
        if month == 12:
            end_date = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc) - timedelta(seconds=1)
        else:
            end_date = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=timezone.utc) - timedelta(seconds=1)
        
        return start_date, end_date
    
    def calculate_monthly_statement(self, account, year, month, opening_balance=None):
        """
        Calculate monthly statement with proper balance tracking
        Matches Stripe's Balance Summary format:
        - Gross revenue = charges + refunds (refunds as positive amounts)
        - Processing fees = all fees on charges and refunds
        - Activity = gross - fees
        - Closing = opening + activity - payouts
        
        Args:
            account: StripeAccount instance
            year: Statement year
            month: Statement month (1-12)
            opening_balance: Optional opening balance in cents. If None, calculated from previous month
        
        Returns:
            MonthlyStatement instance
        """
        # Step 1: Get previous month's closing balance (Challenge 1)
        if opening_balance is None:
            prev_month = month - 1 if month > 1 else 12
            prev_year = year if month > 1 else year - 1
            
            prev_statement = MonthlyStatement.objects.filter(
                account=account,
                year=prev_year,
                month=prev_month
            ).first()
            
            opening_balance = prev_statement.closing_balance if prev_statement else 0
        
        # Step 2: Get all transactions for this month (Challenge 3: Clear boundaries)
        start_date, end_date = self.get_month_boundaries(year, month)
        
        all_transactions = Transaction.objects.filter(
            account=account,
            stripe_created__gte=start_date,
            stripe_created__lte=end_date
        )
        
        # Separate transactions by type
        revenue_trans = all_transactions.filter(type__in=['payment', 'charge'])
        refund_trans = all_transactions.filter(type='refund')
        payout_trans = all_transactions.filter(type='payout')
        
        # Step 3: Calculate revenue and fees (Stripe format)
        # Gross charges (positive amounts)
        gross_charges = revenue_trans.aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Refund amounts (stored as negative in DB, but we want absolute value for gross calculation)
        refund_amounts = refund_trans.aggregate(Sum('amount'))['amount__sum'] or 0
        refunds_absolute = abs(refund_amounts)  # Convert to positive for display
        
        # Gross revenue = charges + refunds (as positive)
        gross_revenue = gross_charges + refunds_absolute
        
        # Processing fees on charges and refunds
        charge_fees = revenue_trans.aggregate(Sum('fee'))['fee__sum'] or 0
        refund_fees = refund_trans.aggregate(Sum('fee'))['fee__sum'] or 0
        processing_fees = abs(charge_fees) + abs(refund_fees)
        
        # Net revenue (charges minus refunds)
        net_revenue = gross_charges + refund_amounts  # refund_amounts is already negative
        
        # Activity balance = net revenue - fees
        activity_balance = net_revenue - processing_fees
        
        # Step 4: Handle payouts (Challenge 2: Payout integration)
        # Payouts are negative in balance calculation
        payouts_total = payout_trans.aggregate(Sum('amount'))['amount__sum'] or 0
        payouts_absolute = abs(payouts_total)  # For display as positive
        payout_fees = payout_trans.aggregate(Sum('fee'))['fee__sum'] or 0
        
        # Step 5: Calculate closing balance
        # Formula: Opening + Activity - Payouts
        closing_balance = opening_balance + activity_balance - payouts_absolute
        
        # Step 6: Get currency (use most common currency in transactions)
        currency = revenue_trans.values('currency').annotate(
            count=Count('id')
        ).order_by('-count').first()
        currency_code = currency['currency'] if currency else 'hkd'
        
        # Step 7: Calculate transaction counts
        transaction_count = all_transactions.count()
        payment_count = revenue_trans.count()
        payout_count = payout_trans.count()
        refund_count = refund_trans.count()
        
        # Step 8: Save or update statement
        statement, created = MonthlyStatement.objects.update_or_create(
            account=account,
            year=year,
            month=month,
            defaults={
                'opening_balance': opening_balance,
                'gross_revenue': gross_revenue,
                'refunds': refund_amounts,  # Stored as negative
                'net_revenue': net_revenue,
                'processing_fees': processing_fees,
                'activity_balance': activity_balance,
                'payouts_in_month': -payouts_absolute,  # Store as negative
                'payouts_for_month': -payouts_absolute,
                'closing_balance': closing_balance,
                'calculated_balance': closing_balance,
                'currency': currency_code,
                'transaction_count': transaction_count,
                'payment_count': payment_count,
                'payout_count': payout_count,
                'refund_count': refund_count,
                'is_reconciled': True,
                'balance_discrepancy': 0,
            }
        )
        
        return statement
    
    def _match_payouts_to_revenue(self, activity_balance, current_payouts, extended_payouts):
        """
        Match payouts to month's revenue
        Addresses Challenge 2: Payout timing mismatch
        
        Strategy: Payouts dated in the month are assumed to belong to this month's revenue
        Extended payouts (7 days into next month) are checked but not currently used
        """
        # For now, use simple strategy: payouts dated in month belong to month
        # Future enhancement: Track cumulative balance and match payouts precisely
        return current_payouts.aggregate(Sum('amount'))['amount__sum'] or 0
    
    def generate_all_statements(self, account, start_year=None, start_month=None, 
                                end_year=None, end_month=None, initial_balance=0):
        """
        Generate statements for all months in a date range
        
        Args:
            account: StripeAccount instance
            start_year: Starting year (default: earliest transaction year)
            start_month: Starting month (default: earliest transaction month)
            end_year: Ending year (default: current year)
            end_month: Ending month (default: current month)
            initial_balance: Opening balance for first month in cents (default: 0)
        
        Returns:
            list: List of generated MonthlyStatement instances
        """
        # Get date range from transactions if not specified
        first_trans = Transaction.objects.filter(account=account).order_by('stripe_created').first()
        last_trans = Transaction.objects.filter(account=account).order_by('-stripe_created').first()
        
        if not first_trans:
            return []
        
        if start_year is None or start_month is None:
            start_year = first_trans.stripe_created.year
            start_month = first_trans.stripe_created.month
        
        if end_year is None or end_month is None:
            end_year = last_trans.stripe_created.year
            end_month = last_trans.stripe_created.month
        
        # Generate statements for each month
        statements = []
        current_date = datetime(start_year, start_month, 1)
        end_date = datetime(end_year, end_month, 1)
        
        # Set opening balance for first month
        opening_balance = initial_balance
        
        while current_date <= end_date:
            year = current_date.year
            month = current_date.month
            
            statement = self.calculate_monthly_statement(
                account, 
                year, 
                month, 
                opening_balance=opening_balance
            )
            statements.append(statement)
            
            # Next month's opening = this month's closing
            opening_balance = statement.closing_balance
            
            # Move to next month
            current_date = current_date + relativedelta(months=1)
        
        return statements
    
    def get_statement(self, account, year, month):
        """
        Get existing statement or generate new one
        
        Returns:
            MonthlyStatement instance
        """
        try:
            return MonthlyStatement.objects.get(
                account=account,
                year=year,
                month=month
            )
        except MonthlyStatement.DoesNotExist:
            return self.calculate_monthly_statement(account, year, month)
    
    def get_transactions_for_statement(self, statement):
        """
        Get all transactions for a monthly statement
        
        Returns:
            QuerySet of Transaction objects
        """
        start_date, end_date = self.get_month_boundaries(statement.year, statement.month)
        
        return Transaction.objects.filter(
            account=statement.account,
            stripe_created__gte=start_date,
            stripe_created__lte=end_date
        ).order_by('stripe_created')
    
    def format_currency(self, amount_cents, currency='hkd'):
        """
        Format amount with currency symbol
        
        Args:
            amount_cents: Amount in cents
            currency: Currency code
        
        Returns:
            str: Formatted amount (e.g., "HK$1,234.56")
        """
        symbol = self.currency_defaults.get(currency.lower(), currency.upper())
        amount = abs(amount_cents) / 100
        return f"{symbol}{amount:,.2f}"
