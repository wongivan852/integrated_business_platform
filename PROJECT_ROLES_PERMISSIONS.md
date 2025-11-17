# Project Management - Roles & Permissions Guide

**Document Version**: 1.0
**Last Updated**: November 17, 2025
**Application**: Krystal Business Platform - Project Management

---

## Overview

The Project Management application has **four (4) distinct roles** with different levels of access and permissions. This document outlines what each role can and cannot do.

### Role Hierarchy

```
Owner (Highest Authority)
  ↓
Admin
  ↓
Member
  ↓
Viewer (Read-Only Access)
```

---

## 1. Owner Role

**Who Gets This Role**: Project creator or assigned project owner

### ✅ What Owners CAN Do

#### Project Management
- ✓ **Full project control** - Complete access to all project features
- ✓ **Edit project settings** - Change name, description, dates, budget
- ✓ **Delete the project** - Permanently remove the project
- ✓ **Archive/unarchive project** - Control project lifecycle
- ✓ **Change project status** - Update planning, active, on-hold, completed, cancelled

#### Team Management
- ✓ **Add team members** - Invite users to the project
- ✓ **Remove team members** - Remove users from the project
- ✓ **Assign roles** - Change member roles (Owner, Admin, Member, Viewer)
- ✓ **Transfer ownership** - Assign Owner role to another user

#### Task Management
- ✓ **Create tasks** - Add new tasks to the project
- ✓ **Edit all tasks** - Modify any task regardless of assignee
- ✓ **Delete tasks** - Remove tasks from the project
- ✓ **Assign tasks** - Assign tasks to team members
- ✓ **Change task status** - Update task progress and status
- ✓ **Set task dependencies** - Create predecessor/successor relationships
- ✓ **Move/reorder tasks** - Change task hierarchy and position

#### Gantt Chart & Scheduling
- ✓ **Edit Gantt chart** - Modify task dates and durations
- ✓ **Drag and drop tasks** - Reposition tasks visually
- ✓ **Create dependencies** - Link tasks with FS, SS, FF, SF relationships
- ✓ **Save baselines** - Create project snapshots
- ✓ **View all views** - Day, Week, Month, Year views

#### Financial & Reporting
- ✓ **View budget information** - See project budget and costs
- ✓ **Update costs** - Modify actual costs and estimates
- ✓ **Generate reports** - Create project reports and analytics
- ✓ **Export data** - Export tasks and project data

### ❌ What Owners CANNOT Do

- ✗ Cannot access projects they don't own or aren't members of
- ✗ Cannot delete other users' personal templates

---

## 2. Admin Role

**Who Gets This Role**: Trusted team members with management responsibilities

### ✅ What Admins CAN Do

#### Project Management
- ✓ **Edit project settings** - Change name, description, dates, budget
- ✓ **Change project status** - Update project lifecycle status
- ✓ **View all project information** - Full visibility of project data

#### Team Management
- ✓ **Add team members** - Invite users to the project
- ✓ **Remove team members** - Remove users (except Owner)
- ✓ **Assign Member/Viewer roles** - Change roles for team members

#### Task Management
- ✓ **Create tasks** - Add new tasks to the project
- ✓ **Edit all tasks** - Modify any task regardless of assignee
- ✓ **Delete tasks** - Remove tasks from the project
- ✓ **Assign tasks** - Assign tasks to team members
- ✓ **Change task status** - Update task progress and status
- ✓ **Set task dependencies** - Create predecessor/successor relationships
- ✓ **Move/reorder tasks** - Change task hierarchy and position

#### Gantt Chart & Scheduling
- ✓ **Edit Gantt chart** - Modify task dates and durations
- ✓ **Drag and drop tasks** - Reposition tasks visually
- ✓ **Create dependencies** - Link tasks with relationships
- ✓ **Save baselines** - Create project snapshots
- ✓ **View all views** - Day, Week, Month, Year views

#### Financial & Reporting
- ✓ **View budget information** - See project budget and costs
- ✓ **Update costs** - Modify actual costs and estimates
- ✓ **Generate reports** - Create project reports and analytics
- ✓ **Export data** - Export tasks and project data

### ❌ What Admins CANNOT Do

- ✗ **Cannot delete the project** - Only Owner can delete
- ✗ **Cannot change Owner role** - Cannot assign or remove Owner role
- ✗ **Cannot remove the Owner** - Cannot kick out project owner
- ✗ **Cannot transfer ownership** - Cannot make themselves Owner

---

## 3. Member Role

**Who Gets This Role**: Regular team members who actively work on tasks

### ✅ What Members CAN Do

#### Task Management
- ✓ **Create tasks** - Add new tasks to the project
- ✓ **Edit tasks** - Modify task details (title, description, dates)
- ✓ **Delete tasks** - Remove tasks they created
- ✓ **Update task status** - Change status of tasks assigned to them
- ✓ **Add comments** - Comment on tasks
- ✓ **Upload files** - Attach files to tasks
- ✓ **Set task dependencies** - Create task relationships
- ✓ **Move/reorder tasks** - Reorganize task structure

#### Gantt Chart
- ✓ **Edit Gantt chart** - Modify task dates and durations
- ✓ **Drag and drop tasks** - Move tasks in timeline
- ✓ **Create dependencies** - Link related tasks
- ✓ **View all views** - Day, Week, Month, Year views

#### Project Participation
- ✓ **View project information** - See project details and team
- ✓ **View all tasks** - See all tasks in the project
- ✓ **View budget** - See project budget (view only)
- ✓ **View Kanban board** - See task board view
- ✓ **Export data** - Export tasks and project data

### ❌ What Members CANNOT Do

