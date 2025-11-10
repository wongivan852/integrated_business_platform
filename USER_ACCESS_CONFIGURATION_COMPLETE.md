# User Access Configuration - Complete Guide

**Date**: October 28, 2025
**Status**: ✅ **COMPLETED**
**Access Grants Created**: 22
**Total Active Grants**: 23

---

## Executive Summary

Successfully configured user access grants for the Integrated Business Platform using **email addresses as user identifiers**. All 3 active users now have appropriate app access based on their roles.

### Configuration Overview

- **Total Users**: 3
- **Total Access Grants**: 23
- **Average Grants per User**: 7.7
- **Apps Configured**: 9 apps
- **Configuration Method**: Email-based identity matching

---

## 1. Current User Access Status

### 1.1 Admin Users (Full Access)

#### admin@krystal-platform.com (Platform Administrator)
**Role**: Superuser
**Access Level**: Admin (9 apps)

| App | Role | Granted Date |
|-----|------|--------------|
| Asset Management | ADMIN | 2025-10-28 |
| Attendance System | ADMIN | 2025-10-28 |
| CRM System | ADMIN | 2025-10-28 |
| Event Management | ADMIN | 2025-10-27 |
| Expense Claims | ADMIN | 2025-10-28 |
| Leave Management | ADMIN | 2025-10-28 |
| Project Management | ADMIN | 2025-10-28 |
| Cost Quotations | ADMIN | 2025-10-28 |
| Stripe Dashboard | ADMIN | 2025-10-28 |

---

#### ivan.wong@krystal.institute (Ivan Wong)
**Role**: Superuser / IT Manager
**Access Level**: Admin (9 apps)

| App | Role | Granted Date |
|-----|------|--------------|
| Asset Management | ADMIN | 2025-10-28 |
| Attendance System | ADMIN | 2025-10-28 |
| CRM System | ADMIN | 2025-10-28 |
| Event Management | ADMIN | 2025-10-28 |
| Expense Claims | ADMIN | 2025-10-28 |
| Leave Management | ADMIN | 2025-10-28 |
| Project Management | ADMIN | 2025-10-28 |
| Cost Quotations | ADMIN | 2025-10-28 |
| Stripe Dashboard | ADMIN | 2025-10-28 |

---

### 1.2 Regular Employees

#### test.user@krystal.institute (Test User)
**Role**: Employee
**Access Level**: Employee (5 apps)

| App | Role | Granted Date |
|-----|------|--------------|
| Attendance System | EMPLOYEE | 2025-10-28 |
| Event Management | EMPLOYEE | 2025-10-28 |
| Expense Claims | EMPLOYEE | 2025-10-28 |
| Leave Management | EMPLOYEE | 2025-10-28 |
| Project Management | EMPLOYEE | 2025-10-28 |

**Note**: Test user has access to core employee apps but not financial/admin apps (CRM, Quotations, Stripe, Asset Management).

---

## 2. Configuration Method

### 2.1 Email-Based Identity Matching ✅

The system uses **email addresses** as the primary identifier for user access configuration. This approach offers:

**Advantages**:
- ✅ Unique identifier (email is unique per user)
- ✅ Easy to read and verify
- ✅ Matches login credentials
- ✅ Professional and intuitive
- ✅ Works well with SSO systems
- ✅ Easy to audit and track

**Configuration File**: `configure_user_access.py`

```python
USER_ACCESS_CONFIG = {
    'admin@krystal-platform.com': {
        'expense_claims': 'admin',
        'leave_system': 'admin',
        # ... all apps with admin access
    },
    'ivan.wong@krystal.institute': {
        'expense_claims': 'admin',
        'leave_system': 'admin',
        # ... all apps with admin access
    },
    'test.user@krystal.institute': {
        'expense_claims': 'employee',
        'leave_system': 'employee',
        # ... core apps with employee access
    },
}
```

---

### 2.2 Role Levels

The system supports 4 role levels per app:

| Role | Access Level | Permissions |
|------|-------------|-------------|
| **none** | No Access | Cannot access the app at all |
| **employee** | Basic Access | Can use core features, submit requests |
| **manager** | Manager Access | Can approve, manage team, run reports |
| **admin** | Full Access | Complete control, can manage app settings |

---

## 3. Configuration Script Usage

### 3.1 Quick Start

```bash
# 1. Navigate to platform directory
cd /Users/wongivan/ai_tools/business_tools/integrated_business_platform

# 2. Run dry-run to preview changes (recommended)
python configure_user_access.py --dry-run

# 3. Apply configuration
python configure_user_access.py

# 4. View help
python configure_user_access.py --help
```

---

### 3.2 Adding New Users

To add a new user to the access configuration:

1. **Edit `configure_user_access.py`**:

```python
USER_ACCESS_CONFIG = {
    # ... existing users ...

    # Add new user
    'new.employee@krystal.institute': {
        'expense_claims': 'employee',
        'leave_system': 'employee',
        'attendance': 'employee',
    },
}
```

2. **Run the configuration**:

```bash
python configure_user_access.py
```

3. **Verify in admin panel**:
   - Go to http://localhost:8000/admin-panel/
   - Check user's access in User Detail page

---

### 3.3 Updating User Access

To change a user's access level:

1. **Edit the user's configuration** in `configure_user_access.py`

```python
'existing.user@krystal.institute': {
    'expense_claims': 'manager',  # Changed from 'employee' to 'manager'
    'leave_system': 'employee',
},
```

2. **Run the configuration**:

```bash
python configure_user_access.py
```

The script will automatically update the role and log the change.

---

### 3.4 Removing User Access

To remove access to an app:

1. **Remove the app from user's configuration** or set role to `'none'`

```python
'user@krystal.institute': {
    'expense_claims': 'none',  # Explicitly deny access
    # OR remove the line entirely
},
```

2. **Run the configuration**:

```bash
python configure_user_access.py
```

---

## 4. Department-Based Access (Optional)

The configuration script supports automatic role assignment based on department:

```python
DEPARTMENT_ACCESS = {
    'IT': {
        'project_management': 'manager',
        'asset_management': 'manager',
    },
    'Finance': {
        'expense_claims': 'manager',
        'stripe': 'manager',
    },
    'HR': {
        'leave_system': 'manager',
        'attendance': 'manager',
    },
    'Sales': {
        'crm': 'manager',
        'quotations': 'manager',
    },
}
```

**How it works**:
- All users in a department automatically get the configured access
- Individual user configuration overrides department access
- Useful for large organizations with standardized roles

---

## 5. Default Employee Access (Optional)

Set default access for all employees who don't have specific configuration:

```python
DEFAULT_EMPLOYEE_ACCESS = {
    'expense_claims': 'employee',
    'leave_system': 'employee',
    'attendance': 'employee',
}
```

**When to use**:
- New employees should have basic access immediately
- Core apps that everyone needs
- Set to `None` to disable default access

---

## 6. Admin Panel Management

### 6.1 View User Access

1. Go to http://localhost:8000/admin-panel/
2. Click "Manage Users"
3. Click on a user to see their app access

### 6.2 Update Access via Admin Panel

You can also update access through the admin panel UI:

1. Go to User Detail page
2. Change role dropdown for any app
3. Changes save automatically (AJAX)

**Advantages**:
- No need to edit code
- Visual interface
- Changes are logged in audit trail

**When to use**:
- Quick one-off changes
- Non-technical administrators
- Testing access levels

---

## 7. Verification and Testing

### 7.1 Verify Configuration

```bash
# Check access grants in database
python manage.py shell << 'EOF'
from django.contrib.auth import get_user_model
from core.models import UserAppAccess

User = get_user_model()

for user in User.objects.filter(is_active=True):
    grants = UserAppAccess.objects.filter(user=user, is_active=True)
    print(f"{user.email}: {grants.count()} apps")
EOF
```

### 7.2 Test User Login

1. **Test as admin**:
   - Email: admin@krystal-platform.com
   - Should see all 9 apps on dashboard

