# Quick Start Guide - SSO & Admin Panel

## 🚀 Getting Started in 5 Minutes

### Step 1: Verify Server is Running
```bash
cd /Users/wongivan/ai_tools/business_tools/integrated_business_platform
python manage.py runserver 8000
```

Server should start at: **http://localhost:8000/**

---

### Step 2: Log In as Admin
1. Open browser: http://localhost:8000/
2. Log in with:
   - **Email**: ivan.wong@krystal.institute
   - **Password**: krystal2025

---

### Step 3: Access Admin Panel
1. After login, you'll be on the dashboard
2. Navigate to: **http://localhost:8000/admin-panel/**
3. You should see the admin panel dashboard with:
   - Total active users
   - Total apps (6)
   - Recent activity

---

### Step 4: Grant App Access to a User

#### Option A: Via User Detail Page
1. Click "Manage Users"
2. Click on any user
3. For each app card, select a role from dropdown:
   - **No Access** - User cannot access this app
   - **Employee** - Basic access
   - **Manager** - Manager-level access
   - **Admin** - Full administrative access
4. Changes save automatically!

#### Option B: Via App Access Matrix
1. Click "App Access Matrix"
2. See all users and their access in a table
3. Click any cell to change the role
4. Changes save immediately

---

### Step 5: Test SSO Flow

