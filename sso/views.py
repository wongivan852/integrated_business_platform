"""SSO API views for token management."""
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from django.contrib.auth import authenticate, get_user_model
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import jwt

from .utils import SSOTokenManager, SSOPermissionChecker
from .serializers import (
    SSOUserSerializer,
    TokenSerializer,
    TokenRefreshSerializer,
    TokenValidateSerializer
)
from .models import SSOAuditLog

User = get_user_model()


@method_decorator(csrf_exempt, name='dispatch')
class SSOTokenObtainView(APIView):
    """
    Generate SSO tokens for authenticated users.

    POST /api/sso/token/
    {
        "username": "john.doe",
        "password": "password123"
    }

    Returns:
    {
        "access": "jwt_access_token",
        "refresh": "jwt_refresh_token",
        "user": { ... user data ... }
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            SSOAuditLog.log_event(
                'login_failed',
                request=request,
                reason='Missing credentials'
            )
            return Response(
                {'error': 'Username and password are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is None:
            SSOAuditLog.log_event(
                'login_failed',
                request=request,
                username=username,
                reason='Invalid credentials'
            )
            return Response(
                {'error': 'Invalid credentials'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            SSOAuditLog.log_event(
                'login_failed',
                user=user,
                request=request,
                reason='User inactive'
            )
            return Response(
                {'error': 'User account is disabled'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Generate tokens
        tokens = SSOTokenManager.generate_token(user, request)

        # Log successful login
        SSOAuditLog.log_event(
            'login_success',
            user=user,
            request=request,
            token_id=tokens['jti']
        )

        # Serialize user data
        user_serializer = SSOUserSerializer(user)

        return Response({
            'access': tokens['access'],
            'refresh': tokens['refresh'],
            'user': user_serializer.data
        }, status=status.HTTP_200_OK)


@method_decorator(csrf_exempt, name='dispatch')
class SSOTokenRefreshView(APIView):
    """
    Refresh access token using refresh token.

    POST /api/sso/refresh/
    {
        "refresh": "refresh_token"
    }

    Returns:
    {
        "access": "new_jwt_access_token"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response(
                {'error': 'Refresh token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Refresh token
            tokens = SSOTokenManager.refresh_token(refresh_token, request)

            return Response({
                'access': tokens['access']
            }, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError:
            return Response(
                {'error': 'Refresh token has expired'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except jwt.InvalidTokenError as e:
            return Response(
                {'error': f'Invalid refresh token: {str(e)}'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Token refresh failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class SSOTokenValidateView(APIView):
    """
    Validate an SSO token.

    POST /api/sso/validate/
    Authorization: Bearer <token>

    OR

    POST /api/sso/validate/
    {
        "token": "jwt_access_token"
    }

    Returns:
    {
        "valid": true,
        "user": { ... user data ... }
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Get token from Authorization header or request body
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
        else:
            token = request.data.get('token')

        if not token:
            return Response(
                {'error': 'Token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Validate token
            payload = SSOTokenManager.validate_token(token, request)

            # Get user
            user = User.objects.get(id=payload['user_id'])

            # Serialize user data
            user_serializer = SSOUserSerializer(user)

            return Response({
                'valid': True,
                'user': user_serializer.data,
                'payload': payload
            }, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError:
            return Response({
                'valid': False,
                'message': 'Token has expired'
            }, status=status.HTTP_401_UNAUTHORIZED)

        except jwt.InvalidTokenError as e:
            return Response({
                'valid': False,
                'message': f'Invalid token: {str(e)}'
            }, status=status.HTTP_401_UNAUTHORIZED)

        except User.DoesNotExist:
            return Response({
                'valid': False,
                'message': 'User not found'
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                'valid': False,
                'message': f'Validation failed: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@method_decorator(csrf_exempt, name='dispatch')
class SSOUserInfoView(APIView):
    """
    Get current user information from token.

    GET /api/sso/user/
    Authorization: Bearer <token>

    Returns:
    {
        "id": 123,
        "username": "john.doe",
        "email": "john@company.com",
        ... user data ...
    }
    """
    permission_classes = [AllowAny]

    def get(self, request):
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return Response(
                {'error': 'Authorization header required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token = auth_header.split(' ')[1]

        try:
            # Validate token
            payload = SSOTokenManager.validate_token(token, request)

            # Get user
            user = User.objects.get(id=payload['user_id'])

            # Serialize user data
            user_serializer = SSOUserSerializer(user)

            return Response(user_serializer.data, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError:
            return Response(
                {'error': 'Token has expired'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except jwt.InvalidTokenError as e:
            return Response(
                {'error': f'Invalid token: {str(e)}'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            return Response(
                {'error': f'Request failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@method_decorator(csrf_exempt, name='dispatch')
class SSOPermissionCheckView(APIView):
    """
    Check if user has permission to access an app.

    POST /api/sso/check-permission/
    Authorization: Bearer <token>
    {
        "app_name": "leave_system"
    }

    Returns:
    {
        "has_permission": true,
        "app_name": "leave_system"
    }
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Get token from Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            return Response(
                {'error': 'Authorization header required'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        token = auth_header.split(' ')[1]
        app_name = request.data.get('app_name')

        if not app_name:
            return Response(
                {'error': 'app_name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Validate token
            payload = SSOTokenManager.validate_token(token, request)

            # Check permission
            has_permission = SSOPermissionChecker.can_access_app(payload, app_name)

            # Log permission check
            SSOAuditLog.log_event(
                'permission_denied' if not has_permission else 'token_validated',
                user_id=payload.get('user_id'),
                app_name=app_name,
                request=request,
                has_permission=has_permission
            )

            return Response({
                'has_permission': has_permission,
                'app_name': app_name
            }, status=status.HTTP_200_OK)

        except jwt.ExpiredSignatureError:
            return Response(
                {'error': 'Token has expired'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except jwt.InvalidTokenError as e:
            return Response(
                {'error': f'Invalid token: {str(e)}'},
                status=status.HTTP_401_UNAUTHORIZED
            )
        except Exception as e:
            return Response(
                {'error': f'Permission check failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sso_logout(request):
    """
    Logout user and revoke all tokens.

    POST /api/sso/logout/

    Returns:
    {
        "message": "Logged out successfully"
    }
    """
    try:
        # Revoke all user tokens
        SSOTokenManager.revoke_user_tokens(request.user, "User logout")

        # Log event
        SSOAuditLog.log_event(
            'logout',
            user=request.user,
            request=request
        )

        return Response({
            'message': 'Logged out successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({
            'error': f'Logout failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
