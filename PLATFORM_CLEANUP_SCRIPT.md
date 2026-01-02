# Platform App Cleanup - Execution Script

**IMPORTANT**: This script will clean up duplicate and invalid ApplicationConfig entries while preserving Project Management, Stripe Dashboard, and Leave Management.

## 🔒 Pre-Execution Checklist

- [ ] Backup database
- [ ] Test critical apps (Project Management, Stripe, Leave Management)
- [ ] Note down current ApplicationConfig IDs
- [ ] Server is running on port 8080

## 📊 Step 1: Backup & Verify

```bash
# Backup database
cd /home/user/integrated_business_platform
cp db.sqlite3 db.sqlite3.backup.$(date +%Y%m%d_%H%M%S)

# Verify backup
ls -lh db.sqlite3*

# Test critical apps (open in browser)
# - http://192.168.0.104:8080/project-management/
# - http://192.168.0.104:8080/stripe/
# - http://192.168.0.104:8080/leave/
```

## 🗑️ Step 2: Remove Duplicate & Invalid Entries

```bash
cd /home/user/integrated_business_platform
source venv/bin/activate
python3 manage.py shell << 'CLEANUP_EOF'

from authentication.models import ApplicationConfig

print("=" * 80)
print("CLEANUP - Removing Duplicates and Invalid Entries")
print("=" * 80)

# List all current entries
print("\n📋 BEFORE CLEANUP:")
apps = ApplicationConfig.objects.all().order_by('order')
for app in apps:
    status = "🟢" if app.is_active else "🔴"
    print(f"{app.id:3} {status} {app.display_name:<30} → {app.url}")

# Remove duplicates and invalid entries
to_remove = []

# Find duplicate CRM (external)
crm_external = ApplicationConfig.objects.filter(
    display_name='CRM System',
    url='http://localhost:8004/'
).first()
if crm_external:
    to_remove.append(('CRM System (External)', crm_external))

# Find Asset Management System (external)
asset_external = ApplicationConfig.objects.filter(
    display_name='Asset Management System',
    url='http://localhost:8005/'
).first()
if asset_external:
    to_remove.append(('Asset Management System (External)', asset_external))

# Find Asset Dashboard (invalid URL)
asset_dashboard = ApplicationConfig.objects.filter(
    display_name='Asset Dashboard'
).first()
if asset_dashboard:
    to_remove.append(('Asset Dashboard', asset_dashboard))

# Remove them
print("\n🗑️  REMOVING:")
for name, app_obj in to_remove:
    print(f"   Deleting: {name} (ID: {app_obj.id})")
    app_obj.delete()

print(f"\n✅ Removed {len(to_remove)} entries")

# Show remaining
print("\n📋 AFTER CLEANUP:")
apps = ApplicationConfig.objects.all().order_by('order')
for app in apps:
    status = "🟢" if app.is_active else "🔴"
    print(f"{app.id:3} {status} {app.display_name:<30} → {app.url}")

print("\n" + "=" * 80)
CLEANUP_EOF
```

## ✏️ Step 3: Standardize Naming

```bash
python3 manage.py shell << 'RENAME_EOF'

from authentication.models import ApplicationConfig

print("\n📝 STANDARDIZING NAMES:")
print("=" * 80)

# Rename "Asset Tracking" to "Asset Management System"
asset_tracking = ApplicationConfig.objects.filter(
    display_name='Asset Tracking'
).first()

if asset_tracking:
    old_name = asset_tracking.display_name
    asset_tracking.display_name = 'Asset Management System'
    asset_tracking.description = 'Track and manage company assets, locations, and movements'
    asset_tracking.save()
    print(f"✅ Renamed: '{old_name}' → '{asset_tracking.display_name}'")
else:
    print("ℹ️  'Asset Tracking' not found (may already be renamed)")

print("=" * 80)
RENAME_EOF
```

## ➕ Step 4: Add Missing Configs (Optional Sub-modules)

