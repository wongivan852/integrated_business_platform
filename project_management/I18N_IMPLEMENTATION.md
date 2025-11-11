# Internationalization (i18n) Implementation

## Overview

The project management application now supports **Simplified Chinese (简体中文)** parallel with the English version. This implementation covers both the Django backend and React frontend.

## Supported Languages

- **English** (`en`)
- **Simplified Chinese** (`zh-hans`)

## Implementation Details

### 1. Django Backend

#### Configuration (settings.py)

```python
# Supported languages
LANGUAGES = [
    ('en', 'English'),
    ('zh-hans', '简体中文'),
]

# Locale paths for translation files
LOCALE_PATHS = [
    BASE_DIR / 'locale',
    BASE_DIR / 'project_management' / 'locale',
]
```

The `LocaleMiddleware` has been added to handle language switching.

#### Models

All model choice fields have been wrapped with `gettext_lazy` (`_()`) for translation:

```python
from django.utils.translation import gettext_lazy as _

STATUS_CHOICES = [
    ('planning', _('Planning')),
    ('active', _('Active')),
    # ...
]
```

This includes:
- Project statuses, priorities, and view types
- Task statuses and priorities
- Role types
- Action types
- Cost categories
- Widget types and sizes
- And more...

#### Templates

Key templates have been updated with translation tags:

```django
{% load i18n %}

<h1>{% trans "All Projects" %}</h1>
<label>{% trans "Search" %}</label>
<input placeholder="{% trans 'Search projects...' %}" />
```

The `project_list.html` template has been fully translated.

#### Language Switcher

A language switcher has been added to the base template navigation bar:

- Displays current language (English/中文)
- Allows switching between English and Simplified Chinese
- Preserves current page location after language switch

#### Translation Files

Translation file location: `project_management/locale/zh_Hans/LC_MESSAGES/django.po`

This file contains all Chinese translations for:
- Model choice labels
- Template strings
- Form labels and validation messages

### 2. React Frontend

#### i18n Configuration

File: `frontend/src/i18n.ts`

Uses the following libraries:
- `i18next` - Core i18n framework
- `react-i18next` - React bindings
- `i18next-browser-languagedetector` - Automatic language detection

Configuration:
```typescript
i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources,
    fallbackLng: 'en',
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
    }
  });
```

#### Translation Resources

All translations are defined in `i18n.ts` with both English and Chinese versions:

```typescript
const resources = {
  en: {
    translation: {
      "Dashboard": "Dashboard",
      "Gantt Chart": "Gantt Chart",
      // ...
    }
  },
  'zh-hans': {
    translation: {
      "Dashboard": "仪表板",
      "Gantt Chart": "甘特图",
      // ...
    }
  }
};
```

#### Component Usage

Components use the `useTranslation` hook:

```typescript
import { useTranslation } from 'react-i18next';

function MyComponent() {
  const { t } = useTranslation();

  return <h1>{t('Dashboard')}</h1>;
}
```

#### Language Switcher

A language switcher has been added to the React app navigation:

```typescript
const { t, i18n } = useTranslation();

const changeLanguage = (lng: string) => {
  i18n.changeLanguage(lng);
};

// Buttons for EN and 中文
```

The selected language is:
- Highlighted in the UI
- Stored in localStorage
- Automatically detected on page load

## How to Use

### Django Templates

1. **For end users:**
   - Click the language dropdown in the navigation bar
   - Select "English" or "简体中文"
   - The page will reload with the selected language

2. **For developers:**
   - To add new translatable strings in templates:
     ```django
     {% load i18n %}
     {% trans "Your text here" %}
     ```

   - To add new model choices:
     ```python
     from django.utils.translation import gettext_lazy as _

     CHOICES = [
         ('value', _('Display Text')),
     ]
     ```

   - After adding new strings, update the translation file:
     ```bash
     python manage.py makemessages -l zh_Hans
     # Edit the .po file to add Chinese translations
     python manage.py compilemessages
     ```

### React Frontend

1. **For end users:**
   - Click "EN" or "中文" buttons in the navigation bar
   - The UI will immediately switch languages
   - Language preference is saved automatically

2. **For developers:**
   - Add translations to `frontend/src/i18n.ts`:
     ```typescript
     const resources = {
       en: {
         translation: {
           "New Key": "English Text"
         }
       },
       'zh-hans': {
         translation: {
           "New Key": "中文文本"
         }
       }
     };
     ```

   - Use in components:
     ```typescript
     const { t } = useTranslation();
     <div>{t('New Key')}</div>
     ```

## Translation Coverage

### Django Backend
- ✅ Model choice fields (100%)
- ✅ Project list template (100%)
- ⚠️ Other templates (partial - can be expanded)
- ✅ Forms (inherited from models)

### React Frontend
- ✅ Main navigation (100%)
- ✅ Tab labels (100%)
- ✅ Header and titles (100%)
- ✅ Export buttons (100%)
- ⚠️ Detailed content (partial - can be expanded)

## Files Modified

### Configuration
- `business_platform/settings.py` - Language settings and locale paths
- `business_platform/urls.py` - Language switching URL

### Backend
- `project_management/models.py` - Translation wrapping for choice fields
- `project_management/templates/project_management/project_list.html` - Translation tags
- `templates/base.html` - Language switcher

### Frontend
- `project_management/frontend/package.json` - i18n dependencies
- `project_management/frontend/src/i18n.ts` - i18n configuration
- `project_management/frontend/src/main.tsx` - i18n initialization
- `project_management/frontend/src/App.tsx` - Language switcher
- `project_management/frontend/src/pages/iaicc-2025-project-plan.tsx` - Translation usage

### Translation Files
- `project_management/locale/zh_Hans/LC_MESSAGES/django.po` - Chinese translations

## Testing

### Django
1. Access the project management app
2. Use the language switcher in the navbar
3. Verify:
   - Project list displays in selected language
   - Status and priority labels are translated
   - Form labels are translated

### React
1. Access the React frontend
2. Click EN/中文 buttons
3. Verify:
   - Navigation updates immediately
   - Tab labels change
   - Headers and titles change
   - Language preference persists on refresh

## Future Enhancements

1. **Additional Templates**: Add translation tags to remaining Django templates
2. **More Languages**: Add support for Traditional Chinese, Spanish, etc.
3. **Dynamic Content**: Translate user-generated content if needed
4. **RTL Support**: Add support for right-to-left languages like Arabic
5. **Translation Management**: Consider using a translation management platform for larger scale

## Notes

- Language codes: Django uses `zh-hans`, React uses `zh-hans`
- Both systems are synchronized and use the same language identifiers
- Language preference is stored separately:
  - Django: Session/Cookie
  - React: localStorage
- The language switchers work independently but can be synchronized if needed
