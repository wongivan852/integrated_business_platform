# Stripe Balance Summary Terminology - Critical Clarification

## Problem: Misleading Field Names

The Stripe Balance Summary CSV uses **confusing terminology** that doesn't match accounting standards:

### What Stripe Calls "Gross Revenue"

**Stripe's Label**: `activity_gross` - "Account activity before fees"  
**What it Actually Contains**: Charges MINUS Refunds (before fees)

```
Stripe "activity_gross" = Charges + Refunds  (refunds are negative)
                        = 15,199.60 + (-525.19)
                        = 14,674.41 HKD
```

### Proper Accounting Terms

| Stripe Term | Proper Accounting Term | Formula |
|------------|----------------------|---------|
| `activity_gross` | **Net Sales** or **Net Revenue (before fees)** | Charges + Refunds |
| `activity_fee` | **Processing Fees** | Sum of all fees |
| `activity` | **Net Revenue (after fees)** | Net Sales - Fees |

## Database Values (November 2025 CGGE)

```
Charges (17 transactions):     15,199.60 HKD
Refunds (1 transaction):         -525.19 HKD
────────────────────────────────────────────
Net Sales ("Gross" per Stripe): 14,674.41 HKD  ← This is what Stripe calls "Gross"!
Less: Processing Fees:            -799.46 HKD
────────────────────────────────────────────
Net Revenue:                    13,874.95 HKD
```

## The Fix Required

### Current Code (WRONG):
```python
gross_revenue = revenue_trans.aggregate(Sum('amount'))['amount__sum'] or 0  # Only charges
refunds = refund_trans.aggregate(Sum('amount'))['amount__sum'] or 0
processing_fees = all_transactions.exclude(type='payout').aggregate(Sum('fee'))['fee__sum'] or 0

net_revenue = gross_revenue + refunds  # refunds are negative
```

**Result**: 
- `gross_revenue` = 15,199.60 (charges only) ❌
- `net_revenue` = 14,674.41 (charges + refunds) ✅
- `processing_fees` = 799.46 ✅

### Corrected Code (RIGHT):
```python
# Calculate charges and refunds separately for transparency
charges = revenue_trans.aggregate(Sum('amount'))['amount__sum'] or 0
refunds = refund_trans.aggregate(Sum('amount'))['amount__sum'] or 0

# Stripe's "Gross Revenue" is actually Net Sales (includes refunds)
gross_revenue = charges + refunds  # This matches Stripe's activity_gross

processing_fees = all_transactions.exclude(type='payout').aggregate(Sum('fee'))['fee__sum'] or 0

net_revenue = gross_revenue - processing_fees
```

**Result**:
- `charges` = 15,199.60 (for reference)
- `refunds` = -525.19 (for reference)
- `gross_revenue` = 14,674.41 (charges + refunds) ✅ Matches Stripe
- `processing_fees` = 799.46 ✅
- `net_revenue` = 13,874.95 ✅

## Database Schema Implications

### Option 1: Rename Fields (Preferred)
```python
class MonthlyStatement(models.Model):
    # More accurate field names
    charges = models.IntegerField()           # Positive charges only
    refunds = models.IntegerField()           # Negative refunds
    net_sales = models.IntegerField()         # charges + refunds (what Stripe calls "gross")
    processing_fees = models.IntegerField()   # All fees
    net_revenue = models.IntegerField()       # net_sales - fees
```

### Option 2: Keep Names, Document Properly (Current)
```python
class MonthlyStatement(models.Model):
    # Note: "gross_revenue" follows Stripe terminology (includes refunds)
    gross_revenue = models.IntegerField(
        help_text="Account activity before fees (charges + refunds, matches Stripe's 'activity_gross')"
    )
    refunds = models.IntegerField(
        help_text="Refund transactions (negative values)"
    )
    net_revenue = models.IntegerField(
        help_text="Net revenue after fees (gross_revenue - processing_fees)"
    )
    processing_fees = models.IntegerField(
        help_text="Total processing fees (positive value)"
    )
```

## Recommendation

**Use Option 2** to maintain backward compatibility, but:
1. Fix the calculation logic to match Stripe
2. Update documentation and help text
3. Display breakdown clearly in UI:
   ```
   Charges:              $15,199.60
   Less: Refunds:        $  -525.19
   ─────────────────────────────────
   Gross Revenue:        $14,674.41  (Stripe's "activity_gross")
   Less: Fees:           $  -799.46
   ─────────────────────────────────
   Net Revenue:          $13,874.95
   ```

## Why This Matters

### Financial Reconciliation
- Accountants expect "Gross Revenue" to be before refunds
- Stripe's "Gross Revenue" is actually Net Sales
- This causes confusion in financial reporting

### Dashboard Display
Current dashboard might show:
- ❌ "Gross Revenue: $15,199.60" (doesn't match Stripe)

Should show:
- ✅ "Gross Revenue: $14,674.41" (matches Stripe Balance Summary)
- ℹ️ Or better: "Net Sales: $14,674.41 (from $15,199.60 charges - $525.19 refunds)"

## Validation

Using November 2025 CGGE data:

| Metric | Database | Stripe CSV | Match |
|--------|----------|------------|-------|
| Charges | 15,199.60 | N/A | N/A |
| Refunds | -525.19 | N/A | N/A |
| **Gross Revenue (Net Sales)** | **14,674.41** | **14,674.41** | ✅ |
| Processing Fees | 799.46 | 799.46 | ✅ |
| Net Revenue | 13,874.95 | 13,874.95 | ✅ |
| Payouts | 8,356.57 | 8,356.57 | ✅ |
| Opening Balance | 367.38 | 367.38 | ✅ |
| Closing Balance | 5,885.76 | 5,885.76 | ✅ |

## Conclusion

The issue is **not a bug**, but a **terminology mismatch**:
- Stripe uses "Gross Revenue" to mean "Net Sales (before fees)"
- Standard accounting uses "Gross Revenue" to mean "Total Charges (before refunds)"

The fix is to calculate `gross_revenue = charges + refunds` to match Stripe's definition.
