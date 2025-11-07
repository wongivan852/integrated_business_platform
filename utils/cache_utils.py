"""
Cache utilities for expense system.
Simplified version for integrated platform.
"""

from functools import wraps
from django.core.cache import cache
import hashlib
import json


def cache_result(timeout=300, key_prefix=''):
    """
    Decorator to cache function results.

    Args:
        timeout: Cache timeout in seconds (default: 300)
        key_prefix: Prefix for cache key (default: '')
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and arguments
            key_parts = [key_prefix or func.__name__]

            # Add args to key
            for arg in args:
                if hasattr(arg, 'pk'):  # Django model instance
                    key_parts.append(str(arg.pk))
                elif isinstance(arg, (str, int, float, bool)):
                    key_parts.append(str(arg))

            # Add kwargs to key
            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int, float, bool)):
                    key_parts.append(f"{k}={v}")

            # Create cache key
            cache_key = ':'.join(key_parts)

            # Try to get from cache
            result = cache.get(cache_key)
            if result is not None:
                return result

            # Call function and cache result
            result = func(*args, **kwargs)
            cache.set(cache_key, result, timeout)
            return result

        return wrapper
    return decorator


class ExpenseSystemCache:
    """
    Centralized cache management for expense system.
    """

    CACHE_PREFIXES = {
        'claim': 'expense_claim',
        'category': 'expense_category',
        'user': 'expense_user',
        'stats': 'expense_stats',
    }

    @classmethod
    def get(cls, cache_type, key, default=None):
        """Get value from cache."""
        prefix = cls.CACHE_PREFIXES.get(cache_type, 'expense')
        cache_key = f"{prefix}:{key}"
        return cache.get(cache_key, default)

    @classmethod
    def set(cls, cache_type, key, value, timeout=300):
        """Set value in cache."""
        prefix = cls.CACHE_PREFIXES.get(cache_type, 'expense')
        cache_key = f"{prefix}:{key}"
        cache.set(cache_key, value, timeout)

    @classmethod
    def delete(cls, cache_type, key):
        """Delete value from cache."""
        prefix = cls.CACHE_PREFIXES.get(cache_type, 'expense')
        cache_key = f"{prefix}:{key}"
        cache.delete(cache_key)

    @classmethod
    def clear(cls, cache_type=None):
        """Clear all cache for a type, or all expense cache if no type specified."""
        if cache_type:
            # This is a simplified version - in production, use pattern matching
            pass
        else:
            # Clear all (simplified - in production implement proper pattern clearing)
            pass

    @classmethod
    def get_or_set(cls, cache_type, key, callable_func, timeout=300):
        """Get from cache or call function and set result."""
        value = cls.get(cache_type, key)
        if value is None:
            value = callable_func()
            cls.set(cache_type, key, value, timeout)
        return value

    @classmethod
    def get_active_companies(cls):
        """
        Get list of active companies.
        Returns empty list if Company model doesn't exist.
        """
        try:
            from expense_claims.models import Company
            return Company.objects.filter(is_active=True).order_by('name')
        except ImportError:
            # Company model doesn't exist in this setup
            return []
        except Exception:
            # Any other error, return empty list
            return []

    @classmethod
    def get_active_categories(cls):
        """Get list of active expense categories."""
        try:
            from expense_claims.models import ExpenseCategory
            return ExpenseCategory.objects.filter(is_active=True).order_by('name')
        except:
            return []

    @classmethod
    def get_active_currencies(cls):
        """Get list of active currencies."""
        try:
            from expense_claims.models import Currency
            return Currency.objects.filter(is_active=True).order_by('code')
        except:
            return []

    @classmethod
    def invalidate_user_cache(cls, user_id):
        """Invalidate cache for a specific user."""
        cls.delete('user', user_id)
        cls.delete('stats', user_id)

    @classmethod
    def get_dashboard_data(cls, user_id, role):
        """Get dashboard statistics data."""
        # Return empty dict for now - can be implemented later
        return {}

    @classmethod
    def get_user_permissions(cls, user_id):
        """Get user permissions."""
        # Return empty dict for now - can be implemented later
        return {}

    @classmethod
    def get_exchange_rates(cls, date=None):
        """Get currency exchange rates."""
        # Return empty dict for now - can be implemented later
        return {}
