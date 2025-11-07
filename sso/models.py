"""SSO models for tracking tokens and sessions."""
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import timedelta


class SSOToken(models.Model):
    """Track issued SSO tokens for audit and revocation."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sso_tokens'
    )
    jti = models.CharField(max_length=255, unique=True, db_index=True)  # JWT ID
    token = models.TextField()  # Store the actual token (encrypted in production)
    refresh_token = models.TextField(blank=True)

    # Token metadata
    issued_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    last_used = models.DateTimeField(auto_now=True)

    # Request metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_revoked = models.BooleanField(default=False)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revocation_reason = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-issued_at']
        verbose_name = 'SSO Token'
        verbose_name_plural = 'SSO Tokens'
        indexes = [
            models.Index(fields=['jti', 'is_active']),
            models.Index(fields=['user', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.jti[:8]}..."

    def is_valid(self):
        """Check if token is still valid."""
        if self.is_revoked or not self.is_active:
            return False
        if self.expires_at < timezone.now():
            return False
        return True

    def revoke(self, reason="Manual revocation"):
        """Revoke this token."""
        self.is_active = False
        self.is_revoked = True
        self.revoked_at = timezone.now()
        self.revocation_reason = reason
        self.save()

    @classmethod
    def revoke_user_tokens(cls, user):
        """Revoke all tokens for a user."""
        cls.objects.filter(user=user, is_active=True).update(
            is_active=False,
            is_revoked=True,
            revoked_at=timezone.now(),
            revocation_reason="User logout/deactivation"
        )

    @classmethod
    def cleanup_expired(cls):
        """Remove expired tokens (call periodically)."""
        expired_cutoff = timezone.now() - timedelta(days=7)
        cls.objects.filter(expires_at__lt=expired_cutoff).delete()


class SSOSession(models.Model):
    """Track active SSO sessions across applications."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sso_app_sessions'
    )
    token = models.ForeignKey(
        SSOToken,
        on_delete=models.CASCADE,
        related_name='sessions'
    )

    # Application info
    app_name = models.CharField(max_length=100)
    app_url = models.URLField(max_length=500)

    # Session metadata
    started_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)

    # Request metadata
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()

    # Status
    is_active = models.BooleanField(default=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-started_at']
        verbose_name = 'SSO Session'
        verbose_name_plural = 'SSO Sessions'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['token', 'is_active']),
        ]

    def __str__(self):
        return f"{self.user.username} @ {self.app_name}"

    def end_session(self):
        """End this session."""
        self.is_active = False
        self.ended_at = timezone.now()
        self.save()

    @classmethod
    def end_user_sessions(cls, user):
        """End all active sessions for a user."""
        cls.objects.filter(user=user, is_active=True).update(
            is_active=False,
            ended_at=timezone.now()
        )


class SSOAuditLog(models.Model):
    """Audit log for SSO events."""

    EVENT_TYPES = [
        ('token_issued', 'Token Issued'),
        ('token_validated', 'Token Validated'),
        ('token_refreshed', 'Token Refreshed'),
        ('token_revoked', 'Token Revoked'),
        ('login_success', 'Login Success'),
        ('login_failed', 'Login Failed'),
        ('logout', 'Logout'),
        ('permission_denied', 'Permission Denied'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sso_audit_logs'
    )

    event_type = models.CharField(max_length=50, choices=EVENT_TYPES)
    app_name = models.CharField(max_length=100, blank=True)

    # Event details
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    details = models.JSONField(default=dict)

    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'SSO Audit Log'
        verbose_name_plural = 'SSO Audit Logs'
        indexes = [
            models.Index(fields=['user', 'event_type', '-created_at']),
            models.Index(fields=['event_type', '-created_at']),
        ]

    def __str__(self):
        user_str = self.user.username if self.user else "Unknown"
        return f"{self.event_type} - {user_str} @ {self.created_at}"

    @classmethod
    def log_event(cls, event_type, user=None, app_name='', request=None, **details):
        """Helper method to create audit log entries."""
        ip_address = None
        user_agent = ''

        if request:
            ip_address = cls.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')

        return cls.objects.create(
            user=user,
            event_type=event_type,
            app_name=app_name,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details
        )

    @staticmethod
    def get_client_ip(request):
        """Get client IP from request."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
