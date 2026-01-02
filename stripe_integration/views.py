from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.db.models import Sum, Count, Q
from datetime import datetime, timedelta

from .models import StripeAccount, Transaction, StripeCustomer, StripeSubscription, MonthlyStatement
from .services import StripeService, CSVImportService, MonthlyStatementService


@login_required
def dashboard(request):
    """
    Main Stripe dashboard view showing overview and statistics
    """
    service = StripeService()
    stats = service.get_dashboard_stats()
    account_summary = service.get_account_summary()
    recent_transactions = service.get_all_transactions(limit=10)

    context = {
        'stats': stats,
        'account_summary': account_summary,
        'recent_transactions': recent_transactions,
        'page_title': 'Stripe Dashboard',
    }

    return render(request, 'stripe_integration/dashboard.html', context)


@login_required
def transactions_list(request):
    """
    View to list all transactions with filtering and pagination
    """
    # Get filter parameters
    account_id = request.GET.get('account')
    status = request.GET.get('status')
    trans_type = request.GET.get('type')
    search = request.GET.get('search')
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Base query
    transactions = Transaction.objects.all()

    # Apply filters
    if account_id:
        transactions = transactions.filter(account_id=account_id)

    if status:
        transactions = transactions.filter(status=status)

    if trans_type:
        transactions = transactions.filter(type=trans_type)

    if search:
        transactions = transactions.filter(
            Q(stripe_id__icontains=search) |
            Q(customer_email__icontains=search) |
            Q(description__icontains=search)
        )

    if start_date:
        try:
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            transactions = transactions.filter(stripe_created__gte=start_dt)
        except ValueError:
            pass

    if end_date:
        try:
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            transactions = transactions.filter(stripe_created__lte=end_dt)
        except ValueError:
            pass

    # Order by date (most recent first)
    transactions = transactions.order_by('-stripe_created')

    # Pagination
    paginator = Paginator(transactions, 50)  # Show 50 transactions per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get all accounts for filter dropdown
    accounts = StripeAccount.objects.filter(is_active=True)

    context = {
        'page_obj': page_obj,
        'accounts': accounts,
        'selected_account': account_id,
        'selected_status': status,
        'selected_type': trans_type,
        'search_query': search,
        'start_date': start_date,
        'end_date': end_date,
        'page_title': 'Transactions',
    }

    return render(request, 'stripe_integration/transactions_list.html', context)


@login_required
def transaction_detail(request, transaction_id):
    """
    View to show details of a single transaction
    """
    transaction = get_object_or_404(Transaction, id=transaction_id)

    context = {
        'transaction': transaction,
        'page_title': f'Transaction {transaction.stripe_id}',
    }

    return render(request, 'stripe_integration/transaction_detail.html', context)


@login_required
def accounts_list(request):
    """
    View to list all Stripe accounts
    """
    service = StripeService()
    account_summary = service.get_account_summary()

    context = {
        'account_summary': account_summary,
        'page_title': 'Stripe Accounts',
    }

    return render(request, 'stripe_integration/accounts_list.html', context)


@login_required
def account_detail(request, account_id):
    """
    View to show details of a single Stripe account
    """
    account = get_object_or_404(StripeAccount, id=account_id)
    service = StripeService(account_id=account_id)

    # Get recent transactions for this account
    transactions = service.get_account_transactions(account_id, limit=20)

    # Get statistics
    transaction_stats = Transaction.objects.filter(account=account).aggregate(
        total_count=Count('id'),
        total_amount=Sum('amount'),
        total_fees=Sum('fee')
    )

    # Get transaction breakdown by type
    type_breakdown = Transaction.objects.filter(account=account).values('type').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')

    context = {
        'account': account,
        'transactions': transactions,
        'transaction_stats': transaction_stats,
        'type_breakdown': type_breakdown,
        'page_title': f'Account: {account.name}',
    }

    return render(request, 'stripe_integration/account_detail.html', context)


@login_required
def analytics(request):
    """
    Analytics and reporting view
    """
    # Get date range from request or default to last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)

    if request.GET.get('start_date'):
        try:
            start_date = datetime.strptime(request.GET.get('start_date'), '%Y-%m-%d')
        except ValueError:
            pass

    if request.GET.get('end_date'):
        try:
            end_date = datetime.strptime(request.GET.get('end_date'), '%Y-%m-%d')
        except ValueError:
            pass

    service = StripeService()
    transactions = service.get_transactions_by_date_range(start_date, end_date)

    # Calculate statistics
    stats = transactions.aggregate(
        total_count=Count('id'),
        total_amount=Sum('amount'),
        total_fees=Sum('fee')
    )

    # Breakdown by type
    type_breakdown = transactions.values('type').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')

    # Breakdown by status
    status_breakdown = transactions.values('status').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('-total')

    # Daily totals for chart
    daily_totals = transactions.extra(
        select={'day': 'date(stripe_created)'}
    ).values('day').annotate(
        count=Count('id'),
        total=Sum('amount')
    ).order_by('day')

    context = {
        'start_date': start_date.strftime('%Y-%m-%d'),
        'end_date': end_date.strftime('%Y-%m-%d'),
        'stats': stats,
        'type_breakdown': type_breakdown,
        'status_breakdown': status_breakdown,
        'daily_totals': list(daily_totals),
        'page_title': 'Analytics',
    }

    return render(request, 'stripe_integration/analytics.html', context)


