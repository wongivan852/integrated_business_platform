"""
Django signals for automatic attendance tracking
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.conf import settings
import logging

from .client import AttendanceClient

logger = logging.getLogger(__name__)


@receiver(user_logged_in)
def auto_clock_in(sender, request, user, **kwargs):
    """
    Automatically clock in user when they login to business platform
    ONLY if this is their FIRST login of the day (simplicity: one clock-in per day)
    """
    # Check if attendance integration is enabled
    if not getattr(settings, 'ATTENDANCE_INTEGRATION_ENABLED', True):
        return

    try:
        # Get user email
        email = user.email
        if not email:
            logger.warning(f"User {user.username} has no email, cannot auto clock-in")
            return

        # Initialize attendance client
        client = AttendanceClient()

        # Try to login to attendance system with same password
        password = request.session.get('temp_password')  # We'll store this temporarily

        if not password:
            password = getattr(settings, 'ATTENDANCE_DEFAULT_PASSWORD', 'krystal2025')

        # Login to attendance system
        auth_response = client.login_user(email, password)

        if auth_response and 'access_token' in auth_response:
            token = auth_response['access_token']

            # Store token in session for later use
            request.session['attendance_token'] = token
            request.session['attendance_user'] = auth_response.get('user', {})

            # Check if user is already clocked in today
            status = client.get_status(token)

            if status and status.get('is_clocked_in'):
                # Already clocked in today - don't create duplicate record
                logger.info(f"User {email} already clocked in today, skipping duplicate clock-in")
                request.session['attendance_clocked_in'] = True
            else:
                # First login of the day - clock in
                if client.clock_in(token):
                    logger.info(f"✅ FIRST LOGIN - Auto clock-in successful for {email}")
                    request.session['attendance_clocked_in'] = True
                else:
                    logger.warning(f"Auto clock-in failed for {email}")
        else:
            logger.warning(f"Attendance system login failed for {email}")

    except Exception as e:
        logger.error(f"Auto clock-in error: {e}")


@receiver(user_logged_out)
def auto_clock_out(sender, request, user, **kwargs):
    """
    Automatically clock out user when they logout from business platform
    This marks the LAST logout of the day (simplicity: one attendance record per day)
    """
    # Check if attendance integration is enabled
    if not getattr(settings, 'ATTENDANCE_INTEGRATION_ENABLED', True):
        return

    try:
        # Get attendance token from session
        token = request.session.get('attendance_token')

        if not token:
            logger.info("No attendance token in session, skipping auto clock-out")
            return

        # Initialize attendance client
        client = AttendanceClient()

        # Check if user is currently clocked in
        status = client.get_status(token)

        if status and status.get('is_clocked_in'):
            # User is clocked in - this is their last logout, clock them out
            if client.clock_out(token):
                logger.info(f"✅ LAST LOGOUT - Auto clock-out successful for {user.email if user else 'unknown'}")
            else:
                logger.warning(f"Auto clock-out failed for {user.email if user else 'unknown'}")
        else:
            # User not clocked in (already clocked out or never clocked in)
            logger.info(f"User {user.email if user else 'unknown'} not clocked in, skipping clock-out")

        # Clean up session
        request.session.pop('attendance_token', None)
        request.session.pop('attendance_user', None)
        request.session.pop('attendance_clocked_in', None)

    except Exception as e:
        logger.error(f"Auto clock-out error: {e}")
