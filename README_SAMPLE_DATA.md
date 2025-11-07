# Sample Data Quick Reference

**Integrated Business Platform - Expense Claims System**

---

## 🚀 Quick Start

### View Sample Claims
```bash
# Access the expense claims system
http://localhost:8003/expense-claims/

# Login with any authorized user to view the claims
```

### Create Sample Claims
```bash
# Create 2 sample expense claims
python manage.py create_sample_claims

# Clear existing samples and create new ones
python manage.py create_sample_claims --clear
```

---

## 📋 Sample Claims Created

### 1. IAICC AI Conference 2024 ⭐
- **Claim Number**: CGGE2025100001
- **Claimant**: Ivan Wong (ivan.wong@krystal.institute)
- **Company**: Krystal Institute Limited (KI)
- **Total**: 5,091.80 HKD
- **Items**:
  - Taxi (Shenzhen): 85 CNY = 91.80 HKD
  - Keynote speaker honorarium: 5,000 HKD

### 2. Business Development Trip
- **Claim Number**: CGGE2025100002
- **Claimant**: Jacky Chan (jacky.chan@krystal.institute)
- **Company**: Krystal Technology Limited (KT)
- **Total**: 350.00 HKD
- **Items**:
  - Business lunch with client: 350 HKD

---

## 🛠️ Management Commands

### Setup Commands (Run Once)
```bash
# 1. Create 4 companies
python manage.py setup_krystal_companies

# 2. Create 9 expense categories
python manage.py setup_expense_categories

# 3. Create sample claims (optional)
python manage.py create_sample_claims
```

### Verification Commands
```bash
# Check companies
python manage.py shell -c "
from expense_claims.models import Company
for c in Company.objects.all():
    print(f'{c.code}: {c.name}')
"

# Check categories
python manage.py shell -c "
from expense_claims.models import ExpenseCategory
for cat in ExpenseCategory.objects.all():
    print(f'{cat.code}: {cat.name} ({cat.name_chinese})')
"

# Check sample claims
python manage.py shell -c "
from expense_claims.models import ExpenseClaim
for claim in ExpenseClaim.objects.all():
    print(f'{claim.claim_number}: {claim.event_name} - {claim.total_amount_hkd} HKD')
"

# Check currencies
python manage.py shell -c "
from expense_claims.models import Currency
for curr in Currency.objects.all():
    print(f'{curr.code}: {curr.name} ({curr.symbol})')
"
```

---

## 📊 Current System Status

### ✅ Foundational Data (Ready)
- **Companies**: 4 (KI, KT, CGGE, 数谱(深圳))
- **Categories**: 9 (with Chinese translations)
- **Currencies**: 6 (HKD, CNY, USD, EUR, GBP, JPY)
- **Users**: 17 (including Ivan Wong)

### ✅ Sample Data (Optional)
- **Expense Claims**: 2 sample claims
- **Expense Items**: 3 line items total
- **Status**: Draft (ready for testing workflows)

---

## 🔄 Sample Data Management

### When to Use Sample Claims
- ✅ Testing expense claim functionality
- ✅ Demonstrating approval workflows
- ✅ Training new users
- ✅ Testing PDF generation
- ✅ Validating multi-currency calculations

### When to Clear Sample Claims
- ⚠️ Before production deployment
- ⚠️ After testing is complete
- ⚠️ When creating fresh test scenarios

### How to Clear Sample Claims
```bash
# Option 1: Use the --clear flag
python manage.py create_sample_claims --clear

# Option 2: Manual deletion via Django shell
python manage.py shell -c "
from expense_claims.models import ExpenseClaim
ExpenseClaim.objects.filter(claim_number__in=['CGGE2025100001', 'CGGE2025100002']).delete()
print('Sample claims deleted')
"
```

⚠️ **Note**: Ivan Wong's data is protected per USER_DATA_POLICY.md. Exercise caution when clearing data.

---

