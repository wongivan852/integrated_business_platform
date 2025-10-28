/**
 * Real-Time UI Helper Functions
 * Provides UI update functions for WebSocket events
 */

/**
 * Show toast notification
 * @param {string} message - Notification message
 * @param {string} type - Notification type (success, error, warning, info)
 * @param {number} duration - Duration in milliseconds (default: 5000)
 */
function showToast(message, type = 'info', duration = 5000) {
    // Create toast container if it doesn't exist
    let container = document.getElementById('toast-container');
    if (!container) {
        container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    // Create toast element
    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;

    // Icon based on type
    const icons = {
        success: '✓',
        error: '✕',
        warning: '⚠',
        info: 'ℹ'
    };

    toast.innerHTML = `
        <div class="toast-icon">${icons[type] || icons.info}</div>
        <div class="toast-content">
            <div class="toast-message">${message}</div>
        </div>
        <button class="toast-close" onclick="this.parentElement.remove()">×</button>
    `;

    // Add to container
    container.appendChild(toast);

    // Auto-remove after duration
    setTimeout(() => {
        toast.style.animation = 'toast-slide-out 0.3s ease-out';
        setTimeout(() => toast.remove(), 300);
    }, duration);
}

/**
 * Update presence indicators
 * @param {number} projectId - Project ID
 */
async function updatePresenceIndicators(projectId) {
    try {
        const response = await fetch(`/project-management/projects/${projectId}/presence/`);
        const data = await response.json();

        const container = document.getElementById('presence-indicators');
        if (!container) return;

        // Clear existing indicators
        container.innerHTML = '';

        // Add online users
        data.online_users.forEach(user => {
            const indicator = document.createElement('div');
            indicator.className = 'presence-item';
            indicator.dataset.userId = user.id;
            indicator.innerHTML = `
                <img src="${user.avatar || '/static/images/default-avatar.png'}"
                     class="presence-avatar"
                     alt="${user.username}">
                <span class="presence-status online"></span>
                <span class="presence-name">${user.username}</span>
            `;
            container.appendChild(indicator);
        });

        // Add count
        const count = document.createElement('span');
        count.className = 'presence-count';
        count.textContent = `${data.online_users.length} online`;
        container.appendChild(count);

    } catch (error) {
        console.error('Error updating presence indicators:', error);
    }
}

/**
 * Add task to list
 * @param {Object} task - Task object
 */
function addTaskToList(task) {
    const taskList = document.getElementById('task-list');
    if (!taskList) return;

    const taskElement = createTaskElement(task);
    taskElement.classList.add('new');

    // Add to beginning of list
    if (taskList.firstChild) {
        taskList.insertBefore(taskElement, taskList.firstChild);
    } else {
        taskList.appendChild(taskElement);
    }

    // Remove 'new' class after animation
    setTimeout(() => taskElement.classList.remove('new'), 2000);
}

/**
 * Update task in list
 * @param {Object} task - Task object
 */
function updateTaskInList(task) {
    const taskElement = document.querySelector(`[data-task-id="${task.id}"]`);
    if (!taskElement) return;

    // Highlight the update
    taskElement.classList.add('updated');
    setTimeout(() => taskElement.classList.remove('updated'), 2000);

    // Update task fields
    const titleElement = taskElement.querySelector('.task-title');
    if (titleElement) titleElement.textContent = task.title;

    const statusElement = taskElement.querySelector('.task-status');
    if (statusElement) {
        statusElement.textContent = task.status;
        statusElement.className = `task-status status-${task.status.toLowerCase()}`;
    }

    const priorityElement = taskElement.querySelector('.task-priority');
    if (priorityElement) {
        priorityElement.textContent = task.priority;
        priorityElement.className = `task-priority priority-${task.priority.toLowerCase()}`;
    }
}

/**
 * Create task element
 * @param {Object} task - Task object
 * @returns {HTMLElement} Task element
 */
function createTaskElement(task) {
    const div = document.createElement('div');
    div.className = 'task-item';
    div.dataset.taskId = task.id;
    div.innerHTML = `
        <div class="task-header">
            <h4 class="task-title">${task.title}</h4>
            <span class="task-status status-${task.status.toLowerCase()}">${task.status}</span>
        </div>
        <div class="task-meta">
            <span class="task-priority priority-${task.priority.toLowerCase()}">${task.priority}</span>
            ${task.assignee ? `<span class="task-assignee">${task.assignee.username}</span>` : ''}
            ${task.due_date ? `<span class="task-due-date">${task.due_date}</span>` : ''}
        </div>
    `;
    return div;
}

/**
 * Update task details page
 * @param {Object} task - Task object
 */
function updateTaskDetails(task) {
    // Update title
    const titleElement = document.getElementById('task-title');
    if (titleElement) titleElement.textContent = task.title;

    // Update status
    const statusElement = document.getElementById('task-status');
    if (statusElement) {
        statusElement.textContent = task.status;
        statusElement.className = `badge bg-${getStatusColor(task.status)}`;
    }

    // Update priority
    const priorityElement = document.getElementById('task-priority');
    if (priorityElement) {
        priorityElement.textContent = task.priority;
        priorityElement.className = `badge bg-${getPriorityColor(task.priority)}`;
    }

    // Update description
    const descriptionElement = document.getElementById('task-description');
    if (descriptionElement) descriptionElement.textContent = task.description;

    // Show update notification
    showToast('Task has been updated', 'info');
}

/**
 * Add comment to list
 * @param {Object} comment - Comment object
 */
function addCommentToList(comment) {
    const commentList = document.getElementById('comment-list');
    if (!commentList) return;

    const commentElement = document.createElement('div');
    commentElement.className = 'comment-item new';
    commentElement.dataset.commentId = comment.id;
    commentElement.innerHTML = `
        <div class="comment-header">
            <img src="${comment.user.avatar || '/static/images/default-avatar.png'}"
                 class="comment-avatar"
                 alt="${comment.user.username}">
            <div class="comment-meta">
                <strong>${comment.user.username}</strong>
                <span class="comment-time">Just now</span>
            </div>
        </div>
        <div class="comment-body">${comment.content}</div>
    `;

    // Add to end of list
    commentList.appendChild(commentElement);

    // Scroll to new comment
    commentElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });

    // Remove 'new' class after animation
    setTimeout(() => commentElement.classList.remove('new'), 2000);
}

