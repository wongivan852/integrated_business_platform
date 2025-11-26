# Integrated Business Platform - Current Status
**Date:** November 26, 2025
**Version:** Production

## Platform Overview

### Primary Platform (Integrated Business Platform)
- **Repository:** https://github.com/wongivan852/integrated_business_platform
- **Production URL:** dashboard.krystal.technology
- **Database:** PostgreSQL (krystal_platform)
- **Active Users:** 26 users (18 HK + 8 CN regions)

---

## Core Features

### 1. Single Sign-On (SSO)
- ✅ Centralized authentication system
- ✅ OAuth2 integration ready
- ✅ Session management across all apps
- ✅ Middleware for authentication enforcement
- **Location:** `/sso/` app
- **API Endpoints:** `/api/sso/`

### 2. Admin Panel
- ✅ User management interface
- ✅ App access matrix (26 active users)
- ✅ Role-based access control
- ✅ Application configuration management
- **Location:** `/admin_panel/` app
- **URL:** `/admin-panel/`
- **Key Views:**
  - User list: `/admin-panel/users/`
  - App access matrix: `/admin-panel/app-access-matrix/`

### 3. Authentication System
- ✅ Custom CompanyUser model
- ✅ Multi-region support (HK, CN)
- ✅ Department-based organization
- ✅ Employee ID management
- **Location:** `/authentication/` app

---

## Integrated Applications (10 Active)

### Business Management
1. **CRM System** - `/crm/` - Customer relationship management
2. **Cost Quotation System** - `/quotations/` - Quote management
3. **Expense Claim System** - `/expense-claims/` - Employee expense tracking

### HR & Operations
4. **Leave Management System** - `/leave/` - Annual and sick leave
5. **Staff Attendance** - `/attendance/` - Employee check-in/out
6. **QR Code Attendance** - `/qr-attendance/` - Multi-venue QR scanning

### Project & Asset Management
7. **Project Management System** - `/project-management/` - Task and project tracking
8. **Asset Tracking** - `/assets/` - Company asset management

### Events & Analytics
9. **Event Management System** - `/event-management/` - Event planning
10. **Stripe Dashboard** - `http://localhost:8006/` - Payment analytics

---

## User Distribution

### By Region
- **Hong Kong (HK):** 18 users
- **China (CN):** 8 users

### By Department
- **SALES:** Multiple users
- **IT:** 6 users
- **OPERATIONS:** 2 users
- **ADMIN:** 2 users
- **FINANCE:** 1 user
- **MANAGEMENT:** 2 users

### User Files Exported
- ✅ `active_users_26.csv` - Complete user list
- ✅ `active_users_26.json` - JSON format export
- ✅ `staff_list.csv` - Historical staff list

---

## Infrastructure

### SSO & Security
- CSRF protection configured
- Trusted origins: dashboard.krystal.technology
- Session-based authentication
- Middleware for app access control

### Database
- **Production:** PostgreSQL
- **Database Name:** krystal_platform
- **User:** platformadmin
- **Backup:** SQLite3 fallback available

### Configuration Files
- `.env` - Environment variables
- `business_platform/settings.py` - Django settings
- `requirements-sso.txt` - SSO dependencies

---

## Recent Updates

### Latest Commits
1. ✅ Added 26 active users export (PostgreSQL)
2. ✅ SSO integration with nginx configurations
3. ✅ App access matrix implementation
4. ✅ CRM system integration with SSO
5. ✅ QR attendance multi-venue support

---

## Secondary Tier Applications

### Separate Repositories (Already on GitHub)
These apps are integrated via SSO but maintain separate repositories:

1. **company_crm_system** - Individual CRM repo
2. **stripe-dashboard** - Analytics dashboard repo
3. **company-leave-system** - Leave management repo
4. **company-cost-quotation-system** - Quotation system repo
5. **company_expense_claim_system** - Expense claims repo

### Future Development
- Secondary tier apps to be deployed on other servers
- Will connect via SSO to main platform
- Microservices architecture approach

---

## Documentation Files

### SSO Documentation
- `SSO_IMPLEMENTATION_COMPLETE.md`
- `SSO_AND_ADMIN_PANEL_COMPLETE.md`
- `SSO_LINUX_SERVER_DEPLOYMENT.md`
- `SSO_USERS_README.md`
- `SSO_ADMIN_EVALUATION_REPORT.md`

### System Documentation
- `VERSION.md` - Version history
- `README.md` - Platform overview

---

## Next Steps

### For Production
1. ✅ SSO fully implemented
2. ✅ Admin panel operational
3. ✅ 26 active users configured
4. ✅ 10 integrated applications active
5. ⏳ Secondary tier apps deployment (planned)

### For Development Server
- Deploy secondary tier applications
- Configure inter-server SSO
- Set up API gateways
- Implement load balancing

---

## Repository Structure

```
integrated_business_platform/
├── admin_panel/          # Admin interface
├── authentication/       # User authentication
├── sso/                  # Single Sign-On
├── core/                 # Core models
├── crm/                  # CRM integration
├── quotations/           # Quotation system
├── expense_claims/       # Expense management
├── leave_management/     # Leave system
├── attendance/           # Staff attendance
├── qr_attendance/        # QR attendance
├── project_management/   # Project tracking
├── assets/               # Asset management
├── event_management/     # Event planning
├── stripe_integration/   # Payment analytics
├── nginx-backup/         # Server configs
└── business_platform/    # Main settings
```

---

**Status:** ✅ Production Ready
**Last Updated:** 2025-11-26
**Maintained by:** wongivan852
