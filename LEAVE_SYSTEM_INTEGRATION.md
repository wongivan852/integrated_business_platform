# Leave Management System Integration

## Overview
The Company Leave System has been successfully integrated into the Integrated Business Platform.

## Access Points

### Dashboard
- The Leave Management System is now visible on the main dashboard at `http://localhost:8000/dashboard/`
- Card Title: **Leave Management System**
- Icon: Calendar (fa-calendar-alt)
- Color: Green gradient

### Direct URL
- Access directly at: `http://localhost:8000/leave/`

## Features

The integrated leave system includes:

1. **Employee Management**
   - Employee profiles with department and position
   - Region-based management (Hong Kong/China)
   - Employee registration workflow

2. **Leave Applications**
   - Submit leave requests
   - Track application status (Pending, Approved, Rejected, Cancelled)
   - Support for various leave types
   - Document upload for medical certificates

3. **Leave Types**
   - Annual Leave
   - Sick Leave
   - Emergency Leave
   - Maternity/Paternity Leave
   - Special Leave Applications
   - Special Work Claims

4. **Approval Workflow**
   - Manager approval system
   - Rejection with reasons
   - Status tracking

5. **Leave Balance**
   - Track annual leave balances
   - View used and remaining days
   - Carry-forward functionality

6. **Special Features**
   - Holiday management
   - Employee import functionality
   - Balance download/export
   - Pending registration system

## Database Models

- **Employee**: User profiles with company details
- **LeaveType**: Configurable leave types
- **LeaveApplication**: Leave requests and approvals
- **SpecialLeaveApplication**: Special leave requests
- **SpecialWorkClaim**: Work claim requests
- **LeaveBalance**: Track employee leave balances
- **Holiday**: Public holidays management
- **PendingRegistration**: Employee registration workflow
- **EmployeeImport**: Bulk employee import tracking

## Management Commands

### Setup Leave App
```bash
python manage.py setup_leave_app
```
This command ensures the Leave Management System is properly configured in the ApplicationConfig.

## Configuration

The leave system is configured in:
- `settings.py`: Added to `INSTALLED_APPS` as `leave_management`
- `urls.py`: Mapped to `/leave/` endpoint
- `ApplicationConfig`: Activated with display settings

## Templates

All leave system templates are located in:
```
leave_management/templates/leave/
```

## Admin Interface

Access the Django admin at `http://localhost:8000/admin/` to manage:
- Employees
- Leave Types
- Leave Applications
- Special Leave/Work Claims
- Leave Balances
- Holidays

## Future Enhancements

Potential improvements:
- Email notifications for leave approvals/rejections
- Calendar integration
- Mobile responsive design improvements
- Analytics dashboard for HR
- Integration with attendance system
- Automated leave balance calculations