/**
 * Update task assignment
 * @param {Object} data - Assignment data
 */
function updateTaskAssignment(data) {
    const assigneeElement = document.getElementById('task-assignee');
    if (!assigneeElement) return;

    assigneeElement.innerHTML = `
        <img src="${data.assigned_to.avatar || '/static/images/default-avatar.png'}"
             class="assignee-avatar"
             alt="${data.assigned_to.username}">
        <span>${data.assigned_to.username}</span>
    `;
}

/**
 * Add notification to list
 * @param {Object} notification - Notification object
 */
function addNotificationToList(notification) {
    const notificationList = document.getElementById('notification-list');
    if (!notificationList) return;

    const notificationElement = document.createElement('div');
    notificationElement.className = 'notification-item unread new';
    notificationElement.dataset.notificationId = notification.id;
    notificationElement.innerHTML = `
        <div class="notification-icon notification-${notification.type}">
            ${getNotificationIcon(notification.type)}
        </div>
        <div class="notification-content">
            <div class="notification-title">${notification.title}</div>
            <div class="notification-message">${notification.message}</div>
            <div class="notification-time">Just now</div>
        </div>
    `;

    // Add click handler
    notificationElement.addEventListener('click', () => {
        if (notification.action_url) {
            window.location.href = notification.action_url;
        }
    });

    // Add to beginning of list
    if (notificationList.firstChild) {
        notificationList.insertBefore(notificationElement, notificationList.firstChild);
    } else {
        notificationList.appendChild(notificationElement);
    }

    // Remove 'new' class after animation
    setTimeout(() => notificationElement.classList.remove('new'), 2000);
}

/**
 * Reload project data
 */
async function reloadProjectData() {
    // Reload project statistics or refresh the page section
    const projectId = document.body.dataset.projectId;
    if (!projectId) return;

    try {
        const response = await fetch(`/project-management/projects/${projectId}/api/data/`);
        const data = await response.json();

        // Update project statistics
        updateProjectStatistics(data);
    } catch (error) {
        console.error('Error reloading project data:', error);
    }
}

/**
 * Update project statistics
 * @param {Object} data - Project data
 */
function updateProjectStatistics(data) {
    // Update task counts
    const totalTasksElement = document.getElementById('total-tasks');
    if (totalTasksElement) totalTasksElement.textContent = data.total_tasks;

    const completedTasksElement = document.getElementById('completed-tasks');
    if (completedTasksElement) completedTasksElement.textContent = data.completed_tasks;

    // Update progress bar
    const progressBar = document.getElementById('project-progress-bar');
    if (progressBar) {
        progressBar.style.width = `${data.progress_percentage}%`;
        progressBar.textContent = `${data.progress_percentage}%`;
    }
}

/**
 * Get status color class
 * @param {string} status - Status value
 * @returns {string} Bootstrap color class
 */
function getStatusColor(status) {
    const colors = {
        'pending': 'secondary',
        'in_progress': 'primary',
        'completed': 'success',
        'on_hold': 'warning',
        'cancelled': 'danger'
    };
    return colors[status.toLowerCase()] || 'secondary';
}

/**
 * Get priority color class
 * @param {string} priority - Priority value
 * @returns {string} Bootstrap color class
 */
function getPriorityColor(priority) {
    const colors = {
        'low': 'success',
        'medium': 'info',
        'high': 'warning',
        'critical': 'danger'
    };
    return colors[priority.toLowerCase()] || 'secondary';
}

/**
 * Get notification icon
 * @param {string} type - Notification type
 * @returns {string} Icon HTML
 */
function getNotificationIcon(type) {
    const icons = {
        'task_assigned': '📋',
        'task_updated': '✏️',
        'task_completed': '✅',
        'comment_added': '💬',
        'project_updated': '📁',
        'milestone_reached': '🎯',
        'deadline_approaching': '⏰',
        'budget_alert': '💰',
        'team_member_added': '👥',
        'resource_assigned': '🔧'
    };
    return icons[type] || '📢';
}

/**
 * Request browser notification permission
 */
async function requestNotificationPermission() {
    if ('Notification' in window && Notification.permission === 'default') {
        try {
            const permission = await Notification.requestPermission();
            if (permission === 'granted') {
                showToast('Browser notifications enabled', 'success');
            }
        } catch (error) {
            console.error('Error requesting notification permission:', error);
        }
    }
}

// Request notification permission on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        // Request permission after 3 seconds to avoid interrupting user
        setTimeout(requestNotificationPermission, 3000);
    });
} else {
    setTimeout(requestNotificationPermission, 3000);
}

// Expose functions globally
window.showToast = showToast;
window.updatePresenceIndicators = updatePresenceIndicators;
window.addTaskToList = addTaskToList;
window.updateTaskInList = updateTaskInList;
window.updateTaskDetails = updateTaskDetails;
window.addCommentToList = addCommentToList;
window.updateTaskAssignment = updateTaskAssignment;
window.addNotificationToList = addNotificationToList;
window.reloadProjectData = reloadProjectData;
