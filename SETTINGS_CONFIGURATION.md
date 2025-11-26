# Settings Configuration Analysis
**Date:** November 26, 2025
**Project:** Integrated Business Platform

---

## 1. Settings.py Location

**File:** `/home/user/Desktop/integrated_business_platform/business_platform/settings.py`

---

## 2. Network & Security Settings Found

### ALLOWED_HOSTS
**Line 20 in settings.py:**
```python
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost,127.0.0.1,0.0.0.0,*').split(',')
```

**Configuration:**
- Uses environment variable from `.env` file
- **Default value:** `['localhost', '127.0.0.1', '0.0.0.0', '*']`
- **Current .env value:** `localhost,127.0.0.1,0.0.0.0,*`
- **Status:** ✅ Allows all hosts (wildcard `*`)

### CORS_ALLOWED_ORIGINS
**Lines 200-204 in settings.py:**
```python
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

**Configuration:**
- **CORS_ALLOW_ALL_ORIGINS:** Set to `DEBUG` value (currently `True`)
- **Allowed Origins:** 
  - http://localhost:3000
  - http://127.0.0.1:3000
- **Status:** ✅ Allows all origins when DEBUG=True

### CSRF_TRUSTED_ORIGINS
**Status:** ⚠️ **NOT FOUND in settings.py**

**Available in .env:** 
```bash
CSRF_TRUSTED_ORIGINS=https://dashboard.krystal.technology
```

**Issue:** The CSRF_TRUSTED_ORIGINS variable is defined in `.env` but NOT imported/used in `settings.py`

**Related CSRF Setting Found:**
- Line 304: `CSRF_COOKIE_SECURE = False`

---

## 3. Environment Variables (.env file)

**Location:** `/home/user/Desktop/integrated_business_platform/.env`

### Security Settings
```bash
SECRET_KEY=django-insecure-integrated-platform-key-2025
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,*
CSRF_TRUSTED_ORIGINS=https://dashboard.krystal.technology
```

### Database Configuration
```bash
USE_SQLITE=False
DB_NAME=krystal_platform
DB_USER=platformadmin
DB_PASSWORD=5514
DB_HOST=localhost
DB_PORT=5432
```

### Application Ports
```bash
LEAVE_PORT=8001
QUOTATION_PORT=8002
EXPENSE_PORT=8003
CRM_PORT=8004
ASSET_PORT=8005
STRIPE_PORT=8006
```

### SSO Configuration
```bash
SSO_SECRET_KEY=QrWyU0NmtAj2Ogd1QOPFcl4YSqtMpwQ9HyCV1ebbAlo
```

---

## 4. Recommendations

### CRITICAL: Add CSRF_TRUSTED_ORIGINS to settings.py

The `.env` file contains `CSRF_TRUSTED_ORIGINS` but it's not being loaded in `settings.py`.

**Add to settings.py (around line 21):**
```python
CSRF_TRUSTED_ORIGINS = config('CSRF_TRUSTED_ORIGINS', default='').split(',') if config('CSRF_TRUSTED_ORIGINS', default='') else []
```

Or more explicitly:
```python
CSRF_TRUSTED_ORIGINS = [
    'https://dashboard.krystal.technology',
]
```

### Update ALLOWED_HOSTS for Production

Current setting allows all hosts (`*`). For production, specify exact domains:

```python
ALLOWED_HOSTS = [
    'localhost',
    '127.0.0.1',
    '192.168.0.104',
    'dashboard.krystal.technology',
]
```

### Update CORS for Production Network Access

Add network IP to CORS settings:

```python
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://192.168.0.104:3000",
    "http://192.168.0.104:8000",
    "https://dashboard.krystal.technology",
]
```

---

## 5. Current Configuration Summary

| Setting | In settings.py? | In .env? | Status |
|---------|----------------|----------|--------|
| **ALLOWED_HOSTS** | ✅ Yes (Line 20) | ✅ Yes | ✅ Working |
| **CORS_ALLOWED_ORIGINS** | ✅ Yes (Lines 200-204) | ❌ No | ✅ Working |
| **CSRF_TRUSTED_ORIGINS** | ❌ **NO** | ✅ Yes | ⚠️ **Not Imported** |
| **SECRET_KEY** | ✅ Yes | ✅ Yes | ✅ Working |
| **DEBUG** | ✅ Yes | ✅ Yes | ✅ Working |
| **Database Settings** | ✅ Yes | ✅ Yes | ✅ Working |

---

## 6. Server Information

**Current Running Server:**
- **Location:** `/home/user/Desktop/integrated_business_platform`
- **Port:** 8000
- **IP:** 192.168.0.104
- **Access:** http://192.168.0.104:8000

**Settings File:** `/home/user/Desktop/integrated_business_platform/business_platform/settings.py`
**Environment File:** `/home/user/Desktop/integrated_business_platform/.env`

---

## 7. How settings.py Reads .env

The project uses `python-decouple` to read environment variables:

```python
from decouple import config

# Example usage:
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')
DEBUG = config('DEBUG', default=True, cast=bool)
SECRET_KEY = config('SECRET_KEY', default='insecure-key')
```

---

**Generated:** 2025-11-26
**Status:** Settings analyzed and documented
