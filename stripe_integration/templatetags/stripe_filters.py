"""
Custom template filters for Stripe integration
"""
from django import template

register = template.Library()


@register.filter
def cents_to_dollars(value):
    """
    Convert cents (integer) to dollars (float with 2 decimals)
    """
    try:
        return value / 100.0
    except (ValueError, TypeError):
        return 0.0


@register.filter
def format_currency(value, currency='USD'):
    """
    Format amount with currency symbol
    """
    try:
        amount = value / 100.0
        symbols = {
            'hkd': 'HK$',
            'usd': '$',
            'eur': '€',
            'gbp': '£',
        }
        symbol = symbols.get(currency.lower(), currency.upper())
        return f"{symbol}{amount:,.2f}"
    except (ValueError, TypeError):
        return f"{currency.upper()} 0.00"
