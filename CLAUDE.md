# CLAUDE.md - Project Context for AI Assistants

> This file provides essential context for Claude Code and other AI assistants working on this project.
> **Last Updated:** 2025-12-19

---

## Project Overview

**Krystal Business Platform** - An integrated Django-based enterprise platform managing multiple business applications under a single SSO (Single Sign-On) authentication system.

### Key Facts
- **Framework:** Django 5.x with Python 3.12
- **Database:** PostgreSQL (`krystal_platform`)
- **Server:** Gunicorn on port 8080
- **Version:** 1.2.0 (as of 2025-11-17)

---

## Architecture

### Directory Structure
```
/home/user/Desktop/integrated_business_platform/
├── business_platform/     # Django project settings
├── authentication/        # SSO & user management
├── dashboard/             # Main dashboard app
├── expense_claims/        # Expense claim system (PRIMARY FOCUS)
├── expense_documents/     # Document attachments
├── expense_reports/       # Reporting module
├── assets/                # Asset tracking
├── locations/             # Location management
├── movements/             # Asset movements
├── project_management/    # Project & task management
├── event_management/      # Event tracking
├── leave_management/      # Leave requests
├── attendance/            # Basic attendance
├── qr_attendance/         # QR-based event attendance
├── crm/                   # Customer relationship management
├── quotations/            # Quotation system
├── stripe_integration/    # Payment processing
├── sso/                   # Single Sign-On module
├── templates/             # Shared templates
│   ├── base.html          # Main base template
│   └── claims/            # Expense claims templates
├── static/                # Static files
├── media/                 # User uploads
└── venv/                  # Python virtual environment
```

---

## Database Configuration

```
Host: localhost
Port: 5432
Database: krystal_platform
User: platformadmin
Password: 5514
```

### Important: Table Naming Convention
The expense claims models use `db_table` with `claims_` prefix:
- `claims_company` - Companies
- `claims_currency` - Currencies
- `claims_expenseclaim` - Main claims
- `claims_expenseitem` - Line items
- `claims_exchangerate` - Exchange rates

---

## Running the Application

### Production (Gunicorn on port 8080)
```bash
cd /home/user/Desktop/integrated_business_platform
source venv/bin/activate
gunicorn -c gunicorn_config.py business_platform.wsgi:application
```

### Development (Django runserver)
```bash
cd /home/user/Desktop/integrated_business_platform
source venv/bin/activate
python manage.py runserver 0.0.0.0:8080
```

### Restart Gunicorn
```bash
kill -9 $(lsof -t -i:8080) 2>/dev/null
sleep 2
cd /home/user/Desktop/integrated_business_platform && source venv/bin/activate
gunicorn -c gunicorn_config.py business_platform.wsgi:application > /tmp/gunicorn_8080.log 2>&1 &
```

---

## Key URLs

| URL | Description |
|-----|-------------|
| http://localhost:8080/ | Main dashboard |
| http://localhost:8080/expense-claims/ | Expense claims list |
| http://localhost:8080/expense-claims/new/ | Create new claim |
| http://localhost:8080/admin/ | Django admin |
| http://localhost:8080/auth/login/ | SSO login |

---

## Expense Claims Module (Primary Focus)

### Models
- **Company** - Business entities (CGEL, KIL, KT, KHL)
- **Currency** - Supported currencies with HKD as base
- **ExpenseClaim** - Main claim header
- **ExpenseItem** - Individual expense line items
- **ExpenseCategory** - Expense categories
- **ExchangeRate** - Currency exchange rates

### Key Features
1. **Sort By dropdown** - Date of Occurrence, Claim #, Amount, Created
2. **Date of Occurrence column** - Shows expense date range
3. **Move Up/Down buttons** - Manual claim reordering
4. **Claim For** - Submit claims on behalf of others
5. **Multi-currency support** - Auto-convert to HKD
6. **Receipt attachments** - Photo/document uploads
7. **Print templates** - Individual and combined printing

