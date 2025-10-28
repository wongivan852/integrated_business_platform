/**
 * WebSocket Client for Real-Time Collaboration
 * Handles WebSocket connections, reconnection, and real-time updates
 */

class WebSocketClient {
    /**
     * Base WebSocket client with reconnection and heartbeat
     * @param {string} url - WebSocket URL
     * @param {Object} options - Configuration options
     */
    constructor(url, options = {}) {
        this.url = url;
        this.ws = null;
        this.reconnectInterval = options.reconnectInterval || 3000;
        this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
        this.reconnectAttempts = 0;
        this.heartbeatInterval = options.heartbeatInterval || 30000;
        this.heartbeatTimer = null;
        this.isConnected = false;
        this.eventHandlers = {};
        this.reconnectTimer = null;
        this.shouldReconnect = true;
    }

    /**
     * Connect to WebSocket server
     */
    connect() {
        try {
            // Construct WebSocket URL
            const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
            const wsUrl = `${protocol}//${window.location.host}${this.url}`;

            console.log(`[WebSocket] Connecting to ${wsUrl}...`);
            this.ws = new WebSocket(wsUrl);

            // Connection opened
            this.ws.onopen = (event) => {
                console.log('[WebSocket] Connected successfully');
                this.isConnected = true;
                this.reconnectAttempts = 0;
                this.startHeartbeat();
                this.trigger('open', event);
            };

            // Listen for messages
            this.ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    console.log('[WebSocket] Message received:', data);

                    // Handle pong response
                    if (data.type === 'pong') {
                        console.log('[WebSocket] Heartbeat received');
                        return;
                    }

                    // Trigger event handlers
                    this.trigger(data.type, data);
                    this.trigger('message', data);
                } catch (error) {
                    console.error('[WebSocket] Error parsing message:', error);
                }
            };

            // Connection closed
            this.ws.onclose = (event) => {
                console.log('[WebSocket] Connection closed', event);
                this.isConnected = false;
                this.stopHeartbeat();
                this.trigger('close', event);

                // Attempt reconnection
                if (this.shouldReconnect && this.reconnectAttempts < this.maxReconnectAttempts) {
                    this.reconnect();
                }
            };

