# Application Version Management

## Current Version
**Version**: 1.2.0
**Last Updated**: 2025-11-17 16:45

## How to Update Version

When you make significant changes to the application, update the version to reflect the update time in the UI.

### Steps:

1. Open `business_platform/settings.py`

2. Update the version constants:
   ```python
   # Application Version
   APP_VERSION = '1.2.0'  # Change to new version (e.g., '1.3.0')
   APP_VERSION_DATE = '2025-11-17 16:45'  # Change to current date/time
   ```

3. Save the file

4. Restart the Django server (if running):
   ```bash
   # The server will auto-reload if DEBUG=True
   # Or manually restart:
   python manage.py runserver
   ```

5. The "Updated" badge in the Gantt chart will now show the new date/time

## Version Format

- **APP_VERSION**: Semantic versioning (MAJOR.MINOR.PATCH)
  - MAJOR: Breaking changes
  - MINOR: New features (backwards compatible)
  - PATCH: Bug fixes

- **APP_VERSION_DATE**: Format `YYYY-MM-DD HH:MM`
  - Example: `2025-11-17 16:45`

## Where Version is Displayed

- Gantt Chart header: "✓ Updated [DATE/TIME]"
- Hover tooltip shows version number
- Available in all templates via `{{ APP_VERSION }}` and `{{ APP_VERSION_DATE }}`

## Example Version History

```
1.2.0 - 2025-11-17 16:45
  - Added auto-scrolling task update notifications
  - Added file upload to Gantt task editor
  - Added maintenance mode system

1.1.0 - 2025-11-16 14:30
  - Fixed task date persistence
  - Added search to dependencies
  - Improved Chinese text rendering

1.0.0 - 2025-11-01 10:00
  - Initial release
```

## Notes

- The version date only changes when you manually update it in settings.py
- This ensures users see when the app was last significantly updated
- No need to update for minor code changes or bug fixes unless you want to