```bash
python3 manage.py shell << 'ADD_EOF'

from authentication.models import ApplicationConfig

print("\n➕ ADDING MISSING CONFIGURATIONS:")
print("=" * 80)

# These are sub-modules, can be added for completeness
# But typically accessed through parent apps

missing_configs = [
    {
        'name': 'expense_documents',
        'display_name': 'Expense Documents',
        'description': 'Manage expense claim documents and attachments',
        'url': '/expense-documents/',
        'icon': 'fas fa-file-invoice',
        'color': '#e91e63',
        'order': 50,
        'is_active': False,  # Hidden, accessed via Expense Claims
    },
    {
        'name': 'expense_reports',
        'display_name': 'Expense Reports',
        'description': 'Generate and view expense reports',
        'url': '/expense-reports/',
        'icon': 'fas fa-chart-bar',
        'color': '#9c27b0',
        'order': 51,
        'is_active': False,  # Hidden, accessed via Expense Claims
    },
    {
        'name': 'locations',
        'display_name': 'Asset Locations',
        'description': 'Manage asset storage locations',
        'url': '/locations/',
        'icon': 'fas fa-map-marker-alt',
        'color': '#00bcd4',
        'order': 52,
        'is_active': False,  # Hidden, accessed via Asset Management
    },
    {
        'name': 'movements',
        'display_name': 'Asset Movements',
        'description': 'Track asset movements and transfers',
        'url': '/movements/',
        'icon': 'fas fa-truck',
        'color': '#00bcd4',
        'order': 53,
        'is_active': False,  # Hidden, accessed via Asset Management
    },
]

for config in missing_configs:
    app, created = ApplicationConfig.objects.get_or_create(
        name=config['name'],
        defaults=config
    )
    if created:
        print(f"✅ Added: {config['display_name']} (hidden sub-module)")
    else:
        print(f"ℹ️  Already exists: {config['display_name']}")

print("=" * 80)
ADD_EOF
```

## 🎨 Step 5: Reorganize Display Order

```bash
python3 manage.py shell << 'REORDER_EOF'

from authentication.models import ApplicationConfig

print("\n🎨 REORGANIZING DISPLAY ORDER:")
print("=" * 80)

# Define desired order with categories
app_order = {
    # Financial Management
    'expense_claims': {'order': 10, 'category': 'financial'},
    'quotations': {'order': 11, 'category': 'financial'},
    'stripe_dashboard': {'order': 12, 'category': 'financial'},
    
    # Asset & Inventory
    'assets': {'order': 20, 'category': 'assets'},
    
    # Human Resources
    'leave_management': {'order': 30, 'category': 'hr'},
    'attendance': {'order': 31, 'category': 'hr'},
    'qr_attendance': {'order': 32, 'category': 'hr'},
    
    # Project & Event Management
    'project_management': {'order': 40, 'category': 'projects'},
    'event_management': {'order': 41, 'category': 'projects'},
    
    # Customer Management
    'crm': {'order': 50, 'category': 'customer'},
    
    # Sub-modules (hidden)
    'expense_documents': {'order': 100, 'category': 'hidden'},
    'expense_reports': {'order': 101, 'category': 'hidden'},
    'locations': {'order': 102, 'category': 'hidden'},
    'movements': {'order': 103, 'category': 'hidden'},
}

for name, config in app_order.items():
    try:
        app = ApplicationConfig.objects.get(name=name)
        app.order = config['order']
        app.save()
        print(f"✅ {app.display_name:<30} → Order: {config['order']:3}")
    except ApplicationConfig.DoesNotExist:
        print(f"⚠️  App '{name}' not found in database")

print("=" * 80)
REORDER_EOF
```

## 🔍 Step 6: Verify Results

