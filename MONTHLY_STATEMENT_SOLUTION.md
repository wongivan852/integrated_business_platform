# Monthly Statement Solution - Addressing 3 Key Challenges

**Date**: 2025-12-01  
**Status**: Solution Design

## 🎯 The 3 Challenges Identified

### Challenge 1: Opening and Closing Balance Not Consistent
**Problem**:
- No opening balance tracked
- Closing balance = Opening + Net (but opening is unknown)
- Each month starts fresh without carry-forward
- Running balance breaks across months

**Current State**:
```
July 2025:
  Revenue: $2,456.14
  Fees: $96.01
  Payouts: $-2,729.30
  Net: $-369.17
  
  But what was the OPENING balance? Unknown!
  So CLOSING balance cannot be calculated correctly.
```

### Challenge 2: Payout Cannot Be Fully Integrated
**Problem**:
- Payouts are negative amounts (money leaving Stripe to bank)
- Payouts don't match monthly accumulated balance
- Timing issue: Revenue earned in Month A, payout received in Month B
- Payout for October might appear in November transactions

**Example**:
```
October 2025:
  Customer payments: $1,000 (revenue)
  Fees: $50
  Net available: $950
  
But payout of $950 might be dated November 1st!
Where should it appear in monthly statement?
```

### Challenge 3: Month-End Transaction Cannot Be Clearly Located
**Problem**:
- Last transaction date varies (not always on 31st)
- Transactions timestamped throughout the day
- Payouts might be in next month but relate to current month
- No clear cut-off for "end of month"
- Balance at month-end is ambiguous

**Example**:
```
July 31, 2025:
  - Last payment: July 28, 09:05
  - Payout 1: July 29, 00:11 ← Is this July or August?
  - Payout 2: July 31, 00:11 ← Belongs to July
  - August 1 payment: 08:00 ← Clearly August
  
  Where do we draw the line?
```

## ✅ Comprehensive Solution

### Phase 1: Data Model Enhancement

#### New Model: MonthlyStatement

```python
class MonthlyStatement(models.Model):
    """
    Stores monthly statement data with proper balance tracking
    """
    account = models.ForeignKey(StripeAccount, on_delete=models.CASCADE)
    year = models.IntegerField()
    month = models.IntegerField()  # 1-12
    
    # Balance tracking
    opening_balance = models.IntegerField(default=0)  # in cents
    closing_balance = models.IntegerField(default=0)  # in cents
    
    # Revenue (before fees)
    gross_revenue = models.IntegerField(default=0)  # payments + charges
    refunds = models.IntegerField(default=0)  # refunds (negative)
    net_revenue = models.IntegerField(default=0)  # gross_revenue + refunds
    
    # Fees
    processing_fees = models.IntegerField(default=0)
    
    # Activity balance (revenue - fees)
    activity_balance = models.IntegerField(default=0)  # net_revenue - fees
    
    # Payouts
    payouts_in_month = models.IntegerField(default=0)  # payouts dated in this month
    payouts_for_month = models.IntegerField(default=0)  # payouts for this month's revenue
    
    # Balance calculation
    # closing = opening + net_revenue - fees - payouts
    calculated_balance = models.IntegerField(default=0)
    
    # Reconciliation
    is_reconciled = models.BooleanField(default=False)
    reconciliation_notes = models.TextField(blank=True)
    
    # Timestamps
    generated_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['account', 'year', 'month']
        ordering = ['-year', '-month']
```

### Phase 2: Balance Tracking Strategy

#### Strategy: Rolling Balance Method

```python
def calculate_monthly_statement(account, year, month):
    """
    Calculate monthly statement with proper balance tracking
    """
    # Step 1: Get previous month's closing balance
    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    
    prev_statement = MonthlyStatement.objects.filter(
        account=account,
        year=prev_year,
        month=prev_month
    ).first()
    
    opening_balance = prev_statement.closing_balance if prev_statement else 0
    
    # Step 2: Get all transactions for this month
    start_date = datetime(year, month, 1, 0, 0, 0)
    end_date = (start_date + relativedelta(months=1)) - timedelta(seconds=1)
    
    transactions = Transaction.objects.filter(
        account=account,
        stripe_created__gte=start_date,
        stripe_created__lte=end_date
    ).exclude(type='payout')  # Handle payouts separately
    
    # Step 3: Calculate revenue and fees
    revenue_trans = transactions.filter(type__in=['payment', 'charge'])
    refund_trans = transactions.filter(type='refund')
    
    gross_revenue = revenue_trans.aggregate(Sum('amount'))['amount__sum'] or 0
    refunds = refund_trans.aggregate(Sum('amount'))['amount__sum'] or 0
    processing_fees = transactions.aggregate(Sum('fee'))['fee__sum'] or 0
    
    net_revenue = gross_revenue + refunds  # refunds are negative
    activity_balance = net_revenue - processing_fees
    
    # Step 4: Handle payouts intelligently
    # Method A: Payouts dated within the month
    payouts_in_month = Transaction.objects.filter(
        account=account,
        type='payout',
        stripe_created__gte=start_date,
        stripe_created__lte=end_date
    ).aggregate(Sum('amount'))['amount__sum'] or 0
    
    # Method B: Match payouts to accumulated balance
    # (More complex - need to track which payout relates to which period)
    
    # Step 5: Calculate closing balance
    closing_balance = opening_balance + activity_balance + payouts_in_month
    
    # Step 6: Save statement
    statement, created = MonthlyStatement.objects.update_or_create(
        account=account,
        year=year,
        month=month,
        defaults={
            'opening_balance': opening_balance,
            'gross_revenue': gross_revenue,
            'refunds': refunds,
            'net_revenue': net_revenue,
            'processing_fees': processing_fees,
            'activity_balance': activity_balance,
            'payouts_in_month': payouts_in_month,
            'closing_balance': closing_balance,
            'calculated_balance': closing_balance,
        }
    )
    
    return statement
```

