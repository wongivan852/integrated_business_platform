# Business Platform SSO Integration Guide

**Complete Step-by-Step Implementation Guide**
**Date:** October 2, 2025
**Version:** 2.0.0

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Master Platform Setup](#master-platform-setup)
3. [Secondary Apps Setup](#secondary-apps-setup)
4. [Testing SSO](#testing-sso)
5. [Deployment](#deployment)
6. [Troubleshooting](#troubleshooting)

---

## Overview

This guide will help you implement JWT-based Single Sign-On (SSO) across all business applications, eliminating redundant logins.

### Before SSO
- ❌ Login separately to each app
- ❌ Multiple sessions to manage
- ❌ Inconsistent user experience

### After SSO
- ✅ Login once to master platform
- ✅ Access all apps seamlessly
- ✅ Centralized user management

---

## Master Platform Setup

### Step 1: Install Dependencies

```bash
cd /Users/wongivan/ai_tools/business_tools/integrated_business_platform

# Install new requirements
pip install djangorestframework-simplejwt==5.3.0 PyJWT==2.8.0

# Or use the updated requirements file
pip install -r requirements-sso.txt
```

### Step 2: Update Settings

Add to `business_platform/settings.py`:

```python
# Add 'sso' to INSTALLED_APPS
LOCAL_APPS = [
    'core',
    'authentication',
    'dashboard',
    'app_integration',
    'sso',  # NEW
]

# Add SSO middleware AFTER authentication middleware
MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'sso.middleware.SSOTokenInjectionMiddleware',  # NEW - After auth middleware
    'business_platform.middleware.AppAccessMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# Add at the end of settings.py
# ========== SSO Configuration ==========
SSO_SECRET_KEY = config('SSO_SECRET_KEY', default=SECRET_KEY)
SSO_ALGORITHM = 'HS256'
SSO_TOKEN_LIFETIME = 3600  # 1 hour
SSO_REFRESH_LIFETIME = 86400  # 24 hours

# Simple JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(seconds=SSO_TOKEN_LIFETIME),
    'REFRESH_TOKEN_LIFETIME': timedelta(seconds=SSO_REFRESH_LIFETIME),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': False,
    'ALGORITHM': SSO_ALGORITHM,
    'SIGNING_KEY': SSO_SECRET_KEY,
    'VERIFYING_KEY': None,
    'AUTH_HEADER_TYPES': ('Bearer',),
}
```

### Step 3: Update URLs

Update `business_platform/urls.py`:

```python
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('auth/', include('authentication.urls')),
    path('dashboard/', include('dashboard.urls')),
    path('apps/', include('app_integration.urls')),
    path('api/sso/', include('sso.urls')),  # NEW - SSO API endpoints
    path('', include('dashboard.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
```

### Step 4: Create Database Tables

```bash
# Create migrations
python manage.py makemigrations sso

# Apply migrations
python manage.py migrate
```

### Step 5: Update Environment Variables

Create/update `.env`:

```bash
# Generate a secure SSO secret key (use same key across all apps!)
SSO_SECRET_KEY=your-very-secure-256-bit-secret-key-here-change-in-production

# Optional: customize token lifetimes
SSO_TOKEN_LIFETIME=3600
SSO_REFRESH_LIFETIME=86400
```

**Important:** The `SSO_SECRET_KEY` MUST be the same across all applications!

### Step 6: Test SSO Endpoints

```bash
# Start the server
python manage.py runserver

# Test token generation (in another terminal)
curl -X POST http://localhost:8000/api/sso/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}'

# You should get a response with access and refresh tokens
```

---

## Secondary Apps Setup

### For Each Secondary App (Leave, Quotation, Expense, CRM, Asset, Stripe)

### Step 1: Create SSO Integration Module

Create directory structure in each app:

```bash
# Example for company-leave-system
cd /Users/wongivan/ai_tools/business_tools/company-leave-system

# Create SSO module
mkdir -p sso_integration
touch sso_integration/__init__.py
touch sso_integration/backend.py
touch sso_integration/middleware.py
touch sso_integration/utils.py
```

### Step 2: Create SSO Authentication Backend

File: `sso_integration/backend.py`

```python
"""SSO Authentication Backend for secondary apps."""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
import requests
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class SSOBackend(ModelBackend):
    """
    Authenticate users using SSO tokens from master platform.
    """

    def authenticate(self, request, sso_token=None, **kwargs):
        """
        Authenticate user using SSO token.

        Args:
            request: HTTP request
            sso_token: JWT token from master platform

        Returns:
            User instance if authentication successful, None otherwise
        """
        if not sso_token:
            return None

        try:
            # Validate token with master platform
            from django.conf import settings
            master_url = getattr(settings, 'SSO_MASTER_URL', 'http://localhost:8000')
            validate_url = f"{master_url}/api/sso/validate/"

            response = requests.post(
                validate_url,
                json={'token': sso_token},
                headers={'Content-Type': 'application/json'},
                timeout=5
            )

            if response.status_code != 200:
                logger.warning(f"SSO token validation failed: {response.status_code}")
                return None

            data = response.json()

            if not data.get('valid'):
                logger.warning("SSO token is invalid")
                return None

            # Extract user data from response
            user_data = data.get('user', {})
            user_id = user_data.get('id')
            username = user_data.get('username')

            if not username:
                logger.error("No username in SSO response")
                return None

            # Get or create local user
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': user_data.get('email', ''),
                    'first_name': user_data.get('first_name', ''),
                    'last_name': user_data.get('last_name', ''),
                    'is_staff': user_data.get('is_staff', False),
                    'is_superuser': user_data.get('is_superuser', False),
                    'is_active': user_data.get('is_active', True),
                }
            )

            if not created:
                # Update existing user
                user.email = user_data.get('email', user.email)
                user.first_name = user_data.get('first_name', user.first_name)
                user.last_name = user_data.get('last_name', user.last_name)
                user.is_staff = user_data.get('is_staff', user.is_staff)
                user.is_superuser = user_data.get('is_superuser', user.is_superuser)
                user.save()

            # Store SSO data in user object for middleware
            user.sso_data = user_data
            user.sso_payload = data.get('payload', {})

            logger.info(f"SSO authentication successful for user: {username}")
            return user

        except requests.RequestException as e:
            logger.error(f"SSO validation request failed: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"SSO authentication failed: {str(e)}")
            return None

    def get_user(self, user_id):
        """Get user by ID."""
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
```

### Step 3: Create SSO Middleware

File: `sso_integration/middleware.py`

```python
"""SSO Middleware for secondary apps."""
from django.contrib.auth import login
from django.utils.deprecation import MiddlewareMixin
from .backend import SSOBackend
import logging

logger = logging.getLogger(__name__)


class SSOAuthenticationMiddleware(MiddlewareMixin):
    """
    Middleware to automatically authenticate users via SSO token.

    This middleware:
    1. Checks for SSO token in request (URL parameter, cookie, or header)
    2. Validates token with master platform
    3. Automatically logs in the user
    4. Maintains session
    """

    def process_request(self, request):
        """Process incoming request for SSO authentication."""

        # Skip if user is already authenticated
        if request.user.is_authenticated:
            return None

        # Get SSO token from various sources
        sso_token = self._get_sso_token(request)

        if not sso_token:
            return None  # No token, continue to normal auth

        # Authenticate using SSO backend
        backend = SSOBackend()
        user = backend.authenticate(request, sso_token=sso_token)

        if user:
            # Log the user in
            user.backend = 'sso_integration.backend.SSOBackend'
            login(request, user)

            # Store token in session for future requests
            request.session['sso_token'] = sso_token

            logger.info(f"User {user.username} authenticated via SSO")

        return None

    def _get_sso_token(self, request):
        """
        Extract SSO token from request.

        Checks in order:
        1. URL parameter (?sso_token=...)
        2. Authorization header (Bearer token)
        3. Cookie (sso_token)
        4. Session (sso_token)
        """
        # 1. URL parameter
        token = request.GET.get('sso_token')
        if token:
            return token

        # 2. Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]

        # 3. Cookie
        token = request.COOKIES.get('sso_token')
        if token:
            return token

        # 4. Session
        token = request.session.get('sso_token')
        if token:
            return token

        return None
```

### Step 4: Update Settings

For each secondary app, update `settings.py`:

```python
# Add SSO backend to AUTHENTICATION_BACKENDS
AUTHENTICATION_BACKENDS = [
    'sso_integration.backend.SSOBackend',  # NEW - SSO auth (try first)
    'django.contrib.auth.backends.ModelBackend',  # Fallback to local auth
]

# Add SSO middleware AFTER Django's AuthenticationMiddleware
MIDDLEWARE = [
    # ... other middleware ...
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'sso_integration.middleware.SSOAuthenticationMiddleware',  # NEW - After auth
    # ... rest of middleware ...
]

# Add SSO configuration
SSO_ENABLED = True
SSO_MASTER_URL = 'http://localhost:8000'  # Master platform URL
SSO_SECRET_KEY = 'your-very-secure-256-bit-secret-key-here-change-in-production'  # SAME as master!
SSO_FALLBACK_LOCAL_AUTH = True  # Allow local login if SSO fails
```

### Step 5: Create Environment File

For each secondary app, create/update `.env`:

```bash
# SSO Configuration
SSO_ENABLED=True
SSO_MASTER_URL=http://localhost:8000
SSO_SECRET_KEY=your-very-secure-256-bit-secret-key-here-change-in-production
SSO_FALLBACK_LOCAL_AUTH=True
```

### Step 6: Install Dependencies

For each secondary app:

```bash
pip install PyJWT==2.8.0 requests==2.31.0
```

---

## Testing SSO

### Test Flow:

1. **Login to Master Platform**
   ```
   http://localhost:8000/auth/login/
   ```

2. **Access Secondary App with Token**
   ```
   http://localhost:8001/?sso_token=<your_jwt_token>
   ```

3. **Verify Auto-Login**
   - User should be automatically logged in
   - No login page should appear
   - User data should match master platform

### Manual Testing Script:

```bash
#!/bin/bash

# Test SSO Integration

echo "1. Getting SSO token from master platform..."
TOKEN_RESPONSE=$(curl -s -X POST http://localhost:8000/api/sso/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin"}')

ACCESS_TOKEN=$(echo $TOKEN_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['access'])")

echo "✓ Got access token"

echo "2. Testing Leave System (port 8001)..."
curl -s "http://localhost:8001/?sso_token=$ACCESS_TOKEN" | grep -q "Welcome" && echo "✓ Leave System SSO works" || echo "✗ Leave System SSO failed"

echo "3. Testing Quotation System (port 8002)..."
curl -s "http://localhost:8002/?sso_token=$ACCESS_TOKEN" | grep -q "Welcome" && echo "✓ Quotation System SSO works" || echo "✗ Quotation System SSO failed"

echo "4. Testing Expense System (port 8003)..."
curl -s "http://localhost:8003/?sso_token=$ACCESS_TOKEN" | grep -q "Welcome" && echo "✓ Expense System SSO works" || echo "✗ Expense System SSO failed"

echo "5. Testing CRM System (port 8004)..."
curl -s "http://localhost:8004/?sso_token=$ACCESS_TOKEN" | grep -q "Welcome" && echo "✓ CRM System SSO works" || echo "✗ CRM System SSO failed"

echo "6. Testing Asset Management (port 8005)..."
curl -s "http://localhost:8005/?sso_token=$ACCESS_TOKEN" | grep -q "Welcome" && echo "✓ Asset Management SSO works" || echo "✗ Asset Management SSO failed"

echo "7. Testing Stripe Dashboard (port 8006)..."
curl -s "http://localhost:8006/?sso_token=$ACCESS_TOKEN" | grep -q "Welcome" && echo "✓ Stripe Dashboard SSO works" || echo "✗ Stripe Dashboard SSO failed"

echo ""
echo "SSO Integration Test Complete!"
```

---

## Deployment

### Step 1: Set Environment Variables

On your server, set these environment variables for ALL apps:

```bash
export SSO_SECRET_KEY="your-production-secret-key-256-bits"
export SSO_ENABLED=True
export SSO_MASTER_URL=https://your-domain.com
```

**CRITICAL:** Use the SAME `SSO_SECRET_KEY` across all apps!

### Step 2: Deploy Master Platform First

```bash
cd integrated_business_platform
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart business-platform
```

### Step 3: Deploy Secondary Apps

For each app:

```bash
cd company-leave-system
python manage.py migrate  # If needed
sudo systemctl restart leave-system
```

### Step 4: Update Nginx Configuration

Update your nginx config to pass SSO tokens:

```nginx
location /apps/leave/ {
    proxy_pass http://localhost:8001/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;

    # Pass SSO token as parameter
    if ($cookie_sso_token) {
        rewrite ^(.*)$ $1?sso_token=$cookie_sso_token break;
    }
}
```

### Step 5: Verify SSO Works

1. Login to master platform
2. Click on each app in the dashboard
3. Verify you're NOT asked to login again
4. Check user session in each app matches

---

## Troubleshooting

### Issue: "Token validation failed"

**Symptoms:** Cannot login to secondary apps

**Solution:**
1. Verify `SSO_SECRET_KEY` is EXACTLY the same in all apps
2. Check master platform is running and accessible
3. Test token endpoint: `curl http://localhost:8000/api/sso/token/`

### Issue: "User not authenticated after SSO"

**Symptoms:** Token valid but user not logged in

**Solution:**
1. Check SSO backend is in `AUTHENTICATION_BACKENDS`
2. Verify SSO middleware is AFTER `AuthenticationMiddleware`
3. Check app logs for authentication errors

### Issue: "Permission denied in secondary app"

**Symptoms:** User logged in but cannot access features

**Solution:**
1. Check UserProfile permissions in master platform
2. Verify permissions are included in JWT token
3. Update user permissions in master platform admin

### Debug Mode

Enable debug logging in each app's settings.py:

```python
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'sso_integration': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

---

## Quick Reference

### Master Platform SSO Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/api/sso/token/` | POST | Get access/refresh tokens |
| `/api/sso/refresh/` | POST | Refresh access token |
| `/api/sso/validate/` | POST | Validate token |
| `/api/sso/user/` | GET | Get user info |
| `/api/sso/logout/` | POST | Logout and revoke tokens |

### Environment Variables

| Variable | Master | Secondary | Example |
|----------|--------|-----------|---------|
| `SSO_SECRET_KEY` | ✓ | ✓ | `your-256-bit-key` |
| `SSO_MASTER_URL` | ✗ | ✓ | `http://localhost:8000` |
| `SSO_ENABLED` | ✓ | ✓ | `True` |
| `SSO_TOKEN_LIFETIME` | ✓ | ✗ | `3600` (1 hour) |
| `SSO_REFRESH_LIFETIME` | ✓ | ✗ | `86400` (24 hours) |

---

## Next Steps

1. ✅ Review this guide
2. ✅ Implement master platform SSO
3. ✅ Test SSO endpoints
4. ✅ Implement one secondary app
5. ✅ Test integration
6. ✅ Roll out to remaining apps
7. ✅ Deploy to production

---

**Documentation Version:** 2.0.0
**Last Updated:** October 2, 2025
**Status:** ✅ Ready for Implementation

