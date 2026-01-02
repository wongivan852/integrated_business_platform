"""
URL Configuration for Stripe Integration App
"""
from django.urls import path
from . import views

app_name = 'stripe'

urlpatterns = [
    # Main dashboard
    path('', views.dashboard, name='dashboard'),

    # Transactions
    path('transactions/', views.transactions_list, name='transactions_list'),
    path('transactions/<int:transaction_id>/', views.transaction_detail, name='transaction_detail'),

    # Accounts
    path('accounts/', views.accounts_list, name='accounts_list'),
    path('accounts/<int:account_id>/', views.account_detail, name='account_detail'),

    # Analytics
    path('analytics/', views.analytics, name='analytics'),

    # CSV Import
    path('import/', views.csv_import, name='csv_import'),

    # Monthly Statements
    path('statements/', views.monthly_statements, name='monthly_statements'),
    path('statements/<int:statement_id>/', views.monthly_statement_detail, name='monthly_statement_detail'),
    path('statements/generate/', views.generate_monthly_statement, name='generate_monthly_statement'),
    path('statements/generate-all/', views.generate_all_statements, name='generate_all_statements'),

    # API Endpoints
    path('api/transactions/', views.api_transactions, name='api_transactions'),
    path('api/accounts/', views.api_accounts, name='api_accounts'),
    path('api/stats/', views.api_dashboard_stats, name='api_stats'),
]