            // Connection error
            this.ws.onerror = (error) => {
                console.error('[WebSocket] Error:', error);
                this.trigger('error', error);
            };

        } catch (error) {
            console.error('[WebSocket] Connection error:', error);
            this.reconnect();
        }
    }

    /**
     * Send message to server
     * @param {Object} data - Data to send
     */
    send(data) {
        if (this.isConnected && this.ws.readyState === WebSocket.OPEN) {
            const message = typeof data === 'string' ? data : JSON.stringify(data);
            this.ws.send(message);
            console.log('[WebSocket] Message sent:', data);
        } else {
            console.warn('[WebSocket] Cannot send message - not connected');
        }
    }

    /**
     * Close WebSocket connection
     */
    close() {
        this.shouldReconnect = false;
        this.stopHeartbeat();
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }
        if (this.ws) {
            this.ws.close();
        }
    }

    /**
     * Reconnect to WebSocket server
     */
    reconnect() {
        if (this.reconnectTimer) {
            clearTimeout(this.reconnectTimer);
        }

        this.reconnectAttempts++;
        const delay = this.reconnectInterval * Math.min(this.reconnectAttempts, 5);

        console.log(`[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);

        this.reconnectTimer = setTimeout(() => {
            this.connect();
        }, delay);
    }

    /**
     * Start heartbeat (ping/pong)
     */
    startHeartbeat() {
        this.stopHeartbeat();
        this.heartbeatTimer = setInterval(() => {
            this.send({ type: 'ping' });
        }, this.heartbeatInterval);
    }

    /**
     * Stop heartbeat
     */
    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }

    /**
     * Register event handler
     * @param {string} eventType - Event type
     * @param {Function} callback - Callback function
     */
    on(eventType, callback) {
        if (!this.eventHandlers[eventType]) {
            this.eventHandlers[eventType] = [];
        }
        this.eventHandlers[eventType].push(callback);
    }

    /**
     * Unregister event handler
     * @param {string} eventType - Event type
     * @param {Function} callback - Callback function
     */
    off(eventType, callback) {
        if (this.eventHandlers[eventType]) {
            this.eventHandlers[eventType] = this.eventHandlers[eventType].filter(
                handler => handler !== callback
            );
        }
    }

    /**
     * Trigger event handlers
     * @param {string} eventType - Event type
     * @param {*} data - Event data
     */
    trigger(eventType, data) {
        if (this.eventHandlers[eventType]) {
            this.eventHandlers[eventType].forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    console.error(`[WebSocket] Error in ${eventType} handler:`, error);
                }
            });
        }
    }
}


/**
 * Project WebSocket Manager
 * Handles project-level real-time updates
 */
class ProjectWebSocket extends WebSocketClient {
    constructor(projectId) {
        super(`/ws/projects/${projectId}/`);
        this.projectId = projectId;
        this.setupHandlers();
    }

    setupHandlers() {
        this.on('connection_established', (data) => {
            console.log('[ProjectWS] Connected to project', data.project_id);
            this.updatePresence();
        });

        this.on('user_joined', (data) => {
            console.log('[ProjectWS] User joined:', data.username);
            this.showNotification(`${data.username} joined the project`, 'info');
            this.updateOnlineUsers();
        });

        this.on('user_left', (data) => {
            console.log('[ProjectWS] User left:', data.username);
            this.updateOnlineUsers();
        });

        this.on('project_updated', (data) => {
            console.log('[ProjectWS] Project updated:', data);
            this.handleProjectUpdate(data);
        });

        this.on('task_created', (data) => {
            console.log('[ProjectWS] Task created:', data);
            this.handleTaskCreated(data);
        });

        this.on('task_updated', (data) => {
            console.log('[ProjectWS] Task updated:', data);
            this.handleTaskUpdated(data);
        });
    }

    updatePresence() {
        const currentPage = window.location.pathname;
        this.send({
            type: 'update_presence',
            page: currentPage
        });
    }

    handleProjectUpdate(data) {
        // Update project information in UI
        const changes = data.changes || {};
        let message = `${data.updated_by.username} updated the project`;

        if (changes.status) {
            message = `${data.updated_by.username} changed project status to ${changes.new_value}`;
        }

        this.showNotification(message, 'info');

        // Reload project data if needed
        if (typeof window.reloadProjectData === 'function') {
            window.reloadProjectData();
        }
    }

    handleTaskCreated(data) {
        const message = `${data.created_by.username} created task: ${data.task.title}`;
        this.showNotification(message, 'success');

        // Add task to task list
        if (typeof window.addTaskToList === 'function') {
            window.addTaskToList(data.task);
        }
    }

    handleTaskUpdated(data) {
        const message = `${data.updated_by.username} updated task: ${data.task.title}`;
        this.showNotification(message, 'info');

        // Update task in UI
        if (typeof window.updateTaskInList === 'function') {
            window.updateTaskInList(data.task);
        }
    }

    updateOnlineUsers() {
        // Fetch and update online users list
        if (typeof window.updatePresenceIndicators === 'function') {
            window.updatePresenceIndicators(this.projectId);
        }
    }

    showNotification(message, type = 'info') {
        // Show toast notification
        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
        } else {
            console.log(`[Notification] ${message}`);
        }
    }
}


/**
 * Task WebSocket Manager
 * Handles task-level real-time updates
 */
class TaskWebSocket extends WebSocketClient {
    constructor(taskId) {
        super(`/ws/tasks/${taskId}/`);
        this.taskId = taskId;
        this.typingTimer = null;
        this.setupHandlers();
    }

    setupHandlers() {
        this.on('connection_established', (data) => {
            console.log('[TaskWS] Connected to task', data.task_id);
        });

        this.on('task_updated', (data) => {
            console.log('[TaskWS] Task updated:', data);
            this.handleTaskUpdate(data);
        });

        this.on('comment_added', (data) => {
            console.log('[TaskWS] Comment added:', data);
            this.handleCommentAdded(data);
        });

        this.on('user_typing', (data) => {
            console.log('[TaskWS] User typing:', data);
            this.handleUserTyping(data);
        });

        this.on('task_assigned', (data) => {
            console.log('[TaskWS] Task assigned:', data);
            this.handleTaskAssigned(data);
        });
    }

    handleTaskUpdate(data) {
        // Update task details in UI
        if (typeof window.updateTaskDetails === 'function') {
            window.updateTaskDetails(data.task);
        }

        const message = `${data.updated_by.username} updated this task`;
        this.showNotification(message, 'info');
    }

    handleCommentAdded(data) {
        // Add comment to comment list
        if (typeof window.addCommentToList === 'function') {
            window.addCommentToList(data.comment);
        }
    }

    handleUserTyping(data) {
        // Show typing indicator
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            if (data.is_typing) {
                indicator.textContent = `${data.username} is typing...`;
                indicator.style.display = 'block';
            } else {
                indicator.style.display = 'none';
            }
        }
    }

    handleTaskAssigned(data) {
        const message = `Task assigned to ${data.assigned_to.username}`;
        this.showNotification(message, 'success');

        if (typeof window.updateTaskAssignment === 'function') {
            window.updateTaskAssignment(data);
        }
    }

    sendTypingIndicator(isTyping) {
        this.send({
            type: 'typing',
            is_typing: isTyping
        });
    }

    startTyping() {
        if (this.typingTimer) {
            clearTimeout(this.typingTimer);
        }

        this.sendTypingIndicator(true);

        this.typingTimer = setTimeout(() => {
            this.sendTypingIndicator(false);
        }, 3000);
    }

    showNotification(message, type = 'info') {
        if (typeof window.showToast === 'function') {
            window.showToast(message, type);
        } else {
            console.log(`[Notification] ${message}`);
        }
    }
}


/**
 * Notification WebSocket Manager
 * Handles user-level notifications
 */
class NotificationWebSocket extends WebSocketClient {
    constructor() {
        super('/ws/notifications/');
        this.setupHandlers();
    }

    setupHandlers() {
        this.on('connection_established', (data) => {
            console.log('[NotificationWS] Connected');
        });

        this.on('new_notification', (data) => {
            console.log('[NotificationWS] New notification:', data);
            this.handleNewNotification(data);
        });

        this.on('notification_read', (data) => {
            console.log('[NotificationWS] Notification read:', data);
            this.handleNotificationRead(data);
        });

        this.on('unread_count', (data) => {
            console.log('[NotificationWS] Unread count:', data.count);
            this.updateUnreadCount(data.count);
        });
    }

    handleNewNotification(data) {
        // Show notification popup
        this.showNotificationPopup(data.notification);

        // Update notification list
        if (typeof window.addNotificationToList === 'function') {
            window.addNotificationToList(data.notification);
        }

        // Update unread count
        this.incrementUnreadCount();

        // Play notification sound
        this.playNotificationSound();
    }

    handleNotificationRead(data) {
        // Update notification UI
        const notificationElement = document.querySelector(`[data-notification-id="${data.notification_id}"]`);
        if (notificationElement) {
            notificationElement.classList.remove('unread');
            notificationElement.classList.add('read');
        }

        // Decrement unread count
        this.decrementUnreadCount();
    }

    updateUnreadCount(count) {
        const badge = document.getElementById('notification-badge');
        if (badge) {
            if (count > 0) {
                badge.textContent = count > 99 ? '99+' : count;
                badge.style.display = 'inline-block';
            } else {
                badge.style.display = 'none';
            }
        }
    }

    incrementUnreadCount() {
        const badge = document.getElementById('notification-badge');
        if (badge) {
            const currentCount = parseInt(badge.textContent) || 0;
            this.updateUnreadCount(currentCount + 1);
        }
    }

    decrementUnreadCount() {
        const badge = document.getElementById('notification-badge');
        if (badge) {
            const currentCount = parseInt(badge.textContent) || 0;
            this.updateUnreadCount(Math.max(0, currentCount - 1));
        }
    }

    showNotificationPopup(notification) {
        // Create toast notification
        if (typeof window.showToast === 'function') {
            window.showToast(notification.title, 'info');
        }

        // Browser notification (if permission granted)
        if ('Notification' in window && Notification.permission === 'granted') {
            new Notification(notification.title, {
                body: notification.message,
                icon: '/static/images/logo.png'
            });
        }
    }

    playNotificationSound() {
        // Play notification sound
        const audio = new Audio('/static/sounds/notification.mp3');
        audio.volume = 0.3;
        audio.play().catch(err => console.log('Cannot play sound:', err));
    }

    markAsRead(notificationId) {
        this.send({
            type: 'mark_read',
            notification_id: notificationId
        });
    }
}


// Global WebSocket instances
window.projectWebSocket = null;
window.taskWebSocket = null;
window.notificationWebSocket = null;

/**
 * Initialize WebSocket connections
 */
function initializeWebSockets() {
    // Initialize notification WebSocket for all authenticated users
    if (document.body.dataset.userId) {
        window.notificationWebSocket = new NotificationWebSocket();
        window.notificationWebSocket.connect();
    }

    // Initialize project WebSocket if on project page
    const projectId = document.body.dataset.projectId;
    if (projectId) {
        window.projectWebSocket = new ProjectWebSocket(projectId);
        window.projectWebSocket.connect();
    }

    // Initialize task WebSocket if on task page
    const taskId = document.body.dataset.taskId;
    if (taskId) {
        window.taskWebSocket = new TaskWebSocket(taskId);
        window.taskWebSocket.connect();
    }
}

// Initialize on page load
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeWebSockets);
} else {
    initializeWebSockets();
}

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    if (window.projectWebSocket) {
        window.projectWebSocket.close();
    }
    if (window.taskWebSocket) {
        window.taskWebSocket.close();
    }
    if (window.notificationWebSocket) {
        window.notificationWebSocket.close();
    }
});