- ✗ **Cannot edit project settings** - Cannot change project name, dates, budget
- ✗ **Cannot delete the project** - No project deletion rights
- ✗ **Cannot add/remove team members** - No team management access
- ✗ **Cannot assign roles** - Cannot change member permissions
- ✗ **Cannot delete tasks created by others** - Only own tasks
- ✗ **Cannot save baselines** - No baseline management
- ✗ **Cannot modify budget** - Read-only access to financial data

---

## 4. Viewer Role

**Who Gets This Role**: Stakeholders, clients, observers who need visibility only

### ✅ What Viewers CAN Do

#### Read-Only Access
- ✓ **View project information** - See project details and settings
- ✓ **View all tasks** - See all tasks and their details
- ✓ **View Gantt chart** - See project timeline (read-only)
- ✓ **View Kanban board** - See task board (read-only)
- ✓ **View team members** - See who's on the project
- ✓ **View dependencies** - See task relationships
- ✓ **View budget information** - See project budget and costs
- ✓ **View comments** - Read task discussions
- ✓ **View files** - Download attached files
- ✓ **Export data** - Export tasks and project data for viewing

### ❌ What Viewers CANNOT Do

- ✗ **Cannot create tasks** - No task creation rights
- ✗ **Cannot edit tasks** - Cannot modify any task information
- ✗ **Cannot delete tasks** - No deletion rights
- ✗ **Cannot change task status** - Cannot update progress
- ✗ **Cannot add comments** - No commenting rights
- ✗ **Cannot upload files** - No file upload rights
- ✗ **Cannot edit Gantt chart** - No timeline modifications
- ✗ **Cannot drag and drop** - No visual editing
- ✗ **Cannot create dependencies** - No relationship creation
- ✗ **Cannot add/remove team members** - No team management
- ✗ **Cannot edit project settings** - No project modifications
- ✗ **Cannot save baselines** - No baseline management

---

## Quick Reference Table

| **Permission** | Owner | Admin | Member | Viewer |
|---|:---:|:---:|:---:|:---:|
| **View project** | ✓ | ✓ | ✓ | ✓ |
| **View tasks** | ✓ | ✓ | ✓ | ✓ |
| **View Gantt chart** | ✓ | ✓ | ✓ | ✓ |
| **View budget** | ✓ | ✓ | ✓ | ✓ |
| **Export data** | ✓ | ✓ | ✓ | ✓ |
| | | | | |
| **Create tasks** | ✓ | ✓ | ✓ | ✗ |
| **Edit tasks** | ✓ | ✓ | ✓ | ✗ |
| **Delete tasks** | ✓ | ✓ | ✓* | ✗ |
| **Add comments** | ✓ | ✓ | ✓ | ✗ |
| **Upload files** | ✓ | ✓ | ✓ | ✗ |
| | | | | |
| **Edit Gantt chart** | ✓ | ✓ | ✓ | ✗ |
| **Create dependencies** | ✓ | ✓ | ✓ | ✗ |
| **Move/reorder tasks** | ✓ | ✓ | ✓ | ✗ |
| | | | | |
| **Edit project settings** | ✓ | ✓ | ✗ | ✗ |
| **Update budget** | ✓ | ✓ | ✗ | ✗ |
| **Save baselines** | ✓ | ✓ | ✗ | ✗ |
| | | | | |
| **Add team members** | ✓ | ✓ | ✗ | ✗ |
| **Remove team members** | ✓ | ✓ | ✗ | ✗ |
| **Assign roles** | ✓ | ✓** | ✗ | ✗ |
| | | | | |
| **Delete project** | ✓ | ✗ | ✗ | ✗ |
| **Transfer ownership** | ✓ | ✗ | ✗ | ✗ |

**Notes**:
- \* Members can only delete their own tasks
- \*\* Admins can assign Member/Viewer roles, but not Admin/Owner roles

---

## Role Assignment Best Practices

### When to Assign Each Role

#### 👑 **Owner**
- Project Manager
- Product Owner
- Department Head
- Person ultimately responsible for project success

#### 🔧 **Admin**
- Team Leads
- Scrum Masters
- Deputy Project Managers
- Trusted senior team members who need management capabilities

#### 👤 **Member**
- Developers
- Designers
- Analysts
- Any team member actively working on tasks
- Contributors who need to create and update tasks

#### 👁️ **Viewer**
- Stakeholders
- Clients
- Executives
- External consultants
- Anyone who needs visibility but shouldn't make changes

---

## Security Notes

1. **Role Hierarchy**: Higher roles inherit all permissions from lower roles
2. **Owner Special Rights**: Only Owners can delete projects or transfer ownership
3. **Admin Limitations**: Admins have broad permissions but cannot override Owner authority
4. **Member Protection**: Members can only delete their own tasks, not others'
5. **Viewer Restrictions**: Viewers have strictly read-only access with no modification rights

---

## Frequently Asked Questions

### Q: Can I have multiple Owners on a project?
**A**: No, each project has exactly one Owner. However, you can assign multiple Admins who have similar permissions.

### Q: Can Members see tasks assigned to other people?
**A**: Yes, Members can view all tasks in the project, not just their own.

### Q: Can Viewers export project data?
**A**: Yes, Viewers can export data for viewing purposes, but they cannot modify the project.

### Q: What happens if the Owner leaves the company?
**A**: Contact a system administrator to transfer ownership to another team member.

### Q: Can I change my own role?
**A**: No, only Owners and Admins can assign roles to team members.

### Q: Do Viewers get notifications?
**A**: Yes, Viewers receive notifications about project updates based on their notification settings.

---

## Need Help?

If you have questions about roles and permissions:

1. **Contact your Project Owner** - They can adjust your role if needed
2. **Contact Project Admin** - They can help with most permission questions
3. **System Administrator** - For account or system-level issues

---

**Document End**

*This document applies to the Krystal Business Platform Project Management application.*
