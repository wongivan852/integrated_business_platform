# Quick Start Guide

## ✅ What's Been Configured

Your Integrated Business Platform is now running with:

1. **Production Server**: Gunicorn (multi-worker, production-ready)
2. **Network Access**: Configured to accept connections from all interfaces
3. **Featured Apps**: Fully implemented and ready to use
4. **Static Files**: Collected and ready to serve
5. **Database**: Migrated and up to date

---

## 🚀 What YOU Need to Provide/Configure

### For Local WiFi Network Access:

#### 1. **Determine Your Network Access Method**

Your server is running behind an **Envoy proxy**, which means you need to find out:

**Ask yourself or your network admin:**
- Is there an external URL already configured for this server?
- Is there a load balancer or reverse proxy with a public endpoint?
- Do you have access to configure the Envoy proxy?

**To find your external URL:**
```bash
# Check environment variables
env | grep -iE "url|host|domain" | grep -v "ANTHROPIC"

# Or ask your infrastructure provider
# Check cloud dashboard if running in cloud (AWS, GCP, Azure, etc.)
```

#### 2. **If Using Direct IP Access (Bypassing Proxy)**

You'll need to:
- Configure your router/network to allow access to port 8000
- Or set up port forwarding from a different port
- Or configure the Envoy proxy to pass through to your application

#### 3. **Server Firewall** (If Applicable)

If your server has a firewall, allow port 8000:
```bash
# Check if firewall is active
sudo ufw status
# or
sudo iptables -L

# If needed, allow port 8000
sudo ufw allow 8000/tcp
```

### For Internet Access with Domain:

#### You Need to Provide:

1. **Domain Name** - Purchase from registrar (GoDaddy, Namecheap, etc.)
2. **Static Public IP** - Request from ISP or use Dynamic DNS service
3. **Router Configuration** - Set up port forwarding (80/443 → server:8000)
4. **DNS Configuration** - Point domain to your public IP
5. **SSL Certificate** - Obtain from Let's Encrypt (free)

See **NETWORK_SETUP_GUIDE.md** for complete instructions.

---

## 🧪 How to Test Featured Apps (Right Now)

You can test the application locally first:

### Step 1: Access Admin Panel
```
URL: http://localhost:8000/admin/
(Or from the server: curl http://localhost:8000/admin/)
```

### Step 2: Mark Apps as Featured
1. Login with superuser credentials
2. Navigate to: **Authentication → Application Configurations**
3. Click on an app (e.g., "CRM", "Expense Claims", "Leave System")
4. Check the **"Is Featured"** checkbox
5. Save
6. Repeat for 2-3 apps

**Or use bulk action:**
- Select multiple apps with checkboxes
- Choose **"Mark as featured"** from Actions dropdown
- Click **"Go"**

### Step 3: View Dashboard
```
URL: http://localhost:8000/dashboard/
```

You should see:
- **Featured Apps Section** at the top with special styling
- Featured badge on cards
- Gradient borders
- **All Applications Section** below with regular apps

---

## 📝 Server Management

### Check if Server is Running
```bash
ps aux | grep gunicorn
lsof -i :8000
```

### Restart Server
```bash
pkill gunicorn
/home/user/integrated_business_platform/start_server.sh
```

### View Application
```bash
# From server terminal
curl http://localhost:8000/
```

### Update Application (After Making Changes)
```bash
cd /home/user/integrated_business_platform
git pull
python manage.py migrate
python manage.py collectstatic --noinput
pkill gunicorn
./start_server.sh
```

---

## 📂 Important Files Created

```
/home/user/integrated_business_platform/
├── gunicorn_config.py          # Production server configuration
├── start_server.sh             # Server startup script
├── NETWORK_SETUP_GUIDE.md      # Complete network setup instructions
├── SERVER_STATUS.md            # Current server status
└── QUICK_START.md             # This file
```

---

## ⚠️ Important Security Notes

**Before Exposing to Internet:**
1. Set `DEBUG=False` in `.env`
2. Generate a strong `SECRET_KEY`
3. Update `ALLOWED_HOSTS` with your domain
4. Install SSL certificate (HTTPS)
5. Set up Nginx reverse proxy
6. Configure security headers

**Current Settings** (for development):
- DEBUG=True ⚠️ (Change before production!)
- SECRET_KEY: Default (Change before production!)
- ALLOWED_HOSTS: * (Allows all - okay for now)

---

## 🆘 Troubleshooting

### Problem: Can't access from other devices on WiFi

**Check:**
1. Server is running: `ps aux | grep gunicorn`
2. Port is listening: `lsof -i :8000`
3. Server IP hasn't changed: `hostname -I`
4. Firewall allows port 8000
5. Devices are on the same network
6. No proxy/VPN blocking access

### Problem: 503 Service Unavailable

**Reason**: Your server is behind Envoy proxy
**Solution**: You need to find the external URL or configure the proxy

### Problem: Static files not loading

**Fix:**
```bash
python manage.py collectstatic --noinput --clear
```

---

## 📞 Next Steps

**Immediate:**
1. ✅ Test application locally (http://localhost:8000/)
2. ✅ Test featured apps functionality in admin
3. 🔍 Determine your network access method (proxy URL, direct IP, etc.)
4. 🔧 Configure network access based on your infrastructure

**For Production:**
5. 📖 Read NETWORK_SETUP_GUIDE.md
6. 🌐 Get domain name
7. 🔒 Set up SSL/HTTPS
8. ⚙️ Configure production settings
9. 🚀 Deploy to internet

---

## Summary

✅ **Server Status**: Running on port 8000
✅ **Application**: Fully functional
✅ **Featured Apps**: Implemented
⏳ **Network Access**: Needs configuration based on your infrastructure

**What you need to know**: How to access your server from external devices (proxy URL, direct IP setup, etc.)

**All documentation is ready** - check the files above for detailed instructions!
