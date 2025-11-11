# Local Deployment Guide - Bilingual Project Management App

## 🚀 Quick Start

This guide will help you deploy and test the bilingual project management application locally.

---

## ✅ Prerequisites Checklist

Before starting, ensure you have:

- [x] Python 3.11+ installed
- [x] Node.js and npm installed (for React frontend)
- [x] PostgreSQL or SQLite database
- [x] Virtual environment activated
- [x] All dependencies installed

---

## 📦 Step 1: Install Dependencies

### Python Dependencies

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install Python packages
pip install -r requirements.txt

# Verify Django installation
python -c "import django; print(f'Django {django.get_version()} installed')"
```

**Expected output:**
```
Django 4.2.16 installed
```

### Frontend Dependencies (Already Done)

The React frontend has already been built with i18n support. Build files are located at:
```
project_management/static/project_management/frontend/
```

---

## 🗄️ Step 2: Database Setup

### Option A: Using SQLite (Easiest for local testing)

```bash
# Set environment variable
export USE_SQLITE=True

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

### Option B: Using PostgreSQL

```bash
# Make sure PostgreSQL is running
# Update .env file with your database credentials:
DB_NAME=business_platform_db
DB_USER=postgres
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser
```

---

## 🌍 Step 3: Collect Static Files

```bash
# Collect all static files (including React build)
python manage.py collectstatic --noinput
```

**Expected output:**
```
175 static files copied to '/path/to/staticfiles'
```

This includes:
- Django admin assets
- Project management CSS/JS
- React frontend build (with i18n support)

---

## 🔤 Step 4: Translation Setup (Optional)

### Install gettext tools (for .mo file compilation)

**Ubuntu/Debian:**
```bash
sudo apt-get install gettext
```

**Mac:**
```bash
brew install gettext
```

**Windows:**
Download from: https://mlocati.github.io/articles/gettext-iconv-windows.html

### Compile translation messages

```bash
# Compile messages
python manage.py compilemessages

# Verify .mo file was created
ls -la project_management/locale/zh_Hans/LC_MESSAGES/
```

**Note:** If gettext is not installed, the app will still work! Model translations use `gettext_lazy` which doesn't require .mo files. Only template translations need compiled .mo files.

---

## 🏃 Step 5: Run the Development Server

```bash
# Start Django development server
python manage.py runserver

# Server will start at: http://127.0.0.1:8000/
```

**Expected output:**
```
Starting development server at http://127.0.0.1:8000/
Quit the server with CONTROL-C.
```

---

## 🧪 Step 6: Test the Bilingual Features

### A. Test Django Backend (Templates)

1. **Open browser:** http://127.0.0.1:8000/

2. **Login** with your superuser credentials

3. **Navigate to Project Management:**
   ```
   http://127.0.0.1:8000/project-management/
   ```

4. **Find the language switcher** in the navigation bar:
   - Look for the **🌐 globe icon** dropdown
   - Click to see "English" and "简体中文" options

5. **Switch to Chinese:**
   - Click "简体中文"
   - Page should reload in Chinese

6. **Verify translations:**
   - "All Projects" → "所有项目"
   - "Total Projects" → "项目总数"
   - "Active Projects" → "进行中项目"
   - "Search" → "搜索"
   - Status options: "Planning" → "计划中", "Active" → "进行中"

### B. Test React Frontend

1. **Navigate to React app:**
   ```
   http://127.0.0.1:8000/project-management/app/
   ```
   (Or wherever your React routes are configured)

2. **Find language switcher:**
   - Look for **EN** and **中文** buttons in navigation
   - Should be in the top-right corner

3. **Click "中文" button:**
   - UI should switch instantly (no page reload)
   - "Dashboard" → "仪表板"
   - "Gantt Chart" → "甘特图"
   - "WBS" → "工作分解结构"
   - "Resources" → "资源"

4. **Refresh page:**
   - Language preference should persist (stored in localStorage)

### C. Test Validators (Django Shell)

```bash
# Open Django shell
python manage.py shell
```