```bash
python3 manage.py shell << 'VERIFY_EOF'

from authentication.models import ApplicationConfig

print("\n" + "=" * 80)
print("FINAL APPLICATION CONFIGURATION")
print("=" * 80)

apps = ApplicationConfig.objects.all().order_by('order', 'display_name')

categories = {
    'financial': '💰 Financial Management',
    'assets': '📦 Asset & Inventory',
    'hr': '👥 Human Resources',
    'projects': '📊 Project & Event Management',
    'customer': '🤝 Customer Management',
    'hidden': '🔒 Sub-Modules (Hidden)',
}

current_category = None
for app in apps:
    # Detect category based on order
    if 10 <= app.order < 20:
        category = 'financial'
    elif 20 <= app.order < 30:
        category = 'assets'
    elif 30 <= app.order < 40:
        category = 'hr'
    elif 40 <= app.order < 50:
        category = 'projects'
    elif 50 <= app.order < 60:
        category = 'customer'
    else:
        category = 'hidden'
    
    if category != current_category:
        print(f"\n{categories.get(category, 'Other')}")
        print("-" * 80)
        current_category = category
    
    status = "🟢" if app.is_active else "🔴"
    print(f"{status} [{app.order:3}] {app.display_name:<30} → {app.url}")

print("\n" + "=" * 80)
print(f"Total Apps: {apps.count()}")
print(f"Active: {apps.filter(is_active=True).count()}")
print(f"Inactive: {apps.filter(is_active=False).count()}")
print("=" * 80)
VERIFY_EOF
```

## ✅ Step 7: Test Critical Apps

```bash
echo "Testing critical apps..."
echo "1. Project Management: http://192.168.0.104:8080/project-management/"
echo "2. Stripe Dashboard: http://192.168.0.104:8080/stripe/"
echo "3. Leave Management: http://192.168.0.104:8080/leave/"
echo ""
echo "Please test these URLs in your browser and verify they work!"
```

## 🔄 Step 8: Restart Server

```bash
# Restart gunicorn to apply changes
pkill -f "gunicorn.*8080"
sleep 2
cd /home/user/integrated_business_platform
source venv/bin/activate
gunicorn business_platform.wsgi:application --bind 0.0.0.0:8080 --workers 2 --daemon

sleep 3
echo "✅ Server restarted on port 8080"

# Check server status
ps aux | grep "gunicorn.*8080" | grep -v grep
```

## 📋 Post-Execution Checklist

- [ ] All 3 critical apps working (Project Management, Stripe, Leave Management)
- [ ] Dashboard displays correctly
- [ ] No duplicate entries
- [ ] Proper display order
- [ ] SSO authentication works
- [ ] Server is stable

## 🆘 Rollback (If Something Goes Wrong)

```bash
# Stop server
pkill -f "gunicorn.*8080"

# Restore backup
cd /home/user/integrated_business_platform
cp db.sqlite3 db.sqlite3.failed
# Find your backup file
ls -lt db.sqlite3.backup.* | head -1
# Replace with actual backup filename:
cp db.sqlite3.backup.YYYYMMDD_HHMMSS db.sqlite3

# Restart server
source venv/bin/activate
gunicorn business_platform.wsgi:application --bind 0.0.0.0:8080 --workers 2 --daemon
```

## 📈 Expected Results

**Before**:
- 13 ApplicationConfig entries
- 2 duplicates
- 1 invalid URL
- Inconsistent naming
- No clear organization

**After**:
- 10 active app entries (clean, no duplicates)
- 4 inactive sub-module entries (for completeness)
- Standardized naming
- Organized by category
- Proper display order

## 🎯 Summary of Changes

1. ✅ Removed 3 duplicate/invalid entries
2. ✅ Standardized "Asset Tracking" → "Asset Management System"
3. ✅ Added 4 sub-module configs (marked inactive)
4. ✅ Reorganized display order by category
5. ✅ Maintained all 3 critical apps (Project Management, Stripe, Leave)

---

**Ready to Execute**: Yes, safe to proceed with these commands.
