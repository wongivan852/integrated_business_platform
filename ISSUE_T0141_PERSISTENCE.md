# Issue Report: T0141 Task Persistence Problem

**Date Reported**: November 16, 2025
**Component**: Project Management - Gantt Chart
**Severity**: High
**Status**: Unresolved

## Problem Description

Task T0141 (Venue Selection & Contract) in the IAICC 2025 project cannot persist date/duration changes after page refresh. Changes appear to save (API returns 200 OK), but revert to original values upon refresh.

## Task Details

- **Task ID**: 449
- **Task Code**: T0141 (previously "1.1", updated to standard format)
- **Title**: Venue Selection & Contract
- **Original State**: Nov 7-20, 2025 (14 days)
- **Attempted Changes**: Various end dates (e.g., Nov 22, Nov 25)
- **Process Owner**: tim.tan@krystal.institute (ID: 758)

## Investigation Summary

### 1. Database Layer ✅ Working
- Changes ARE being saved to database correctly
- Manual database updates persist properly
- Task model fields are correct

### 2. API Layer ✅ Working
- `/api/gantt/tasks/449/update-dates/` endpoint receives correct data
- Returns 200 OK with correct response
- Server logs show successful updates

### 3. Frontend Issues Identified

#### Issue A: Template Error (FIXED)
- **Problem**: Template used `{{ task.text }}` instead of `{{ task.title }}`
- **Location**: Line 2108 in project_gantt.html
- **Status**: Fixed

#### Issue B: Task Code Conversion (FIXED)
- **Problem**: Non-standard codes ("1.1") were being auto-converted
- **Solution**: Updated to standard T#### format (T0141)
- **Status**: Fixed - 20+ tasks updated

#### Issue C: Date Persistence (UNRESOLVED)
- **Symptom**: Dates revert after page refresh
- **Observation**: Changes save to DB but don't display correctly
- **Suspected Cause**:
  - Possible issue in `onTaskLoading` event (lines 799-907)
  - May be recalculating dates from duration on load
  - Could be timezone/date parsing issue

## Code Locations

### Frontend Files
- `/project_management/templates/project_management/project_gantt.html`
  - Lines 799-907: onTaskLoading event handler
  - Lines 2105-2130: Task data initialization
  - Lines 3231-3273: debouncedSaveDates function
  - Lines 3647-3717: onAfterTaskUpdate event

### Backend Files
- `/project_management/views/gantt_views.py`
  - Lines 503-561: api_update_task_dates function
  - Lines 755-843: api_create_task function

### Model
- `/project_management/models.py`
  - Task model with date fields

## Attempted Fixes

1. ✅ Fixed template field reference (task.text → task.title)
2. ✅ Updated task codes to standard format
3. ✅ Added debounced save mechanism
4. ✅ Enhanced onAfterTaskUpdate to save dates
5. ✅ Added logging to track date updates
6. ❌ Date persistence still not working

## Server Logs Sample

```
INFO 13:51:35 Update task 449: progress=0, title=Venue Selection & Contract, process_owner_id=758
INFO 13:51:35 Task 449 updated successfully
INFO 13:51:35 POST /api/gantt/tasks/449/update-dates/ 200
INFO 13:51:36 POST /api/gantt/tasks/449/update-dates/ 200
```

## Reproduction Steps

1. Navigate to Project Management → IAICC 2025 → Gantt View
2. Locate task T0141 "Venue Selection & Contract"
3. Edit task by dragging end date or using lightbox
4. Observe successful save (console shows ✓)
5. Refresh page
6. Task reverts to original dates (Nov 7-20)

## Next Investigation Steps

1. **Check JavaScript Console**
   - Look for date parsing errors
   - Verify what dates are being sent
   - Check onTaskLoading debug output

2. **Test Date Format**
   - Verify date string format consistency
   - Check for timezone issues
   - Test with different date formats

3. **Debug onTaskLoading**
   - Add console.log for received vs calculated dates
   - Check if duration is overriding end_date
   - Verify date object types

4. **Check Gantt Configuration**
   - Review gantt.config.date settings
   - Check work_time calculations
   - Verify calendar settings

5. **Test Other Tasks**
   - Check if issue is specific to T0141
   - Test with newly created tasks
   - Compare working vs non-working tasks

## Temporary Workaround

Currently, dates can be manually updated via Django shell:
```python
from project_management.models import Task
task = Task.objects.get(id=449)
task.end_date = date(2025, 11, 25)
task.duration = (task.end_date - task.start_date).days + 1
task.save()
```

## Environment

- Django 4.2.16
- DHTMLX Gantt (version unknown)
- Python 3.12
- Browser: (user's browser)
- OS: Linux 6.8.0-87-generic

## Related Issues

- Frontend task code standardization (resolved)
- Multiple API calls for same update (improved with debouncing)
- Process owner assignment working correctly

## Contact

Reported by user on November 16, 2025
To be revisited: November 17, 2025

---

*This issue is logged for follow-up investigation. The root cause appears to be in the frontend date handling during page load, but requires further debugging to identify the exact mechanism causing the reversion.*