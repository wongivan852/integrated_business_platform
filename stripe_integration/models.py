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