## 📖 Documentation References

### Complete Documentation
- **SAMPLE_CLAIMS_CREATED.md** - Detailed sample claims documentation
- **DATA_IMPORT_SUMMARY.md** - All imported data summary
- **GITLAB_DATASET_ANALYSIS.md** - Source data analysis
- **USER_DATA_POLICY.md** - Data protection policy
- **EXPENSE_SYSTEM_VALIDATION.md** - System validation report

### Key Files
```
integrated_business_platform/
├── expense_claims/
│   ├── models.py                          # Data models
│   ├── management/commands/
│   │   ├── setup_krystal_companies.py     # Create companies
│   │   ├── setup_expense_categories.py    # Create categories
│   │   └── create_sample_claims.py        # Create sample claims ⭐
│   ├── views.py                           # Main views
│   └── urls.py                            # URL routing
├── templates/claims/                       # 9 claim templates
└── [Documentation files above]
```

---

## 🧪 Testing Workflows

### Test Expense Claim Creation
1. Login to http://localhost:8003/
2. Navigate to Expense Claims
3. Click "Create New Claim"
4. Fill in claim details
5. Add expense items
6. Submit for approval

### Test Approval Workflow
1. View sample claims
2. Test status transitions:
   - Draft → Submitted
   - Submitted → Under Review
   - Under Review → Approved
   - Approved → Paid

### Test Multi-Currency
1. Create claim with CNY expenses
2. Verify exchange rate calculation
3. Check HKD conversion
4. Validate total amounts

### Test PDF Generation
1. Open claim detail page
2. Click "Print" or "Generate PDF"
3. Verify claim data in PDF
4. Test with/without receipts options

---

## 💡 Tips

### Development
```bash
# Start development server
venv/bin/python manage.py runserver 0.0.0.0:8003

# Access admin panel
http://localhost:8003/admin/

# Access expense claims
http://localhost:8003/expense-claims/
```

### Debugging
```bash
# Check database migrations
python manage.py showmigrations expense_claims

# Verify data integrity
python manage.py check

# Run Django shell for testing
python manage.py shell
```

### Data Reset
```bash
# Nuclear option: Reset all expense claims
python manage.py shell -c "
from expense_claims.models import ExpenseClaim
ExpenseClaim.objects.all().delete()
print('All claims deleted')
"

# Then recreate samples
python manage.py create_sample_claims
```

---

## 🎯 Next Steps

### For Testing
1. ✅ Sample claims created - ready to test
2. ✅ View claims at http://localhost:8003/expense-claims/
3. ✅ Test approval workflows
4. ✅ Test PDF generation

### For Production
1. Review and clear sample data
2. Configure user permissions
3. Set up email notifications
4. Configure production settings
5. Deploy to production environment

---

## 📞 Support

### Command Help
```bash
# Get help for any management command
python manage.py create_sample_claims --help
python manage.py setup_krystal_companies --help
python manage.py setup_expense_categories --help
```

### Common Issues

**Issue**: Command not found
```bash
# Solution: Make sure you're in the project directory
cd /home/user/Desktop/integrated_business_platform
```

**Issue**: No users found
```bash
# Solution: Check if users exist in database
python manage.py shell -c "
from authentication.models import CompanyUser
print(f'Total users: {CompanyUser.objects.count()}')
"
```

**Issue**: Exchange rate errors
```bash
# Solution: Verify currencies exist
python manage.py shell -c "
from expense_claims.models import Currency
for c in Currency.objects.all():
    print(f'{c.code} - {c.name}')
"
```

---

## ✅ System Ready

The integrated business platform is now ready with:
- ✅ Foundational data imported
- ✅ Sample claims created
- ✅ Multi-currency support configured
- ✅ Bilingual support enabled
- ✅ Complete documentation available

**Start testing**: http://localhost:8003/expense-claims/

---

**Last Updated**: October 30, 2025
**Status**: ✅ Ready for Testing