2. **Test as regular employee**:
   - Email: test.user@krystal.institute
   - Should see only 5 apps on dashboard

3. **Test SSO Launch**:
   - Click on any app card
   - Should be automatically logged in with JWT token
   - Check role permissions in the app

---

## 8. Database Status

### Current State (as of 2025-10-28)

```
Total Active Users:        3
Total Access Grants:       23
Average Grants per User:   7.7

Admin Users:               2 (18 grants)
Regular Users:             1 (5 grants)

Configured Apps:           9
  - Asset Management
  - Attendance System
  - CRM System
  - Event Management
  - Expense Claims
  - Leave Management
  - Project Management
  - Cost Quotations
  - Stripe Dashboard
```

---

## 9. Audit Trail

### Access Grant Tracking

Every access grant is tracked with:
- User email
- App code
- Role granted
- Granted by (who made the change)
- Granted at (timestamp)
- Modified by (if updated)
- Modified at (if updated)

### Viewing Audit Logs

```bash
# Via Admin Panel
http://localhost:8000/admin-panel/audit-logs/

# Via database query
python manage.py shell << 'EOF'
from core.models import AppAccessAuditLog
for log in AppAccessAuditLog.objects.all()[:10]:
    print(f"{log.action}: {log.user.email} @ {log.app_code}")
EOF
```

---

## 10. Best Practices

### 10.1 Email Format

✅ **Recommended**:
```
user@company.com
first.last@company.com
department.user@company.com
```

❌ **Avoid**:
```
user123  (use email instead)
user_name  (ambiguous)
```

### 10.2 Role Assignment Strategy

1. **Start with minimal access**:
   - Grant only what's needed
   - Use employee role by default
   - Promote to manager/admin as needed

2. **Department-based roles**:
   - IT: Admin access to technical apps
   - Finance: Manager access to financial apps
   - HR: Manager access to HR apps
   - Sales: Manager access to CRM/quotations

3. **Regular review**:
   - Review access quarterly
   - Remove access for inactive users
   - Update roles based on position changes

### 10.3 Security Considerations

1. **Principle of Least Privilege**:
   - Grant minimum access required
   - Don't give admin access unnecessarily

2. **Regular Audits**:
   - Review admin panel audit logs
   - Check for unusual access patterns
   - Verify user access matches their role

3. **Offboarding**:
   - Deactivate user account (user.is_active = False)
   - All access grants automatically become inactive
   - SSO tokens are revoked

---

## 11. Troubleshooting

### Issue: User can't see any apps on dashboard

**Solution**:
1. Check if user has any access grants:
   ```bash
   python manage.py shell -c "
   from django.contrib.auth import get_user_model
   from core.models import UserAppAccess
   user = get_user_model().objects.get(email='user@company.com')
   print(UserAppAccess.objects.filter(user=user, is_active=True))
   "
   ```

2. Grant access via configuration script or admin panel

---

### Issue: User has wrong access level

**Solution**:
1. Check configuration in `configure_user_access.py`
2. Run configuration script again
3. Or update via admin panel

---

### Issue: Changes not taking effect

**Solution**:
1. Verify configuration was applied (check success message)
2. Clear browser cache
3. Log out and log back in
4. Check database directly:
   ```bash
   python manage.py shell -c "
   from core.models import UserAppAccess
   UserAppAccess.objects.filter(user__email='user@company.com').values()
   "
   ```

---

## 12. Future Enhancements

### Planned Features:

1. **Bulk Import/Export**:
   - CSV import for multiple users
   - Excel export of current access matrix

2. **Access Request Workflow**:
   - Users can request access
   - Managers approve/deny requests
   - Automatic email notifications

3. **Time-Limited Access**:
   - Grant temporary access with expiration
   - Automatic revocation after date

4. **Group-Based Access**:
   - Define groups (e.g., "Finance Team")
   - Grant access to entire group
   - Easier management for large teams

---

## 13. Migration Guide

### From Manual to Email-Based Configuration

If you have users configured manually:

