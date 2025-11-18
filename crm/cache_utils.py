# cache_utils.py - Advanced Caching Utilities for CRM Performance
from django.core.cache import cache
from django.conf import settings
from django.db.models import QuerySet
from functools import wraps
import hashlib
import json
import logging

logger = logging.getLogger(__name__)

class CacheManager:
    """Advanced cache management for CRM system"""
    
    @staticmethod
    def generate_cache_key(*args, **kwargs):
        """Generate a consistent cache key from arguments"""
        cache_data = {
            'args': args,
            'kwargs': sorted(kwargs.items()) if kwargs else {}
        }
        cache_string = json.dumps(cache_data, sort_keys=True, default=str)
        return hashlib.md5(cache_string.encode()).hexdigest()
    
    @staticmethod
    def cache_queryset(cache_key, queryset, timeout=None):
        """Cache queryset results with automatic serialization"""
        if timeout is None:
            timeout = settings.CACHE_TTL.get('query_cache', 300)
        
        try:
            # Convert queryset to list for caching
            data = list(queryset.values()) if hasattr(queryset, 'values') else list(queryset)
            cache.set(cache_key, data, timeout)
            logger.info(f"Cached queryset with key: {cache_key}")
            return data
        except Exception as e:
            logger.error(f"Failed to cache queryset: {e}")
            return list(queryset)
    
    @staticmethod
    def get_cached_queryset(cache_key):
        """Retrieve cached queryset results"""
        try:
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                logger.info(f"Cache hit for key: {cache_key}")
                return cached_data
            logger.info(f"Cache miss for key: {cache_key}")
            return None
        except Exception as e:
            logger.error(f"Failed to get cached data: {e}")
            return None
    
    @staticmethod
    def invalidate_pattern(pattern):
        """Invalidate cache keys matching a pattern"""
        try:
            # This is a simple implementation - in production consider Redis with pattern matching
            cache.delete_many([f"{pattern}*"])
            logger.info(f"Invalidated cache pattern: {pattern}")
        except Exception as e:
            logger.error(f"Failed to invalidate cache pattern: {e}")

def cache_result(timeout=None, key_prefix=''):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = f"{key_prefix}:{func.__name__}:{CacheManager.generate_cache_key(*args, **kwargs)}"
            
            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                logger.info(f"Cache hit for function {func.__name__}")
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_timeout = timeout or settings.CACHE_TTL.get('api_responses', 300)
            cache.set(cache_key, result, cache_timeout)
            logger.info(f"Cached result for function {func.__name__}")
            
            return result
        return wrapper
    return decorator

def cache_queryset_result(timeout=None, key_prefix='queryset'):
    """Decorator specifically for queryset caching"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = f"{key_prefix}:{func.__name__}:{CacheManager.generate_cache_key(*args, **kwargs)}"
            
            # Check cache first
            cached_data = CacheManager.get_cached_queryset(cache_key)
            if cached_data is not None:
                return cached_data
            
            # Execute function and cache
            result = func(*args, **kwargs)
            if isinstance(result, QuerySet):
                return CacheManager.cache_queryset(cache_key, result, timeout)
            else:
                cache_timeout = timeout or settings.CACHE_TTL.get('query_cache', 300)
                cache.set(cache_key, result, cache_timeout)
                return result
        return wrapper
    return decorator

# Cache warming utilities
class CacheWarmer:
    """Pre-warm frequently accessed cache entries"""
    
    @staticmethod
    def warm_customer_stats():
        """Pre-warm customer statistics cache"""
        from .models import Customer
        
        try:
            # Warm up common customer queries
            cache_key = "customer_stats_total"
            total_customers = Customer.objects.count()
            cache.set(cache_key, total_customers, settings.CACHE_TTL['dashboard_stats'])
            
            cache_key = "customer_stats_active"
            active_customers = Customer.objects.filter(status='active').count()
            cache.set(cache_key, active_customers, settings.CACHE_TTL['dashboard_stats'])
            
            cache_key = "customer_stats_by_type"
            stats_by_type = {}
            for customer_type, _ in Customer.CUSTOMER_TYPES:
                stats_by_type[customer_type] = Customer.objects.filter(customer_type=customer_type).count()
            cache.set(cache_key, stats_by_type, settings.CACHE_TTL['dashboard_stats'])
            
            logger.info("Customer stats cache warmed successfully")
            
        except Exception as e:
            logger.error(f"Failed to warm customer stats cache: {e}")
    
    @staticmethod
    def warm_country_codes():
        """Pre-warm country codes cache"""
        from .models import Customer
        
        try:
            cache_key = "country_codes_list"
            country_codes = dict(Customer.COUNTRY_CHOICES)
            cache.set(cache_key, country_codes, settings.CACHE_TTL['country_codes'])
            
            cache_key = "country_code_mapping"
            country_mapping = Customer.COUNTRY_CODE_MAP
            cache.set(cache_key, country_mapping, settings.CACHE_TTL['country_codes'])
            
            logger.info("Country codes cache warmed successfully")
            
        except Exception as e:
            logger.error(f"Failed to warm country codes cache: {e}")

# Cache invalidation signals
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

@receiver([post_save, post_delete], sender='crm.Customer')
def invalidate_customer_cache(sender, **kwargs):
    """Invalidate customer-related cache on model changes"""
    try:
        cache.delete_many([
            'customer_stats_total',
            'customer_stats_active', 
            'customer_stats_by_type'
        ])
        
        # Invalidate customer search cache pattern
        CacheManager.invalidate_pattern('customer_search')
        
        logger.info("Customer cache invalidated")
        
    except Exception as e:
        logger.error(f"Failed to invalidate customer cache: {e}")

@receiver([post_save, post_delete], sender='crm.Course')
def invalidate_course_cache(sender, **kwargs):
    """Invalidate course-related cache on model changes"""
    try:
        cache.delete('course_list')
        logger.info("Course cache invalidated")
        
    except Exception as e:
        logger.error(f"Failed to invalidate course cache: {e}")