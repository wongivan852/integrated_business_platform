/**
 * Service Worker for Project Management PWA
 * Phase 6.5: Mobile PWA
 *
 * Features:
 * - Offline caching with cache-first strategy
 * - Background sync for offline operations
 * - Push notification support
 * - Smart cache management
 */

const CACHE_VERSION = 'v1.0.0';
const CACHE_NAME = `project-management-${CACHE_VERSION}`;

// Assets to cache on install
const CORE_ASSETS = [
    '/',
    '/static/css/bootstrap.min.css',
    '/static/css/style.css',
    '/static/js/jquery.min.js',
    '/static/js/bootstrap.bundle.min.js',
    '/static/js/pwa-app.js',
    '/offline/',
];

// Cache strategies
const CACHE_STRATEGIES = {
    'cache-first': ['/static/'],
    'network-first': ['/projects/', '/api/'],
    'network-only': ['/admin/', '/auth/'],
};

// =============================================================================
// Service Worker Lifecycle
// =============================================================================

/**
 * Install event - cache core assets
 */
self.addEventListener('install', (event) => {
    console.log('[SW] Installing service worker...');

    event.waitUntil(
        caches.open(CACHE_NAME)
            .then((cache) => {
                console.log('[SW] Caching core assets');
                return cache.addAll(CORE_ASSETS);
            })
            .then(() => {
                console.log('[SW] Service worker installed successfully');
                return self.skipWaiting();
            })
            .catch((error) => {
                console.error('[SW] Installation failed:', error);
            })
    );
});

/**
 * Activate event - clean up old caches
 */
self.addEventListener('activate', (event) => {
    console.log('[SW] Activating service worker...');

    event.waitUntil(
        caches.keys()
            .then((cacheNames) => {
                return Promise.all(
                    cacheNames
                        .filter((cacheName) => {
                            return cacheName.startsWith('project-management-') &&
                                   cacheName !== CACHE_NAME;
                        })
                        .map((cacheName) => {
                            console.log('[SW] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        })
                );
            })
            .then(() => {
                console.log('[SW] Service worker activated successfully');
                return self.clients.claim();
            })
    );
});

// =============================================================================
// Fetch Strategy
// =============================================================================

/**
 * Fetch event - handle network requests with caching strategies
 */
self.addEventListener('fetch', (event) => {
    const { request } = event;
    const url = new URL(request.url);

    // Skip cross-origin requests
    if (url.origin !== location.origin) {
        return;
    }

    // Determine strategy based on URL
    const strategy = getStrategy(url.pathname);

    if (strategy === 'cache-first') {
        event.respondWith(cacheFirst(request));
    } else if (strategy === 'network-first') {
        event.respondWith(networkFirst(request));
    } else if (strategy === 'network-only') {
        event.respondWith(fetch(request));
    } else {
        event.respondWith(networkFirst(request));
    }
});

/**
 * Determine caching strategy for a URL
 */
function getStrategy(pathname) {
    for (const [strategy, patterns] of Object.entries(CACHE_STRATEGIES)) {
        for (const pattern of patterns) {
            if (pathname.startsWith(pattern)) {
                return strategy;
            }
        }
    }
    return 'network-first';
}

/**
 * Cache-first strategy
 * Try cache first, fall back to network
 */
async function cacheFirst(request) {
    const cache = await caches.open(CACHE_NAME);
    const cached = await cache.match(request);

    if (cached) {
        console.log('[SW] Serving from cache:', request.url);
        return cached;
    }

    try {
        console.log('[SW] Fetching from network:', request.url);
        const response = await fetch(request);

        // Cache successful responses
        if (response && response.status === 200) {
            cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        console.error('[SW] Fetch failed:', error);
        return getOfflinePage();
    }
}

/**
 * Network-first strategy
 * Try network first, fall back to cache
 */
async function networkFirst(request) {
    try {
        console.log('[SW] Fetching from network:', request.url);
        const response = await fetch(request);

        // Cache successful responses
        if (response && response.status === 200) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, response.clone());
        }

        return response;
    } catch (error) {
        console.log('[SW] Network failed, serving from cache:', request.url);
        const cache = await caches.open(CACHE_NAME);
        const cached = await cache.match(request);

        if (cached) {
            return cached;
        }

        // Return offline page for navigation requests
        if (request.mode === 'navigate') {
            return getOfflinePage();
        }

        throw error;
    }
}

/**
 * Get offline fallback page
 */
async function getOfflinePage() {
    const cache = await caches.open(CACHE_NAME);
    return cache.match('/offline/') || new Response('Offline');
}

// =============================================================================
// Background Sync
// =============================================================================

/**
 * Background sync event - sync offline operations
 */
self.addEventListener('sync', (event) => {
    console.log('[SW] Background sync triggered:', event.tag);

    if (event.tag === 'sync-offline-queue') {
        event.waitUntil(syncOfflineQueue());
    }
});

/**
 * Sync offline operations queue
 */
async function syncOfflineQueue() {
    try {
        console.log('[SW] Syncing offline queue...');

        // Get pending operations from IndexedDB
        const operations = await getOfflineOperations();

        for (const operation of operations) {
            try {
                await syncOperation(operation);
                await markOperationComplete(operation.id);
                console.log('[SW] Synced operation:', operation.id);
            } catch (error) {
                console.error('[SW] Failed to sync operation:', error);
                await markOperationFailed(operation.id, error.message);
            }
        }

        // Notify clients about sync completion
        await notifyClients({
            type: 'sync-complete',
            count: operations.length
        });

        console.log('[SW] Offline queue synced successfully');
    } catch (error) {
        console.error('[SW] Failed to sync offline queue:', error);
        throw error;
    }
}

/**
 * Sync a single operation
 */
async function syncOperation(operation) {
    const { method, url, data } = operation;

    const response = await fetch(url, {
        method: method,
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': operation.csrfToken || '',
        },
        body: data ? JSON.stringify(data) : undefined,
    });

    if (!response.ok) {
        throw new Error(`Sync failed: ${response.statusText}`);
    }

    return response.json();
}

// =============================================================================
// Push Notifications
// =============================================================================

/**
 * Push event - handle incoming push notifications
 */
self.addEventListener('push', (event) => {
    console.log('[SW] Push notification received');

    let notification = {
        title: 'Project Management',
        body: 'You have a new notification',
        icon: '/static/icons/icon-192.png',
        badge: '/static/icons/badge-72.png',
        tag: 'default',
        data: {},
    };

    if (event.data) {
        try {
            const data = event.data.json();
            notification = {
                ...notification,
                ...data,
            };
        } catch (error) {
            console.error('[SW] Failed to parse push data:', error);
        }
    }

    event.waitUntil(
        self.registration.showNotification(notification.title, {
            body: notification.body,
            icon: notification.icon,
            badge: notification.badge,
            tag: notification.tag,
            data: notification.data,
            actions: notification.actions || [],
            vibrate: [200, 100, 200],
        })
    );
});

/**
 * Notification click event - handle notification interactions
 */
self.addEventListener('notificationclick', (event) => {
    console.log('[SW] Notification clicked:', event.notification.tag);

    event.notification.close();

    const data = event.notification.data || {};
    const url = data.url || '/';

    event.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true })
            .then((clientList) => {
                // Check if there's already a window open
                for (const client of clientList) {
                    if (client.url === url && 'focus' in client) {
                        return client.focus();
                    }
                }

                // Open new window if none exists
                if (clients.openWindow) {
                    return clients.openWindow(url);
                }
            })
    );
});

