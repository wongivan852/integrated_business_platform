# 🔧 Stripe Dashboard Integration - DEBUG COMPLETE

## Problem Identified

The Stripe Dashboard integration was failing due to a **port mismatch**:

```
❌ BEFORE:
- Django Platform running on: port 8000
- Stripe Dashboard running on: port 8006  
- Stripe SSO configured for: port 8080
- Result: SSO redirect failed (404 error)

✅ AFTER:
- Django Platform running on: port 8080 (FIXED)
- Stripe Dashboard running on: port 8006
- Stripe SSO configured for: port 8080
- Result: SSO redirect works perfectly
```

## Root Cause

The integrated business platform was started on port **8000** instead of the correct port **8080**. All the integrated apps (Stripe, CRM, Leave System, etc.) are configured to use SSO authentication on port **8080**.

## Solution Applied

### 1. Stopped Django Platform on Wrong Port
```bash
ps aux | grep "manage.py runserver.*8000"
kill [PID]
```

### 2. Started Django Platform on Correct Port
```bash
cd /home/user/Desktop/integrated_business_platform
source venv/bin/activate
python manage.py runserver 0.0.0.0:8080
```

### 3. Verified Integration
- ✅ Django platform accessible on http://localhost:8080/
- ✅ Stripe dashboard accessible on http://localhost:8006/
- ✅ SSO redirect working: 8006 → 8080/auth/login/
- ✅ ApplicationConfig active and configured correctly
- ✅ Users granted access to Stripe dashboard

## Current Status: ✅ WORKING

### Platform Configuration
```
┌─────────────────────────────────────────┐
│  Django Business Platform               │
│  Port: 8080 ✅                          │
│  URL: http://localhost:8080/            │
│  - SSO Authentication Hub               │
│  - User Access Control                  │
│  - Application Dashboard                │
└─────────────┬───────────────────────────┘
              │
              │ SSO Authentication
              │ (redirect for login)
              ↓
┌─────────────────────────────────────────┐
│  Stripe Dashboard (Flask)               │
│  Port: 8006 ✅                          │
│  URL: http://localhost:8006/            │
│  - Transaction Analytics                │
│  - Monthly Statements                   │
│  - Payout Reconciliation                │
└─────────────────────────────────────────┘
```

### SSO Flow
```
1. User clicks "Stripe Dashboard" card on platform dashboard
2. Browser navigates to: http://localhost:8006/
3. Stripe app detects no auth session
4. Stripe redirects to: http://localhost:8080/auth/login/?app=stripe_dashboard&return_to=http://localhost:8006/
5. User logs in on Django platform (port 8080)
6. Django creates SSO token
7. User redirected back to: http://localhost:8006/
8. Stripe app validates SSO token
9. User sees Stripe dashboard
```

## How to Access

### 1. Ensure Platform is Running on Port 8080
```bash
cd /home/user/Desktop/integrated_business_platform
source venv/bin/activate
python manage.py runserver 0.0.0.0:8080
```

### 2. Open Browser
```
http://localhost:8080/
```

### 3. Login
Use any of these accounts:
- admin@krystal-platform.com
- ivan.wong@krystal.institute
- pm-admin@krystal.institute

### 4. Click "Stripe Dashboard" Card
You'll see a card with the Stripe icon (purple). Click "Launch App".

### 5. Access Stripe Features
- Transaction analytics
- Monthly statements
- Payout reconciliation
- Customer/subscription management
- CSV import/export

## Verification Checklist

- [x] Django platform running on port 8080
- [x] Stripe dashboard running on port 8006
- [x] ApplicationConfig is active
- [x] Users have access granted
- [x] SSO redirect working (8006 → 8080)
- [x] Login page loads correctly
- [x] Stripe dashboard accessible after login

## Configuration Files

### ApplicationConfig (Database)
```python
{
    'name': 'stripe_dashboard',
    'display_name': 'Stripe Dashboard',
    'url': 'http://localhost:8006/',
    'icon': 'fab fa-stripe-s',
    'is_active': True,
    'color': '#635bff'
}
```

### BUSINESS_APPS (settings.py)
```python
'stripe_dashboard': {
    'name': 'Stripe Dashboard',
    'description': 'Payment processing and financial reports',
    'path': '/apps/stripe/',
    'icon': 'fab fa-stripe-s',
    'color': '#635bff',
    'internal_port': 8006,
    'app_root': '../stripe-dashboard/',
}
```

## Common Issues and Solutions

### Issue: Platform not accessible on port 8080
**Solution**: Check if platform is running
```bash
ps aux | grep "manage.py runserver"
netstat -tlnp | grep 8080
```

### Issue: Stripe dashboard returns 404
**Solution**: Check if Stripe Flask app is running
```bash
ps aux | grep stripe
lsof -i :8006
```

### Issue: SSO redirect fails
**Solution**: Verify platform is on port 8080 (not 8000 or other port)
```bash
curl -s http://localhost:8080/ | head -5
```

### Issue: User doesn't see Stripe Dashboard card
**Solution**: Grant user access
```bash
python manage.py shell
>>> from authentication.models import CompanyUser
>>> user = CompanyUser.objects.get(username='your_username')
>>> if 'stripe_dashboard' not in user.apps_access:
...     user.apps_access.append('stripe_dashboard')
...     user.save()
```

## Important Notes

1. **Always run Django platform on port 8080** - This is the SSO authentication hub port
2. **Don't change Stripe app port 8006** - It's correctly configured
3. **Stripe app is mature and production-ready** - No code changes needed
4. **SSO is automatic** - No additional configuration required

## Documentation Reference

See `KRYSTAL_PLATFORM_DOCUMENTATION.md` for complete platform setup:
- Lines 15: Shows port 8080 as master SSO hub
- Lines 118: SSO_BASE_URL=http://localhost:8080
- Lines 140: Correct startup command using port 8080
- Lines 175-180: Platform port configuration

## Quick Start Command

```bash
# Start the platform on correct port
cd /home/user/Desktop/integrated_business_platform
source venv/bin/activate
python manage.py runserver 0.0.0.0:8080

# Access in browser
# http://localhost:8080/
```

---

**Debug Date**: 2025-11-03  
**Issue**: Port mismatch (8000 vs 8080)  
**Status**: ✅ FIXED  
**Solution**: Started Django platform on correct port 8080  
**Result**: Stripe Dashboard integration fully operational
