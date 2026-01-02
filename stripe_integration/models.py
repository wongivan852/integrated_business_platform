from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

User = get_user_model()


class StripeAccount(models.Model):
    """Model to store Stripe account information"""
    name = models.CharField(max_length=100, help_text="Friendly name for this Stripe account")
    api_key = models.CharField(max_length=200, help_text="Stripe API key (encrypted)")
    account_id = models.CharField(max_length=100, unique=True, null=True, blank=True,
                                  help_text="Stripe account ID")
    is_active = models.BooleanField(default=True, help_text="Whether this account is active")
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Add owner tracking for multi-tenant support
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='stripe_accounts_created')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stripe Account'
        verbose_name_plural = 'Stripe Accounts'

    def __str__(self):
        return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"


class Transaction(models.Model):
    """Model to store Stripe transactions"""

    STATUS_CHOICES = [
        ('succeeded', 'Succeeded'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
        ('canceled', 'Canceled'),
        ('refunded', 'Refunded'),
    ]

    TYPE_CHOICES = [
        ('charge', 'Charge'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('payout', 'Payout'),
        ('adjustment', 'Adjustment'),
        ('fee', 'Fee'),
        ('transfer', 'Transfer'),
        ('other', 'Other'),
    ]

    stripe_id = models.CharField(max_length=100, unique=True,
                                help_text="Stripe transaction ID")
    account = models.ForeignKey(StripeAccount, on_delete=models.CASCADE,
                               related_name='transactions')

    # Transaction details
    amount = models.IntegerField(help_text="Amount in cents")
    fee = models.IntegerField(default=0, help_text="Processing fee in cents")
    currency = models.CharField(max_length=3, default='usd',
                               help_text="Currency code (e.g., usd, eur, hkd)")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    type = models.CharField(max_length=50, choices=TYPE_CHOICES, default='charge')

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    stripe_created = models.DateTimeField(help_text="Transaction date from Stripe")

    # Customer and transaction metadata
    customer_email = models.EmailField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    stripe_metadata = models.JSONField(null=True, blank=True,
                                      help_text="Additional metadata from Stripe")

    class Meta:
        ordering = ['-stripe_created']
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [
            models.Index(fields=['stripe_id']),
            models.Index(fields=['account', '-stripe_created']),
            models.Index(fields=['status']),
            models.Index(fields=['type']),
        ]

    def __str__(self):
        return f"{self.stripe_id}: {self.amount_formatted} {self.currency.upper()}"

    @property
    def amount_formatted(self):
        """Return amount in dollars/euros etc (divided by 100)"""
        return self.amount / 100

    @property
    def fee_formatted(self):
        """Return fee in dollars/euros etc (divided by 100)"""
        return self.fee / 100

    @property
    def net_amount_formatted(self):
        """Return net amount after fees in dollars/euros etc"""
        return self.amount_formatted - self.fee_formatted


class StripeCustomer(models.Model):
    """Model to track Stripe customers"""
    stripe_id = models.CharField(max_length=100, unique=True,
                                help_text="Stripe customer ID")
    account = models.ForeignKey(StripeAccount, on_delete=models.CASCADE,
                               related_name='customers')
    email = models.EmailField()
    name = models.CharField(max_length=200, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    metadata = models.JSONField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    stripe_created = models.DateTimeField(help_text="Customer created date from Stripe")

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stripe Customer'
        verbose_name_plural = 'Stripe Customers'
        indexes = [
            models.Index(fields=['stripe_id']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f"{self.email} ({self.stripe_id})"


class StripeSubscription(models.Model):
    """Model to track Stripe subscriptions"""

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
        ('canceled', 'Canceled'),
        ('incomplete', 'Incomplete'),
        ('incomplete_expired', 'Incomplete Expired'),
        ('trialing', 'Trialing'),
        ('paused', 'Paused'),
    ]

    stripe_id = models.CharField(max_length=100, unique=True,
                                help_text="Stripe subscription ID")
    account = models.ForeignKey(StripeAccount, on_delete=models.CASCADE,
                               related_name='subscriptions')
    customer = models.ForeignKey(StripeCustomer, on_delete=models.CASCADE,
                                related_name='subscriptions')

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    plan_name = models.CharField(max_length=200, null=True, blank=True)
    amount = models.IntegerField(help_text="Subscription amount in cents")
    currency = models.CharField(max_length=3, default='usd')
    interval = models.CharField(max_length=20, null=True, blank=True,
                               help_text="Billing interval (e.g., month, year)")

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    stripe_created = models.DateTimeField(help_text="Subscription created date from Stripe")
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at = models.DateTimeField(null=True, blank=True)
    canceled_at = models.DateTimeField(null=True, blank=True)

    metadata = models.JSONField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Stripe Subscription'
        verbose_name_plural = 'Stripe Subscriptions'
        indexes = [
            models.Index(fields=['stripe_id']),
            models.Index(fields=['status']),
            models.Index(fields=['customer']),
        ]

    def __str__(self):
        return f"{self.customer.email} - {self.plan_name} ({self.status})"

    @property
    def amount_formatted(self):
        """Return amount in dollars/euros etc (divided by 100)"""
        return self.amount / 100


class MonthlyStatement(models.Model):
    """
    Monthly statement for Stripe account with proper balance tracking
    Addresses: Opening/Closing balance, Payout reconciliation, Month-end definition
    """
    account = models.ForeignKey(StripeAccount, on_delete=models.CASCADE,
                               related_name='monthly_statements')
    year = models.IntegerField(help_text="Statement year")
    month = models.IntegerField(help_text="Statement month (1-12)")
    currency = models.CharField(max_length=3, default='hkd', 
                               help_text="Currency code (hkd, usd, etc)")
    
    # Balance tracking (all amounts in cents)
    opening_balance = models.IntegerField(default=0, 
                                        help_text="Opening balance at start of month (cents)")
    closing_balance = models.IntegerField(default=0,
                                        help_text="Closing balance at end of month (cents)")
    
    # Revenue (before fees)
    gross_revenue = models.IntegerField(default=0,
                                      help_text="Total payments + charges (cents)")
    refunds = models.IntegerField(default=0,
                                 help_text="Total refunds - negative (cents)")
    net_revenue = models.IntegerField(default=0,
                                    help_text="Gross revenue + refunds (cents)")
    
    # Fees
    processing_fees = models.IntegerField(default=0,
                                        help_text="Total Stripe processing fees (cents)")
    
    # Activity balance (revenue - fees, before payouts)
    activity_balance = models.IntegerField(default=0,
                                         help_text="Net revenue - fees (cents)")
    
    # Payouts
    payouts_in_month = models.IntegerField(default=0,
                                         help_text="Payouts dated within month - negative (cents)")
    payouts_for_month = models.IntegerField(default=0,
                                          help_text="Payouts matched to this month's revenue (cents)")
    
    # Balance calculation: closing = opening + activity_balance + payouts
    calculated_balance = models.IntegerField(default=0,
                                           help_text="Calculated closing balance (cents)")
    
    # Transaction counts
    transaction_count = models.IntegerField(default=0,
                                          help_text="Total transactions in month")
    payment_count = models.IntegerField(default=0,
                                      help_text="Number of payments/charges")
    payout_count = models.IntegerField(default=0,
                                     help_text="Number of payouts")
    refund_count = models.IntegerField(default=0,
                                     help_text="Number of refunds")
    
    # Reconciliation
    is_reconciled = models.BooleanField(default=False,
                                      help_text="Whether balances are reconciled")
    reconciliation_notes = models.TextField(blank=True,
                                          help_text="Notes about reconciliation")
    balance_discrepancy = models.IntegerField(default=0,
                                            help_text="Difference if not reconciled (cents)")
    
    # Timestamps
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['account', 'year', 'month']
        ordering = ['-year', '-month']
        verbose_name = 'Monthly Statement'
        verbose_name_plural = 'Monthly Statements'
        indexes = [
            models.Index(fields=['account', 'year', 'month']),
            models.Index(fields=['year', 'month']),
        ]
    
    def __str__(self):
        return f"{self.account.name} - {self.year}-{self.month:02d} ({self.currency.upper()})"
    
    @property
    def month_name(self):
        """Return month name"""
        import calendar
        return calendar.month_name[self.month]
    
    @property
    def opening_balance_formatted(self):
        """Return opening balance in standard format"""
        return self.opening_balance / 100
    
    @property
    def closing_balance_formatted(self):
        """Return closing balance in standard format"""
        return self.closing_balance / 100
    
    @property
    def gross_revenue_formatted(self):
        """Return gross revenue in standard format"""
        return self.gross_revenue / 100
    
    @property
    def net_revenue_formatted(self):
        """Return net revenue in standard format"""
        return self.net_revenue / 100
    
    @property
    def processing_fees_formatted(self):
        """Return fees in standard format"""
        return self.processing_fees / 100
    
    @property
    def activity_balance_formatted(self):
        """Return activity balance in standard format"""
        return self.activity_balance / 100
    
    @property
    def payouts_in_month_formatted(self):
        """Return payouts in standard format"""
        return abs(self.payouts_in_month) / 100  # Show as positive
    
    @property
    def net_change_formatted(self):
        """Return net change (closing - opening)"""
        return (self.closing_balance - self.opening_balance) / 100
    
    def get_currency_symbol(self):
        """Return currency symbol"""
        symbols = {
            'hkd': 'HK$',
            'usd': '$',
            'eur': '€',
            'gbp': '£',
            'cny': '¥',
        }
        return symbols.get(self.currency.lower(), self.currency.upper())
