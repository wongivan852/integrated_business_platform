"""
Attendance API Client
Handles communication with attendance system
"""
import requests
import logging
from django.conf import settings

logger = logging.getLogger(__name__)


class AttendanceClient:
    """Client for attendance system API"""

    def __init__(self):
        self.api_url = getattr(settings, 'ATTENDANCE_API_URL', 'http://localhost:8007')
        self.timeout = 5  # seconds

    def login_user(self, email, password):
        """
        Login to attendance system and get JWT token

        Args:
            email: User email
            password: User password

        Returns:
            dict: Token response with access_token and user info
            None: If login failed
        """
        try:
            response = requests.post(
                f"{self.api_url}/api/auth/login",
                json={"email": email, "password": password},
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Attendance login failed for {email}: {response.status_code}")
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Attendance API connection error: {e}")
            return None

    def clock_in(self, token):
        """
        Clock in user

        Args:
            token: JWT access token

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.api_url}/api/attendance/clock-in",
                headers={"Authorization": f"Bearer {token}"},
                json={"method": "manual", "device_hostname": "Business Platform"},
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.info("User clocked in successfully")
                return True
            else:
                logger.warning(f"Clock-in failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Clock-in API error: {e}")
            return False

    def clock_out(self, token):
        """
        Clock out user

        Args:
            token: JWT access token

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = requests.post(
                f"{self.api_url}/api/attendance/clock-out",
                headers={"Authorization": f"Bearer {token}"},
                json={"method": "manual"},
                timeout=self.timeout
            )

            if response.status_code == 200:
                logger.info("User clocked out successfully")
                return True
            else:
                logger.warning(f"Clock-out failed: {response.status_code}")
                return False

        except requests.exceptions.RequestException as e:
            logger.error(f"Clock-out API error: {e}")
            return False

    def get_status(self, token):
        """
        Get current attendance status

        Args:
            token: JWT access token

        Returns:
            dict: Status information
            None: If request failed
        """
        try:
            response = requests.get(
                f"{self.api_url}/api/attendance/status",
                headers={"Authorization": f"Bearer {token}"},
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Status API error: {e}")
            return None

    def get_today_records(self, token):
        """
        Get today's attendance records

        Args:
            token: JWT access token

        Returns:
            dict: Attendance records
            None: If request failed
        """
        try:
            from datetime import date
            today = date.today().isoformat()

            response = requests.get(
                f"{self.api_url}/api/attendance/daily",
                headers={"Authorization": f"Bearer {token}"},
                params={"date": today},
                timeout=self.timeout
            )

            if response.status_code == 200:
                return response.json()
            else:
                return None

        except requests.exceptions.RequestException as e:
            logger.error(f"Daily records API error: {e}")
            return None
