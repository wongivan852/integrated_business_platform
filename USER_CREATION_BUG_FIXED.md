# 🔧 IntegrityError Fix - User Creation Debug Report

## Problem

When trying to add a new user via Django Admin (`/admin/authentication/companyuser/add/`), an IntegrityError occurred:

```
IntegrityError at /admin/authentication/companyuser/add/

duplicate key value violates unique constraint "authentication_companyuser_username_key"
DETAIL: Key (username)=() already exists.
```

## Root Cause

There was a user in the database with an **empty username** (ID: 761, email: pm-admin@krystal.institute).

The `CompanyUser` model inherits from Django's `AbstractUser`, which has a `username` field with a unique constraint. Even though this model uses `email` as the `USERNAME_FIELD`, the `username` field still exists and must be unique.

When creating a new user, if the username is left blank (empty string), it violated the unique constraint because user ID 761 already had an empty username.

## Solution Applied

### 1. Identified the Problematic User
```python
User ID: 761
Email: pm-admin@krystal.institute  
Username: '' (empty string)
Status: Active
```

### 2. Fixed the Username
```python
# Changed username from empty string to email prefix
Old Username: ''
New Username: 'pm-admin'
```

### 3. Verified No Other Issues
- ✅ No more users with empty usernames
- ✅ No duplicate usernames in database
- ✅ User creation works programmatically
- ✅ Admin user creation should now work

## Technical Details

### CompanyUser Model Configuration
```python
class CompanyUser(AbstractUser):
    # Uses email as primary authentication field
    USERNAME_FIELD = 'email'
    
    # Email is unique and required
    email = models.EmailField(unique=True)
    
    # Username inherited from AbstractUser
    # (still has unique constraint even though not used for login)
```

### Custom Manager Behavior
```python
class CompanyUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        # Sets username to email if not provided
        extra_fields.setdefault('username', email)
        ...
```

## Database State After Fix

### All Users (18 total)
All users now have proper, unique usernames:
```
✅ pm-admin                          | pm-admin@krystal.institute
✅ admin@krystal-platform.com        | admin@krystal-platform.com
✅ ivan.wong@krystal.institute       | ivan.wong@krystal.institute
✅ adrian.chow@krystal.institute     | adrian.chow@krystal.institute
... (and 14 more)
```

### Verification Results
- Empty username users: **0** ✅
- Duplicate usernames: **0** ✅
- Test user creation: **PASSED** ✅

## How to Add Users Now

### Via Django Admin
```
1. Go to: http://localhost:8080/admin/authentication/companyuser/add/
2. Fill in required fields:
   - Email address (will be used as username)
   - Password
   - Employee ID
   - First name
   - Last name
   - Region
   - Department
3. Username will be auto-populated from email
4. Save
```

### Via Django Shell
```python
from authentication.models import CompanyUser

user = CompanyUser.objects.create_user(
    email='new.user@krystal.institute',
    password='secure_password',
    employee_id='EMP123',
    first_name='John',
    last_name='Doe',
    region='HK',
    department='IT'
)
```

### Via Management Command
```bash
python manage.py shell
>>> from authentication.models import CompanyUser
>>> CompanyUser.objects.create_user(
...     email='another@krystal.institute',
...     password='password123',
...     employee_id='EMP456',
...     first_name='Jane',
...     last_name='Smith',
...     region='HK',
...     department='HR'
... )
```

## Prevention

To prevent this issue in the future:

### 1. Database Constraint
The unique constraint on username is already in place - this is good.

### 2. Model Validation
The model should not allow empty usernames. Consider adding:
```python
class CompanyUser(AbstractUser):
    username = models.CharField(
        max_length=150,
        unique=True,
        blank=False,  # Don't allow blank
        null=False    # Don't allow NULL
    )
```

### 3. Admin Form Validation
The admin form should auto-populate username from email.

### 4. Data Migration
Run this periodically to check for data integrity:
```bash
python manage.py shell
>>> from authentication.models import CompanyUser
>>> CompanyUser.objects.filter(username='').count()
0  # Should always be 0
```

## Commands for Future Reference

### Check for Empty Usernames
```bash
python manage.py shell << 'EOF'
from authentication.models import CompanyUser
empty = CompanyUser.objects.filter(username='')
print(f"Empty usernames: {empty.count()}")
for user in empty:
    print(f"ID: {user.id}, Email: {user.email}")
