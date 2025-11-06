# Network Setup Guide - Integrated Business Platform

## Current Configuration

### Server Details
- **Server IP Address**: `21.0.0.42`
- **Application Port**: `8000`
- **Server Software**: Gunicorn + Django
- **Static Files**: Collected in `/staticfiles/`

### Application URLs
- **Local Access**: http://localhost:8000/
- **Network Access**: http://21.0.0.42:8000/
- **Admin Panel**: http://21.0.0.42:8000/admin/
- **Dashboard**: http://21.0.0.42:8000/dashboard/

---

## Phase 1: Local WiFi Network Access (Current Setup)

### What's Already Configured:
✅ Django ALLOWED_HOSTS configured to accept all hosts
✅ Gunicorn running on 0.0.0.0:8000 (all network interfaces)
✅ Static files collected
✅ Database migrations applied

### What YOU Need to Configure:

#### 1. **Router Configuration** (if not accessible from WiFi devices)
You may need to configure your router to allow internal network access:

```
- Log into your WiFi router admin panel
- Check if any firewall rules block port 8000
- Ensure devices on WiFi can communicate with server
- No port forwarding needed for internal network
```

#### 2. **Server Firewall** (if applicable)
If your Linux server has a firewall enabled:

```bash
# For UFW (Ubuntu Firewall)
sudo ufw allow 8000/tcp
sudo ufw reload

# For iptables
sudo iptables -A INPUT -p tcp --dport 8000 -j ACCEPT
sudo iptables-save

# For firewalld
sudo firewall-cmd --permanent --add-port=8000/tcp
sudo firewall-cmd --reload
```

#### 3. **Test Local Network Access**
From any device on your WiFi network:
```
Open browser and go to: http://21.0.0.42:8000/
```

**Troubleshooting if not accessible:**
- Check if server IP changed: `hostname -I`
- Verify Gunicorn is running: `ps aux | grep gunicorn`
- Check if port is listening: `lsof -i :8000`
- Ping the server: `ping 21.0.0.42`

---

## Phase 2: Internet Access with Domain (Future Setup)

### Prerequisites You Need to Prepare:

#### 1. **Domain Name**
- Purchase/register a domain name (e.g., `yourbusiness.com`)
- Have access to DNS management panel

#### 2. **Static Public IP or Dynamic DNS**
Choose one option:

**Option A: Static Public IP** (Recommended)
- Contact your ISP to get a static public IP address
- Note down the public IP address
- This IP will be used for DNS A record

**Option B: Dynamic DNS** (If static IP not available)
- Sign up for a DDNS service (DuckDNS, No-IP, Dynu, etc.)
- Install DDNS client on your server
- Configure automatic IP updates

#### 3. **Router Port Forwarding**
Configure your router to forward external port 80/443 to server:

```
External Port 80  → Server IP: 21.0.0.42:8000 (HTTP)
External Port 443 → Server IP: 21.0.0.42:8000 (HTTPS)
```

Or use same port:
```
External Port 8000 → Server IP: 21.0.0.42:8000
```

### What Needs to Be Configured:

#### 1. **DNS Configuration**
In your domain registrar's DNS panel, add:

```
Type: A Record
Name: @ (or yourbusiness.com)
Value: YOUR_PUBLIC_IP
TTL: 3600

Type: A Record
Name: www
Value: YOUR_PUBLIC_IP
TTL: 3600
```

#### 2. **SSL Certificate** (HTTPS - Mandatory for Production)
You'll need to install:
- Nginx or Apache as reverse proxy
- Let's Encrypt SSL certificate (free)

#### 3. **Django Production Settings**
Update `.env` file:

```env
DEBUG=False
ALLOWED_HOSTS=yourbusiness.com,www.yourbusiness.com,21.0.0.42
SECRET_KEY=<generate-a-strong-random-secret-key>
```

#### 4. **Security Headers**
Configure these in production:
- CSRF_TRUSTED_ORIGINS
- SECURE_SSL_REDIRECT
- SESSION_COOKIE_SECURE
- CSRF_COOKIE_SECURE

---

## Production Deployment Checklist

### Before Going Live:

- [ ] Set `DEBUG=False` in .env
- [ ] Generate strong SECRET_KEY
- [ ] Update ALLOWED_HOSTS with your domain
- [ ] Install and configure Nginx reverse proxy
- [ ] Obtain SSL certificate (Let's Encrypt)
- [ ] Configure HTTPS redirect
- [ ] Set up database backups
- [ ] Configure log rotation
- [ ] Set up monitoring (optional: Sentry, New Relic)
- [ ] Configure email backend for error notifications
- [ ] Test featured apps functionality
- [ ] Create systemd service for auto-start on reboot

---

## Nginx Reverse Proxy Configuration (For Production)

Create `/etc/nginx/sites-available/business_platform`:

```nginx
server {
    listen 80;
    server_name yourbusiness.com www.yourbusiness.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourbusiness.com www.yourbusiness.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/yourbusiness.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourbusiness.com/privkey.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Static files
    location /static/ {
        alias /home/user/integrated_business_platform/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Media files
    location /media/ {
        alias /home/user/integrated_business_platform/media/;
        expires 30d;
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/business_platform /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## Systemd Service for Auto-Start

Create `/etc/systemd/system/business_platform.service`:

```ini
[Unit]
Description=Krystal Business Platform
After=network.target

[Service]
Type=notify
User=root
Group=root
WorkingDirectory=/home/user/integrated_business_platform
ExecStart=/usr/local/bin/gunicorn business_platform.wsgi:application \
    --config /home/user/integrated_business_platform/gunicorn_config.py \
    --bind 0.0.0.0:8000

Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl enable business_platform
sudo systemctl start business_platform
sudo systemctl status business_platform
```

---

## Quick Commands Reference

### Check Server Status
```bash
# Check if Gunicorn is running
ps aux | grep gunicorn

# Check listening ports
lsof -i :8000

# View Gunicorn logs
journalctl -u business_platform -f

# Restart the service
sudo systemctl restart business_platform
```

### Update Application
```bash
cd /home/user/integrated_business_platform
git pull
python manage.py migrate
python manage.py collectstatic --noinput
sudo systemctl restart business_platform
```

### Test Network Connectivity
```bash
# From server
curl http://localhost:8000/

# Get current server IP
hostname -I

# Check DNS resolution (after domain setup)
nslookup yourbusiness.com
```

---

## Current Status Summary

```
✅ Server Running: Gunicorn on 0.0.0.0:8000
✅ Local Access: http://localhost:8000/
✅ Network IP: 21.0.0.42
✅ Static Files: Collected
✅ Database: Migrations applied
✅ Featured Apps: Implemented and ready to test

⏳ Pending Configuration:
   - Router firewall rules (if needed)
   - Public domain DNS setup
   - SSL certificate installation
   - Nginx reverse proxy (for production)
```

---

## Support Contact

For technical issues or questions, contact your system administrator or refer to:
- Django Documentation: https://docs.djangoproject.com/
- Gunicorn Documentation: https://docs.gunicorn.org/
- Let's Encrypt: https://letsencrypt.org/

---

**Note**: The server is currently running in development mode with DEBUG=True. This is acceptable for local network testing but MUST be changed to DEBUG=False before exposing to the internet.
