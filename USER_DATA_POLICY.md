# User Data Policy - Integrated Business Platform

**Date**: October 30, 2025
**Platform**: Krystal Integrated Business Platform

---

## Authorized Test Users and Data

### Ivan Wong (ivan.wong@krystal.institute)

**Status**: ✅ **AUTHORIZED USER**

**Permissions**:
- Employee ID: IVAN.WONG
- Region: HK (Hong Kong)
- Department: General
- Role: Staff Member
- Apps Access: Project Management, Expense System

**Data Policy**:
All expense claims, documents, and related data created by **ivan.wong@krystal.institute** are:

✅ **AUTHORIZED DATASET** - To be preserved and treated as legitimate test/production data
✅ **PROTECTED** - Not to be deleted during system maintenance
✅ **REFERENCE DATA** - Can be used for training, testing, and demonstration purposes

### Data Protection Measures

1. **Backup Policy**: All data from ivan.wong@krystal.institute will be included in system backups
2. **Retention**: No automatic deletion or cleanup of Ivan Wong's data
3. **Access**: Ivan Wong has full CRUD (Create, Read, Update, Delete) access to his own data
4. **Audit Trail**: All actions on Ivan Wong's data are logged in system audit trails

### Available Resources for Ivan Wong

**Companies**:
- ✅ Krystal Institute Limited (KI)
- ✅ Krystal Technology Limited (KT)
- ✅ CG Global Entertainment Limited (CGGE)
- ✅ 数谱环球(深圳)科技有限公司 (数谱(深圳))

**Expense Categories**:
- ✅ All 9 expense categories with bilingual support

**Currencies**:
- ✅ All 6 supported currencies (HKD, CNY, USD, EUR, GBP, JPY)

**Features**:
- ✅ Create expense claims across all companies
- ✅ Upload receipts and documents
- ✅ Submit claims for approval
- ✅ Access project management system
- ✅ Generate PDF reports
- ✅ View claim history and status

---

## Other Authorized Users

The platform currently has **17 users** from Krystal Institute:

1. Jacky Chan (jacky.chan@krystal.institute)
2. Adrian Chow (adrian.chow@krystal.institute)
3. Eugene Choy (eugene.choy@krystal.institute)
4. Jeff Koo (jeff.koo@krystal.institute)
5. Milne Man (milne.man@krystal.institute)
6. Danny Ng (danny.ng@krystal.institute)
7. Cloudy Poon (cloudy.poon@krystal.institute)
8. Tom Sin (tom.sin@krystal.institute)
9. SS Tam (ss.tam@krystal.institute)
10. Cat Tan (cat.tan@krystal.institute)
11. Tim Tan (tim.tan@krystal.institute)
12. **Ivan Wong (ivan.wong@krystal.institute)** ⭐ **AUTHORIZED DATASET USER**
13. Swing Wong (swing.w@krystal.institute)
14. YW Yeung (yw.yeung@krystal.institute)
15. Catina Yiu (catina.yiu@krystal.institute)
16. Sidne Lui (sidne.lui@krystal.institute)
17. Platform Administrator (admin@krystal-platform.com)

All user data is protected and preserved according to data retention policies.

---

## Data Usage Guidelines

### For System Administrators:

```bash
# Query Ivan Wong's data
python manage.py shell -c "
from expense_claims.models import ExpenseClaim
from authentication.models import CompanyUser
ivan = CompanyUser.objects.get(email='ivan.wong@krystal.institute')
claims = ExpenseClaim.objects.filter(claimant=ivan)
print(f'Ivan Wong has {claims.count()} expense claims')
"

# Backup Ivan Wong's data specifically
python manage.py dumpdata expense_claims expense_documents \
  --natural-foreign --natural-primary \
  --indent 2 > ivan_wong_data_backup.json

# Note: DO NOT delete Ivan Wong's data during cleanup operations
```

### For Developers:

- ✅ Ivan Wong's data can be used for testing and validation
- ✅ Use as reference for expected data structure
- ✅ Can be replicated for demo purposes
- ❌ DO NOT modify or delete without authorization
- ❌ DO NOT use for external sharing without approval

---

## Data Retention Policy

| Data Type | Retention Period | Notes |
|-----------|------------------|-------|
| Expense Claims (Ivan Wong) | **Permanent** | Authorized dataset - never auto-delete |
| Receipts/Documents | **Permanent** | Linked to claims |
| Audit Logs | **Permanent** | For compliance |
| Comments/History | **Permanent** | Part of claim lifecycle |
| User Profile | **Active** | Maintained as active user |

---

## System Notes

**Created**: October 30, 2025
**Last Updated**: October 30, 2025
**Authorized By**: System Administrator
**Policy Version**: 1.0

**Change Log**:
- 2025-10-30: Initial policy created
- 2025-10-30: Ivan Wong designated as authorized dataset user
- 2025-10-30: Confirmed ivan.wong@krystal.institute has expense_system access

---

## Contact

For questions about this data policy or Ivan Wong's dataset:
- **Email**: admin@krystal-platform.com
- **Platform**: http://localhost:8003
- **Admin Panel**: http://localhost:8003/admin/

---

**✅ CONFIRMED**: All data from ivan.wong@krystal.institute is authorized, protected, and will be preserved.
