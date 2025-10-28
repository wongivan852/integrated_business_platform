"""
Third-Party Integrations Package for Phase 6.4
Provides integration handlers for GitHub, Slack, Jira, and Calendar services
"""

from .base import BaseIntegration, IntegrationError
from .github_integration import GitHubIntegration
from .slack_integration import SlackIntegration
from .jira_integration import JiraIntegration


__all__ = [
    'BaseIntegration',
    'IntegrationError',
    'GitHubIntegration',
    'SlackIntegration',
    'JiraIntegration',
]