### Phase 3: Payout Reconciliation

#### Method: Payout Matching Logic

```python
def reconcile_payouts(account, year, month):
    """
    Match payouts to the month they represent
    """
    # Get the statement
    statement = MonthlyStatement.objects.get(account=account, year=year, month=month)
    
    # Strategy 1: Simple date-based
    # Include any payout dated within the month
    
    # Strategy 2: Balance-based (more accurate)
    # Track cumulative balance and match payouts to it
    
    # Get all payouts in a window (current month + next 7 days)
    start_date = datetime(year, month, 1)
    end_date = start_date + relativedelta(months=1) + timedelta(days=7)
    
    payouts = Transaction.objects.filter(
        account=account,
        type='payout',
        stripe_created__gte=start_date,
        stripe_created__lt=end_date
    ).order_by('stripe_created')
    
    # Match payouts to accumulated balance
    accumulated_balance = statement.activity_balance
    payouts_for_month = 0
    
    for payout in payouts:
        payout_amount = abs(payout.amount)  # Convert to positive
        
        if payouts_for_month + payout_amount <= accumulated_balance:
            payouts_for_month += payout_amount
        else:
            # This payout belongs to next month
            break
    
    statement.payouts_for_month = -payouts_for_month  # Store as negative
    statement.save()
    
    return statement
```

### Phase 4: Month-End Definition

#### Clear Cut-Off Rules

```python
def get_month_boundaries(year, month):
    """
    Get clear start and end boundaries for a month
    """
    # Start: First second of the month
    start_date = datetime(year, month, 1, 0, 0, 0, tzinfo=timezone.utc)
    
    # End: Last second of the month
    if month == 12:
        end_date = datetime(year + 1, 1, 1, 0, 0, 0, tzinfo=timezone.utc) - timedelta(seconds=1)
    else:
        end_date = datetime(year, month + 1, 1, 0, 0, 0, tzinfo=timezone.utc) - timedelta(seconds=1)
    
    return start_date, end_date

def get_month_transactions(account, year, month, include_payout_window=False):
    """
    Get all transactions for a month with clear boundaries
    """
    start_date, end_date = get_month_boundaries(year, month)
    
    # Base query: All transactions within month boundaries
    transactions = Transaction.objects.filter(
        account=account,
        stripe_created__gte=start_date,
        stripe_created__lte=end_date
    )
    
    if include_payout_window:
        # Extended window for payout matching
        # Include payouts up to 7 days into next month
        extended_end = end_date + timedelta(days=7)
        
        payouts = Transaction.objects.filter(
            account=account,
            type='payout',
            stripe_created__gt=end_date,
            stripe_created__lte=extended_end
        )
        
        return transactions, payouts
    
    return transactions
```

## 📊 Implementation Plan

### Step 1: Create MonthlyStatement Model (Day 1)
- [ ] Add model to `stripe_integration/models.py`
- [ ] Create migration
- [ ] Run migration

### Step 2: Create Balance Calculation Service (Day 1-2)
- [ ] `MonthlyStatementService` class
- [ ] `calculate_monthly_statement()` method
- [ ] `reconcile_payouts()` method
- [ ] `carry_forward_balance()` method

### Step 3: Create Statement Generator (Day 2-3)
- [ ] Generate HTML statement
- [ ] Match PDF sample format
- [ ] Include all required fields:
  - Opening balance
  - Revenue breakdown
  - Fees
  - Payouts (with reconciliation)
  - Closing balance
  - Transaction details

### Step 4: Create Views & Templates (Day 3)
- [ ] Monthly statement view
- [ ] Statement list view
- [ ] Generate statement button
- [ ] Export PDF functionality
- [ ] Export CSV functionality

### Step 5: Initialize Historical Statements (Day 4)
- [ ] Set initial opening balance (manually or from external source)
- [ ] Generate statements for all past months
- [ ] Verify balance consistency
- [ ] Reconcile all payouts

## 🎯 Expected Results

### Before (Current Issues)
```
October 2025:
  Revenue: $1,110.45
  Fees: $60.07
  Net: $1,050.38
  
  Opening Balance: ??? (Unknown)
  Closing Balance: ??? (Cannot calculate)
  Payouts: ??? (Mixed with revenue)
```

### After (With Solution)
```
October 2025:
  Opening Balance: $999.55  ← Carried from September
  
  Revenue Activity:
    Gross Revenue: $1,110.45
    Fees: -$60.07
    Net Activity: $1,050.38
    
  Payouts:
    In Month: -$1,682.55  ← Actual payouts dated in October
    
  Closing Balance: $367.38  ← Calculated: 999.55 + 1,050.38 - 1,682.55
  
  ✅ Balances reconciled
  ✅ Payouts properly tracked
  ✅ Ready for next month (closing → opening)
```

## ✅ Next Steps

1. **Review this solution design**
2. **Confirm the approach addresses all 3 challenges**
3. **Set initial opening balance** (What was the Stripe balance on the first day of your data?)
4. **Implement MonthlyStatement model**
5. **Create statement generator**
6. **Generate historical statements**
7. **Test with your data**

---

**Key Question**: What was the **opening Stripe balance** for the earliest month in your data? This is needed to bootstrap the balance tracking system.

Once I have that, I can implement this solution and generate accurate monthly statements!