### Important Templates
- `templates/claims/claim_list.html` - Main claims list
- `templates/claims/claim_form.html` - Create/edit claim
- `templates/claims/claim_detail.html` - View claim details
- `templates/claims/print_claims.html` - Print single claim
- `templates/claims/print_combined_claims.html` - Print multiple claims
- `templates/claims/print_with_receipts.html` - Print with receipt images

---

## Git Repositories

### GitHub (Primary)
```bash
git push github main
# URL: https://github.com/wongivan852/integrated_business_platform.git
```

### GitLab (Secondary)
```bash
git push gitlab main
# URL: https://gitlab.kryedu.org/company_apps/integrated_business_platform.git
```

---

## Design Decisions

### UI/UX Conventions
- Bootstrap 5.1.3 for styling
- Font Awesome 6.0 for icons
- DataTables for sortable tables
- jQuery 3.6.0 for DOM manipulation
- Krystal brand colors in `static/css/krystal-brand.css`

### Template Inheritance
```
base.html
└── claims/claim_list.html (extends base.html)
└── claims/claim_form.html (extends base.html)
└── claims/print_base.html (standalone for printing)
    └── claims/print_claims.html
```

### Authentication
- Custom User model in `authentication/models.py`
- SSO with JWT tokens
- Session-based authentication for web UI

---

## Common Issues & Solutions

### 1. Template Changes Not Visible
```bash
# Restart Gunicorn to reload templates
kill -9 $(lsof -t -i:8080) && sleep 2
gunicorn -c gunicorn_config.py business_platform.wsgi:application &
```

### 2. Database Migrations
```bash
python manage.py makemigrations expense_claims
python manage.py migrate
```

### 3. Static Files Not Loading
```bash
python manage.py collectstatic --noinput
```

### 4. Check Server Status
```bash
curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/expense-claims/
```

---

## Recent Changes (December 2025)

### 2025-12-19
- Restored claim_list.html with Sort By dropdown
- Added Date of Occurrence column
- Added Move Up/Down buttons for claim reordering
- Fixed print templates for PDF handling and image loading

### Known Working Features
- Expense claim creation with multi-currency
- Receipt photo uploads
- Claim printing (single and combined)
- Sort By dropdown (Date of Occurrence, Claim #, Amount, Created)
- DataTables for sortable columns
- Claim For (submit on behalf of others)

---

## Companies in System

| Code | Name | Type |
|------|------|------|
| CGEL | CG Global Entertainment Limited | Entertainment |
| KIL | Krystal Institute Limited | Institute |
| KT | Krystal Technology Limited | Technology |
| KHL | Krystal Holdings Limited | Holding |

---

## Coding Conventions

### Python
- Use Django ORM, avoid raw SQL
- Use `gettext_lazy` for translatable strings
- Follow PEP 8 style guide

### Templates
- Use Django template tags, not inline JavaScript
- Keep JavaScript in `{% block extra_js %}`
- Use Bootstrap classes for styling

### JavaScript
- Use vanilla JS or jQuery (no React/Vue)
- Event delegation for dynamic elements
- CSRF token for AJAX requests

---

## Environment Variables (.env)

```
SECRET_KEY=django-insecure-integrated-platform-key-2025
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,*
USE_SQLITE=False
DB_NAME=krystal_platform
DB_USER=platformadmin
DB_PASSWORD=5514
DB_HOST=localhost
DB_PORT=5432
SSO_SECRET_KEY=QrWyU0NmtAj2Ogd1QOPFcl4YSqtMpwQ9HyCV1ebbAlo
```

---

## For Claude Code Sessions

When starting a new session, consider:

1. **Read this file first** to understand context
2. **Check git status** for uncommitted changes
3. **Verify server is running** on port 8080
4. **Test changes in browser** before committing

### Useful Commands to Start
```bash
cd /home/user/Desktop/integrated_business_platform
git status
lsof -i:8080  # Check if server is running
cat VERSION   # Check current version
```