1. **Export current access**:
   ```bash
   python manage.py shell << 'EOF'
   from core.models import UserAppAccess
   for access in UserAppAccess.objects.filter(is_active=True):
       print(f"'{access.user.email}': {{'{access.app_code}': '{access.role}'}},")
   EOF
   ```

2. **Add to `USER_ACCESS_CONFIG`** in `configure_user_access.py`

3. **Run configuration script** to normalize

---

## 14. API Access (Advanced)

You can also manage access via API:

```python
from core.models import UserAppAccess
from django.contrib.auth import get_user_model

User = get_user_model()

# Grant access
user = User.objects.get(email='user@company.com')
UserAppAccess.objects.create(
    user=user,
    app_code='expense_claims',
    role='employee',
    granted_by=admin_user
)

# Update access
access = UserAppAccess.objects.get(user=user, app_code='expense_claims')
access.role = 'manager'
access.modified_by = admin_user
access.save()

# Revoke access
access.is_active = False
access.save()
```

---

## 15. Configuration Files

### Primary Files:
1. **configure_user_access.py** - Main configuration script
2. **core/models.py** - UserAppAccess and AppAccessAuditLog models
3. **apps/app_integrations/registry.py** - INTEGRATED_APPS registry

### Admin Panel:
- **admin_panel/views.py** - Admin panel views
- **admin_panel/templates/** - Admin panel templates

---

## 16. Quick Reference

### Commands:

```bash
# Preview changes (dry-run)
python configure_user_access.py --dry-run

# Apply configuration
python configure_user_access.py

# Show help
python configure_user_access.py --help

# Check current access
python manage.py shell -c "from core.models import UserAppAccess; print(UserAppAccess.objects.filter(is_active=True).count())"
```

### URLs:

```
Admin Panel:         http://localhost:8000/admin-panel/
User Management:     http://localhost:8000/admin-panel/users/
App Access Matrix:   http://localhost:8000/admin-panel/app-access-matrix/
Audit Logs:          http://localhost:8000/admin-panel/audit-logs/
```

---

## 17. Success Metrics

✅ **Configuration Completed**:
- 22 new access grants created
- 3 users configured
- 9 apps available
- 0 errors during configuration

✅ **Coverage**:
- 100% of active users have appropriate access
- Admin users: Full access to all apps
- Regular users: Access to core employee apps

✅ **Quality**:
- Email-based identity matching implemented
- Audit trail ready (AppAccessAuditLog model)
- Flexible configuration script created
- Comprehensive documentation provided

---

## 18. Conclusion

User access configuration is now **complete and operational**. The email-based identity system provides:

- ✅ Clear and intuitive user identification
- ✅ Easy configuration management
- ✅ Flexible role assignment
- ✅ Department-based automation options
- ✅ Complete audit trail
- ✅ Admin panel for quick changes

**Next Steps**:
1. Test user logins to verify access
2. Train administrators on admin panel usage
3. Set up regular access review schedule
4. Monitor audit logs for security

---

**Configuration Status**: ✅ **COMPLETE**
**Date Completed**: October 28, 2025
**Configured By**: System Administrator
**Total Access Grants**: 23 active grants

---

## Appendix A: Complete User Access Matrix

| User | Expense | Leave | Asset | CRM | Quotations | Stripe | Events | Projects | Attendance |
|------|---------|-------|-------|-----|------------|--------|--------|----------|------------|
| admin@krystal-platform.com | ADMIN | ADMIN | ADMIN | ADMIN | ADMIN | ADMIN | ADMIN | ADMIN | ADMIN |
| ivan.wong@krystal.institute | ADMIN | ADMIN | ADMIN | ADMIN | ADMIN | ADMIN | ADMIN | ADMIN | ADMIN |
| test.user@krystal.institute | EMP | EMP | - | - | - | - | EMP | EMP | EMP |

Legend:
- ADMIN = Full administrative access
- EMP = Employee access
- \- = No access

---

**Document Version**: 1.0
**Last Updated**: October 28, 2025
