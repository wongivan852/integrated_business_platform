# Network Configuration - Integrated Business Platform
**Date:** November 26, 2025
**Server IP:** 192.168.0.104

---

## Network Interfaces

### Primary Network IP
- **Main IP:** `192.168.0.104` (wlp2s0 - WiFi interface)
- **Subnet:** 192.168.0.0/24
- **Broadcast:** 192.168.0.255

### Docker Networks
- `172.20.0.1/16` - Docker bridge br-12ea510d5ec8
- `172.17.0.1/16` - Default docker0 bridge
- `172.21.0.1/16` - Docker bridge br-cc3115bb4b07
- `172.19.0.1/16` - Docker bridge br-cf2820a4a63c
- `172.18.0.1/16` - Docker bridge br-d44060b080d5

### Loopback
- `127.0.0.1` - localhost

---

## Application Ports

### Primary Platform (Integrated Business Platform)
- **Port:** 8000 (default Django)
- **Access:** http://192.168.0.104:8000
- **Binding:** 0.0.0.0 (all interfaces)

### CRM System
- **Port:** 8082, 8083
- **Access:** https://192.168.0.104 (via nginx)
- **Proxy:** nginx → 127.0.0.1:8082
- **SSL:** Enabled (TLS 1.2/1.3)
- **Process:** Gunicorn with 3 workers

### Stripe Dashboard
- **Port:** 8081
- **Access:** http://localhost:8006 (internal)
- **Proxy:** nginx → 127.0.0.1:8081
- **Config:** nginx-backup/20250930_090209/stripe-dashboard

---

## Django Configuration

### Allowed Hosts
```python
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']
```

### CSRF Trusted Origins
```python
CSRF_TRUSTED_ORIGINS = ['https://dashboard.krystal.technology']
```

### CORS Configuration
```python
CORS_ALLOW_ALL_ORIGINS = DEBUG
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]
```

---

## Nginx Reverse Proxy Configuration

### Company CRM (Port 8082)
```nginx
server {
    listen 80;
    server_name 192.168.0.104;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl;
    server_name 192.168.0.104;
    
    ssl_certificate /etc/ssl/crm/crm.crt;
    ssl_certificate_key /etc/ssl/crm/crm.key;
    
    location / {
        proxy_pass http://127.0.0.1:8082;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Stripe Dashboard (Port 8081)
```nginx
server {
    listen 80;
    server_name _;
    
    location / {
        proxy_pass http://127.0.0.1:8081;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Access URLs

### Internal Access (Local Network)
- **Main Platform:** http://192.168.0.104:8000
- **Admin Panel:** http://192.168.0.104:8000/admin-panel/
- **App Access Matrix:** http://192.168.0.104:8000/admin-panel/app-access-matrix/
- **CRM System:** https://192.168.0.104 (SSL)
- **Stripe Dashboard:** http://localhost:8081 (internal only)

### External/Production Access
- **Dashboard:** https://dashboard.krystal.technology
- **SSO API:** https://dashboard.krystal.technology/api/sso/

---

## Database Connections

### PostgreSQL
- **Host:** localhost (127.0.0.1)
- **Port:** 5432
- **Database:** krystal_platform
- **User:** platformadmin
- **Connection:** Internal only

---

## Security Configuration

### SSL/TLS
- **CRM SSL Certificates:** /etc/ssl/crm/
- **Protocols:** TLSv1.2, TLSv1.3
- **Ciphers:** ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512

### Security Headers
```nginx
X-Frame-Options: DENY
X-Content-Type-Options: nosniff
X-XSS-Protection: 1; mode=block
```

### Rate Limiting
- Stripe Dashboard: 20 requests burst with nodelay

---

## Firewall & Network Access

### Open Ports
- **80** - HTTP (nginx)
- **443** - HTTPS (nginx with SSL)
- **8000** - Django main platform
- **8082** - CRM backend (proxied via nginx)
- **8083** - CRM Gunicorn (alternative)
- **5432** - PostgreSQL (internal only)

### Access Control
- Platform accessible on LAN: `192.168.0.0/24`
- External access via domain: `dashboard.krystal.technology`
- Docker networks isolated: `172.x.x.x/16`

---

## Running Services

### Gunicorn (CRM)
```bash
/usr/local/bin/python3.11 /home/crm/.local/bin/gunicorn crm_project.wsgi:application \
  --bind 0.0.0.0:8083 \
  --workers 3 \
  --timeout 120
```

### Django Development Server (CRM)
```bash
/opt/crm/venv/bin/python manage.py runserver 0.0.0.0:8082
```

---

## Network Diagnostics

### Check IP Address
```bash
hostname -I
# Output: 192.168.0.104 172.20.0.1 172.17.0.1 172.21.0.1 172.19.0.1 172.18.0.1
```

### Check Listening Ports
```bash
ss -tlnp | grep -E "8000|8006|8081|8082|8083|5432"
```

### Test Connections
```bash
# Internal
curl http://127.0.0.1:8000
curl http://192.168.0.104:8000

# CRM
curl https://192.168.0.104 -k

# Database
PGPASSWORD='5514' psql -U platformadmin -h localhost -d krystal_platform -c "SELECT 1;"
```

---

## Environment Variables (.env)

```bash
# Hosts
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,*
CSRF_TRUSTED_ORIGINS=https://dashboard.krystal.technology

# Database
DB_HOST=localhost
DB_PORT=5432
DB_NAME=krystal_platform
DB_USER=platformadmin

# Application Ports
STRIPE_PORT=8006
```

---

## Network Topology

```
Internet/LAN (192.168.0.0/24)
        ↓
[192.168.0.104:80/443] - Nginx Reverse Proxy
        ↓
    ┌───┴───┬───────────┬─────────────┐
    ↓       ↓           ↓             ↓
[8000]  [8082]      [8081]        [8083]
Django   CRM     Stripe Dashboard  CRM Gunicorn
    ↓       ↓           ↓
    └───────┴───────────┘
            ↓
    [PostgreSQL :5432]
    krystal_platform DB
```

---

## Notes

### For Remote Access
1. Ensure firewall allows ports 80, 443, 8000
2. Configure DNS: dashboard.krystal.technology → 192.168.0.104
3. SSL certificates must be valid for the domain
4. Update CSRF_TRUSTED_ORIGINS with the actual domain

### For Local Development
1. Access via http://192.168.0.104:8000
2. All apps accessible through main platform with SSO
3. Direct app access via respective ports (8081, 8082, 8083)

### Docker Networking
- Multiple Docker networks detected (172.x.x.x)
- Each Docker network isolated by default
- Use host networking or bridge for inter-container communication

---

**Last Updated:** 2025-11-26
**Server Location:** Local Development/Production
**IP Address:** 192.168.0.104
