# performance_middleware.py - Performance Monitoring Middleware
import time
import logging
from django.conf import settings
from django.db import connection
from django.core.cache import cache

logger = logging.getLogger('crm.performance')

class PerformanceMonitoringMiddleware:
    """Middleware to monitor request performance and database queries"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Skip performance monitoring for static files and admin
        if (request.path.startswith('/static/') or 
            request.path.startswith('/media/') or
            request.path.startswith('/admin/jsi18n/')):
            return self.get_response(request)
        
        # Record start time and query count
        start_time = time.time()
        start_queries = len(connection.queries)
        
        # Process request
        response = self.get_response(request)
        
        # Calculate metrics
        end_time = time.time()
        total_time = end_time - start_time
        query_count = len(connection.queries) - start_queries
        
        # Log slow requests (>1 second)
        if total_time > 1.0:
            logger.warning(
                f"SLOW REQUEST: {request.method} {request.path} "
                f"took {total_time:.3f}s with {query_count} queries"
            )
        
        # Log high query count requests (>20 queries)
        if query_count > 20:
            logger.warning(
                f"HIGH QUERY COUNT: {request.method} {request.path} "
                f"executed {query_count} queries in {total_time:.3f}s"
            )
        
        # Add performance headers for debugging
        if settings.DEBUG:
            response['X-Response-Time'] = f"{total_time:.3f}s"
            response['X-Query-Count'] = str(query_count)
        
        # Log all requests in debug mode
        if settings.DEBUG and total_time > 0.1:  # Log requests >100ms
            logger.info(
                f"REQUEST: {request.method} {request.path} "
                f"- {total_time:.3f}s - {query_count} queries"
            )
        
        return response

class CachePerformanceMiddleware:
    """Middleware to monitor cache performance"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Track cache operations during request
        cache_hits = 0
        cache_misses = 0
        
        # Monkey patch cache methods to count hits/misses
        original_get = cache.get
        original_set = cache.set
        
        def tracked_get(key, default=None, version=None):
            nonlocal cache_hits, cache_misses
            result = original_get(key, default, version)
            if result is not None and result != default:
                cache_hits += 1
            else:
                cache_misses += 1
            return result
        
        def tracked_set(key, value, timeout=None, version=None):
            return original_set(key, value, timeout, version)
        
        # Apply tracking
        cache.get = tracked_get
        cache.set = tracked_set
        
        try:
            response = self.get_response(request)
            
            # Calculate cache efficiency
            total_operations = cache_hits + cache_misses
            if total_operations > 0:
                efficiency = (cache_hits / total_operations) * 100
                
                # Add cache headers for debugging
                if settings.DEBUG:
                    response['X-Cache-Hits'] = str(cache_hits)
                    response['X-Cache-Misses'] = str(cache_misses)
                    response['X-Cache-Efficiency'] = f"{efficiency:.1f}%"
                
                # Log poor cache performance
                if total_operations > 5 and efficiency < 50:
                    logger.warning(
                        f"LOW CACHE EFFICIENCY: {request.path} "
                        f"- {efficiency:.1f}% ({cache_hits}/{total_operations})"
                    )
            
            return response
        
        finally:
            # Restore original methods
            cache.get = original_get
            cache.set = original_set