"""
Base Integration Class for Third-Party Services
Provides common functionality for all integrations
"""

import requests
import json
import hmac
import hashlib
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
from django.utils import timezone
from django.conf import settings


class IntegrationError(Exception):
    """Base exception for integration errors"""
    pass


class BaseIntegration(ABC):
    """
    Base class for third-party service integrations.
    All integration handlers should inherit from this class.
    """

    def __init__(self, integration):
        """
        Initialize integration with ProjectIntegration instance.

        Args:
            integration: ProjectIntegration model instance
        """
        self.integration = integration
        self.provider = integration.provider
        self.project = integration.project
        self.session = requests.Session()

    @abstractmethod
    def authenticate(self):
        """
        Authenticate with the third-party service.
        Should return True if successful, False otherwise.
        """
        pass

    @abstractmethod
    def sync_tasks(self):
        """
        Synchronize tasks between the platform and external service.
        Should handle both import and export of tasks.
        """
        pass

    @abstractmethod
    def process_webhook(self, payload, headers):
        """
        Process incoming webhook from the service.

        Args:
            payload: Webhook payload dict
            headers: HTTP headers dict

        Returns:
            dict: Processing result
        """
        pass

    def _make_request(self, method, url, **kwargs):
        """
        Make HTTP request to external API with error handling.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE)
            url: Request URL
            **kwargs: Additional request parameters

        Returns:
            Response object

        Raises:
            IntegrationError: If request fails
        """
        from ..models import IntegrationLog

        start_time = datetime.now()

        try:
            # Add authentication headers
            if 'headers' not in kwargs:
                kwargs['headers'] = {}

            kwargs['headers'].update(self._get_auth_headers())

            # Make request
            response = self.session.request(method, url, **kwargs)

            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds() * 1000

            # Log successful request
            IntegrationLog.log_action(
                action_type='api_call',
                provider=self.provider,
                description=f'{method} {url}',
                integration=self.integration,
                status='success' if response.ok else 'error',
                request_data={
                    'method': method,
                    'url': url,
                    'params': kwargs.get('params', {}),
                },
                response_data={
                    'status_code': response.status_code,
                    'body': response.text[:1000] if not response.ok else None,
                },
                duration_ms=int(duration)
            )

            response.raise_for_status()
            return response

        except requests.exceptions.RequestException as e:
            # Calculate duration
            duration = (datetime.now() - start_time).total_seconds() * 1000

            # Log error
            IntegrationLog.log_action(
                action_type='error',
                provider=self.provider,
                description=f'API request failed: {method} {url}',
                integration=self.integration,
                status='error',
                error_message=str(e),
                request_data={
                    'method': method,
                    'url': url,
                },
                duration_ms=int(duration)
            )

            raise IntegrationError(f'API request failed: {str(e)}')

    def _get_auth_headers(self):
        """
        Get authentication headers for API requests.
        Override in subclasses for specific auth methods.

        Returns:
            dict: Authentication headers
        """
        headers = {}

        if self.integration.access_token:
            headers['Authorization'] = f'Bearer {self.integration.access_token}'

        return headers

    def verify_webhook_signature(self, payload, signature, secret=None):
        """
        Verify webhook signature to ensure authenticity.

        Args:
            payload: Raw webhook payload (bytes or str)
            signature: Signature from webhook headers
            secret: Webhook secret (optional, uses provider secret if not provided)

        Returns:
            bool: True if signature is valid
        """
        if secret is None:
            secret = self.provider.webhook_secret

        if not secret:
            # No secret configured, skip verification
            return True

        if isinstance(payload, str):
            payload = payload.encode('utf-8')

        # Calculate expected signature
        expected_signature = hmac.new(
            secret.encode('utf-8'),
            payload,
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(signature, expected_signature)

    def refresh_token(self):
        """
        Refresh OAuth access token using refresh token.
        Override in subclasses for specific OAuth flows.

        Returns:
            bool: True if refresh successful
        """
        if not self.integration.refresh_token:
            return False

        try:
            response = requests.post(
                self.provider.oauth_token_url,
                data={
                    'grant_type': 'refresh_token',
                    'refresh_token': self.integration.refresh_token,
                    'client_id': self.provider.client_id,
                    'client_secret': self.provider.client_secret,
                }
            )

            if response.ok:
                data = response.json()
                self.integration.access_token = data['access_token']

                if 'refresh_token' in data:
                    self.integration.refresh_token = data['refresh_token']

                if 'expires_in' in data:
                    self.integration.token_expires_at = timezone.now() + timedelta(
                        seconds=data['expires_in']
                    )

                self.integration.save()
                return True

        except Exception as e:
            from ..models import IntegrationLog
            IntegrationLog.log_action(
                'error',
                self.provider,
                f'Token refresh failed: {str(e)}',
                integration=self.integration,
                status='error',
                error_message=str(e)
            )

        return False

    def update_sync_status(self, status, error=None):
        """
        Update integration sync status.

        Args:
            status: Sync status (success, error, syncing)
            error: Error message if status is error
        """
        self.integration.sync_status = status

        if status == 'success':
            self.integration.last_sync = timezone.now()
            self.integration.sync_error = ''
        elif status == 'error' and error:
            self.integration.sync_error = error

        self.integration.save(update_fields=['sync_status', 'last_sync', 'sync_error'])

    def map_status(self, external_status):
        """
        Map external status to internal task status.
        Override in subclasses for specific mappings.

        Args:
            external_status: Status from external service

        Returns:
            str: Internal status (pending, in_progress, completed, cancelled)
        """
        # Default mapping
        status_map = {
            'open': 'pending',
            'in progress': 'in_progress',
            'in_progress': 'in_progress',
            'done': 'completed',
            'closed': 'completed',
            'resolved': 'completed',
            'cancelled': 'cancelled',
            'canceled': 'cancelled',
        }

        return status_map.get(external_status.lower(), 'pending')

    def map_priority(self, external_priority):
        """
        Map external priority to internal task priority.

        Args:
            external_priority: Priority from external service

        Returns:
            str: Internal priority (low, medium, high, critical)
        """
        # Default mapping
        priority_map = {
            'lowest': 'low',
            'low': 'low',
            'minor': 'low',
            'medium': 'medium',
            'normal': 'medium',
            'major': 'high',
            'high': 'high',
            'highest': 'critical',
            'critical': 'critical',
            'blocker': 'critical',
        }

        if isinstance(external_priority, int):
            # Map numeric priorities (1-5)
            if external_priority <= 2:
                return 'low'
            elif external_priority == 3:
                return 'medium'
            elif external_priority == 4:
                return 'high'
            else:
                return 'critical'

        return priority_map.get(str(external_priority).lower(), 'medium')

    def create_external_task_mapping(self, task, external_id, external_key=None, external_url=None):
        """
        Create mapping between internal task and external task.

        Args:
            task: Task model instance
            external_id: External task ID
            external_key: External task key (optional)
            external_url: External task URL (optional)

        Returns:
            ExternalTaskMapping instance
        """
        from ..models import ExternalTaskMapping

        mapping, created = ExternalTaskMapping.objects.get_or_create(
            task=task,
            integration=self.integration,
            defaults={
                'external_id': external_id,
                'external_key': external_key or external_id,
                'external_url': external_url or '',
                'created_by': self.project.owner,
            }
        )

        if not created:
            # Update existing mapping
            mapping.external_id = external_id
            if external_key:
                mapping.external_key = external_key
            if external_url:
                mapping.external_url = external_url
            mapping.save()

        return mapping

    def __str__(self):
        return f'{self.provider.get_provider_type_display()} Integration for {self.project.name}'
