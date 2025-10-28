"""
REST API URL Configuration for Project Management
Defines all API endpoints using DRF routers
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)

from .viewsets import (
    ProjectViewSet,
    TaskViewSet,
    ResourceViewSet,
    NotificationViewSet,
    UserPresenceViewSet,
    ProjectTemplateViewSet,
    DashboardViewSet,
)


# Create a router and register our viewsets with it
router = DefaultRouter()

# Register viewsets with the router
router.register(r'projects', ProjectViewSet, basename='project')
router.register(r'tasks', TaskViewSet, basename='task')
router.register(r'resources', ResourceViewSet, basename='resource')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'presence', UserPresenceViewSet, basename='presence')
router.register(r'templates', ProjectTemplateViewSet, basename='template')
router.register(r'dashboard', DashboardViewSet, basename='dashboard')

app_name = 'api'

# The API URLs are now determined automatically by the router
urlpatterns = [
    # JWT Authentication endpoints
    path('auth/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/token/verify/', TokenVerifyView.as_view(), name='token_verify'),

    # API Root and router URLs
    path('', include(router.urls)),
]

"""
API Endpoint Documentation
==========================

Authentication:
--------------
POST   /api/auth/token/          - Obtain JWT access & refresh tokens
POST   /api/auth/token/refresh/  - Refresh access token
POST   /api/auth/token/verify/   - Verify token validity

Projects:
---------
GET    /api/projects/                           - List all accessible projects
POST   /api/projects/                           - Create new project
GET    /api/projects/{id}/                      - Retrieve project details
PUT    /api/projects/{id}/                      - Update project (full)
PATCH  /api/projects/{id}/                      - Update project (partial)
DELETE /api/projects/{id}/                      - Delete project
GET    /api/projects/{id}/tasks/                - List project tasks
GET    /api/projects/{id}/milestones/           - List project milestones
GET    /api/projects/{id}/statistics/           - Get project statistics
POST   /api/projects/{id}/add_member/           - Add team member
POST   /api/projects/{id}/remove_member/        - Remove team member

Query Parameters for Projects:
  - status: Filter by status (planning, active, on_hold, completed, cancelled)
  - priority: Filter by priority (low, medium, high, critical)
  - owner: Filter by owner ID
  - search: Search in name, description, project_code
  - ordering: Order by created_at, start_date, end_date, progress_percentage

Tasks:
------
GET    /api/tasks/                              - List all accessible tasks
POST   /api/tasks/                              - Create new task
GET    /api/tasks/{id}/                         - Retrieve task details
PUT    /api/tasks/{id}/                         - Update task (full)
PATCH  /api/tasks/{id}/                         - Update task (partial)
DELETE /api/tasks/{id}/                         - Delete task
POST   /api/tasks/{id}/assign/                  - Assign task to user
POST   /api/tasks/{id}/update_status/           - Update task status
GET    /api/tasks/my_tasks/                     - Get current user's tasks
GET    /api/tasks/overdue/                      - Get overdue tasks

Query Parameters for Tasks:
  - status: Filter by status (pending, in_progress, completed, cancelled)
  - priority: Filter by priority (low, medium, high, critical)
  - project: Filter by project ID
  - assignee: Filter by assignee ID
  - search: Search in title, description
  - ordering: Order by created_at, due_date, priority, status

Milestones:
-----------
GET    /api/milestones/                         - List all accessible milestones
POST   /api/milestones/                         - Create new milestone
GET    /api/milestones/{id}/                    - Retrieve milestone details
PUT    /api/milestones/{id}/                    - Update milestone (full)
PATCH  /api/milestones/{id}/                    - Update milestone (partial)
DELETE /api/milestones/{id}/                    - Delete milestone

Query Parameters for Milestones:
  - project: Filter by project ID
  - status: Filter by status
  - ordering: Order by due_date, created_at

Resources:
----------
GET    /api/resources/                          - List all resources
POST   /api/resources/                          - Create new resource
GET    /api/resources/{id}/                     - Retrieve resource details
PUT    /api/resources/{id}/                     - Update resource (full)
PATCH  /api/resources/{id}/                     - Update resource (partial)
DELETE /api/resources/{id}/                     - Delete resource
GET    /api/resources/available/                - Get available resources

Query Parameters for Resources:
  - is_active: Filter by active status
  - role: Filter by role
  - search: Search in username, role, skills
  - ordering: Order by hourly_rate, availability_hours

Notifications:
--------------
GET    /api/notifications/                      - List user's notifications
GET    /api/notifications/{id}/                 - Retrieve notification details
DELETE /api/notifications/{id}/                 - Delete notification
POST   /api/notifications/{id}/mark_read/       - Mark notification as read
POST   /api/notifications/mark_all_read/        - Mark all as read
GET    /api/notifications/unread/               - Get unread notifications
GET    /api/notifications/unread_count/         - Get unread count

Query Parameters for Notifications:
  - is_read: Filter by read status (true/false)
  - notification_type: Filter by type
  - ordering: Order by created_at (default: -created_at)

User Presence:
--------------
GET    /api/presence/                           - List presence records
GET    /api/presence/{id}/                      - Retrieve presence details
GET    /api/presence/online/                    - Get currently online users

Query Parameters for Presence:
  - project: Filter by project ID
  - is_online: Filter by online status (true/false)

Project Templates:
------------------
GET    /api/templates/                          - List all accessible templates
POST   /api/templates/                          - Create new template
GET    /api/templates/{id}/                     - Retrieve template details
PUT    /api/templates/{id}/                     - Update template (full)
PATCH  /api/templates/{id}/                     - Update template (partial)
DELETE /api/templates/{id}/                     - Delete template
POST   /api/templates/{id}/use_template/        - Create project from template

Query Parameters for Templates:
  - category: Filter by category
  - is_public: Filter by public status (true/false)
  - search: Search in name, description
  - ordering: Order by created_at (default: -created_at)

Dashboard:
----------
GET    /api/dashboard/statistics/               - Get overall dashboard statistics

Response Format:
----------------
Success Response:
{
    "count": 25,
    "next": "http://example.com/api/projects/?page=2",
    "previous": null,
    "results": [...]
}

Error Response:
{
    "detail": "Error message here"
}

or

{
    "field_name": ["Error message for this field"]
}

Authentication:
--------------
All endpoints require authentication via JWT tokens.

To authenticate:
1. Obtain tokens: POST /api/auth/token/ with username and password
2. Use access token in Authorization header: "Bearer <access_token>"
3. Refresh token when expired: POST /api/auth/token/refresh/

Example:
--------
# Get access token
POST /api/auth/token/
{
    "username": "john",
    "password": "securepass123"
}

Response:
{
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}

# Use token in requests
GET /api/projects/
Headers:
    Authorization: Bearer eyJ0eXAiOiJKV1QiLCJhbGc...

Pagination:
-----------
All list endpoints are paginated. Default page size is 25 items.
Use ?page=2 to access next page.

Filtering & Search:
-------------------
# Filter by status
GET /api/projects/?status=active

# Search
GET /api/projects/?search=website

# Ordering
GET /api/projects/?ordering=-created_at

# Multiple filters
GET /api/tasks/?status=in_progress&priority=high&assignee=5

Rate Limiting:
--------------
API requests are rate limited to:
- Authenticated users: 1000 requests/hour
- Anonymous users: 100 requests/hour

Versioning:
-----------
Current API version: v1
Future versions will be accessible via: /api/v2/...
"""
