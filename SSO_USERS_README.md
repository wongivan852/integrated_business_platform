# SSO and User Management - Integrated Business Platform

## Overview
This platform includes a comprehensive Single Sign-On (SSO) system with user management for the Krystal Institute business operations.

## User Export Information
Last Updated: 2025-11-25
Total Users: 18

### User Structure
Users are stored in the `authentication_companyuser` model with the following fields:
- Employee ID
- Email (used for login)
- Name (First & Last)
- Region (HK/CN/GLOBAL)
- Department
- Active Status
- Staff/Admin Permissions

### Departments
- General
- HR
- Finance
- IT
- Operations
- Sales & Marketing
- Management
- Administration

### Regions
- HK (Hong Kong)
- CN (China)
- GLOBAL

## SSO Features
1. JWT-based authentication
2. Token management and revocation
3. Session tracking
4. Cross-platform integration
5. CSRF protection for trusted origins

## Files Included
- `users_export_formatted.json` - User data (passwords excluded for security)
- SSO models, views, and admin interfaces
- Authentication middleware and utilities

## Security Notes
⚠️ **IMPORTANT**: 
- Passwords are NOT included in the export
- Database file (db.sqlite3) is NOT pushed to GitHub
- Production secrets should use environment variables
- CSRF trusted origins configured for dashboard.krystal.technology

## Integration
The SSO system integrates with:
- CRM System
- QR Attendance System
- Project Management
- Expense Claims
- Event Management
- Leave Management
