from django.contrib import admin
from .models import StripeAccount, Transaction, StripeCustomer, StripeSubscription


@admin.register(StripeAccount)
class StripeAccountAdmin(admin.ModelAdmin):
    list_display = ['name', 'account_id', 'is_active', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'account_id']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Account Information', {
            'fields': ('name', 'account_id', 'is_active')
        }),
        ('API Configuration', {
            'fields': ('api_key',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ['stripe_id', 'account', 'amount_display', 'currency', 'status', 'type', 'stripe_created']
    list_filter = ['status', 'type', 'currency', 'account', 'stripe_created']
    search_fields = ['stripe_id', 'customer_email', 'description']
    readonly_fields = ['stripe_id', 'created_at', 'amount_display', 'fee_display', 'net_amount_display']
    date_hierarchy = 'stripe_created'

    fieldsets = (
        ('Transaction Details', {
            'fields': ('stripe_id', 'account', 'status', 'type')
        }),
        ('Financial Information', {
            'fields': ('amount', 'amount_display', 'fee', 'fee_display', 'net_amount_display', 'currency')
        }),
        ('Customer Information', {
            'fields': ('customer_email', 'description')
        }),
        ('Metadata', {
            'fields': ('stripe_metadata', 'created_at', 'stripe_created'),
            'classes': ('collapse',)
        }),
    )

    def amount_display(self, obj):
        return f"{obj.amount_formatted:.2f}"
    amount_display.short_description = 'Amount'

    def fee_display(self, obj):
        return f"{obj.fee_formatted:.2f}"
    fee_display.short_description = 'Fee'

    def net_amount_display(self, obj):
        return f"{obj.net_amount_formatted:.2f}"
    net_amount_display.short_description = 'Net Amount'


@admin.register(StripeCustomer)
class StripeCustomerAdmin(admin.ModelAdmin):
    list_display = ['email', 'name', 'stripe_id', 'account', 'created_at']
    list_filter = ['account', 'created_at']
    search_fields = ['email', 'name', 'stripe_id']
    readonly_fields = ['stripe_id', 'created_at', 'stripe_created']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Customer Information', {
            'fields': ('stripe_id', 'account', 'email', 'name', 'description')
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at', 'stripe_created'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StripeSubscription)
class StripeSubscriptionAdmin(admin.ModelAdmin):
    list_display = ['customer', 'plan_name', 'amount_display', 'status', 'interval', 'current_period_end']
    list_filter = ['status', 'account', 'interval', 'created_at']
    search_fields = ['stripe_id', 'customer__email', 'plan_name']
    readonly_fields = ['stripe_id', 'created_at', 'stripe_created', 'amount_display']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Subscription Details', {
            'fields': ('stripe_id', 'account', 'customer', 'status')
        }),
        ('Plan Information', {
            'fields': ('plan_name', 'amount', 'amount_display', 'currency', 'interval')
        }),
        ('Billing Period', {
            'fields': ('current_period_start', 'current_period_end')
        }),
        ('Cancellation', {
            'fields': ('cancel_at', 'canceled_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('metadata', 'created_at', 'stripe_created'),
            'classes': ('collapse',)
        }),
    )

    def amount_display(self, obj):
        return f"{obj.amount_formatted:.2f}"
    amount_display.short_description = 'Amount'