```python
# Test Chinese phone validator
from project_management.validators import chinese_phone_validator
chinese_phone_validator('13800138000')  # ✅ Should pass
# chinese_phone_validator('12345678901')  # ❌ Should raise ValidationError

# Test phone normalization
from project_management.validators import normalize_phone_number
phone = normalize_phone_number('138-0013-8000')
print(phone)  # Should print: +8613800138000

# Test display formatting
from project_management.validators import format_phone_for_display
display = format_phone_for_display('+8613800138000', 'zh')
print(display)  # Should print: 138-0013-8000

# Test Chinese name validator
from project_management.validators import chinese_name_validator
chinese_name_validator('张三')  # ✅ Should pass
chinese_name_validator('李四')  # ✅ Should pass
# chinese_name_validator('John')  # ❌ Should raise ValidationError

# Test bilingual name validator (accepts both)
from project_management.validators import bilingual_name_validator
bilingual_name_validator('张三')  # ✅ Should pass
bilingual_name_validator('John Smith')  # ✅ Should pass
```

### D. Test API (if configured)

```bash
# Test with curl
curl http://127.0.0.1:8000/api/projects/?lang=zh-hans

# Or use Python requests
python -c "
import requests
response = requests.get('http://127.0.0.1:8000/api/projects/',
                        params={'lang': 'zh-hans'})
print(response.json())
"
```

---

## 🔍 Step 7: Verify Everything Works

### Checklist:

#### Django Backend
- [ ] Server starts without errors
- [ ] Can login to admin
- [ ] Can access project management app
- [ ] Language switcher is visible (🌐 icon)
- [ ] Can switch between English and Chinese
- [ ] Project list shows in correct language
- [ ] Model choices are translated (Status, Priority)
- [ ] Forms show correct language

#### React Frontend
- [ ] React app loads
- [ ] Language buttons (EN/中文) are visible
- [ ] Clicking switches language instantly
- [ ] Language persists on page refresh
- [ ] All UI elements translate
- [ ] No console errors

#### Validators
- [ ] Chinese phone validator works
- [ ] Phone normalization works
- [ ] Name validators work
- [ ] No import errors

#### Static Files
- [ ] CSS loads correctly
- [ ] JavaScript loads correctly
- [ ] React bundle loads
- [ ] No 404 errors for static files

---

## 🐛 Troubleshooting

### Issue: "Can't find msgfmt" when compiling messages

**Solution:** Install gettext tools or skip this step. The app will work without .mo files for model translations.

```bash
# Ubuntu/Debian
sudo apt-get install gettext

# Mac
brew install gettext
```

### Issue: Language switcher not visible

**Check:**
1. Are you logged in? The switcher is in the authenticated navbar
2. Clear browser cache and hard refresh (Ctrl+Shift+R)
3. Check that LocaleMiddleware is enabled in settings.py

**Verify middleware:**
```bash
python manage.py shell
```
```python
from django.conf import settings
print('django.middleware.locale.LocaleMiddleware' in settings.MIDDLEWARE)
# Should print: True
```

### Issue: React language buttons not working

**Check:**
1. Is the React app loading? Check browser console for errors
2. Clear localStorage: DevTools → Application → Local Storage → Clear
3. Hard refresh the page
4. Verify i18n is initialized:

```javascript
// In browser console:
localStorage.getItem('i18nextLng')
// Should show current language
```

### Issue: Translations not showing in templates

**Check:**
1. Did you add `{% load i18n %}` at the top of the template?
2. Are you using `{% trans "text" %}` tags?
3. Is LANGUAGE_CODE in settings correct?

```bash
python manage.py shell
```
```python
from django.conf import settings
print(settings.LANGUAGES)
# Should show: [('en', 'English'), ('zh-hans', '简体中文')]
```

### Issue: Static files not loading

**Solution:**
```bash
# Recollect static files
python manage.py collectstatic --clear --noinput

# Check DEBUG setting
python manage.py shell
```
```python
from django.conf import settings
print(f"DEBUG: {settings.DEBUG}")
# Should be True for local development
```

### Issue: Database errors

**Solution:**
```bash
# Run migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations project_management
```

### Issue: React build is outdated

**Solution:**
```bash
cd project_management/frontend
npm run build
cd ../..
python manage.py collectstatic --noinput
```

---

## 📊 Verification Commands

### Quick Health Check

```bash
# Run all checks
python manage.py check

# Check translations
python manage.py check --deploy

# Run tests
python manage.py test project_management.tests.test_validators

# Check static files
ls -la staticfiles/project_management/frontend/

# Check locale files
ls -la project_management/locale/zh_Hans/LC_MESSAGES/
```

