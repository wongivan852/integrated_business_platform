"""
Workflow Engine for Phase 6.6
Executes workflows with triggers and actions
"""

from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import logging
import time
import requests

from .models import (
    Workflow,
    WorkflowTrigger,
    WorkflowAction,
    WorkflowExecution,
    Task,
    Project,
    Notification,
)

logger = logging.getLogger(__name__)


class WorkflowEngine:
    """
    Main workflow execution engine.
    Handles trigger evaluation and action execution.
    """

    def __init__(self):
        self.action_handlers = {
            'send_email': self.handle_send_email,
            'send_notification': self.handle_send_notification,
            'update_task': self.handle_update_task,
            'create_task': self.handle_create_task,
            'assign_task': self.handle_assign_task,
            'change_status': self.handle_change_status,
            'add_comment': self.handle_add_comment,
            'webhook': self.handle_webhook,
            'delay': self.handle_delay,
            'conditional': self.handle_conditional,
        }

    # =========================================================================
    # Main Execution Flow
    # =========================================================================

    def execute_workflow(self, workflow, context, triggered_by=None, trigger=None):
        """
        Execute a workflow with given context.

        Args:
            workflow: Workflow instance
            context: Dictionary with execution context (task, project, etc.)
            triggered_by: User who triggered the workflow
            trigger: WorkflowTrigger instance that triggered execution

        Returns:
            WorkflowExecution instance
        """
        # Create execution record
        execution = WorkflowExecution.objects.create(
            workflow=workflow,
            trigger=trigger,
            triggered_by=triggered_by,
            context=context,
            status='pending',
            max_attempts=workflow.max_retries
        )

        try:
            # Check if workflow can execute
            if not workflow.can_execute():
                execution.mark_failed('Workflow is not active')
                return execution

            # Mark as running
            execution.mark_running()
            logger.info(f'Executing workflow: {workflow.name}')

            # Get actions in order
            actions = workflow.actions.filter(is_active=True).order_by('order')

            results = []
            for action in actions:
                try:
                    # Check action condition
                    if action.condition and not self.evaluate_condition(action.condition, context):
                        logger.info(f'Skipping action {action.id}: condition not met')
                        continue

                    # Execute action
                    result = self.execute_action(action, context, execution)
                    results.append({
                        'action_id': action.id,
                        'action_type': action.action_type,
                        'success': True,
                        'result': result
                    })

                    logger.info(f'Action {action.id} executed successfully')

                except Exception as e:
                    logger.error(f'Action {action.id} failed: {str(e)}')

                    results.append({
                        'action_id': action.id,
                        'action_type': action.action_type,
                        'success': False,
                        'error': str(e)
                    })

                    # Check if should continue on error
                    if not action.continue_on_error:
                        raise

            # Mark as completed
            execution.mark_completed(result={'actions': results})
            workflow.increment_execution_count()

            logger.info(f'Workflow executed successfully: {workflow.name}')

            return execution

        except Exception as e:
            logger.exception(f'Workflow execution failed: {workflow.name}')
            execution.mark_failed(str(e))
            return execution

    def execute_action(self, action, context, execution):
        """Execute a single action"""
        handler = self.action_handlers.get(action.action_type)

        if not handler:
            raise ValueError(f'Unknown action type: {action.action_type}')

        return handler(action, context, execution)

    # =========================================================================
    # Trigger Evaluation
    # =========================================================================

    def check_triggers(self, event_type, context):
        """
        Check if any workflows should be triggered by an event.

        Args:
            event_type: Type of event (task_created, task_updated, etc.)
            context: Event context data

        Returns:
            List of triggered workflows
        """
        triggered_workflows = []

        # Find active workflows with matching triggers
        triggers = WorkflowTrigger.objects.filter(
            trigger_type=event_type,
            is_active=True,
            workflow__status='active'
        ).select_related('workflow')

        for trigger in triggers:
            # Check trigger conditions
            if trigger.check_conditions(context):
                logger.info(f'Trigger matched: {trigger.workflow.name}')

                # Execute workflow
                execution = self.execute_workflow(
                    workflow=trigger.workflow,
                    context=context,
                    trigger=trigger
                )

                triggered_workflows.append(execution)
                trigger.increment_trigger_count()

        return triggered_workflows

    def evaluate_condition(self, condition, context):
        """
        Evaluate a condition against context.

        Condition format:
        {
            'field': 'status',
            'operator': 'equals',
            'value': 'completed'
        }
        """
        if not condition:
            return True

        field = condition.get('field')
        operator = condition.get('operator', 'equals')
        expected_value = condition.get('value')

        actual_value = context.get(field)

        if operator == 'equals':
            return actual_value == expected_value
        elif operator == 'not_equals':
            return actual_value != expected_value
        elif operator == 'contains':
            return expected_value in str(actual_value)
        elif operator == 'greater_than':
            return actual_value > expected_value
        elif operator == 'less_than':
            return actual_value < expected_value
        elif operator == 'in':
            return actual_value in expected_value
        else:
            logger.warning(f'Unknown operator: {operator}')
            return False

    # =========================================================================
    # Action Handlers
    # =========================================================================

    def handle_send_email(self, action, context, execution):
        """Send email action"""
        params = action.parameters

        to_email = params.get('to')
        subject = self.replace_variables(params.get('subject', ''), context)
        message = self.replace_variables(params.get('message', ''), context)
        from_email = params.get('from', settings.DEFAULT_FROM_EMAIL)

        send_mail(
            subject=subject,
            message=message,
            from_email=from_email,
            recipient_list=[to_email],
            fail_silently=False
        )

        return {'sent': True, 'to': to_email}

    def handle_send_notification(self, action, context, execution):
        """Send notification action"""
        params = action.parameters

        user_id = params.get('user_id')
        title = self.replace_variables(params.get('title', ''), context)
        message = self.replace_variables(params.get('message', ''), context)
        notification_type = params.get('type', 'info')

        # Get task from context if available
        task = context.get('task')

        notification = Notification.objects.create(
            user_id=user_id,
            title=title,
            message=message,
            notification_type=notification_type,
            task=task if isinstance(task, Task) else None
        )

        return {'notification_id': notification.id}

    def handle_update_task(self, action, context, execution):
        """Update task action"""
        params = action.parameters

        task = context.get('task')
        if not task or not isinstance(task, Task):
            raise ValueError('No task in context')

        # Update fields
        for field, value in params.items():
            if hasattr(task, field):
                setattr(task, field, value)

        task.save()

        return {'task_id': task.id, 'updated_fields': list(params.keys())}

    def handle_create_task(self, action, context, execution):
        """Create new task action"""
        params = action.parameters

        project_id = params.get('project_id') or context.get('project_id')
        if not project_id:
            raise ValueError('No project_id specified')

        title = self.replace_variables(params.get('title', ''), context)
        description = self.replace_variables(params.get('description', ''), context)

        task = Task.objects.create(
            project_id=project_id,
            title=title,
            description=description,
            status=params.get('status', 'pending'),
            priority=params.get('priority', 'medium'),
            assignee_id=params.get('assignee_id')
        )

        return {'task_id': task.id}

    def handle_assign_task(self, action, context, execution):
        """Assign task to user action"""
        params = action.parameters

        task = context.get('task')
        if not task or not isinstance(task, Task):
            raise ValueError('No task in context')

        assignee_id = params.get('assignee_id')
        if not assignee_id:
            raise ValueError('No assignee_id specified')

        task.assignee_id = assignee_id
        task.save(update_fields=['assignee'])

        return {'task_id': task.id, 'assignee_id': assignee_id}

    def handle_change_status(self, action, context, execution):
        """Change task status action"""
        params = action.parameters

        task = context.get('task')
        if not task or not isinstance(task, Task):
            raise ValueError('No task in context')

        new_status = params.get('status')
        if not new_status:
            raise ValueError('No status specified')

        old_status = task.status
        task.status = new_status
        task.save(update_fields=['status'])

        return {
            'task_id': task.id,
            'old_status': old_status,
            'new_status': new_status
        }

    def handle_add_comment(self, action, context, execution):
        """Add comment to task action"""
        params = action.parameters

        task = context.get('task')
        if not task or not isinstance(task, Task):
            raise ValueError('No task in context')

        comment_text = self.replace_variables(params.get('comment', ''), context)

        # Add comment to task (you may need to create a Comment model)
        # For now, we'll just return success
        return {
            'task_id': task.id,
            'comment': comment_text
        }

    def handle_webhook(self, action, context, execution):
        """Call webhook action"""
        params = action.parameters

        url = params.get('url')
        method = params.get('method', 'POST')
        headers = params.get('headers', {})
        data = params.get('data', {})

        # Replace variables in data
        for key, value in data.items():
            if isinstance(value, str):
                data[key] = self.replace_variables(value, context)

        response = requests.request(
            method=method,
            url=url,
            json=data,
            headers=headers,
            timeout=30
        )

        return {
            'status_code': response.status_code,
            'response': response.text[:500]  # Truncate response
        }

    def handle_delay(self, action, context, execution):
        """Delay execution action"""
        params = action.parameters

        delay_seconds = params.get('seconds', 0)
        time.sleep(delay_seconds)

        return {'delayed': delay_seconds}

    def handle_conditional(self, action, context, execution):
        """Conditional branching action"""
        params = action.parameters

        condition = params.get('condition', {})
        true_actions = params.get('true_actions', [])
        false_actions = params.get('false_actions', [])

        # Evaluate condition
        result = self.evaluate_condition(condition, context)

        # Execute appropriate branch
        actions_to_execute = true_actions if result else false_actions

        branch_results = []
        for action_config in actions_to_execute:
            # Execute sub-action
            # (Implementation depends on action_config structure)
            pass

        return {
            'condition_result': result,
            'branch': 'true' if result else 'false',
            'actions_executed': len(branch_results)
        }

    # =========================================================================
    # Utilities
    # =========================================================================

    def replace_variables(self, text, context):
        """
        Replace variables in text with context values.

        Example:
            text = "Task {{task.title}} is due on {{task.due_date}}"
            context = {'task': task_instance}
            result = "Task My Task is due on 2024-12-31"
        """
        if not text or not isinstance(text, str):
            return text

        import re

        # Find all variables in format {{variable.path}}
        pattern = r'\{\{([^}]+)\}\}'
        matches = re.findall(pattern, text)

        for match in matches:
            path = match.strip().split('.')
            value = context

            # Navigate path
            for key in path:
                if hasattr(value, key):
                    value = getattr(value, key)
                elif isinstance(value, dict):
                    value = value.get(key)
                else:
                    value = None
                    break

            # Replace in text
            if value is not None:
                text = text.replace(f'{{{{{match}}}}}', str(value))

        return text


# Global engine instance
workflow_engine = WorkflowEngine()


# ============================================================================
# Helper Functions
# ============================================================================

def trigger_workflow_event(event_type, context, triggered_by=None):
    """
    Trigger workflows based on an event.

    Usage:
        trigger_workflow_event('task_created', {'task': task}, user)
    """
    return workflow_engine.check_triggers(event_type, context)


def execute_workflow_manually(workflow_id, context, user):
    """
    Manually execute a workflow.

    Usage:
        execute_workflow_manually(workflow.id, {'task': task}, request.user)
    """
    try:
        workflow = Workflow.objects.get(id=workflow_id)
        return workflow_engine.execute_workflow(workflow, context, triggered_by=user)
    except Workflow.DoesNotExist:
        raise ValueError(f'Workflow {workflow_id} not found')
