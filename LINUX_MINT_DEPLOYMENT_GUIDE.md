# Integrated Business Platform - Linux Mint Deployment Guide

**Target Server**: Linux Mint (Ubuntu-based)
**Platform Version**: v2.0 with Phase 6 Complete
**Total Apps**: 9 business applications
**Deployment Type**: Production with SSO
**Claude Code Support**: ✅ Enabled (Server-side assistance available)

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Server Requirements](#server-requirements)
3. [Pre-Deployment Checklist](#pre-deployment-checklist)
4. [Installation Steps](#installation-steps)
5. [Database Configuration](#database-configuration)
6. [Application Setup](#application-setup)
7. [Web Server Configuration](#web-server-configuration)
8. [SSL/HTTPS Setup](#sslhttps-setup)
9. [Environment Variables](#environment-variables)
10. [User Access Configuration](#user-access-configuration)
11. [Testing & Verification](#testing--verification)
12. [Maintenance & Monitoring](#maintenance--monitoring)
13. [Troubleshooting](#troubleshooting)
14. [Claude Code Server Assistance](#claude-code-server-assistance)

---

## Overview

This guide will help you deploy the Integrated Business Platform on a Linux Mint server. The platform includes:

### 9 Business Applications:
1. **Expense Claims** (Port 8001)
2. **Leave Management** (Port 8002)
3. **Asset Management** (Port 8003)
4. **CRM System** (Port 8004)
5. **Cost Quotations** (Port 8005)
6. **Stripe Dashboard** (Port 8081)
7. **Event Management** (Port 8000 - integrated)
8. **Project Management** (Port 8000 - integrated)
9. **Attendance System** (Port 8000 - integrated)

### Core Features:
- ✅ JWT-based Single Sign-On (SSO)
- ✅ Role-Based Access Control (RBAC)
- ✅ Admin Panel for user management
- ✅ Real-time collaboration (WebSocket)
- ✅ REST API with JWT authentication
- ✅ Progressive Web App (PWA) support
- ✅ Workflow automation
- ✅ Third-party integrations (GitHub, Slack, Jira)

---

## Server Requirements

### Minimum Specifications:
```
CPU:     4 cores (8 cores recommended)
RAM:     8 GB (16 GB recommended)
Disk:    50 GB SSD (100 GB recommended)
Network: 1 Gbps Ethernet
OS:      Linux Mint 21.x or higher (Ubuntu 22.04 based)
```

### Software Requirements:
```
Python:     3.8 or higher (3.10 recommended)
PostgreSQL: 14 or higher
Redis:      6.x or higher
Nginx:      1.18 or higher
Git:        2.x
Supervisor: 4.x (for process management)
Certbot:    (for SSL certificates)
```

### Network Requirements:
```
Open Ports: 80 (HTTP), 443 (HTTPS), 8000-8005, 8081
Firewall:   UFW configured
DNS:        Domain name pointed to server IP
```

---

## Pre-Deployment Checklist

Before starting deployment, ensure you have:

- [ ] Root or sudo access to Linux Mint server
- [ ] Server IP address and domain name
- [ ] GitLab repository access (`gitlab.kryedu.org/company_apps`)
- [ ] Database credentials planned
- [ ] Secret keys generated (Django SECRET_KEY, SSO_SECRET_KEY)
- [ ] SSL certificate method chosen (Let's Encrypt recommended)
- [ ] Email service configured (for notifications)
- [ ] Backup strategy planned

### Generate Secret Keys:

```bash
# Generate Django SECRET_KEY
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"

# Generate SSO_SECRET_KEY (different from above)
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Installation Steps

### Step 1: System Update and Preparation

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Install essential build tools
sudo apt install -y build-essential software-properties-common \
    curl wget git vim nano htop tree net-tools

# Install Python 3.10 (if not already installed)
sudo add-apt-repository ppa:deadsnakes/ppa -y
sudo apt update
sudo apt install -y python3.10 python3.10-dev python3.10-venv \
    python3-pip python3-setuptools
```

### Step 2: Install Database (PostgreSQL)

```bash
# Install PostgreSQL
sudo apt install -y postgresql postgresql-contrib

# Start and enable PostgreSQL
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Create database and user
sudo -u postgres psql << EOF
CREATE DATABASE integrated_platform;
CREATE USER platform_user WITH PASSWORD 'your_secure_password';
ALTER ROLE platform_user SET client_encoding TO 'utf8';
ALTER ROLE platform_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE platform_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE integrated_platform TO platform_user;
\q
EOF
```

### Step 3: Install Redis (for caching and WebSocket)

```bash
# Install Redis
sudo apt install -y redis-server

# Configure Redis for production
sudo nano /etc/redis/redis.conf
# Set: supervised systemd
# Set: bind 127.0.0.1 ::1
# Set: maxmemory 256mb
# Set: maxmemory-policy allkeys-lru

# Restart Redis
sudo systemctl restart redis
sudo systemctl enable redis

# Test Redis
redis-cli ping  # Should return PONG
```

### Step 4: Install Nginx (Web Server)

```bash
# Install Nginx
sudo apt install -y nginx

# Start and enable Nginx
sudo systemctl start nginx
sudo systemctl enable nginx

# Test Nginx
curl http://localhost  # Should show Nginx welcome page
```

### Step 5: Setup Firewall (UFW)

```bash
# Install and configure UFW
sudo apt install -y ufw

# Allow SSH, HTTP, HTTPS
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'

# Allow application ports (optional for direct access)
sudo ufw allow 8000:8005/tcp
sudo ufw allow 8081/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

### Step 6: Create Application User

```bash
# Create dedicated user for application
sudo useradd -m -s /bin/bash platform
sudo passwd platform  # Set a password

# Add to sudo group (optional)
sudo usermod -aG sudo platform

# Switch to platform user
sudo su - platform
```

### Step 7: Clone Repository

```bash
# As platform user, clone from GitLab
cd /home/platform
git clone https://gitlab.kryedu.org/company_apps/integrated_business_platform.git
cd integrated_business_platform

# Or clone all business apps
mkdir -p /home/platform/apps
cd /home/platform/apps

# Clone each app repository
git clone https://gitlab.kryedu.org/company_apps/integrated_business_platform.git
git clone https://gitlab.kryedu.org/company_apps/expense_claims.git
git clone https://gitlab.kryedu.org/company_apps/leave_management.git
# ... clone other apps as needed
```

### Step 8: Create Virtual Environment

```bash
# For integrated platform
cd /home/platform/apps/integrated_business_platform

# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip setuptools wheel
```

### Step 9: Install Python Dependencies

```bash
# Install requirements
pip install -r requirements.txt

# Additional production packages
pip install gunicorn daphne psycopg2-binary redis celery

# Verify installations
pip list | grep -E "(Django|gunicorn|daphne|psycopg2|redis|celery)"
```

---

## Database Configuration

### Step 1: Update Django Settings for Production

Create production settings file:

```bash
# Create production settings
nano /home/platform/apps/integrated_business_platform/business_platform/settings_prod.py
```

```python
"""
Production settings for Integrated Business Platform
Import from base settings and override for production
"""
from .settings import *
import os

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'your-production-secret-key')
SSO_SECRET_KEY = os.environ.get('SSO_SECRET_KEY', 'your-sso-secret-key')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = [
    'your-domain.com',
    'www.your-domain.com',
    'your-server-ip',
    'localhost',
]

# Database - PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'integrated_platform'),
        'USER': os.environ.get('DB_USER', 'platform_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'your_secure_password'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'CONN_MAX_AGE': 600,  # Connection pooling
    }
}

# Cache - Redis
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        },
        'KEY_PREFIX': 'platform',
        'TIMEOUT': 300,
    }
}

# Channel Layers - Redis for WebSocket
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            'hosts': [('127.0.0.1', 6379)],
        },
    },
}

# Session - Database backed
SESSION_ENGINE = 'django.contrib.sessions.backends.cached_db'
SESSION_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_AGE = 86400  # 24 hours

# CSRF
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = True
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_TRUSTED_ORIGINS = [
    'https://your-domain.com',
    'https://www.your-domain.com',
]

# Security Settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'

# Static files
STATIC_ROOT = '/home/platform/static/integrated_platform/'
STATIC_URL = '/static/'

# Media files
MEDIA_ROOT = '/home/platform/media/integrated_platform/'
MEDIA_URL = '/media/'

# Email configuration (example with Gmail)
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.environ.get('EMAIL_USER')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_PASSWORD')
DEFAULT_FROM_EMAIL = 'noreply@your-domain.com'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/home/platform/logs/integrated_platform/django.log',
            'maxBytes': 1024 * 1024 * 15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['file'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
```

### Step 2: Create Environment File

```bash
# Create .env file for production
nano /home/platform/apps/integrated_business_platform/.env.production
```

```bash
# Django Settings
DJANGO_SETTINGS_MODULE=business_platform.settings_prod
DJANGO_SECRET_KEY=your-generated-secret-key-here
SSO_SECRET_KEY=your-generated-sso-secret-key-here

# Database
DB_NAME=integrated_platform
DB_USER=platform_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=5432

# Email (example)
EMAIL_USER=your-email@gmail.com
EMAIL_PASSWORD=your-app-specific-password

# Redis
REDIS_URL=redis://127.0.0.1:6379/1

# Application
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,your-server-ip
```

### Step 3: Run Migrations

```bash
# Activate virtual environment
source venv/bin/activate

# Set environment variables
export $(cat .env.production | xargs)

# Run migrations
python manage.py migrate --settings=business_platform.settings_prod

# Create superuser
python manage.py createsuperuser --settings=business_platform.settings_prod

# Collect static files
python manage.py collectstatic --noinput --settings=business_platform.settings_prod
```

---

## Application Setup

### Step 1: Configure User Access

```bash
# Configure user access using email-based identity
python configure_user_access.py

# Or via Django shell
python manage.py shell --settings=business_platform.settings_prod
>>> from core.models import UserAppAccess
>>> from django.contrib.auth import get_user_model
>>> User = get_user_model()
>>> # Grant access to users...
```

### Step 2: Initialize Integration Providers

```bash
# Initialize GitHub, Slack, Jira integrations
python manage.py init_integrations --settings=business_platform.settings_prod

# Initialize permission system
python manage.py init_permissions --settings=business_platform.settings_prod
```

### Step 3: Test Application

```bash
# Test Django server (development mode)
python manage.py runserver 0.0.0.0:8000 --settings=business_platform.settings_prod

# Test from browser
# http://your-server-ip:8000

# Stop test server (Ctrl+C)
```

---

## Web Server Configuration

### Nginx Configuration for Integrated Platform

```bash
# Create Nginx configuration
sudo nano /etc/nginx/sites-available/integrated_platform
```

```nginx
# Integrated Business Platform - Nginx Configuration

upstream platform_app {
    server 127.0.0.1:8000;
}

upstream platform_websocket {
    server 127.0.0.1:8000;
}

# HTTP to HTTPS redirect
server {
    listen 80;
    listen [::]:80;
    server_name your-domain.com www.your-domain.com;

    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }

    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS server
server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name your-domain.com www.your-domain.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_prefer_server_ciphers on;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Max upload size
    client_max_body_size 50M;

    # Logging
    access_log /var/log/nginx/platform_access.log;
    error_log /var/log/nginx/platform_error.log;

    # Static files
    location /static/ {
        alias /home/platform/static/integrated_platform/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/platform/media/integrated_platform/;
        expires 7d;
    }

    # WebSocket upgrade for real-time features
    location /ws/ {
        proxy_pass http://platform_websocket;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 86400;
    }

    # Application
    location / {
        proxy_pass http://platform_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
}
```

### Enable Nginx Configuration

```bash
# Create symbolic link
sudo ln -s /etc/nginx/sites-available/integrated_platform /etc/nginx/sites-enabled/

# Test Nginx configuration
sudo nginx -t

# Reload Nginx
sudo systemctl reload nginx
```

---

## SSL/HTTPS Setup

### Install Certbot (Let's Encrypt)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Obtain SSL certificate
sudo certbot --nginx -d your-domain.com -d www.your-domain.com

# Test automatic renewal
sudo certbot renew --dry-run

# Certbot will automatically renew certificates
sudo systemctl status certbot.timer
```

---

## Process Management with Supervisor

### Install Supervisor

```bash
sudo apt install -y supervisor
```

### Configure Gunicorn (for HTTP/HTTPS)

```bash
# Create Gunicorn configuration
sudo nano /etc/supervisor/conf.d/platform_gunicorn.conf
```

```ini
[program:platform_gunicorn]
command=/home/platform/apps/integrated_business_platform/venv/bin/gunicorn \
    --workers 4 \
    --bind 127.0.0.1:8000 \
    --timeout 120 \
    --access-logfile /home/platform/logs/integrated_platform/gunicorn_access.log \
    --error-logfile /home/platform/logs/integrated_platform/gunicorn_error.log \
    business_platform.wsgi:application

directory=/home/platform/apps/integrated_business_platform
user=platform
autostart=true
autorestart=true
redirect_stderr=true
environment=PATH="/home/platform/apps/integrated_business_platform/venv/bin",
    DJANGO_SETTINGS_MODULE="business_platform.settings_prod",
    DJANGO_SECRET_KEY="your-secret-key",
    SSO_SECRET_KEY="your-sso-key",
    DB_PASSWORD="your-db-password"
```

### Configure Daphne (for WebSocket)

```bash
# Create Daphne configuration
sudo nano /etc/supervisor/conf.d/platform_daphne.conf
```

```ini
[program:platform_daphne]
command=/home/platform/apps/integrated_business_platform/venv/bin/daphne \
    -b 127.0.0.1 \
    -p 8001 \
    business_platform.asgi:application

directory=/home/platform/apps/integrated_business_platform
user=platform
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/home/platform/logs/integrated_platform/daphne.log
environment=PATH="/home/platform/apps/integrated_business_platform/venv/bin",
    DJANGO_SETTINGS_MODULE="business_platform.settings_prod"
```

### Configure Celery (for background tasks)

```bash
# Create Celery worker configuration
sudo nano /etc/supervisor/conf.d/platform_celery.conf
```

```ini
[program:platform_celery]
command=/home/platform/apps/integrated_business_platform/venv/bin/celery -A business_platform worker \
    --loglevel=info \
    --logfile=/home/platform/logs/integrated_platform/celery.log

directory=/home/platform/apps/integrated_business_platform
user=platform
autostart=true
autorestart=true
redirect_stderr=true
environment=PATH="/home/platform/apps/integrated_business_platform/venv/bin",
    DJANGO_SETTINGS_MODULE="business_platform.settings_prod"
```

### Start All Services

```bash
# Create log directories
sudo mkdir -p /home/platform/logs/integrated_platform
sudo chown -R platform:platform /home/platform/logs

# Reload Supervisor
sudo supervisorctl reread
sudo supervisorctl update

# Start all services
sudo supervisorctl start platform_gunicorn
sudo supervisorctl start platform_daphne
sudo supervisorctl start platform_celery

# Check status
sudo supervisorctl status
```

---

## User Access Configuration

### Configure Initial Users

```bash
# As platform user
cd /home/platform/apps/integrated_business_platform
source venv/bin/activate

# Run user access configuration
python configure_user_access.py --dry-run  # Preview
python configure_user_access.py            # Apply

# Or via admin panel after deployment
# https://your-domain.com/admin-panel/
```

---

## Testing & Verification

### System Health Check

```bash
# Check all services
sudo supervisorctl status

# Check Nginx
sudo systemctl status nginx

# Check PostgreSQL
sudo systemctl status postgresql

# Check Redis
redis-cli ping

# Check disk space
df -h

# Check memory
free -h

# Check logs
tail -f /home/platform/logs/integrated_platform/django.log
tail -f /home/platform/logs/integrated_platform/gunicorn_error.log
```

### Application Testing

```bash
# Test Django
curl -I https://your-domain.com/

# Test SSO API
curl -X POST https://your-domain.com/api/sso/token/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin@company.com","password":"password"}'

# Test admin panel
curl -I https://your-domain.com/admin-panel/

# Test WebSocket (if applicable)
# Use browser console or WebSocket client
```

### Browser Testing

1. Visit https://your-domain.com/
2. Login with credentials
3. Check dashboard loads correctly
4. Test app launching (SSO)
5. Verify admin panel access
6. Test user access configuration

---

## Maintenance & Monitoring

### Regular Maintenance Tasks

```bash
# Daily backups
sudo -u postgres pg_dump integrated_platform > /backup/$(date +%Y%m%d)_platform.sql

# Weekly log rotation
sudo logrotate /etc/logrotate.d/integrated_platform

# Monthly updates
sudo apt update && sudo apt upgrade -y

# Check disk space
df -h | grep -E '(Filesystem|/dev/sd|/dev/nvme)'
```

### Monitoring Setup

```bash
# Install monitoring tools
sudo apt install -y htop iotop nethogs

# Monitor real-time
htop  # CPU and memory
iotop  # Disk I/O
nethogs  # Network usage

# Check application logs
sudo tail -f /home/platform/logs/integrated_platform/*.log

# Monitor Supervisor processes
sudo supervisorctl tail -f platform_gunicorn
sudo supervisorctl tail -f platform_daphne
```

---

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

```bash
# Check logs
sudo tail -100 /home/platform/logs/integrated_platform/gunicorn_error.log

# Check Supervisor status
sudo supervisorctl status

# Restart services
sudo supervisorctl restart platform_gunicorn
sudo supervisorctl restart platform_daphne
```

#### 2. Database Connection Issues

```bash
# Check PostgreSQL status
sudo systemctl status postgresql

# Test database connection
sudo -u postgres psql -d integrated_platform -c "SELECT version();"

# Check database credentials in .env.production
```

#### 3. Static Files Not Loading

```bash
# Collect static files again
cd /home/platform/apps/integrated_business_platform
source venv/bin/activate
python manage.py collectstatic --noinput --settings=business_platform.settings_prod

# Check permissions
sudo chown -R platform:platform /home/platform/static/
```

#### 4. SSL Certificate Issues

```bash
# Check certificate
sudo certbot certificates

# Renew certificate
sudo certbot renew

# Test certificate
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

---

## Claude Code Server Assistance

### 🤖 Using Claude Code on the Server

Your Linux Mint server also has Claude Code installed, which can significantly help with:

#### 1. **Automated Troubleshooting**

```bash
# Claude Code can help diagnose issues
claude-code "Check why Gunicorn won't start"
claude-code "Analyze nginx error logs and suggest fixes"
claude-code "Why is PostgreSQL using high memory?"
```

#### 2. **Configuration Management**

```bash
# Claude Code can help with configuration
claude-code "Review and optimize nginx configuration for performance"
claude-code "Update PostgreSQL settings for 16GB RAM server"
claude-code "Configure Redis for production use"
```

#### 3. **Deployment Automation**

Ask Claude Code to create deployment scripts:

```bash
# Example: Ask Claude Code to create auto-deployment script
claude-code "Create a script to pull latest from GitLab, run migrations, and restart services"
```

Claude Code can generate:
```bash
#!/bin/bash
# auto_deploy.sh - Generated by Claude Code

cd /home/platform/apps/integrated_business_platform
git pull origin master
source venv/bin/activate
python manage.py migrate --settings=business_platform.settings_prod
python manage.py collectstatic --noinput --settings=business_platform.settings_prod
sudo supervisorctl restart platform_gunicorn
sudo supervisorctl restart platform_daphne
```

#### 4. **Security Audits**

```bash
# Claude Code can perform security checks
claude-code "Audit server security configuration and suggest improvements"
claude-code "Check for common security vulnerabilities in Django settings"
claude-code "Review firewall rules and suggest hardening"
```

#### 5. **Performance Optimization**

```bash
# Claude Code can analyze performance
claude-code "Analyze Django query performance and suggest optimizations"
claude-code "Review Gunicorn worker settings for 8GB RAM"
claude-code "Optimize PostgreSQL for web application workload"
```

#### 6. **Monitoring Setup**

```bash
# Claude Code can help setup monitoring
claude-code "Create a monitoring script to check all services and send alerts"
claude-code "Setup log aggregation and analysis"
claude-code "Create dashboard for application metrics"
```

### Pro Tips for Using Claude Code on Server:

1. **Use Specific Commands**: Be specific about what you need
   ```bash
   claude-code "Check integrated_business_platform Gunicorn logs for errors in last 100 lines"
   ```

2. **Context Sharing**: Claude Code has access to server files
   ```bash
   claude-code "Read /etc/nginx/sites-available/integrated_platform and suggest improvements"
   ```

3. **Automated Scripts**: Generate maintenance scripts
   ```bash
   claude-code "Create a health check script that tests all 9 business apps"
   ```

4. **Documentation**: Generate server documentation
   ```bash
   claude-code "Document the current server configuration to a markdown file"
   ```

5. **Quick Fixes**: Rapid problem solving
   ```bash
   claude-code "Fix permission issues with /home/platform/static directory"
   ```

### Setting Up Claude Code Helpers

Create helper aliases in `.bashrc`:

```bash
# Add to /home/platform/.bashrc
alias cc='claude-code'
alias cc-check='claude-code "Check all platform services status"'
alias cc-logs='claude-code "Show recent errors from all platform logs"'
alias cc-restart='claude-code "Safely restart all platform services"'
alias cc-backup='claude-code "Create database backup and verify integrity"'
```

---

## Automated Deployment Script

```bash
# Create deployment script with Claude Code assistance
nano /home/platform/deploy_platform.sh
```

```bash
#!/bin/bash
# Integrated Business Platform - Automated Deployment Script
# Generated with Claude Code assistance

set -e  # Exit on error

echo "=== Integrated Business Platform Deployment ==="
echo "Starting deployment at $(date)"

# Configuration
APP_DIR="/home/platform/apps/integrated_business_platform"
VENV_DIR="$APP_DIR/venv"
LOG_DIR="/home/platform/logs/integrated_platform"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print success
success() {
    echo -e "${GREEN}✓ $1${NC}"
}

# Function to print error
error() {
    echo -e "${RED}✗ $1${NC}"
}

# Pull latest code
echo "1. Pulling latest code from GitLab..."
cd $APP_DIR
git pull origin master && success "Code updated" || error "Git pull failed"

# Activate virtual environment
echo "2. Activating virtual environment..."
source $VENV_DIR/bin/activate && success "Virtual environment activated"

# Install/update dependencies
echo "3. Installing dependencies..."
pip install -r requirements.txt -q && success "Dependencies installed"

# Run migrations
echo "4. Running database migrations..."
python manage.py migrate --settings=business_platform.settings_prod && success "Migrations complete"

# Collect static files
echo "5. Collecting static files..."
python manage.py collectstatic --noinput --settings=business_platform.settings_prod && success "Static files collected"

# Restart services
echo "6. Restarting application services..."
sudo supervisorctl restart platform_gunicorn && success "Gunicorn restarted"
sudo supervisorctl restart platform_daphne && success "Daphne restarted"
sudo supervisorctl restart platform_celery && success "Celery restarted"

# Reload Nginx
echo "7. Reloading Nginx..."
sudo nginx -t && sudo systemctl reload nginx && success "Nginx reloaded"

# Check service status
echo "8. Checking service status..."
sudo supervisorctl status | grep platform

echo ""
echo "=== Deployment Complete at $(date) ==="
echo "Application is now live at https://your-domain.com"
```

Make executable:
```bash
chmod +x /home/platform/deploy_platform.sh
```

---

## Summary Checklist

### Pre-Deployment:
- [ ] Server meets minimum requirements
- [ ] Domain name configured and DNS updated
- [ ] SSH access configured
- [ ] Secret keys generated

### Installation:
- [ ] System packages updated
- [ ] Python 3.10 installed
- [ ] PostgreSQL installed and configured
- [ ] Redis installed and running
- [ ] Nginx installed
- [ ] Firewall configured (UFW)
- [ ] Application user created

### Configuration:
- [ ] Repository cloned
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] Production settings configured
- [ ] Environment variables set
- [ ] Database migrations run
- [ ] Superuser created
- [ ] Static files collected

### Web Server:
- [ ] Nginx configuration created
- [ ] SSL certificate obtained (Let's Encrypt)
- [ ] Nginx reloaded with SSL

### Process Management:
- [ ] Supervisor installed
- [ ] Gunicorn configured
- [ ] Daphne configured (WebSocket)
- [ ] Celery configured (background tasks)
- [ ] All services started and verified

### User Configuration:
- [ ] User access configured (email-based)
- [ ] Initial users granted app access
- [ ] Admin panel accessible

### Testing:
- [ ] HTTPS working
- [ ] Application loads correctly
- [ ] Login working
- [ ] Dashboard showing apps
- [ ] SSO app launch working
- [ ] Admin panel accessible
- [ ] WebSocket connections working (if applicable)

### Monitoring:
- [ ] Log files created and writable
- [ ] Monitoring tools installed
- [ ] Backup script configured
- [ ] Claude Code helpers configured

---

## Support and Resources

### Documentation:
- `SSO_AND_ADMIN_PANEL_COMPLETE.md` - SSO documentation
- `USER_ACCESS_CONFIGURATION_COMPLETE.md` - User access guide
- `SSO_ADMIN_EVALUATION_REPORT.md` - System evaluation
- `PHASE_6_COMPLETE.md` - Phase 6 features

### Admin Panel:
- URL: https://your-domain.com/admin-panel/
- User Management: Manage user app access
- App Access Matrix: Visual access overview
- Audit Logs: Track all permission changes

### Claude Code on Server:
- Use for troubleshooting
- Configuration optimization
- Security audits
- Performance tuning
- Automated maintenance

---

**Deployment Guide Version**: 1.0
**Last Updated**: October 28, 2025
**Platform Version**: v2.0 with Phase 6 Complete
**Total Apps**: 9 business applications

**Status**: ✅ Ready for Production Deployment

---

## Notes for Deployment Engineer

This guide assumes you have Claude Code running on the Linux Mint server, which can significantly speed up the deployment process. Use Claude Code to:

1. Generate missing configuration files
2. Troubleshoot any issues that arise
3. Optimize settings for your specific hardware
4. Create custom monitoring and maintenance scripts
5. Perform security audits and hardening

The combination of this comprehensive guide and Claude Code assistance on the server makes deployment more reliable and faster!

**Good luck with your deployment! 🚀**
