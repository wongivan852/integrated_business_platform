"""
URL configuration for Project Management app
"""

from django.urls import path, include
from ..views import project_views, task_views, kanban_views, gantt_views, resource_views, evm_views, template_views, analytics_views, notification_views, export_views

app_name = 'project_management'

urlpatterns = [
    # Project URLs
    path('', project_views.project_list, name='project_list'),
    path('create/', project_views.project_create, name='project_create'),
    path('<int:pk>/', project_views.project_detail, name='project_detail'),
    path('<int:pk>/edit/', project_views.project_edit, name='project_edit'),
    path('<int:pk>/delete/', project_views.project_delete, name='project_delete'),

    # Team Member Management
    path('<int:pk>/members/add/', project_views.project_add_member, name='project_add_member'),
    path('<int:pk>/members/<int:member_id>/remove/', project_views.project_remove_member, name='project_remove_member'),

    # View switching
    path('<int:pk>/gantt/', gantt_views.gantt_chart_view, name='project_gantt'),
    path('<int:pk>/kanban/', project_views.project_kanban_view, name='project_kanban'),
    path('<int:project_pk>/files/', project_views.project_file_pool, name='project_file_pool'),

    # Task URLs
    path('<int:project_pk>/tasks/', task_views.task_list, name='task_list'),
    path('<int:project_pk>/tasks/create/', task_views.task_create, name='task_create'),
    path('<int:project_pk>/tasks/<int:pk>/', task_views.task_detail, name='task_detail'),
    path('<int:project_pk>/tasks/<int:pk>/edit/', task_views.task_edit, name='task_edit'),
    path('<int:project_pk>/tasks/<int:pk>/delete/', task_views.task_delete, name='task_delete'),

    # Task Attachment URLs
    path('<int:project_pk>/tasks/<int:task_pk>/attachments/upload/', task_views.task_upload_attachment, name='task_upload_attachment'),
    path('<int:project_pk>/tasks/<int:task_pk>/attachments/<int:attachment_pk>/delete/', task_views.task_delete_attachment, name='task_delete_attachment'),

    # Task API endpoints (Kanban)
    path('<int:project_pk>/api/tasks/quick-create/', task_views.api_task_quick_create, name='api_task_quick_create'),
    path('<int:project_pk>/api/tasks/<int:pk>/move/', task_views.api_task_move, name='api_task_move'),
    path('<int:project_pk>/api/tasks/<int:pk>/update-field/', task_views.api_task_update_field, name='api_task_update_field'),

    # Kanban Column API endpoints
    path('<int:project_pk>/api/columns/create/', kanban_views.api_column_create, name='api_column_create'),
    path('<int:project_pk>/api/columns/<int:column_id>/update/', kanban_views.api_column_update, name='api_column_update'),
    path('<int:project_pk>/api/columns/<int:column_id>/delete/', kanban_views.api_column_delete, name='api_column_delete'),
    path('<int:project_pk>/api/columns/reorder/', kanban_views.api_column_reorder, name='api_column_reorder'),

    # Gantt Chart API endpoints
    path('<int:project_pk>/api/gantt/tasks/create/', gantt_views.api_create_task, name='api_gantt_create_task'),
    path('<int:project_pk>/api/gantt/tasks/<int:task_id>/check-delete/', gantt_views.api_check_task_deletion, name='api_gantt_check_delete'),
    path('<int:project_pk>/api/gantt/tasks/<int:task_id>/delete/', gantt_views.api_delete_task, name='api_gantt_delete_task'),
    path('<int:project_pk>/api/gantt/tasks/<int:task_id>/reorder/', gantt_views.api_reorder_task, name='api_gantt_reorder_task'),
    path('<int:project_pk>/api/gantt/tasks/<int:task_id>/update-dates/', gantt_views.api_update_task_dates, name='api_gantt_update_dates'),
    path('<int:project_pk>/api/gantt/tasks/<int:task_id>/update-progress/', gantt_views.api_update_task_progress, name='api_gantt_update_progress'),
    path('<int:project_pk>/api/gantt/dependencies/add/', gantt_views.api_add_dependency, name='api_gantt_add_dependency'),
    path('<int:project_pk>/api/gantt/dependencies/<int:dependency_id>/remove/', gantt_views.api_remove_dependency, name='api_gantt_remove_dependency'),
    path('<int:project_pk>/api/gantt/dependencies/remove/', gantt_views.api_remove_dependency_by_tasks, name='api_gantt_remove_dependency_by_tasks'),
    path('<int:project_pk>/api/gantt/baselines/create/', gantt_views.api_create_baseline, name='api_gantt_create_baseline'),
    path('<int:project_pk>/api/gantt/baselines/<int:baseline_id>/delete/', gantt_views.api_delete_baseline, name='api_gantt_delete_baseline'),

    # Phase 4: Resource Management URLs
    path('resources/', resource_views.resource_list, name='resource_list'),
    path('resources/<int:resource_id>/', resource_views.resource_detail, name='resource_detail'),
    path('resources/workload/', resource_views.resource_workload, name='resource_workload'),
    path('resources/capacity-report/', resource_views.resource_capacity_report, name='resource_capacity_report'),
    path('<int:pk>/resources/allocate/', resource_views.project_resource_allocation, name='project_resource_allocation'),

    # Resource API endpoints
    path('<int:project_pk>/api/resources/tasks/<int:task_id>/assign/', resource_views.api_assign_resource, name='api_assign_resource'),
    path('<int:project_pk>/api/resources/assignments/<int:assignment_id>/remove/', resource_views.api_remove_resource_assignment, name='api_remove_resource_assignment'),
    path('api/resources/availability/', resource_views.api_resource_availability, name='api_resource_availability'),

    # Phase 4: Earned Value Management (EVM) URLs
    path('<int:pk>/evm/', evm_views.evm_dashboard, name='evm_dashboard'),
    path('<int:pk>/evm/report/', evm_views.evm_report, name='evm_report'),
    path('<int:pk>/costs/', evm_views.project_costs, name='project_costs'),
    path('<int:pk>/costs/add/', evm_views.cost_entry_form, name='cost_entry_form'),
    path('<int:pk>/costs/tasks/', evm_views.task_cost_tracking, name='task_cost_tracking'),

    # EVM API endpoints
    path('<int:pk>/api/evm/snapshot/', evm_views.api_create_evm_snapshot, name='api_create_evm_snapshot'),
    path('<int:project_pk>/api/tasks/<int:task_id>/cost/', evm_views.api_update_task_cost, name='api_update_task_cost'),

    # Phase 5: Project Templates URLs
    path('templates/', template_views.template_list, name='template_list'),
    path('templates/<int:template_id>/', template_views.template_detail, name='template_detail'),
    path('templates/create/', template_views.template_create, name='template_create'),
    path('templates/<int:template_id>/edit/', template_views.template_edit, name='template_edit'),
    path('templates/<int:template_id>/delete/', template_views.template_delete, name='template_delete'),
    path('templates/<int:template_id>/use/', template_views.project_from_template, name='project_from_template'),

    # Template API endpoints
    path('<int:project_pk>/api/save-as-template/', template_views.api_save_as_template, name='api_save_as_template'),
    path('templates/<int:template_id>/api/tasks/add/', template_views.api_add_template_task, name='api_add_template_task'),
    path('templates/<int:template_id>/api/tasks/<int:task_id>/remove/', template_views.api_remove_template_task, name='api_remove_template_task'),

    # Phase 5: Analytics & Reporting URLs
    path('analytics/', analytics_views.analytics_dashboard, name='analytics_dashboard'),
    path('<int:pk>/analytics/', analytics_views.project_analytics, name='project_analytics'),
    path('analytics/portfolio/', analytics_views.portfolio_analytics, name='portfolio_analytics'),
    path('analytics/team/', analytics_views.team_performance, name='team_performance'),
    path('analytics/trends/', analytics_views.trend_analysis, name='trend_analysis'),
    path('analytics/predictions/', analytics_views.predictive_analytics, name='predictive_analytics'),

    # Dashboard Customization URLs
    path('analytics/customize/', analytics_views.customize_dashboard, name='customize_dashboard'),
    path('analytics/customize/save/', analytics_views.api_save_dashboard_layout, name='api_save_dashboard_layout'),
    path('analytics/customize/reset/', analytics_views.api_reset_dashboard_layout, name='api_reset_dashboard_layout'),

    # Phase 5: Notification URLs
    path('notifications/', notification_views.notification_list, name='notification_list'),
    path('notifications/<int:notification_id>/mark-read/', notification_views.api_mark_as_read, name='api_mark_notification_read'),
    path('notifications/mark-all-read/', notification_views.api_mark_all_as_read, name='api_mark_all_notifications_read'),
    path('notifications/<int:notification_id>/delete/', notification_views.api_delete_notification, name='api_delete_notification'),
    path('notifications/unread-count/', notification_views.api_get_unread_count, name='api_unread_count'),

    # Phase 5: Export/Reporting URLs
    path('export/projects/csv/', export_views.export_projects_csv, name='export_projects_csv'),
    path('export/projects/excel/', export_views.export_projects_excel, name='export_projects_excel'),
    path('<int:pk>/export/analytics/pdf/', export_views.export_project_analytics_pdf_view, name='export_project_analytics_pdf'),
    path('<int:project_pk>/export/tasks/csv/', export_views.export_tasks_csv, name='export_tasks_csv'),
    path('<int:project_pk>/export/tasks/excel/', export_views.export_tasks_excel_view, name='export_tasks_excel'),
    path('export/resources/allocation/', export_views.export_resource_allocation_view, name='export_resource_allocation'),
    path('export/portfolio/analytics/', export_views.export_portfolio_analytics_view, name='export_portfolio_analytics'),

    # Phase 6.4: Third-Party Integrations URLs
    path('integrations/', include('project_management.urls.integration_urls')),
]
