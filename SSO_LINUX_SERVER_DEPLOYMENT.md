# SSO System - Linux Server Deployment Guide

**Complete Production Deployment on Linux Server**
**Version:** 2.0.0
**Target:** Ubuntu/Debian/RHEL/CentOS Linux Servers
**Date:** October 2, 2025

---

## 📋 Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Preparation](#server-preparation)
3. [Master Platform Deployment](#master-platform-deployment)
4. [Secondary Apps Deployment](#secondary-apps-deployment)
5. [Nginx Configuration](#nginx-configuration)
6. [SSL/HTTPS Setup](#sslhttps-setup)
7. [Systemd Services](#systemd-services)
8. [Database Setup](#database-setup)
9. [Testing & Verification](#testing--verification)
10. [Monitoring & Maintenance](#monitoring--maintenance)
11. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### System Requirements

**Minimum:**
- OS: Ubuntu 20.04+ / Debian 11+ / RHEL 8+ / CentOS 8+
- CPU: 4 cores
- RAM: 8GB
- Storage: 50GB SSD
- Network: 100 Mbps

**Recommended:**
- OS: Ubuntu 22.04 LTS
- CPU: 8 cores
- RAM: 16GB
- Storage: 100GB SSD
- Network: 1 Gbps

### Software Requirements

```bash
# Required packages
- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Nginx 1.20+
- Git
- Supervisor or Systemd
```

---

## Server Preparation

### Step 1: Update System

```bash
# Ubuntu/Debian
sudo apt update && sudo apt upgrade -y

# RHEL/CentOS
sudo dnf update -y
```

### Step 2: Install Required Packages

```bash
# Ubuntu/Debian
sudo apt install -y python3 python3-pip python3-venv \
    postgresql postgresql-contrib \
    redis-server \
    nginx \
    git \
    supervisor \
    build-essential \
    libpq-dev \
    python3-dev

# RHEL/CentOS
sudo dnf install -y python3 python3-pip python3-virtualenv \
    postgresql-server postgresql-contrib \
    redis \
    nginx \
    git \
    supervisor \
    gcc \
    postgresql-devel \
    python3-devel
```

### Step 3: Create Application User

```bash
# Create dedicated user for applications
sudo useradd -m -s /bin/bash appadmin
sudo usermod -aG sudo appadmin  # Optional: if you need sudo access

# Switch to application user
sudo su - appadmin
```

### Step 4: Create Directory Structure

```bash
# Create base directories
mkdir -p ~/apps
mkdir -p ~/logs
mkdir -p ~/backups
mkdir -p ~/venvs
mkdir -p ~/configs

# Set permissions
chmod 755 ~/apps
chmod 755 ~/logs
```

---

## Master Platform Deployment

### Step 1: Clone Repository

```bash
cd ~/apps
git clone https://gitlab.kryedu.org/company_apps/integrated_business_platform.git
cd integrated_business_platform
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv ~/venvs/master-platform
source ~/venvs/master-platform/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 3: Install Dependencies

```bash
# Install SSO-enabled requirements
pip install -r requirements-sso.txt

# Verify installation
pip list | grep -E "Django|djangorestframework|PyJWT"
```

### Step 4: Configure Environment

```bash
# Create .env file
cat > .env << 'EOF'
# Django Settings
DEBUG=False
SECRET_KEY=your-production-secret-key-change-this-immediately
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,server-ip

# Database Configuration
DB_NAME=business_platform_db
DB_USER=business_platform_user
DB_PASSWORD=secure-database-password-change-this
DB_HOST=localhost
DB_PORT=5432

# SSO Configuration (CRITICAL: Use same key across ALL apps!)
SSO_SECRET_KEY=your-very-secure-256-bit-sso-secret-key-change-this
SSO_TOKEN_LIFETIME=3600
SSO_REFRESH_LIFETIME=86400
SSO_ALGORITHM=HS256

# CORS Settings
CORS_ALLOWED_ORIGINS=https://your-domain.com,https://www.your-domain.com

# Security Settings
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True
SECURE_SSL_REDIRECT=True
EOF

# Secure the environment file
chmod 600 .env
```

### Step 5: Generate Secure Keys

```bash
# Generate Django SECRET_KEY
python3 << 'PYEOF'
from django.core.management.utils import get_random_secret_key
print(f"SECRET_KEY={get_random_secret_key()}")
PYEOF

# Generate SSO_SECRET_KEY (256-bit)
python3 << 'PYEOF'
import secrets
print(f"SSO_SECRET_KEY={secrets.token_urlsafe(32)}")
PYEOF

# Update .env file with generated keys
# IMPORTANT: Save the SSO_SECRET_KEY - you'll need it for ALL apps!
```

### Step 6: Setup Database

```bash
# Create database and user
sudo -u postgres psql << 'EOF'
CREATE DATABASE business_platform_db;
CREATE USER business_platform_user WITH PASSWORD 'secure-database-password-change-this';
ALTER ROLE business_platform_user SET client_encoding TO 'utf8';
ALTER ROLE business_platform_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE business_platform_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE business_platform_db TO business_platform_user;
\q
EOF
```

### Step 7: Run Migrations

```bash
# Activate virtual environment
source ~/venvs/master-platform/bin/activate

# Run migrations
python manage.py migrate

# Create SSO tables
python manage.py makemigrations sso
python manage.py migrate sso

# Create superuser
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### Step 8: Test Application

```bash
# Test server runs
python manage.py runserver 0.0.0.0:8000

# In another terminal, test SSO endpoint
curl http://localhost:8000/api/sso/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}'

# Should return JWT tokens
# Press Ctrl+C to stop test server
```

---

## Secondary Apps Deployment

### General Process for Each App

**Apps to Deploy:**
1. company-leave-system (Port 8001)
2. company-cost-quotation-system (Port 8002)
3. company_expense_claim_system (Port 8003)
4. company_crm_system (Port 8004)
5. company_asset_management (Port 8005)
6. stripe-dashboard (Port 8006)

### Step 1: Clone App Repository

```bash
# Example for Leave System
cd ~/apps
git clone https://gitlab.kryedu.org/company_apps/company-leave-system.git
cd company-leave-system
```

### Step 2: Create Virtual Environment

```bash
# Create app-specific virtual environment
python3 -m venv ~/venvs/leave-system
source ~/venvs/leave-system/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
pip install PyJWT==2.8.0 requests==2.31.0  # SSO dependencies
```

### Step 3: Create SSO Integration Module

```bash
# Create SSO module
mkdir -p sso_integration
touch sso_integration/__init__.py

# Create backend.py
cat > sso_integration/backend.py << 'PYEOF'
"""SSO Authentication Backend for secondary apps."""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
import requests
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class SSOBackend(ModelBackend):
    """Authenticate users using SSO tokens from master platform."""

    def authenticate(self, request, sso_token=None, **kwargs):
        if not sso_token:
            return None

        try:
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
                return None

            user_data = data.get('user', {})
            username = user_data.get('username')

            if not username:
                return None

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
                user.email = user_data.get('email', user.email)
                user.first_name = user_data.get('first_name', user.first_name)
                user.last_name = user_data.get('last_name', user.last_name)
                user.is_staff = user_data.get('is_staff', user.is_staff)
                user.save()

            user.sso_data = user_data
            logger.info(f"SSO authentication successful for user: {username}")
            return user

        except Exception as e:
            logger.error(f"SSO authentication failed: {str(e)}")
            return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
PYEOF

# Create middleware.py
cat > sso_integration/middleware.py << 'PYEOF'
"""SSO Middleware for secondary apps."""
from django.contrib.auth import login
from django.utils.deprecation import MiddlewareMixin
from .backend import SSOBackend
import logging

logger = logging.getLogger(__name__)


class SSOAuthenticationMiddleware(MiddlewareMixin):
    """Automatically authenticate users via SSO token."""

    def process_request(self, request):
        if request.user.is_authenticated:
            return None

        sso_token = self._get_sso_token(request)
        if not sso_token:
            return None

        backend = SSOBackend()
        user = backend.authenticate(request, sso_token=sso_token)

        if user:
            user.backend = 'sso_integration.backend.SSOBackend'
            login(request, user)
            request.session['sso_token'] = sso_token
            logger.info(f"User {user.username} authenticated via SSO")

        return None

    def _get_sso_token(self, request):
        # Check URL parameter
        token = request.GET.get('sso_token')
        if token:
            return token

        # Check Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            return auth_header.split(' ')[1]

        # Check cookie
        token = request.COOKIES.get('sso_token')
        if token:
            return token

        # Check session
        token = request.session.get('sso_token')
        if token:
            return token

        return None
PYEOF
```

### Step 4: Update Settings

```bash
# Add to settings.py (find the appropriate locations and add these lines)

# In AUTHENTICATION_BACKENDS section (add at the top of the list):
cat >> settings_addition.txt << 'EOF'

# SSO Authentication Backends
AUTHENTICATION_BACKENDS = [
    'sso_integration.backend.SSOBackend',  # SSO auth (try first)
    'django.contrib.auth.backends.ModelBackend',  # Fallback to local auth
]

# SSO Configuration
SSO_ENABLED = True
SSO_MASTER_URL = os.environ.get('SSO_MASTER_URL', 'http://localhost:8000')
SSO_SECRET_KEY = os.environ.get('SSO_SECRET_KEY', SECRET_KEY)
SSO_FALLBACK_LOCAL_AUTH = True
EOF

# Note: Manually add SSO middleware to MIDDLEWARE list after AuthenticationMiddleware
# Example:
# MIDDLEWARE = [
#     ...
#     'django.contrib.auth.middleware.AuthenticationMiddleware',
#     'sso_integration.middleware.SSOAuthenticationMiddleware',  # Add this line
#     ...
# ]
```

### Step 5: Configure Environment

```bash
# Create .env file for secondary app
cat > .env << 'EOF'
# App Settings
DEBUG=False
SECRET_KEY=app-specific-secret-key-change-this
ALLOWED_HOSTS=your-domain.com,server-ip

# Database (if app has its own DB)
DB_NAME=leave_system_db
DB_USER=leave_system_user
DB_PASSWORD=secure-password-change-this
DB_HOST=localhost
DB_PORT=5432

# SSO Configuration (MUST match master platform!)
SSO_ENABLED=True
SSO_MASTER_URL=http://localhost:8000
SSO_SECRET_KEY=SAME-SSO-SECRET-KEY-AS-MASTER-PLATFORM
SSO_FALLBACK_LOCAL_AUTH=True
EOF

chmod 600 .env
```

### Step 6: Run Migrations

```bash
# Activate virtual environment
source ~/venvs/leave-system/bin/activate

# Run migrations
python manage.py migrate

# Create superuser (optional, for fallback local auth)
python manage.py createsuperuser

# Collect static files
python manage.py collectstatic --noinput
```

### Step 7: Repeat for All Apps

Repeat Steps 1-6 for each secondary app:
- company-cost-quotation-system (Port 8002)
- company_expense_claim_system (Port 8003)
- company_crm_system (Port 8004)
- company_asset_management (Port 8005)
- stripe-dashboard (Port 8006)

**Remember:** Use the SAME `SSO_SECRET_KEY` in ALL apps!

---

## Systemd Services

### Step 1: Create Service Files

#### Master Platform Service

```bash
sudo tee /etc/systemd/system/business-platform.service > /dev/null << 'EOF'
[Unit]
Description=Business Platform Master Application
After=network.target postgresql.service redis.service

[Service]
Type=notify
User=appadmin
Group=appadmin
WorkingDirectory=/home/appadmin/apps/integrated_business_platform
Environment="PATH=/home/appadmin/venvs/master-platform/bin"
ExecStart=/home/appadmin/venvs/master-platform/bin/gunicorn \
    --workers 4 \
    --threads 2 \
    --worker-class gthread \
    --bind 127.0.0.1:8000 \
    --timeout 300 \
    --access-logfile /home/appadmin/logs/master-access.log \
    --error-logfile /home/appadmin/logs/master-error.log \
    business_platform.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

#### Leave System Service

```bash
sudo tee /etc/systemd/system/leave-system.service > /dev/null << 'EOF'
[Unit]
Description=Company Leave System
After=network.target postgresql.service

[Service]
Type=notify
User=appadmin
Group=appadmin
WorkingDirectory=/home/appadmin/apps/company-leave-system
Environment="PATH=/home/appadmin/venvs/leave-system/bin"
ExecStart=/home/appadmin/venvs/leave-system/bin/gunicorn \
    --workers 2 \
    --bind 127.0.0.1:8001 \
    --timeout 300 \
    --access-logfile /home/appadmin/logs/leave-access.log \
    --error-logfile /home/appadmin/logs/leave-error.log \
    leave_system.wsgi:application

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

### Step 2: Create Services for Other Apps

Create similar service files for:
- `quotation-system.service` (Port 8002)
- `expense-system.service` (Port 8003)
- `crm-system.service` (Port 8004)
- `asset-system.service` (Port 8005)
- `stripe-dashboard.service` (Port 8006)

### Step 3: Enable and Start Services

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable business-platform
sudo systemctl enable leave-system
sudo systemctl enable quotation-system
sudo systemctl enable expense-system
sudo systemctl enable crm-system
sudo systemctl enable asset-system
sudo systemctl enable stripe-dashboard

# Start services
sudo systemctl start business-platform
sudo systemctl start leave-system
sudo systemctl start quotation-system
sudo systemctl start expense-system
sudo systemctl start crm-system
sudo systemctl start asset-system
sudo systemctl start stripe-dashboard

# Check status
sudo systemctl status business-platform
sudo systemctl status leave-system
# ... check others
```

---

## Nginx Configuration

### Step 1: Create Main Configuration

```bash
sudo tee /etc/nginx/sites-available/business-platform << 'EOF'
upstream master_platform {
    server 127.0.0.1:8000;
}

upstream leave_system {
    server 127.0.0.1:8001;
}

upstream quotation_system {
    server 127.0.0.1:8002;
}

upstream expense_system {
    server 127.0.0.1:8003;
}

upstream crm_system {
    server 127.0.0.1:8004;
}

upstream asset_system {
    server 127.0.0.1:8005;
}

upstream stripe_dashboard {
    server 127.0.0.1:8006;
}

server {
    listen 80;
    server_name your-domain.com www.your-domain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL Configuration (update paths)
    ssl_certificate /etc/ssl/certs/your-domain.crt;
    ssl_certificate_key /etc/ssl/private/your-domain.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security Headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/business-platform-access.log;
    error_log /var/log/nginx/business-platform-error.log;

    # File upload limits
    client_max_body_size 100M;
    client_body_timeout 300s;

    # Master Platform (main)
    location / {
        proxy_pass http://master_platform;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }

    # SSO API endpoints
    location /api/sso/ {
        proxy_pass http://master_platform;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Leave System
    location /apps/leave/ {
        rewrite ^/apps/leave/(.*)$ /$1 break;
        proxy_pass http://leave_system;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Pass SSO token
        if ($cookie_sso_token) {
            set $args $args&sso_token=$cookie_sso_token;
        }
    }

    # Quotation System
    location /apps/quotations/ {
        rewrite ^/apps/quotations/(.*)$ /$1 break;
        proxy_pass http://quotation_system;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Expense System
    location /apps/expenses/ {
        rewrite ^/apps/expenses/(.*)$ /$1 break;
        proxy_pass http://expense_system;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # CRM System
    location /apps/crm/ {
        rewrite ^/apps/crm/(.*)$ /$1 break;
        proxy_pass http://crm_system;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Asset System
    location /apps/assets/ {
        rewrite ^/apps/assets/(.*)$ /$1 break;
        proxy_pass http://asset_system;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Stripe Dashboard
    location /apps/stripe/ {
        rewrite ^/apps/stripe/(.*)$ /$1 break;
        proxy_pass http://stripe_dashboard;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Static files for master platform
    location /static/ {
        alias /home/appadmin/apps/integrated_business_platform/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/appadmin/apps/integrated_business_platform/media/;
        expires 1d;
    }
}
EOF
```

### Step 2: Enable Site

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/business-platform /etc/nginx/sites-enabled/

# Remove default site
sudo rm -f /etc/nginx/sites-enabled/default

# Test configuration
sudo nginx -t

# Reload nginx
sudo systemctl reload nginx
```

---

## SSL/HTTPS Setup

### Option 1: Let's Encrypt (Free, Recommended)

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Auto-renewal is configured automatically
# Test renewal
sudo certbot renew --dry-run
```

### Option 2: Custom SSL Certificate

```bash
# Copy your certificate files
sudo cp your-domain.crt /etc/ssl/certs/
sudo cp your-domain.key /etc/ssl/private/

# Set permissions
sudo chmod 644 /etc/ssl/certs/your-domain.crt
sudo chmod 600 /etc/ssl/private/your-domain.key

# Update nginx configuration with correct paths
```

---

## Testing & Verification

### Step 1: Check Services

```bash
# Check all services are running
sudo systemctl status business-platform
sudo systemctl status leave-system
sudo systemctl status quotation-system
sudo systemctl status expense-system
sudo systemctl status crm-system
sudo systemctl status asset-system
sudo systemctl status stripe-dashboard
```

### Step 2: Test SSO Endpoints

```bash
# Test token generation
curl -X POST https://your-domain.com/api/sso/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"your_password"}' \
  -k  # Remove -k in production with valid SSL

# Save the token from response
TOKEN="<access_token_from_response>"

# Test token validation
curl -X POST https://your-domain.com/api/sso/validate/ \
  -H "Content-Type: application/json" \
  -d "{\"token\":\"$TOKEN\"}" \
  -k
```

### Step 3: Test SSO Integration

```bash
# Test each app with SSO token
curl "https://your-domain.com/apps/leave/?sso_token=$TOKEN" -k
curl "https://your-domain.com/apps/quotations/?sso_token=$TOKEN" -k
curl "https://your-domain.com/apps/expenses/?sso_token=$TOKEN" -k
curl "https://your-domain.com/apps/crm/?sso_token=$TOKEN" -k
curl "https://your-domain.com/apps/assets/?sso_token=$TOKEN" -k
curl "https://your-domain.com/apps/stripe/?sso_token=$TOKEN" -k
```

### Step 4: Web Browser Testing

1. Open browser to `https://your-domain.com`
2. Login with credentials
3. Click on each app in dashboard
4. Verify you're NOT asked to login again
5. Check browser console for errors

---

## Monitoring & Maintenance

### Setup Log Rotation

```bash
sudo tee /etc/logrotate.d/business-platform << 'EOF'
/home/appadmin/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 appadmin appadmin
    sharedscripts
    postrotate
        systemctl reload nginx > /dev/null 2>&1 || true
        systemctl reload business-platform > /dev/null 2>&1 || true
    endscript
}
EOF
```

### Setup Automated Backups

```bash
# Create backup script
cat > ~/backups/backup.sh << 'BASHEOF'
#!/bin/bash
DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR=~/backups

# Backup databases
sudo -u postgres pg_dump business_platform_db > $BACKUP_DIR/master_db_$DATE.sql

# Backup application code
tar -czf $BACKUP_DIR/apps_$DATE.tar.gz ~/apps/

# Keep only last 7 days
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete
BASHEOF

chmod +x ~/backups/backup.sh

# Add to crontab
crontab -e
# Add this line: 0 2 * * * /home/appadmin/backups/backup.sh
```

### Monitoring Script

```bash
cat > ~/monitor.sh << 'BASHEOF'
#!/bin/bash
echo "=== Business Platform Status ==="
echo ""
echo "Services:"
systemctl is-active business-platform && echo "✓ Master Platform" || echo "✗ Master Platform"
systemctl is-active leave-system && echo "✓ Leave System" || echo "✗ Leave System"
systemctl is-active quotation-system && echo "✓ Quotation System" || echo "✗ Quotation System"
systemctl is-active expense-system && echo "✓ Expense System" || echo "✗ Expense System"
systemctl is-active crm-system && echo "✓ CRM System" || echo "✗ CRM System"
systemctl is-active asset-system && echo "✓ Asset System" || echo "✗ Asset System"
systemctl is-active stripe-dashboard && echo "✓ Stripe Dashboard" || echo "✗ Stripe Dashboard"
systemctl is-active nginx && echo "✓ Nginx" || echo "✗ Nginx"
systemctl is-active postgresql && echo "✓ PostgreSQL" || echo "✗ PostgreSQL"
systemctl is-active redis && echo "✓ Redis" || echo "✗ Redis"
echo ""
echo "Disk Usage:"
df -h | grep -E "/$|/home"
echo ""
echo "Memory Usage:"
free -h
BASHEOF

chmod +x ~/monitor.sh
```

---

## Troubleshooting

### Service Won't Start

```bash
# Check logs
sudo journalctl -u business-platform -n 50
sudo journalctl -u leave-system -n 50

# Check error logs
tail -f ~/logs/master-error.log
tail -f ~/logs/leave-error.log
```

### SSO Token Validation Fails

```bash
# Verify SSO_SECRET_KEY is the same in all apps
grep SSO_SECRET_KEY ~/apps/*/. env

# Check master platform is accessible
curl http://localhost:8000/api/sso/validate/

# Check logs
tail -f ~/logs/master-error.log | grep -i sso
```

### Database Connection Issues

```bash
# Test PostgreSQL connection
psql -U business_platform_user -d business_platform_db -h localhost

# Check PostgreSQL is running
sudo systemctl status postgresql

# Review PostgreSQL logs
sudo tail -f /var/log/postgresql/postgresql-*.log
```

### Permission Errors

```bash
# Fix ownership
sudo chown -R appadmin:appadmin ~/apps
sudo chown -R appadmin:appadmin ~/logs

# Fix permissions
chmod 755 ~/apps
chmod 755 ~/logs
```

---

## Quick Reference Commands

```bash
# Restart all services
sudo systemctl restart business-platform leave-system quotation-system expense-system crm-system asset-system stripe-dashboard nginx

# View logs
tail -f ~/logs/master-error.log
tail -f /var/log/nginx/business-platform-error.log

# Check SSO status
~/monitor.sh

# Backup now
~/backups/backup.sh

# Update applications
cd ~/apps/integrated_business_platform && git pull
sudo systemctl restart business-platform
```

---

## Post-Deployment Checklist

- [ ] All services running
- [ ] SSL certificate installed
- [ ] SSO tokens working
- [ ] All apps accessible
- [ ] Database backups configured
- [ ] Log rotation configured
- [ ] Monitoring setup
- [ ] Firewall configured
- [ ] DNS records updated
- [ ] Admin users created
- [ ] Documentation reviewed
- [ ] Team trained

---

## Security Hardening

```bash
# Configure firewall
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp  # HTTPS
sudo ufw enable

# Disable password authentication for SSH (use keys only)
sudo sed -i 's/PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart sshd

# Set up fail2ban
sudo apt install fail2ban -y
sudo systemctl enable fail2ban
sudo systemctl start fail2ban
```

---

## Production Checklist

- [ ] `DEBUG=False` in all .env files
- [ ] Secure `SECRET_KEY` and `SSO_SECRET_KEY`
- [ ] Strong database passwords
- [ ] SSL/HTTPS enabled
- [ ] Firewall configured
- [ ] Backups automated
- [ ] Monitoring setup
- [ ] Log rotation configured
- [ ] Security headers enabled
- [ ] CORS properly configured
- [ ] Static files served efficiently
- [ ] Media files protected
- [ ] Database indexes optimized
- [ ] Redis configured
- [ ] Systemd services enabled

---

**Deployment Complete!** 🎉

Your SSO-enabled business platform is now running on Linux server.

**Next Steps:**
1. Test all applications
2. Configure backups
3. Set up monitoring
4. Train users
5. Document any customizations

---

**Version:** 2.0.0
**Last Updated:** October 2, 2025
**Support:** Check main documentation for troubleshooting
