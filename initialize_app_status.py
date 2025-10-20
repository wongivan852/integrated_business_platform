"""
Initialize App Status Data for All Business Applications
Run this script to populate the AppStatus and AppFunction models
"""

import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'business_platform.settings')
django.setup()

from core.models import AppStatus, AppFunction
from django.contrib.auth import get_user_model
from datetime import date

User = get_user_model()

# Get admin user (ivan.wong)
try:
    admin = User.objects.get(email='ivan.wong@krystal.institute')
except User.DoesNotExist:
    print("Admin user not found. Creating...")
    admin = User.objects.create_superuser(
        email='ivan.wong@krystal.institute',
        password='krystal2025',
        first_name='Ivan',
        last_name='Wong',
        employee_id='EMP001'
    )

# Application Data
APPS_DATA = [
    {
        'app_code': 'expense_claims',
        'app_name': 'Expense Claims System',
        'status': 'softlaunch',  # Most complete based on documentation
        'priority': 'high',
        'version': '1.2.0',
        'port': 8001,
        'repository_url': 'https://gitlab.kryedu.org/company_apps/company_expense_claim_system',
        'started_at': date(2025, 8, 1),
        'softlaunch_date': date(2025, 9, 15),
        'target_launch_date': date(2025, 11, 1),
        'notes': 'Enhanced with print system, decimal input fixes, GitLab integration complete',
        'functions': [
            {'name': 'Submit Expense Claim', 'code': 'submit_claim', 'status': 'production', 'priority': 'critical', 'is_ui': True, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'Upload Receipts', 'code': 'upload_receipts', 'status': 'production', 'priority': 'critical', 'is_ui': True, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'Approve/Reject Claims', 'code': 'approve_reject', 'status': 'production', 'priority': 'critical', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': True},
            {'name': 'Print Claim Forms', 'code': 'print_forms', 'status': 'production', 'priority': 'high', 'is_ui': True, 'is_api': False, 'has_tests': False, 'has_documentation': True},
            {'name': 'Expense Reports', 'code': 'reports', 'status': 'softlaunch', 'priority': 'medium', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
            {'name': 'Export to Excel', 'code': 'export_excel', 'status': 'softlaunch', 'priority': 'medium', 'is_ui': True, 'is_api': False, 'has_tests': False, 'has_documentation': False},
            {'name': 'Budget Tracking', 'code': 'budget_tracking', 'status': 'developing', 'priority': 'low', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
            {'name': 'Email Notifications', 'code': 'email_notifications', 'status': 'planned', 'priority': 'medium', 'is_ui': False, 'is_api': True, 'has_tests': False, 'has_documentation': False},
        ]
    },
    {
        'app_code': 'leave_system',
        'app_name': 'Leave Management System',
        'status': 'uat',
        'priority': 'high',
        'version': '1.0.0',
        'port': 8002,
        'repository_url': 'https://gitlab.kryedu.org/company_apps/company-leave-system',
        'started_at': date(2025, 7, 1),
        'uat_date': date(2025, 9, 1),
        'target_launch_date': date(2025, 10, 15),
        'notes': 'Core functionality complete, needs UAT testing',
        'functions': [
            {'name': 'Apply for Leave', 'code': 'apply_leave', 'status': 'uat', 'priority': 'critical', 'is_ui': True, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'View Leave Balance', 'code': 'view_balance', 'status': 'uat', 'priority': 'critical', 'is_ui': True, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'Approve Leave Requests', 'code': 'approve_leave', 'status': 'uat', 'priority': 'critical', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': True},
            {'name': 'Leave Calendar View', 'code': 'calendar_view', 'status': 'completed', 'priority': 'high', 'is_ui': True, 'is_api': False, 'has_tests': False, 'has_documentation': True},
            {'name': 'Annual Leave Carryover', 'code': 'carryover', 'status': 'developing', 'priority': 'medium', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
            {'name': 'Public Holiday Management', 'code': 'public_holidays', 'status': 'completed', 'priority': 'medium', 'is_ui': True, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'Leave Reports', 'code': 'reports', 'status': 'developing', 'priority': 'medium', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
        ]
    },
    {
        'app_code': 'stripe',
        'app_name': 'Stripe Dashboard',
        'status': 'uat',
        'priority': 'critical',
        'version': '2.1.0',
        'port': 8081,
        'repository_url': 'https://gitlab.kryedu.org/company_apps/stripe-dashboard',
        'started_at': date(2025, 6, 1),
        'uat_date': date(2025, 9, 25),
        'target_launch_date': date(2025, 10, 31),
        'notes': 'Payout reconciliation fixed, month-to-month balance continuity implemented',
        'functions': [
            {'name': 'Payment Tracking', 'code': 'payment_tracking', 'status': 'production', 'priority': 'critical', 'is_ui': True, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'Payout Reconciliation', 'code': 'payout_reconciliation', 'status': 'uat', 'priority': 'critical', 'is_ui': True, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'Monthly Statements', 'code': 'monthly_statements', 'status': 'uat', 'priority': 'critical', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': True},
            {'name': 'Multi-Company Support', 'code': 'multi_company', 'status': 'uat', 'priority': 'high', 'is_ui': True, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'Balance Continuity Tracking', 'code': 'balance_continuity', 'status': 'uat', 'priority': 'high', 'is_ui': True, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'CSV Export', 'code': 'csv_export', 'status': 'production', 'priority': 'medium', 'is_ui': True, 'is_api': False, 'has_tests': False, 'has_documentation': True},
            {'name': 'Invoice Management', 'code': 'invoice_mgmt', 'status': 'developing', 'priority': 'medium', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
        ]
    },
    {
        'app_code': 'asset_management',
        'app_name': 'Asset Management System',
        'status': 'prototype',
        'priority': 'medium',
        'version': '0.5.0',
        'port': 8003,
        'repository_url': '',
        'started_at': date(2025, 8, 15),
        'prototype_date': date(2025, 9, 10),
        'target_launch_date': date(2025, 12, 1),
        'notes': 'Basic prototype complete, needs more features',
        'functions': [
            {'name': 'Asset Registration', 'code': 'asset_registration', 'status': 'completed', 'priority': 'critical', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': True},
            {'name': 'Asset Movement Tracking', 'code': 'movement_tracking', 'status': 'prototype', 'priority': 'high', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
            {'name': 'QR Code Generation', 'code': 'qr_code', 'status': 'completed', 'priority': 'high', 'is_ui': True, 'is_api': False, 'has_tests': False, 'has_documentation': False},
            {'name': 'Asset Assignment', 'code': 'asset_assignment', 'status': 'developing', 'priority': 'high', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
            {'name': 'Maintenance Scheduling', 'code': 'maintenance', 'status': 'planned', 'priority': 'medium', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
            {'name': 'Depreciation Tracking', 'code': 'depreciation', 'status': 'planned', 'priority': 'low', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
        ]
    },
    {
        'app_code': 'crm',
        'app_name': 'CRM System',
        'status': 'prototype',
        'priority': 'high',
        'version': '0.6.0',
        'port': 8004,
        'repository_url': '',
        'started_at': date(2025, 7, 15),
        'prototype_date': date(2025, 9, 1),
        'target_launch_date': date(2025, 11, 15),
        'notes': 'Customer management prototype ready, needs integration features',
        'functions': [
            {'name': 'Customer Database', 'code': 'customer_db', 'status': 'completed', 'priority': 'critical', 'is_ui': True, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'Contact Management', 'code': 'contact_mgmt', 'status': 'completed', 'priority': 'critical', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': True},
            {'name': 'Lead Tracking', 'code': 'lead_tracking', 'status': 'developing', 'priority': 'high', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
            {'name': 'Sales Pipeline', 'code': 'sales_pipeline', 'status': 'developing', 'priority': 'high', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
            {'name': 'Email Integration', 'code': 'email_integration', 'status': 'planned', 'priority': 'medium', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
            {'name': 'Customer Reports', 'code': 'reports', 'status': 'developing', 'priority': 'medium', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
        ]
    },
    {
        'app_code': 'quotations',
        'app_name': 'Cost Quotation System',
        'status': 'developing',
        'priority': 'medium',
        'version': '0.3.0',
        'port': 8005,
        'repository_url': '',
        'started_at': date(2025, 9, 1),
        'target_launch_date': date(2025, 12, 15),
        'notes': 'Early development stage, basic structure in place',
        'functions': [
            {'name': 'Create Quotation', 'code': 'create_quotation', 'status': 'developing', 'priority': 'critical', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
            {'name': 'Product Catalog', 'code': 'product_catalog', 'status': 'developing', 'priority': 'high', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
            {'name': 'Price Calculation', 'code': 'price_calculation', 'status': 'developing', 'priority': 'critical', 'is_ui': False, 'is_api': True, 'has_tests': False, 'has_documentation': False},
            {'name': 'PDF Generation', 'code': 'pdf_generation', 'status': 'planned', 'priority': 'high', 'is_ui': False, 'is_api': True, 'has_tests': False, 'has_documentation': False},
            {'name': 'Quote Approval Workflow', 'code': 'approval_workflow', 'status': 'planned', 'priority': 'medium', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
            {'name': 'Customer Portal', 'code': 'customer_portal', 'status': 'planned', 'priority': 'low', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': False},
        ]
    },
    {
        'app_code': 'attendance',
        'app_name': 'Attendance System',
        'status': 'softlaunch',
        'priority': 'high',
        'version': '1.0.0',
        'port': 8007,
        'repository_url': 'https://gitlab.kryedu.org/company_apps/attendance-system',
        'started_at': date(2025, 10, 18),
        'softlaunch_date': date(2025, 10, 18),
        'target_launch_date': date(2025, 11, 1),
        'notes': 'Complete WiFi-based attendance system with desktop client. Backend API ready, desktop client functional, deployed to GitLab',
        'functions': [
            {'name': 'WiFi Auto Clock-In', 'code': 'wifi_clock_in', 'status': 'production', 'priority': 'critical', 'is_ui': False, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'WiFi Auto Clock-Out', 'code': 'wifi_clock_out', 'status': 'production', 'priority': 'critical', 'is_ui': False, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'Manual Clock-In/Out', 'code': 'manual_clock', 'status': 'production', 'priority': 'high', 'is_ui': True, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'Desktop System Tray App', 'code': 'desktop_client', 'status': 'softlaunch', 'priority': 'critical', 'is_ui': True, 'is_api': False, 'has_tests': False, 'has_documentation': True},
            {'name': 'Daily Attendance Reports', 'code': 'daily_reports', 'status': 'softlaunch', 'priority': 'high', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': True},
            {'name': 'Monthly Attendance Reports', 'code': 'monthly_reports', 'status': 'softlaunch', 'priority': 'high', 'is_ui': True, 'is_api': True, 'has_tests': False, 'has_documentation': True},
            {'name': 'Attendance Adjustments', 'code': 'adjustments', 'status': 'completed', 'priority': 'medium', 'is_ui': True, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'Public Holiday Management', 'code': 'holidays', 'status': 'production', 'priority': 'medium', 'is_ui': True, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'Work Schedule Config', 'code': 'work_schedule', 'status': 'production', 'priority': 'high', 'is_ui': True, 'is_api': True, 'has_tests': True, 'has_documentation': True},
            {'name': 'Desktop Notifications', 'code': 'notifications', 'status': 'softlaunch', 'priority': 'medium', 'is_ui': True, 'is_api': False, 'has_tests': False, 'has_documentation': True},
            {'name': 'Offline Queue Handling', 'code': 'offline_queue', 'status': 'completed', 'priority': 'medium', 'is_ui': False, 'is_api': False, 'has_tests': False, 'has_documentation': True},
            {'name': 'Web Dashboard', 'code': 'web_dashboard', 'status': 'developing', 'priority': 'medium', 'is_ui': True, 'is_api': False, 'has_tests': False, 'has_documentation': False},
        ]
    },
]

def initialize_apps():
    """Initialize all application status data."""
    print("Initializing App Status Data...")
    print("=" * 60)

    for app_data in APPS_DATA:
        # Extract functions data
        functions_data = app_data.pop('functions', [])

        # Create or update app
        app, created = AppStatus.objects.update_or_create(
            app_code=app_data['app_code'],
            defaults={**app_data, 'owner': admin}
        )

        if created:
            print(f"\n✓ Created: {app.app_name}")
        else:
            print(f"\n↻ Updated: {app.app_name}")

        # Create functions
        for func_data in functions_data:
            function, func_created = AppFunction.objects.update_or_create(
                app=app,
                function_code=func_data['code'],
                defaults={
                    'function_name': func_data['name'],
                    'status': func_data['status'],
                    'priority': func_data['priority'],
                    'is_ui': func_data['is_ui'],
                    'is_api': func_data['is_api'],
                    'has_tests': func_data['has_tests'],
                    'has_documentation': func_data['has_documentation'],
                    'assigned_to': admin,
                }
            )

            if func_created:
                print(f"  + {function.function_name} [{function.status}]")

        # Update completion percentage
        app.update_completion()
        print(f"  Completion: {app.completion_percentage}% ({app.functions_complete}/{app.functions_total} functions)")

    print("\n" + "=" * 60)
    print("✓ Initialization Complete!")
    print("\nSummary:")
    print(f"  Total Apps: {AppStatus.objects.count()}")
    print(f"  Total Functions: {AppFunction.objects.count()}")
    print(f"  In Production: {AppStatus.objects.filter(status='production').count()}")
    print(f"  In Soft Launch: {AppStatus.objects.filter(status='softlaunch').count()}")
    print(f"  In UAT: {AppStatus.objects.filter(status='uat').count()}")
    print(f"  In Prototype: {AppStatus.objects.filter(status='prototype').count()}")
    print(f"  Developing: {AppStatus.objects.filter(status='developing').count()}")
    print("\nApps by Status:")
    for status_code, status_name in [('softlaunch', 'Soft Launch'), ('uat', 'UAT'), ('prototype', 'Prototype'), ('developing', 'Developing')]:
        apps = AppStatus.objects.filter(status=status_code)
        if apps.exists():
            print(f"  {status_name}:")
            for app in apps:
                print(f"    - {app.app_name} ({app.completion_percentage}%)")
    print("\nAccess the dashboard at: http://localhost:8000/admin-panel/app-status/")

if __name__ == '__main__':
    initialize_apps()
