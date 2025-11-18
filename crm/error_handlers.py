# error_handlers.py - Comprehensive error handling for the CRM system
import logging
from django.http import JsonResponse
from django.core.exceptions import ValidationError, PermissionDenied
from django.db import IntegrityError
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
import traceback

logger = logging.getLogger('crm.errors')
security_logger = logging.getLogger('crm.security')


class CRMException(Exception):
    """Base exception class for CRM-specific errors"""
    def __init__(self, message, error_code=None, details=None):
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        super().__init__(self.message)


class CustomerNotFoundError(CRMException):
    """Raised when a customer cannot be found"""
    pass


class CommunicationError(CRMException):
    """Raised when communication services fail"""
    pass


class ValidationError(CRMException):
    """Raised when data validation fails"""
    pass


def custom_exception_handler(exc, context):
    """
    Custom exception handler for REST framework
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    # Log the exception
    request = context.get('request')
    user = getattr(request, 'user', None)
    
    error_data = {
        'exception_type': type(exc).__name__,
        'message': str(exc),
        'path': getattr(request, 'path', ''),
        'method': getattr(request, 'method', ''),
        'user': str(user) if user and user.is_authenticated else 'Anonymous',
    }
    
    if response is not None:
        # Standard DRF exception
        logger.error(f"API Error: {error_data}", extra=error_data)
        
        # Customize error response format
        custom_response_data = {
            'error': True,
            'error_type': type(exc).__name__,
            'message': 'An error occurred processing your request',
            'details': response.data,
            'status_code': response.status_code
        }
        
        response.data = custom_response_data
        
    else:
        # Handle non-DRF exceptions
        if isinstance(exc, CRMException):
            logger.error(f"CRM Error: {error_data}", extra=error_data)
            return Response({
                'error': True,
                'error_type': type(exc).__name__,
                'message': exc.message,
                'error_code': exc.error_code,
                'details': exc.details
            }, status=status.HTTP_400_BAD_REQUEST)
            
        elif isinstance(exc, ValidationError):
            logger.warning(f"Validation Error: {error_data}", extra=error_data)
            return Response({
                'error': True,
                'error_type': 'ValidationError',
                'message': 'Invalid data provided',
                'details': str(exc)
            }, status=status.HTTP_400_BAD_REQUEST)
            
        elif isinstance(exc, PermissionDenied):
            security_logger.warning(f"Permission Denied: {error_data}", extra=error_data)
            return Response({
                'error': True,
                'error_type': 'PermissionDenied',
                'message': 'You do not have permission to perform this action'
            }, status=status.HTTP_403_FORBIDDEN)
            
        elif isinstance(exc, IntegrityError):
            logger.error(f"Database Integrity Error: {error_data}", extra=error_data)
            return Response({
                'error': True,
                'error_type': 'IntegrityError',
                'message': 'A database constraint was violated'
            }, status=status.HTTP_400_BAD_REQUEST)
            
        else:
            # Log unexpected errors with full traceback
            error_data['traceback'] = traceback.format_exc()
            logger.error(f"Unexpected Error: {error_data}", extra=error_data)
            
            return Response({
                'error': True,
                'error_type': 'InternalServerError',
                'message': 'An unexpected error occurred'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    return response


def handle_communication_error(func):
    """
    Decorator for handling communication service errors
    """
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Communication error in {func.__name__}: {str(e)}")
            raise CommunicationError(
                message=f"Communication service error: {str(e)}",
                error_code='COMM_ERROR',
                details={'function': func.__name__, 'original_error': str(e)}
            )
    return wrapper


def safe_execute(func, default_return=None, log_errors=True):
    """
    Safely execute a function and return default value on error
    """
    try:
        return func()
    except Exception as e:
        if log_errors:
            logger.error(f"Safe execution failed: {str(e)}")
        return default_return


class ErrorContext:
    """
    Context manager for error handling
    """
    def __init__(self, operation_name, log_success=False):
        self.operation_name = operation_name
        self.log_success = log_success
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            logger.error(f"Error in {self.operation_name}: {str(exc_val)}")
            return False  # Re-raise the exception
        elif self.log_success:
            logger.info(f"Successfully completed {self.operation_name}")
        return True


# Utility functions for common error scenarios
def validate_required_fields(data, required_fields):
    """
    Validate that all required fields are present and not empty
    """
    missing_fields = []
    for field in required_fields:
        if field not in data or not data[field]:
            missing_fields.append(field)
    
    if missing_fields:
        raise ValidationError(
            message=f"Missing required fields: {', '.join(missing_fields)}",
            error_code='MISSING_FIELDS',
            details={'missing_fields': missing_fields}
        )


def validate_email_format(email):
    """
    Validate email format
    """
    import re
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        raise ValidationError(
            message=f"Invalid email format: {email}",
            error_code='INVALID_EMAIL',
            details={'email': email}
        )


def validate_phone_format(phone):
    """
    Validate phone number format
    """
    import re
    # Basic international phone number validation
    phone_pattern = r'^\+?[1-9]\d{1,14}$'
    if not re.match(phone_pattern, phone.replace(' ', '').replace('-', '')):
        raise ValidationError(
            message=f"Invalid phone format: {phone}",
            error_code='INVALID_PHONE',
            details={'phone': phone}
        )