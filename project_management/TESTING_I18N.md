# Testing the i18n Implementation

## ✅ Build Status

- **React Frontend**: ✅ Built successfully with i18n support
- **Django Backend**: ✅ Configured with translation files

## How to Test

### 1. React Frontend (SPA)

The React frontend is now built and deployed with Chinese language support.

**Location**: `/static/project_management/frontend/`

**To test:**

1. Open the React app in your browser (usually at `/project-management/app/` or wherever it's served)
2. Look for the language switcher buttons in the top navigation: **EN** / **中文**
3. Click the buttons to switch between English and Simplified Chinese
4. Verify the following elements change:
   - Navigation: "Dashboard" → "仪表板"
   - Page title: "IAICC 2025 Project Management Plan" → "IAICC 2025 项目管理计划"
   - Tabs: "Gantt Chart" → "甘特图", "WBS" → "工作分解结构", etc.
   - Export button: "Export CSV" → "导出 CSV"

**Note:** The language preference is saved in localStorage and persists across page refreshes.

### 2. Django Templates

**To test:**

1. Start the Django development server (if not already running):
   ```bash
   python manage.py runserver
   ```

2. Navigate to the project list page:
   ```
   http://localhost:8000/project-management/
   ```

3. Look for the language switcher in the top navigation bar (globe icon 🌐)
4. Click the dropdown and select "简体中文"
5. The page will reload in Chinese

**What should change:**
- Page title: "All Projects" → "所有项目"
- Statistics: "Total Projects" → "项目总数", "Active Projects" → "进行中项目"
- Search placeholder: "Search projects..." → "搜索项目..."
- Status filters: "Planning" → "计划中", "Active" → "进行中", etc.
- Priority levels: "Low" → "低", "Medium" → "中", "High" → "高"
- Action buttons: "View" → "查看", "Filter" → "筛选"

### 3. Model Data (Database)

The model choice labels are also translated:

**To verify:**
1. Create or edit a project
2. Look at status dropdown - should show:
   - English: Planning, Active, On Hold, Completed, Cancelled
   - Chinese: 计划中, 进行中, 暂停, 已完成, 已取消

3. Look at priority dropdown - should show:
   - English: Low, Medium, High, Critical
   - Chinese: 低, 中, 高, 紧急

## Troubleshooting

### React Frontend Not Showing Translations

If the React frontend is still showing only English:

1. **Clear browser cache**: Hard refresh (Ctrl+Shift+R or Cmd+Shift+R)
2. **Check localStorage**: Open DevTools → Application → Local Storage → Clear and reload
3. **Verify build**: Check that the build files have the latest timestamp:
   ```bash
   ls -la static/project_management/frontend/assets/
   ```

### Django Templates Not Showing Translations

If Django templates aren't showing Chinese:

1. **Check middleware**: Ensure `LocaleMiddleware` is enabled in `settings.py` (✅ Already done)
2. **Check language cookie**: Look for `django_language` cookie in DevTools
3. **Verify translation files exist**:
   ```bash
   ls -la project_management/locale/zh_Hans/LC_MESSAGES/
   ```

4. **If .mo files don't exist**, compile them:
   ```bash
   python manage.py compilemessages
   ```

### Language Switcher Not Visible

**Django**: Check that you're logged in - the language switcher is in the authenticated user navbar

**React**: The language buttons (EN / 中文) should always be visible in the top-right navigation

## Expected Behavior

### Language Persistence

- **Django**: Language selection stored in session/cookie
- **React**: Language selection stored in localStorage
- Both systems work independently

### Switching Languages

- **Django**: Page reloads with new language
- **React**: Instant switch without page reload

### Fallback

- If translation is missing, English text is shown
- No errors or blank spaces

## Files to Check

If something isn't working:

1. **Django translation file**: `project_management/locale/zh_Hans/LC_MESSAGES/django.po`
2. **React translation config**: `project_management/frontend/src/i18n.ts`
3. **Language switcher (Django)**: `templates/base.html`
4. **Language switcher (React)**: `project_management/frontend/src/App.tsx`
5. **Build output**: `static/project_management/frontend/assets/`

## Quick Verification Commands

```bash
# Check if translations exist (Django)
cat project_management/locale/zh_Hans/LC_MESSAGES/django.po | grep "msgstr"

# Check React build timestamp
stat static/project_management/frontend/assets/index-*.js

# Check if i18n is initialized (React)
grep -r "useTranslation" project_management/frontend/src/

# Verify language config (Django)
grep "LANGUAGES" business_platform/settings.py
```

## Success Indicators

✅ **React**: Language buttons visible, clicking changes UI immediately
✅ **Django**: Language dropdown visible, selecting reloads page in new language
✅ **Models**: Dropdown options show in selected language
✅ **Persistence**: Language choice saved and restored on refresh

## Need Help?

See the comprehensive documentation in `I18N_IMPLEMENTATION.md` for:
- Full implementation details
- How to add new translations
- Architecture overview
- Developer guide