1. **Create a Test User** (if you haven't):
```bash
cd /Users/wongivan/ai_tools/business_tools/integrated_business_platform
python manage.py shell
```

```python
from django.contrib.auth import get_user_model
User = get_user_model()

# Create test user
user = User.objects.create_user(
    email='test.user@krystal.institute',
    password='test2025',
    first_name='Test',
    last_name='User',
    employee_id='TEST001',
    region='HK',
    department='IT'
)
print(f"Created: {user.email}")
```

2. **Grant Access via Admin Panel**:
   - Go to Admin Panel → Manage Users → test.user@krystal.institute
   - Grant "Employee" access to "Expense Claims"
   - Grant "Employee" access to "Leave Management"

3. **Test Login as Regular User**:
   - Log out (top right)
   - Log in as: test.user@krystal.institute / test2025
   - Dashboard should show ONLY Expense Claims and Leave Management
   - Click on "Expense Claims"
   - You'll see the app launcher page with SSO token

4. **Test Access Denial**:
   - Try to access: http://localhost:8000/dashboard/launch/stripe/
   - You should get error: "You don't have permission to access Stripe Dashboard"
   - You'll be redirected back to dashboard

---

## 🎯 Key URLs to Bookmark

### User Portals
- **Home**: http://localhost:8000/
- **Login**: http://localhost:8000/auth/login/
- **Dashboard**: http://localhost:8000/dashboard/

### Admin Panel (Superuser/Staff Only)
- **Admin Dashboard**: http://localhost:8000/admin-panel/
- **User Management**: http://localhost:8000/admin-panel/users/
- **App Access Matrix**: http://localhost:8000/admin-panel/app-access-matrix/
- **Audit Logs**: http://localhost:8000/admin-panel/audit-logs/

### SSO API
- **Get Token**: POST http://localhost:8000/api/sso/token/
- **Validate Token**: POST http://localhost:8000/api/sso/validate/
- **Refresh Token**: POST http://localhost:8000/api/sso/refresh/
- **User Info**: GET http://localhost:8000/api/sso/user/

---

## 🧪 Test the SSO API

### Get JWT Token
```bash
curl -X POST http://localhost:8000/api/sso/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "ivan.wong@krystal.institute",
    "password": "krystal2025"
  }'
```

You'll get:
```json
{
  "access": "eyJ0eXAiOiJKV1Qi...",
  "refresh": "eyJ0eXAiOiJKV1Qi...",
  "user": {
    "id": 1,
    "email": "ivan.wong@krystal.institute",
    "permissions": {
      "expense_claims": true,
      "leave_system": true,
      "asset_management": true,
      "crm": true,
      "quotations": true,
      "stripe": true
    },
    "roles": {
      "expense_claims": "admin",
      "leave_system": "admin",
      "asset_management": "admin",
      "crm": "admin",
      "quotations": "admin",
      "stripe": "admin"
    }
  }
}
```

### Validate Token
```bash
# Copy the access token from above
TOKEN="paste_your_token_here"

curl -X POST http://localhost:8000/api/sso/validate/ \
  -H "Authorization: Bearer $TOKEN"
```

### Check Permission
```bash
curl -X POST http://localhost:8000/api/sso/check-permission/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "app_name": "expense_claims"
  }'
```

---

## 📋 Common Tasks

### Grant Employee Access to All Users
1. Go to Admin Panel → App Access Matrix
2. For each user row, set "expense_claims" to "Employee"
3. Set "leave_system" to "Employee"
4. Other apps can remain "None"

### Make Someone an App Admin
1. Go to Admin Panel → Manage Users
2. Click on the user
3. Find the app (e.g., "Expense Claims")
4. Change dropdown to "Admin"
5. User now has admin access to that app

### View Who Changed What
1. Go to Admin Panel → View Audit Logs
2. Filter by:
   - Action: "Access Granted", "Role Changed", etc.
   - App: Select specific app
   - User: Type user email
3. See complete history with timestamps

### Bulk Setup for New Department
1. Go to Admin Panel → Manage Users
2. For each new user:
   - Click user
   - Grant access to their department's apps
   - e.g., Finance team → Expense Claims (Manager), Stripe Dashboard (Employee)

---

## 🔒 Security Best Practices

### 1. Token Management
- Access tokens expire after 1 hour
- Refresh tokens expire after 24 hours
- On logout, all user tokens are revoked
- Deactivating a user revokes their tokens

### 2. Role Assignment
- **Employee**: Can use the app's basic features
- **Manager**: Can approve, manage team, run reports
- **Admin**: Full control, can manage app settings
- **None**: No access at all

### 3. Regular Audits
- Review Admin Panel → Audit Logs weekly
- Look for unusual permission changes
- Check for failed access attempts
- Verify new users have appropriate access

---

## 🐛 Common Issues

### "I can't see the Admin Panel"
**Solution**: Only superusers and staff can access it. Run:
```bash
python manage.py shell
```
```python
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(email='your.email@company.com')
user.is_staff = True
user.is_superuser = True
user.save()
```

### "Dashboard is empty"
**Solution**: Admin hasn't granted you access to any apps yet. Contact your administrator.

### "Changes in Admin Panel don't save"
**Solution**:
- Check browser console (F12) for errors
- Make sure you're logged in as admin
- Try refreshing the page

### "Token validation fails"
**Solution**:
- Check token hasn't expired (1 hour limit)
- Verify SSO_SECRET_KEY matches in both integrated platform and individual app
- Make sure token is passed correctly (Authorization: Bearer YOUR_TOKEN)

---

## 📊 Architecture Summary

```
User Login
    ↓
Generate JWT with permissions
    ↓
User sees dashboard (filtered by permissions)
    ↓
User clicks app
    ↓
Check permission in database (UserAppAccess)
    ↓
If allowed: Pass JWT to app
    ↓
App validates JWT
    ↓
User auto-logged in with their role
```

---

## ✅ Verification Checklist

- [ ] Server running on port 8000
- [ ] Can log in as admin
- [ ] Admin panel loads (/admin-panel/)
- [ ] Can view user list
- [ ] Can view app access matrix
- [ ] Can change user permissions via user detail page
- [ ] Changes save automatically
- [ ] Audit logs show permission changes
- [ ] Regular user sees only permitted apps on dashboard
- [ ] Clicking app generates JWT and launches
- [ ] Access denied works for unpermitted apps
- [ ] SSO API endpoints work (token, validate, refresh)

---

## 📚 Next Steps

1. ✅ **Test the system** using the steps above
2. ✅ **Grant permissions** to your team members
3. 📝 **Integrate JWT validation** into each business app
4. 🔒 **Set up production** SSO_SECRET_KEY in environment
5. 📊 **Monitor audit logs** regularly

---

## 🆘 Need Help?

Check the main documentation: `SSO_AND_ADMIN_PANEL_COMPLETE.md`

Key files:
- Models: `/core/models.py`, `/sso/models.py`
- Views: `/admin_panel/views.py`, `/apps/dashboard/views.py`
- Templates: `/admin_panel/templates/`
- API: `/sso/views.py`, `/sso/utils.py`

Happy managing! 🎉
