/**
 * PWA Application Logic
 * Phase 6.5: Mobile PWA
 *
 * Features:
 * - Service worker registration
 * - Install prompt handling
 * - Offline detection and sync
 * - Push notification management
 * - App state management
 */

class PWAApp {
    constructor() {
        this.serviceWorker = null;
        this.installPrompt = null;
        this.isOnline = navigator.onLine;
        this.syncQueue = [];
        this.db = null;

        this.init();
    }

    /**
     * Initialize PWA application
     */
    async init() {
        console.log('[PWA] Initializing application...');

        // Register service worker
        await this.registerServiceWorker();

        // Set up install prompt
        this.setupInstallPrompt();

        // Set up offline/online detection
        this.setupConnectionMonitoring();

        // Initialize IndexedDB
        await this.initDB();

        // Set up push notifications
        await this.setupPushNotifications();

        // Process any pending sync operations
        await this.processSyncQueue();

        // Track installation
        await this.trackInstallation();

        console.log('[PWA] Application initialized successfully');
    }

    // =========================================================================
    // Service Worker Management
    // =========================================================================

    /**
     * Register service worker
     */
    async registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
            console.warn('[PWA] Service workers not supported');
            return;
        }

        try {
            const registration = await navigator.serviceWorker.register('/static/js/service-worker.js', {
                scope: '/'
            });

            this.serviceWorker = registration;

            console.log('[PWA] Service worker registered:', registration.scope);

            // Handle updates
            registration.addEventListener('updatefound', () => {
                const newWorker = registration.installing;
                console.log('[PWA] New service worker found');

                newWorker.addEventListener('statechange', () => {
                    if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                        this.showUpdateNotification();
                    }
                });
            });

            // Listen for messages from service worker
            navigator.serviceWorker.addEventListener('message', (event) => {
                this.handleServiceWorkerMessage(event.data);
            });

        } catch (error) {
            console.error('[PWA] Service worker registration failed:', error);
        }
    }

    /**
     * Handle messages from service worker
     */
    handleServiceWorkerMessage(message) {
        console.log('[PWA] Message from service worker:', message);

        switch (message.type) {
            case 'sync-complete':
                this.onSyncComplete(message.count);
                break;
            default:
                console.log('[PWA] Unknown message type:', message.type);
        }
    }

    /**
     * Show update notification
     */
    showUpdateNotification() {
        const updateBanner = document.getElementById('update-banner');
        if (updateBanner) {
            updateBanner.style.display = 'block';
        }

        // Or use a more sophisticated notification
        if (confirm('New version available! Refresh to update?')) {
            window.location.reload();
        }
    }

    // =========================================================================
    // Install Prompt
    // =========================================================================

    /**
     * Set up install prompt handling
     */
    setupInstallPrompt() {
        window.addEventListener('beforeinstallprompt', (event) => {
            event.preventDefault();
            this.installPrompt = event;
            console.log('[PWA] Install prompt captured');

            // Show custom install button
            this.showInstallButton();
        });

        window.addEventListener('appinstalled', () => {
            console.log('[PWA] App installed successfully');
            this.installPrompt = null;
            this.hideInstallButton();
            this.trackInstallation();
        });
    }

    /**
     * Show install button
     */
    showInstallButton() {
        const installButton = document.getElementById('install-app-btn');
        if (installButton) {
            installButton.style.display = 'block';
            installButton.addEventListener('click', () => this.promptInstall());
        }
    }

    /**
     * Hide install button
     */
    hideInstallButton() {
        const installButton = document.getElementById('install-app-btn');
        if (installButton) {
            installButton.style.display = 'none';
        }
    }

    /**
     * Prompt user to install app
     */
    async promptInstall() {
        if (!this.installPrompt) {
            console.log('[PWA] Install prompt not available');
            return;
        }

        this.installPrompt.prompt();

        const result = await this.installPrompt.userChoice;
        console.log('[PWA] Install prompt result:', result.outcome);

        if (result.outcome === 'accepted') {
            console.log('[PWA] User accepted install');
        } else {
            console.log('[PWA] User dismissed install');
        }

        this.installPrompt = null;
    }

    // =========================================================================
    // Connection Monitoring
    // =========================================================================

    /**
     * Set up online/offline detection
     */
    setupConnectionMonitoring() {
        window.addEventListener('online', () => {
            console.log('[PWA] Connection restored');
            this.isOnline = true;
            this.onOnline();
        });

        window.addEventListener('offline', () => {
            console.log('[PWA] Connection lost');
            this.isOnline = false;
            this.onOffline();
        });

        // Initial status
        this.updateConnectionStatus();
    }

    /**
     * Handle online event
     */
    async onOnline() {
        this.updateConnectionStatus();
        this.showNotification('Back online', 'Connection restored');

        // Process sync queue
        await this.processSyncQueue();

        // Trigger background sync
        if ('serviceWorker' in navigator && 'sync' in self.registration) {
            try {
                await navigator.serviceWorker.ready;
                await self.registration.sync.register('sync-offline-queue');
                console.log('[PWA] Background sync registered');
            } catch (error) {
                console.error('[PWA] Background sync failed:', error);
            }
        }
    }

    /**
     * Handle offline event
     */
    onOffline() {
        this.updateConnectionStatus();
        this.showNotification('Offline', 'Changes will be synced when back online');
    }

    /**
     * Update connection status UI
     */
    updateConnectionStatus() {
        const statusIndicator = document.getElementById('connection-status');
        if (statusIndicator) {
            statusIndicator.className = this.isOnline ? 'online' : 'offline';
            statusIndicator.textContent = this.isOnline ? 'Online' : 'Offline';
        }

        document.body.classList.toggle('offline', !this.isOnline);
    }

    // =========================================================================
    // Offline Sync Queue
    // =========================================================================

    /**
     * Initialize IndexedDB
     */
    async initDB() {
        return new Promise((resolve, reject) => {
            const request = indexedDB.open('project-management-offline', 1);

            request.onerror = () => reject(request.error);
            request.onsuccess = () => {
                this.db = request.result;
                resolve(this.db);
            };

            request.onupgradeneeded = (event) => {
                const db = event.target.result;
                if (!db.objectStoreNames.contains('offline-queue')) {
                    db.createObjectStore('offline-queue', { keyPath: 'id', autoIncrement: true });
                }
                if (!db.objectStoreNames.contains('cache')) {
                    db.createObjectStore('cache', { keyPath: 'key' });
                }
            };
        });
    }

    /**
     * Add operation to sync queue
     */
    async addToSyncQueue(operation) {
        if (!this.db) {
            console.error('[PWA] Database not initialized');
            return;
        }

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['offline-queue'], 'readwrite');
            const store = transaction.objectStore('offline-queue');
            const request = store.add({
                ...operation,
                timestamp: Date.now(),
                attempts: 0,
            });

            request.onsuccess = () => {
                console.log('[PWA] Operation added to sync queue:', request.result);
                resolve(request.result);
            };

            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Process sync queue
     */
    async processSyncQueue() {
        if (!this.isOnline || !this.db) {
            return;
        }

        console.log('[PWA] Processing sync queue...');

        const operations = await this.getSyncQueue();
        console.log(`[PWA] Found ${operations.length} operations to sync`);

        for (const operation of operations) {
            try {
                await this.syncOperation(operation);
                await this.removeFromSyncQueue(operation.id);
                console.log('[PWA] Operation synced:', operation.id);
            } catch (error) {
                console.error('[PWA] Failed to sync operation:', error);
            }
        }
    }

    /**
     * Get sync queue
     */
    async getSyncQueue() {
        if (!this.db) return [];

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['offline-queue'], 'readonly');
            const store = transaction.objectStore('offline-queue');
            const request = store.getAll();

            request.onsuccess = () => resolve(request.result || []);
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Sync operation
     */
    async syncOperation(operation) {
        const response = await fetch(operation.url, {
            method: operation.method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken'),
            },
            body: operation.data ? JSON.stringify(operation.data) : undefined,
        });

        if (!response.ok) {
            throw new Error(`Sync failed: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Remove from sync queue
     */
    async removeFromSyncQueue(id) {
        if (!this.db) return;

        return new Promise((resolve, reject) => {
            const transaction = this.db.transaction(['offline-queue'], 'readwrite');
            const store = transaction.objectStore('offline-queue');
            const request = store.delete(id);

            request.onsuccess = () => resolve();
            request.onerror = () => reject(request.error);
        });
    }

    /**
     * Handle sync complete
     */
    onSyncComplete(count) {
        console.log(`[PWA] Sync complete: ${count} operations`);
        this.showNotification('Sync Complete', `${count} operations synchronized`);
    }

    // =========================================================================
    // Push Notifications
    // =========================================================================

    /**
     * Set up push notifications
     */
    async setupPushNotifications() {
        if (!('Notification' in window)) {
            console.warn('[PWA] Notifications not supported');
            return;
        }

        if (!('PushManager' in window)) {
            console.warn('[PWA] Push notifications not supported');
            return;
        }

        // Check permission status
        const permission = Notification.permission;
        console.log('[PWA] Notification permission:', permission);

        if (permission === 'granted') {
            await this.subscribeToPush();
        } else if (permission === 'default') {
            // Will prompt when user interacts
            this.showNotificationPrompt();
        }
    }

    /**
     * Show notification permission prompt
     */
    showNotificationPrompt() {
        const promptElement = document.getElementById('notification-prompt');
        if (promptElement) {
            promptElement.style.display = 'block';
        }
    }

    /**
     * Request notification permission
     */
    async requestNotificationPermission() {
        const permission = await Notification.requestPermission();
        console.log('[PWA] Notification permission:', permission);

        if (permission === 'granted') {
            await this.subscribeToPush();
            this.showNotification('Notifications Enabled', 'You will receive push notifications');
        }

        return permission;
    }

    /**
     * Subscribe to push notifications
     */
    async subscribeToPush() {
        try {
            const registration = await navigator.serviceWorker.ready;

            // Check if already subscribed
            let subscription = await registration.pushManager.getSubscription();

            if (!subscription) {
                // Subscribe to push
                subscription = await registration.pushManager.subscribe({
                    userVisibleOnly: true,
                    applicationServerKey: this.urlBase64ToUint8Array(window.VAPID_PUBLIC_KEY || '')
                });

                console.log('[PWA] Push subscription created');
            }

            // Send subscription to server
            await this.sendSubscriptionToServer(subscription);

            return subscription;
        } catch (error) {
            console.error('[PWA] Failed to subscribe to push:', error);
        }
    }

    /**
     * Send subscription to server
     */
    async sendSubscriptionToServer(subscription) {
        const response = await fetch('/api/pwa/push-subscription/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken'),
            },
            body: JSON.stringify(subscription.toJSON()),
        });

        if (!response.ok) {
            throw new Error('Failed to send subscription to server');
        }

        console.log('[PWA] Subscription sent to server');
    }

    // =========================================================================
    // Analytics
    // =========================================================================

    /**
     * Track installation
     */
    async trackInstallation() {
        if (window.matchMedia('(display-mode: standalone)').matches) {
            console.log('[PWA] App is installed');

            try {
                await fetch('/api/pwa/track-installation/', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': this.getCookie('csrftoken'),
                    },
                    body: JSON.stringify({
                        platform: this.detectPlatform(),
                        user_agent: navigator.userAgent,
                        timestamp: new Date().toISOString(),
                    }),
                });
            } catch (error) {
                console.error('[PWA] Failed to track installation:', error);
            }
        }
    }

    /**
     * Detect platform
     */
    detectPlatform() {
        const ua = navigator.userAgent;
        if (/Android/i.test(ua)) return 'android';
        if (/iPhone|iPad|iPod/i.test(ua)) return 'ios';
        if (/Windows/i.test(ua)) return 'windows';
        if (/Mac/i.test(ua)) return 'macos';
        if (/Linux/i.test(ua)) return 'linux';
        return 'unknown';
    }

    // =========================================================================
    // Utilities
    // =========================================================================

    /**
     * Show notification
     */
    showNotification(title, body, options = {}) {
        if (Notification.permission === 'granted') {
            new Notification(title, {
                body,
                icon: '/static/icons/icon-192.png',
                ...options
            });
        }
    }

    /**
     * Get cookie value
     */
    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return '';
    }

    /**
     * Convert VAPID key
     */
    urlBase64ToUint8Array(base64String) {
        const padding = '='.repeat((4 - base64String.length % 4) % 4);
        const base64 = (base64String + padding)
            .replace(/-/g, '+')
            .replace(/_/g, '/');

        const rawData = window.atob(base64);
        const outputArray = new Uint8Array(rawData.length);

        for (let i = 0; i < rawData.length; ++i) {
            outputArray[i] = rawData.charCodeAt(i);
        }
        return outputArray;
    }
}

// Initialize PWA app when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.pwaApp = new PWAApp();
    });
} else {
    window.pwaApp = new PWAApp();
}