// =============================================================================
// Message Handling
// =============================================================================

/**
 * Message event - handle messages from clients
 */
self.addEventListener('message', (event) => {
    console.log('[SW] Message received:', event.data);

    const { type, payload } = event.data;

    switch (type) {
        case 'skip-waiting':
            self.skipWaiting();
            break;

        case 'cache-urls':
            cacheUrls(payload.urls);
            break;

        case 'clear-cache':
            clearCache();
            break;

        case 'get-cache-size':
            getCacheSize().then((size) => {
                event.ports[0].postMessage({ size });
            });
            break;

        default:
            console.warn('[SW] Unknown message type:', type);
    }
});

/**
 * Cache specific URLs
 */
async function cacheUrls(urls) {
    const cache = await caches.open(CACHE_NAME);
    return cache.addAll(urls);
}

/**
 * Clear all caches
 */
async function clearCache() {
    const cacheNames = await caches.keys();
    return Promise.all(
        cacheNames.map((cacheName) => caches.delete(cacheName))
    );
}

/**
 * Get total cache size
 */
async function getCacheSize() {
    if ('storage' in navigator && 'estimate' in navigator.storage) {
        const estimate = await navigator.storage.estimate();
        return estimate.usage || 0;
    }
    return 0;
}

/**
 * Notify all clients
 */
async function notifyClients(message) {
    const clients = await self.clients.matchAll({ includeUncontrolled: true });
    clients.forEach((client) => {
        client.postMessage(message);
    });
}

// =============================================================================
// IndexedDB Helpers (for offline queue)
// =============================================================================

const DB_NAME = 'project-management-offline';
const DB_VERSION = 1;
const STORE_NAME = 'offline-queue';

/**
 * Open IndexedDB connection
 */
function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onerror = () => reject(request.error);
        request.onsuccess = () => resolve(request.result);

        request.onupgradeneeded = (event) => {
            const db = event.target.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
            }
        };
    });
}

/**
 * Get pending offline operations
 */
async function getOfflineOperations() {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readonly');
        const store = transaction.objectStore(STORE_NAME);
        const request = store.getAll();

        request.onsuccess = () => resolve(request.result || []);
        request.onerror = () => reject(request.error);
    });
}

/**
 * Mark operation as complete
 */
async function markOperationComplete(id) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readwrite');
        const store = transaction.objectStore(STORE_NAME);
        const request = store.delete(id);

        request.onsuccess = () => resolve();
        request.onerror = () => reject(request.error);
    });
}

/**
 * Mark operation as failed
 */
async function markOperationFailed(id, error) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const transaction = db.transaction([STORE_NAME], 'readwrite');
        const store = transaction.objectStore(STORE_NAME);
        const getRequest = store.get(id);

        getRequest.onsuccess = () => {
            const operation = getRequest.result;
            if (operation) {
                operation.failed = true;
                operation.error = error;
                operation.attempts = (operation.attempts || 0) + 1;
                store.put(operation);
            }
            resolve();
        };

        getRequest.onerror = () => reject(getRequest.error);
    });
}

console.log('[SW] Service worker script loaded');
