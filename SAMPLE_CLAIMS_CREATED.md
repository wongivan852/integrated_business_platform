# Sample Expense Claims Created

**Date**: October 30, 2025
**Command**: `python manage.py create_sample_claims`
**Status**: ✅ COMPLETE

---

## Sample Claims Created

### Claim 1: IAICC AI Conference 2024 ⭐
**Claim Number**: CGGE2025100001
**Claimant**: Ivan Wong (ivan.wong@krystal.institute)
**Company**: Krystal Institute Limited (KI)
**Event**: IAICC AI Conference 2024
**Period**: October 23-29, 2025
**Status**: Draft
**Total Amount**: 5,091.80 HKD

#### Expense Items:

**1. Taxi from SZ Bay Port to CUHKSRI**
- **Category**: Transportation (交通)
- **Description**: Taxi from SZ Bay Port to CUHKSRI
- **Chinese**: 从深圳湾口岸到中大(深圳)的士费
- **Amount**: 85.00 CNY = 91.80 HKD (rate: 1.08)
- **Location**: Shenzhen to CUHK
- **Participants**: Total 2 persons included Jeff and Ivan
- **Receipt**: Yes
- **Notes**: Transportation to AI conference venue

**2. Keynote Speaker Honorarium**
- **Category**: Keynote Speech (主題演講)
- **Description**: Keynote speaker honorarium
- **Chinese**: 主题演讲嘉宾费
- **Amount**: 5,000.00 HKD
- **Receipt**: Yes
- **Notes**: Payment for keynote speech at IAICC conference

---

### Claim 2: Business Development Trip
**Claim Number**: CGGE2025100002
**Claimant**: Jacky Chan (jacky.chan@krystal.institute)
**Company**: Krystal Technology Limited (KT)
**Event**: Business Development Trip
**Period**: October 16-20, 2025
**Status**: Draft
**Total Amount**: 350.00 HKD

#### Expense Items:

**1. Business Lunch with Client**
- **Category**: Business Negotiation (業務商談)
- **Description**: Business lunch with client
- **Chinese**: 与客户商务午餐
- **Amount**: 350.00 HKD
- **Receipt**: Yes
- **Notes**: Client relationship building

---

## Management Command

### Create Sample Claims
```bash
# Create sample claims
python manage.py create_sample_claims

# Clear existing sample claims and create new ones
python manage.py create_sample_claims --clear
```

### Command Features:
- ✅ Creates 2 sample expense claims
- ✅ Uses existing users (Ivan Wong, Jacky Chan)
- ✅ Creates exchange rates if needed
- ✅ Calculates HKD amounts automatically
- ✅ Includes bilingual descriptions
- ✅ Sets up proper claim numbers
- ✅ Links to correct companies and categories
- ✅ Supports `--clear` flag to remove old samples

---

## Data Source

These sample claims are adapted from the **FastAPI version** found in:
```
/company_expense_claim_system/app/utils/seed_data.py
```

Specifically the `create_sample_expense_claims()` function lines 443-552.

---

## Technical Details

### Models Used:
- `ExpenseClaim` - Main claim model
- `ExpenseItem` - Individual expense line items
- `Company` - Business entities (KI, KT, CGGE, 数谱(深圳))
- `ExpenseCategory` - 9 expense categories
- `Currency` - Multi-currency support (HKD, CNY, etc.)
- `ExchangeRate` - Currency conversion rates
- `CompanyUser` - Claimant users

### Exchange Rates Created:
- **HKD**: 1.00 (base currency)
- **CNY**: 1.08 (1 CNY = 1.08 HKD)

### Calculation Example:
```
Taxi expense:
- Original amount: 85.00 CNY
- Exchange rate: 1.08
- Converted amount: 85.00 × 1.08 = 91.80 HKD

Total claim amount:
- Item 1: 91.80 HKD
- Item 2: 5,000.00 HKD
- Total: 5,091.80 HKD
```

---

## Verification

### Check Claims in Database:
```bash
python manage.py shell -c "
from expense_claims.models import ExpenseClaim
claims = ExpenseClaim.objects.all()
for claim in claims:
    print(f'{claim.claim_number}: {claim.event_name} - {claim.total_amount_hkd} HKD')
"
```

### Access via Web Interface:
```
http://localhost:8003/expense-claims/
```

Login with any authorized user to view the claims.

---

## User Data Policy Compliance

### ✅ Ivan Wong's Claim Protected
As per **USER_DATA_POLICY.md**:
- Ivan Wong (ivan.wong@krystal.institute) is an **AUTHORIZED USER**
- His claim (CGGE2025100001) is part of the **AUTHORIZED DATASET**
- This data will be **PRESERVED** and not deleted during cleanup
- Can be used for training, testing, and demonstration

### Sample Data vs Production Data
- **Sample Claims**: CGGE2025100001, CGGE2025100002
- **Status**: Demo/Test data
- **Purpose**: System testing and demonstration
- **Clearable**: Yes, using `--clear` flag (except Ivan Wong's data per policy)

---

## Next Steps

### For Testing:
1. ✅ View claims at http://localhost:8003/expense-claims/
2. ✅ Test approval workflow
3. ✅ Test PDF generation
4. ✅ Test claim editing
5. ✅ Test deletion (draft status only)

### For Production:
1. Keep Ivan Wong's claim as reference dataset
2. Clear other sample claims if needed
3. Let users create real expense claims
4. Monitor and validate workflows

---

## Comparison with Original

| Aspect | FastAPI Version | Django Version | Status |
|--------|----------------|----------------|--------|
| **Number of Claims** | 2 | 2 | ✅ MATCH |
| **Claim 1: Event** | IAICC AI Conference | IAICC AI Conference 2024 | ✅ MATCH |
| **Claim 1: Company** | KIL | KI (Krystal Institute) | ✅ MATCH |
| **Claim 1: Items** | 2 (Taxi + Honorarium) | 2 (Taxi + Honorarium) | ✅ MATCH |
| **Claim 1: Taxi** | 85 RMB | 85 CNY = 91.80 HKD | ✅ MATCH |
| **Claim 1: Honorarium** | 5000 HKD | 5000 HKD | ✅ MATCH |
| **Claim 2: Event** | Business Trip | Business Development Trip | ✅ MATCH |
| **Claim 2: Company** | KTL | KT (Krystal Technology) | ✅ MATCH |
| **Claim 2: Items** | 1 (Lunch) | 1 (Lunch) | ✅ MATCH |
| **Claim 2: Amount** | 350 HKD | 350 HKD | ✅ MATCH |
| **Bilingual Support** | Yes | Yes | ✅ MATCH |
| **Exchange Rates** | 1.08 | 1.08 | ✅ MATCH |

---

## Summary

✅ **Sample claims successfully created** in Django version

The integrated business platform now has **2 sample expense claims** that match the original FastAPI version:

1. **IAICC Conference** - Ivan Wong - 5,091.80 HKD (2 items)
2. **Business Trip** - Jacky Chan - 350.00 HKD (1 item)

These claims demonstrate:
- ✅ Multi-company support
- ✅ Multi-currency handling
- ✅ Bilingual descriptions
- ✅ Exchange rate calculations
- ✅ Claim numbering system
- ✅ Line item structure
- ✅ Category assignments

The system is ready for testing with realistic sample data!

---

**Created By**: Django Management Command
**Command File**: `expense_claims/management/commands/create_sample_claims.py`
**Date**: October 30, 2025
**Status**: ✅ READY FOR TESTING
