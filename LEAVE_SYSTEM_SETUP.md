# Leave Management System - Setup & Troubleshooting

## ✅ System Status

The Leave Management System has been successfully integrated into the Integrated Business Platform.

## Access URLs

- **Dashboard**: http://localhost:8000/dashboard/
- **Leave System**: http://localhost:8000/leave/ (redirects to `/leave/dashboard/`)

## Quick Start

### 1. Ensure Employee Profiles Exist

All users need an Employee profile to access the leave system. Run this command to create profiles for users without one:

```bash
cd ~/Desktop/integrated_business_platform
source venv/bin/activate
python manage.py create_employee_profiles
```

### 2. Start/Restart the Server

#### Using the Start Script (Recommended)
```bash
cd ~/Desktop/integrated_business_platform
./start_server.sh
```

#### Manual Start with Gunicorn
```bash
cd ~/Desktop/integrated_business_platform
source venv/bin/activate
gunicorn business_platform.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --reload \
    --daemon
```

#### Development Server (Alternative)
```bash
cd ~/Desktop/integrated_business_platform
source venv/bin/activate
python manage.py runserver 0.0.0.0:8000
```

### 3. Restart Gunicorn (If Already Running)

If you get a 404 error after updating code, restart Gunicorn:

```bash
# Kill existing Gunicorn processes
pkill -9 -f "gunicorn.*8000"

# Restart Gunicorn
cd ~/Desktop/integrated_business_platform
source venv/bin/activate
gunicorn business_platform.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --reload \
    --daemon
```

## Management Commands

### Setup Leave Application Config
```bash
python manage.py setup_leave_app
```
Ensures the Leave Management System is properly configured and visible on the dashboard.

### Create Employee Profiles
```bash
python manage.py create_employee_profiles
```
Creates Employee profiles for all users without one. Required for leave system access.

## Troubleshooting

### Issue: 404 Error on /leave/

**Cause**: Gunicorn server needs to be restarted to pick up URL changes.

**Solution**:
```bash
pkill -9 -f "gunicorn.*8000"
cd ~/Desktop/integrated_business_platform
source venv/bin/activate
gunicorn business_platform.wsgi:application --bind 0.0.0.0:8000 --workers 4 --daemon
```

### Issue: "No Employee Profile" Error

**Cause**: User doesn't have an Employee record in the database.

**Solution**:
```bash
python manage.py create_employee_profiles
```

### Issue: Leave System Not Showing on Dashboard

**Cause**: ApplicationConfig is not active.

**Solution**:
```bash
python manage.py setup_leave_app
```

### Issue: Permission Denied Errors

**Cause**: User doesn't have proper permissions.

**Solution**:
1. Log in as an admin user
2. Go to Django Admin: http://localhost:8000/admin/
3. Grant necessary permissions to the user

## Database Models

The leave system includes these models:
- **Employee**: User profiles with company details
- **LeaveType**: Types of leave (Annual, Sick, etc.)
- **LeaveApplication**: Leave requests
- **SpecialLeaveApplication**: Special leave requests
- **SpecialWorkClaim**: Work claim requests
- **LeaveBalance**: Employee leave balances
- **Holiday**: Public holidays
- **PendingRegistration**: Employee registration workflow
- **EmployeeImport**: Bulk import tracking

## Configuration Files

- `business_platform/settings.py` - App configuration
- `business_platform/urls.py` - URL routing
- `leave_management/urls.py` - Leave-specific URLs
- `gunicorn_config.py` - Gunicorn server settings

## Logs

Check logs if issues occur:
```bash
# Check Gunicorn logs
tail -f logs/gunicorn-access.log
tail -f logs/gunicorn-error.log

# Check Django logs
tail -f logs/django.log
```

## Production Deployment

For production deployment:

1. Update `.env` file with production settings
2. Set `DEBUG=False`
3. Configure `ALLOWED_HOSTS`
4. Run migrations: `python manage.py migrate`
5. Collect static files: `python manage.py collectstatic`
6. Create employee profiles: `python manage.py create_employee_profiles`
7. Setup leave app: `python manage.py setup_leave_app`
8. Start Gunicorn: `./start_server.sh`

## Support

For issues:
1. Check this troubleshooting guide
2. Review logs in the `logs/` directory
3. Verify database migrations: `python manage.py showmigrations leave_management`
4. Contact system administrator

## Recent Updates

- **2025-11-10**: Integrated Leave Management System
- **2025-11-10**: Created employee profile auto-creation command
- **2025-11-10**: Fixed URL routing and Gunicorn restart procedure