@login_required
def csv_import(request):
    """
    View to import transactions from CSV files
    Supports multiple file upload
    """
    if request.method == 'POST':
        account_id = request.POST.get('account_id')
        uploaded_files = request.FILES.getlist('csv_files')  # Support multiple files

        if not account_id:
            messages.error(request, 'Please select an account.')
            return redirect('stripe:csv_import')

        if not uploaded_files:
            messages.error(request, 'Please upload at least one CSV file.')
            return redirect('stripe:csv_import')

        account = get_object_or_404(StripeAccount, id=account_id)

        # Import statistics across all files
        total_imported = 0
        total_skipped = 0
        total_errors = []
        total_files = len(uploaded_files)
        
        import tempfile
        import os

        for uploaded_file in uploaded_files:
            # Validate file extension
            if not uploaded_file.name.endswith('.csv'):
                messages.warning(request, f"Skipped '{uploaded_file.name}' - not a CSV file.")
                continue

            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix='.csv', mode='wb') as tmp_file:
                for chunk in uploaded_file.chunks():
                    tmp_file.write(chunk)
                tmp_file_path = tmp_file.name

            try:
                # Import from CSV
                csv_service = CSVImportService()
                stats = csv_service.import_from_csv(tmp_file_path, account)

                # Aggregate statistics
                total_imported += stats['imported']
                total_skipped += stats['skipped']
                if stats['errors']:
                    total_errors.extend([f"{uploaded_file.name}: {err}" for err in stats['errors']])

                # Clean up temp file
                os.unlink(tmp_file_path)

            except Exception as e:
                messages.error(request, f"Error importing '{uploaded_file.name}': {str(e)}")
                if os.path.exists(tmp_file_path):
                    os.unlink(tmp_file_path)

        # Show consolidated results
        if total_imported > 0:
            if total_errors:
                messages.warning(
                    request,
                    f"Import completed: {total_imported} transactions imported from {total_files} file(s), "
                    f"{total_skipped} skipped, {len(total_errors)} errors occurred."
                )
                # Show first few errors
                for error in total_errors[:5]:
                    messages.error(request, error)
                if len(total_errors) > 5:
                    messages.info(request, f"... and {len(total_errors) - 5} more errors.")
            else:
                messages.success(
                    request,
                    f"Successfully imported {total_imported} transactions from {total_files} file(s), "
                    f"{total_skipped} skipped (duplicates)."
                )
        else:
            # Check if everything was skipped (all duplicates) vs parsing errors
            if total_skipped > 0:
                messages.info(
                    request,
                    f"All {total_skipped} transactions from {total_files} file(s) already exist in the database for account '{account.name}'. "
                    f"No duplicates were imported. This is normal if you've uploaded these files before."
                )
            else:
                messages.warning(
                    request,
                    f"No transactions were imported from {total_files} file(s). "
                    f"Check that your CSV files contain valid transaction data."
                )

        return redirect('stripe:csv_import')

    # GET request - show import form
    accounts = StripeAccount.objects.filter(is_active=True)
    csv_service = CSVImportService()
    available_files = csv_service.list_csv_files()

    context = {
        'accounts': accounts,
        'available_files': available_files,
        'page_title': 'Import CSV',
    }

    return render(request, 'stripe_integration/csv_import.html', context)


# API Views

@login_required
@require_http_methods(["GET"])
def api_transactions(request):
    """
    API endpoint to get transactions in JSON format
    """
    account_id = request.GET.get('account_id')
    limit = int(request.GET.get('limit', 50))
    offset = int(request.GET.get('offset', 0))

    service = StripeService()

    if account_id:
        transactions = service.get_account_transactions(int(account_id), limit, offset)
    else:
        transactions = service.get_all_transactions(limit, offset)

    data = [{
        'id': t.id,
        'stripe_id': t.stripe_id,
        'account_id': t.account_id,
        'account_name': t.account.name,
        'amount': t.amount_formatted,
        'fee': t.fee_formatted,
        'net_amount': t.net_amount_formatted,
        'currency': t.currency.upper(),
        'status': t.status,
        'type': t.type,
        'created_at': t.created_at.isoformat(),
        'stripe_created': t.stripe_created.isoformat(),
        'customer_email': t.customer_email,
        'description': t.description
    } for t in transactions]

    return JsonResponse({'transactions': data})


