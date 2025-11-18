import logging
import time
from django.http import HttpResponseForbidden, JsonResponse
from django.urls import reverse
from django.utils.deprecation import MiddlewareMixin
from django.core.cache import cache
from django.conf import settings
import hashlib

logger = logging.getLogger('crm.security')

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Comprehensive security headers middleware
    """
    
    def process_response(self, request, response):
        # Security headers
        response['X-Content-Type-Options'] = 'nosniff'
        response['X-Frame-Options'] = 'DENY'
        response['X-XSS-Protection'] = '1; mode=block'
        response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response['Content-Security-Policy'] = csp_policy
        
        # HSTS (only for HTTPS)
        if request.is_secure():
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # Permissions Policy
        response['Permissions-Policy'] = (
            "camera=(), "
            "microphone=(), "
            "geolocation=(), "
            "payment=(), "
            "usb=(), "
            "magnetometer=(), "
            "accelerometer=(), "
            "gyroscope=()"
        )
        
        return response


class RateLimitMiddleware(MiddlewareMixin):
    """
    Advanced rate limiting middleware with different limits for different endpoints
    """
    
    RATE_LIMITS = {
        'default': {'requests': 100, 'window': 60},  # 100 requests per minute
        'api': {'requests': 1000, 'window': 3600},   # 1000 requests per hour for API
        'login': {'requests': 5, 'window': 300},     # 5 login attempts per 5 minutes
        'admin': {'requests': 50, 'window': 60},     # 50 requests per minute for admin
        'export': {'requests': 10, 'window': 600},   # 10 exports per 10 minutes
    }
    
    def process_request(self, request):
        # Skip rate limiting for authenticated superusers in development
        if settings.DEBUG and request.user.is_authenticated and request.user.is_superuser:
            return None
            
        client_ip = self.get_client_ip(request)
        endpoint_type = self.get_endpoint_type(request.path)
        
        # Create rate limit key
        rate_key = f"rate_limit:{endpoint_type}:{client_ip}"
        
        # Get rate limit configuration
        rate_config = self.RATE_LIMITS.get(endpoint_type, self.RATE_LIMITS['default'])
        
        # Check current request count
        current_requests = cache.get(rate_key, 0)
        
        if current_requests >= rate_config['requests']:
            logger.warning(
                f"Rate limit exceeded for {client_ip} on {endpoint_type}: "
                f"{current_requests} requests"
            )
            return JsonResponse({
                'error': 'Rate limit exceeded',
                'detail': f'Too many requests. Limit: {rate_config["requests"]} per {rate_config["window"]} seconds'
            }, status=429)
        
        # Increment request count
        cache.set(rate_key, current_requests + 1, rate_config['window'])
        
        return None
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
    
    def get_endpoint_type(self, path):
        """Determine endpoint type for rate limiting"""
        if path.startswith('/api/'):
            return 'api'
        elif path.startswith('/admin/'):
            return 'admin'
        elif 'login' in path:
            return 'login'
        elif 'export' in path or 'download' in path:
            return 'export'
        else:
            return 'default'


class SecurityAuditMiddleware(MiddlewareMixin):
    """
    Security audit logging middleware
    """
    
    SENSITIVE_PATHS = [
        '/admin/',
        '/api/',
        '/accounts/login/',
        '/accounts/logout/',
        '/customers/export/',
        '/customers/import/',
    ]
    
    SUSPICIOUS_PATTERNS = [
        # SQL injection patterns
        r'(\bunion\b|\bselect\b|\binsert\b|\bupdate\b|\bdelete\b|\bdrop\b)',
        # XSS patterns
        r'(<script|javascript:|onload=|onerror=)',
        # Path traversal
        r'(\.\./|\.\.\\)',
        # Command injection
        r'(;|\||&|`|\$\()',
    ]
    
    def process_request(self, request):
        client_ip = self.get_client_ip(request)
        
        # Log sensitive path access
        if any(request.path.startswith(path) for path in self.SENSITIVE_PATHS):
            logger.info(
                f"Sensitive path access: {client_ip} -> {request.method} {request.path}",
                extra={
                    'client_ip': client_ip,
                    'method': request.method,
                    'path': request.path,
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'user': str(request.user) if request.user.is_authenticated else 'anonymous'
                }
            )
        
        # Check for suspicious patterns
        self.check_suspicious_patterns(request)
        
        return None
    
    def process_response(self, request, response):
        # Log failed authentication attempts
        if (request.path.startswith('/accounts/login/') and 
            response.status_code in [401, 403]):
            logger.warning(
                f"Failed login attempt from {self.get_client_ip(request)}",
                extra={
                    'client_ip': self.get_client_ip(request),
                    'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                    'status_code': response.status_code
                }
            )
        
        return response
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '0.0.0.0')
    
    def check_suspicious_patterns(self, request):
        """Check for suspicious patterns in request"""
        import re
        
        # Check query parameters
        query_string = request.META.get('QUERY_STRING', '')
        
        # Check POST data if available
        post_data = ''
        if hasattr(request, 'POST'):
            post_data = str(request.POST)
        
        # Combine all data to check
        data_to_check = f"{query_string} {post_data} {request.path}".lower()
        
        for pattern in self.SUSPICIOUS_PATTERNS:
            if re.search(pattern, data_to_check, re.IGNORECASE):
                logger.critical(
                    f"Suspicious pattern detected from {self.get_client_ip(request)}: {pattern}",
                    extra={
                        'client_ip': self.get_client_ip(request),
                        'path': request.path,
                        'query_string': query_string[:200],  # Limit log size
                        'pattern': pattern,
                        'user_agent': request.META.get('HTTP_USER_AGENT', '')
                    }
                )
                break


class PerformanceMonitoringMiddleware(MiddlewareMixin):
    """
    Performance monitoring middleware
    """
    
    def process_request(self, request):
        request._start_time = time.time()
        return None
    
    def process_response(self, request, response):
        if hasattr(request, '_start_time'):
            duration = time.time() - request._start_time
            
            # Add performance header
            response['X-Response-Time'] = f"{duration:.3f}s"
            
            # Log slow requests
            if duration > 2.0:  # Log requests taking more than 2 seconds
                logger = logging.getLogger('crm.performance')
                logger.warning(
                    f"Slow request: {request.method} {request.path} took {duration:.3f}s",
                    extra={
                        'method': request.method,
                        'path': request.path,
                        'duration': duration,
                        'status_code': response.status_code,
                        'user': str(request.user) if request.user.is_authenticated else 'anonymous'
                    }
                )
        
        return response