---

## 🎯 Common URLs

| Description | URL |
|-------------|-----|
| **Homepage** | http://127.0.0.1:8000/ |
| **Admin Panel** | http://127.0.0.1:8000/admin/ |
| **Project Management** | http://127.0.0.1:8000/project-management/ |
| **React Frontend** | http://127.0.0.1:8000/project-management/app/ |
| **API** | http://127.0.0.1:8000/api/ |
| **Language Switch** | POST to http://127.0.0.1:8000/i18n/setlang/ |

---

## 📝 Testing Scenarios

### Scenario 1: Create a Project in Chinese

1. Switch to Chinese language (click 简体中文)
2. Click "新建项目" (New Project)
3. Fill in Chinese name: "测试项目"
4. Fill in project code: "TEST001"
5. Set dates and save
6. Verify project appears with Chinese name

### Scenario 2: Test Phone Number Validation

1. Create a test model/form with phone field
2. Try entering: `138-0013-8000`
3. Should be accepted and normalized to `+8613800138000`
4. Try entering: `12345678901` (invalid format)
5. Should show validation error

### Scenario 3: Test Language Switching

1. Create project in English: "Test Project"
2. Switch to Chinese
3. View the same project
4. Create another project in Chinese
5. Switch back to English
6. Both projects should be visible

### Scenario 4: Test API with Language

```bash
# Test API in English
curl "http://127.0.0.1:8000/api/projects/?lang=en"

# Test API in Chinese
curl "http://127.0.0.1:8000/api/projects/?lang=zh-hans"

# Compare responses - field names should be the same,
# but status/priority display values should be translated
```

---

## 🚀 Production Deployment Notes

When deploying to production:

1. **Set DEBUG=False** in settings
2. **Set proper ALLOWED_HOSTS**
3. **Use PostgreSQL** (not SQLite)
4. **Compile messages:** `python manage.py compilemessages`
5. **Collect static files:** `python manage.py collectstatic`
6. **Use gunicorn or uwsgi** instead of runserver
7. **Set up nginx or Apache** for static file serving
8. **Enable HTTPS**
9. **Set up proper logging**

---

## 📚 Documentation References

- **Comprehensive Implementation Guide:** `BILINGUAL_IMPLEMENTATION_GUIDE.md`
- **Summary Document:** `BILINGUAL_REVAMP_SUMMARY.md`
- **Basic i18n:** `I18N_IMPLEMENTATION.md`
- **Testing Guide:** `TESTING_I18N.md`

---

## 💡 Quick Tips

### Tip 1: Test in Browser Developer Tools

```javascript
// Check current language
localStorage.getItem('i18nextLng')

// Change language manually
localStorage.setItem('i18nextLng', 'zh-hans')
location.reload()
```

### Tip 2: Test with Different User Preferences

```python
# In Django shell
from django.contrib.auth import get_user_model
User = get_user_model()
user = User.objects.get(username='admin')
user.preferred_language = 'zh-hans'
user.save()
```

### Tip 3: Monitor Django Translation Loading

```bash
# Run with verbose output
python manage.py runserver --verbosity 2
```

### Tip 4: Clear All Caches

```bash
# Clear Python cache
find . -type d -name __pycache__ -exec rm -rf {} +

# Clear npm cache
cd project_management/frontend
npm cache clean --force

# Restart server
```

---

## ✅ Success Indicators

You've successfully deployed when:

- ✅ Server starts without errors
- ✅ Can login and navigate the site
- ✅ Language switcher appears and works
- ✅ Django templates show translations
- ✅ React app shows translations
- ✅ Language persists across page loads
- ✅ Validators work in Django shell
- ✅ No console errors in browser
- ✅ Static files load correctly

---

## 🎉 You're Ready!

Your bilingual project management application is now deployed locally and ready for testing!

### Next Steps:

1. **Create sample data** in both languages
2. **Test all validators** with various inputs
3. **Test API endpoints** with language parameters
4. **Test forms** in both languages
5. **Report any issues** for fixing

### Need Help?

- Check the comprehensive guides in `BILINGUAL_IMPLEMENTATION_GUIDE.md`
- Review examples in `BILINGUAL_REVAMP_SUMMARY.md`
- Run the test suite: `python manage.py test project_management.tests`

**Happy Testing! 🚀**
