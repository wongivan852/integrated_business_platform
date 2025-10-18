"""
App Registry for Integrated Business Platform
Defines all integrated business applications
"""

INTEGRATED_APPS = {
    'expense_claims': {
        'name': 'Expense Claims',
        'description': 'Submit and manage expense claims with receipts',
        'icon': 'fa-file-invoice-dollar',
        'url': 'http://localhost:8001',
        'internal_path': '/expense-claims/',
        'color': 'primary',
        'gradient': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        'status': 'active',
        'order': 1,
    },
    'leave_system': {
        'name': 'Leave Management',
        'description': 'Apply for leave and manage annual leave balance',
        'icon': 'fa-calendar-check',
        'url': 'http://localhost:8002',
        'internal_path': '/leave/',
        'color': 'success',
        'gradient': 'linear-gradient(135deg, #11998e 0%, #38ef7d 100%)',
        'status': 'active',
        'order': 2,
    },
    'asset_management': {
        'name': 'Asset Management',
        'description': 'Track and manage company assets',
        'icon': 'fa-boxes',
        'url': 'http://localhost:8003',
        'internal_path': '/assets/',
        'color': 'info',
        'gradient': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
        'status': 'active',
        'order': 3,
    },
    'crm': {
        'name': 'CRM System',
        'description': 'Customer relationship management',
        'icon': 'fa-users',
        'url': 'http://localhost:8004',
        'internal_path': '/crm/',
        'color': 'warning',
        'gradient': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)',
        'status': 'active',
        'order': 4,
    },
    'quotations': {
        'name': 'Cost Quotations',
        'description': 'Generate and manage cost quotations',
        'icon': 'fa-file-contract',
        'url': 'http://localhost:8005',
        'internal_path': '/quotations/',
        'color': 'secondary',
        'gradient': 'linear-gradient(135deg, #a8edea 0%, #fed6e3 100%)',
        'status': 'active',
        'order': 5,
    },
    'stripe': {
        'name': 'Stripe Dashboard',
        'description': 'Payment reconciliation and Stripe management',
        'icon': 'fa-stripe-s',
        'url': 'http://localhost:8081',
        'internal_path': '/stripe/',
        'color': 'primary',
        'gradient': 'linear-gradient(135deg, #6a11cb 0%, #2575fc 100%)',
        'status': 'active',
        'order': 6,
    },
}


def get_all_apps():
    """Return all registered apps sorted by order"""
    return sorted(INTEGRATED_APPS.values(), key=lambda x: x['order'])


def get_active_apps():
    """Return only active apps"""
    return [app for app in get_all_apps() if app['status'] == 'active']


def get_app_by_key(key):
    """Get a specific app by its key"""
    return INTEGRATED_APPS.get(key)
