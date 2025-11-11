# Quick Start Guide - Bilingual Project Management

## 🚀 One-Command Deployment

```bash
# Run the automated deployment script
./deploy_local.sh
```

This script will:
- ✅ Check Python installation
- ✅ Activate virtual environment
- ✅ Install all dependencies
- ✅ Run database migrations
- ✅ Set up locale directories
- ✅ Compile translations (if gettext installed)
- ✅ Collect static files
- ✅ Verify React build
- ✅ Run system checks

---

## 🎯 After Deployment

### Start the Server

```bash
python manage.py runserver
```

### Access the Application

| Page | URL |
|------|-----|
| **Main Site** | http://127.0.0.1:8000/ |
| **Admin Panel** | http://127.0.0.1:8000/admin/ |
| **Project Management** | http://127.0.0.1:8000/project-management/ |
| **React Frontend** | http://127.0.0.1:8000/project-management/app/ |

### Test Language Switching

#### Django (Templates)
1. Login to the application
2. Look for **🌐 globe icon** in navigation bar
3. Click dropdown and select "简体中文"
4. Page reloads in Chinese

#### React (Frontend)
1. Navigate to React app
2. Look for **EN** / **中文** buttons in top-right
3. Click to switch languages instantly
4. Language persists on page refresh

---

## 🧪 Quick Tests

### Test in Django Shell

```bash
python manage.py shell
```

```python
# Test phone validator
from project_management.validators import chinese_phone_validator
chinese_phone_validator('13800138000')  # ✅ Pass

# Test phone normalization
from project_management.validators import normalize_phone_number
print(normalize_phone_number('138-0013-8000'))  # +8613800138000

# Test name validators
from project_management.validators import bilingual_name_validator
bilingual_name_validator('张三')  # ✅ Pass
bilingual_name_validator('John Smith')  # ✅ Pass
```

### Test Language Switching

```python
from django.utils.translation import override

# Test with Chinese context
with override('zh-hans'):
    from project_management.models import Project
    project = Project.objects.first()
    print(project.name)  # Shows Chinese name if available
```

---

## 📚 Documentation

- **Full Deployment Guide:** `LOCAL_DEPLOYMENT_GUIDE.md`
- **Implementation Guide:** `project_management/BILINGUAL_IMPLEMENTATION_GUIDE.md` (1000+ lines)
- **Summary:** `project_management/BILINGUAL_REVAMP_SUMMARY.md`
- **Testing Guide:** `project_management/TESTING_I18N.md`

---

## ✅ Verification Checklist

After deployment, verify:

- [ ] Server starts without errors
- [ ] Can login to admin panel
- [ ] Can access project management app
- [ ] Language switcher (🌐) is visible
- [ ] Can switch to Chinese (简体中文)
- [ ] React app loads
- [ ] React language buttons (EN/中文) work
- [ ] Language persists on page refresh
- [ ] No console errors in browser

---

## 🐛 Common Issues

### Issue: "Module not found"
```bash
# Reinstall dependencies
pip install -r requirements.txt
```

### Issue: "Database error"
```bash
# Run migrations
python manage.py migrate
```

### Issue: "Static files not loading"
```bash
# Recollect static files
python manage.py collectstatic --clear --noinput
```

### Issue: "Language switcher not visible"
- Make sure you're logged in
- Clear browser cache (Ctrl+Shift+R)
- Check that LocaleMiddleware is enabled

### Issue: "React not translating"
- Clear localStorage in browser DevTools
- Hard refresh (Ctrl+Shift+R)
- Check browser console for errors

---

## 🎯 Key Features Deployed

### Validators (450+ lines)
- ✅ Chinese phone: `1[3-9]xxxxxxxxx`
- ✅ International phone: E.164 format
- ✅ Chinese ID card: 18-digit with checksum
- ✅ Chinese names: 2-4 characters
- ✅ English names: First Last format
- ✅ Phone normalization & formatting
- ✅ Date format validation

### Bilingual Models (200+ lines)
- ✅ BilingualModel mixin
- ✅ Automatic language switching
- ✅ Timestamp mixin
- ✅ User tracking mixin
- ✅ Soft delete mixin

### Bilingual Forms (350+ lines)
- ✅ Language-aware field configuration
- ✅ Dynamic required fields
- ✅ Automatic phone normalization
- ✅ Cultural validation

### API Serializers (200+ lines)
- ✅ Automatic language selection
- ✅ Phone field with normalization
- ✅ Language detection from request
- ✅ Choice field translations

### Tests (350+ lines)
- ✅ 30+ comprehensive test cases
- ✅ All validators covered
- ✅ Phone normalization tests
- ✅ Language context tests

---

## 💡 Quick Examples

### Create Bilingual Project

```python
from project_management.models import Project

project = Project.objects.create(
    name_en='Website Redesign',
    name_zh='网站重新设计',
    project_code='WEB2024',
    budget=100000.00
)

# Access in current language
print(project.name)  # Auto language-switching
```

### Use Validators

```python
from project_management.validators import (
    chinese_phone_validator,
    normalize_phone_number
)

# Validate
chinese_phone_validator('13800138000')

# Normalize
phone = normalize_phone_number('138-0013-8000')
print(phone)  # +8613800138000
```

### API with Language

```bash
# English
curl "http://127.0.0.1:8000/api/projects/?lang=en"

# Chinese
curl "http://127.0.0.1:8000/api/projects/?lang=zh-hans"
```

---

## 🎉 You're Ready!

Your bilingual project management application is deployed and ready to use!

### What's Included:

- 🌍 **Full bilingual support** (English + Simplified Chinese)
- ✅ **Cultural-aware validation** (Chinese phone, ID, names)
- 📱 **Responsive UI** with language switching
- 🔄 **Automatic data normalization**
- 🧪 **Comprehensive test suite**
- 📚 **Complete documentation**

**Happy coding! 🚀**