@login_required
@require_http_methods(["GET"])
def api_accounts(request):
    """
    API endpoint to get account information in JSON format
    """
    service = StripeService()
    summary = service.get_account_summary()

    data = [{
        'id': s['account'].id,
        'name': s['account'].name,
        'is_active': s['account'].is_active,
        'has_api_key': s['has_api_key'],
        'total_transactions': s['total_transactions'],
        'total_amount': float(s['total_amount']),
        'total_fees': float(s['total_fees']),
        'net_amount': float(s['net_amount']),
        'created_at': s['account'].created_at.isoformat()
    } for s in summary]

    return JsonResponse({'accounts': data})


@login_required
@require_http_methods(["GET"])
def api_dashboard_stats(request):
    """
    API endpoint to get dashboard statistics
    """
    service = StripeService()
    stats = service.get_dashboard_stats()

    return JsonResponse(stats)


@login_required
def monthly_statements(request):
    """
    View to list and generate monthly statements
    """
    account_id = request.GET.get('account')
    year = request.GET.get('year')
    month = request.GET.get('month')
    
    # Get all accounts
    accounts = StripeAccount.objects.filter(is_active=True)
    
    # If specific account selected
    selected_account = None
    statements = []
    
    if account_id:
        selected_account = get_object_or_404(StripeAccount, id=account_id)
        
        # Get all statements for this account
        statements = MonthlyStatement.objects.filter(
            account=selected_account
        ).order_by('-year', '-month')
    
    context = {
        'accounts': accounts,
        'selected_account': selected_account,
        'statements': statements,
        'page_title': 'Monthly Statements',
    }
    
    return render(request, 'stripe_integration/monthly_statements.html', context)


@login_required
def monthly_statement_detail(request, statement_id):
    """
    View to show detailed monthly statement with transactions
    """
    statement = get_object_or_404(MonthlyStatement, id=statement_id)
    service = MonthlyStatementService()
    
    # Get all transactions for this statement
    transactions = service.get_transactions_for_statement(statement)
    
    # Separate by type
    payments = transactions.filter(type__in=['payment', 'charge'])
    refunds = transactions.filter(type='refund')
    payouts = transactions.filter(type='payout')
    
    context = {
        'statement': statement,
        'transactions': transactions,
        'payments': payments,
        'refunds': refunds,
        'payouts': payouts,
        'page_title': f'Statement: {statement.account.name} - {statement.year}/{statement.month:02d}',
    }
    
    return render(request, 'stripe_integration/monthly_statement_detail.html', context)


@login_required
@require_http_methods(["POST"])
def generate_monthly_statement(request):
    """
    Generate or regenerate monthly statement for specific account and month
    """
    account_id = request.POST.get('account_id')
    year = request.POST.get('year')
    month = request.POST.get('month')
    
    if not all([account_id, year, month]):
        messages.error(request, 'Please provide account, year, and month.')
        return redirect('stripe:monthly_statements')
    
    try:
        account = get_object_or_404(StripeAccount, id=account_id)
        year = int(year)
        month = int(month)
        
        if month < 1 or month > 12:
            raise ValueError("Month must be between 1 and 12")
        
        # Generate statement
        service = MonthlyStatementService()
        statement = service.calculate_monthly_statement(account, year, month)
        
        messages.success(
            request,
            f"Successfully generated statement for {account.name} - {year}/{month:02d}"
        )
        
        return redirect('stripe:monthly_statement_detail', statement_id=statement.id)
        
    except ValueError as e:
        messages.error(request, f"Invalid input: {str(e)}")
        return redirect('stripe:monthly_statements')
    except Exception as e:
        messages.error(request, f"Error generating statement: {str(e)}")
        return redirect('stripe:monthly_statements')


@login_required
@require_http_methods(["POST"])
def generate_all_statements(request):
    """
    Generate statements for all months with transactions
    """
    account_id = request.POST.get('account_id')
    initial_balance = request.POST.get('initial_balance', '0')
    
    if not account_id:
        messages.error(request, 'Please select an account.')
        return redirect('stripe:monthly_statements')
    
    try:
        account = get_object_or_404(StripeAccount, id=account_id)
        initial_balance_cents = int(float(initial_balance) * 100) if initial_balance else 0
        
        # Generate all statements
        service = MonthlyStatementService()
        statements = service.generate_all_statements(
            account,
            initial_balance=initial_balance_cents
        )
        
        if statements:
            messages.success(
                request,
                f"Successfully generated {len(statements)} statements for {account.name}"
            )
        else:
            messages.warning(
                request,
                f"No transactions found for {account.name}"
            )
        
        return redirect('stripe:monthly_statements') + f'?account={account_id}'
        
    except Exception as e:
        messages.error(request, f"Error generating statements: {str(e)}")
        return redirect('stripe:monthly_statements')
