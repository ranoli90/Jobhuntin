// Service Worker for JobHuntin - Offline Support
const CACHE_NAME = 'jobhuntin-v1';
const STATIC_CACHE = 'jobhuntin-static-v1';
const STATIC_ASSETS = [
  '/',
  '/index.html',
  '/favicon.svg',
  '/manifest.json',
  // Add critical CSS and JS files
  '/src/main.tsx',
  // Add fonts
  'https://fonts.googleapis.com/css2?family=Inter:ital,opsz,wght@0,14..32,100..900;1,14..32,100..900&family=Instrument+Serif:ital@0;1&display=swap',
  'https://fonts.gstatic.com/s/inter/v13/UcCO3FwrK3iCTeGZlY8aE0A.woff2',
  'https://fonts.gstatic.com/s/instrumentserif/v14/rgIaow6Jg-MJ8e4.woff2'
];

// Install event - cache static assets
self.addEventListener('install', (event) => {
  console.log('[SW] Installing service worker');
  event.waitUntil(
    caches.open(STATIC_CACHE)
      .then((cache) => {
        console.log('[SW] Caching static assets');
        return cache.addAll(STATIC_ASSETS);
      })
      .then(() => self.skipWaiting())
  );
});

// Activate event - clean up old caches
self.addEventListener('activate', (event) => {
  console.log('[SW] Activating service worker');
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames.map((cacheName) => {
          if (cacheName !== STATIC_CACHE && cacheName !== CACHE_NAME) {
            console.log('[SW] Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

// Fetch event - serve from cache when offline
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests and external resources
  if (request.method !== 'GET' || url.origin !== self.location.origin) {
    return;
  }

  // Skip API requests - let them fail gracefully
  if (url.pathname.startsWith('/api/') || url.pathname.startsWith('/auth/')) {
    return;
  }

  event.respondWith(
    caches.match(request)
      .then((response) => {
        // Return cached version if available
        if (response) {
          console.log('[SW] Serving from cache:', request.url);
          return response;
        }

        // Otherwise fetch from network
        return fetch(request).then((response) => {
          // Cache successful responses for static assets
          if (response.ok && STATIC_ASSETS.includes(url.pathname)) {
            const responseClone = response.clone();
            caches.open(STATIC_CACHE).then((cache) => {
              cache.put(request, responseClone);
            });
          }

          return response;
        }).catch(() => {
          // Network failed - try to serve offline page
          if (url.pathname === '/' || url.pathname.startsWith('/app/')) {
            return caches.match('/index.html');
          }
          
          // Return a basic offline response
          return new Response(
            JSON.stringify({ 
              error: 'Offline', 
              message: 'You are currently offline. Please check your internet connection.' 
            }),
            {
              status: 503,
              statusText: 'Service Unavailable',
              headers: {
                'Content-Type': 'application/json',
              }
            }
          );
        });
      })
  );
});

// Message event - handle cache management
self.addEventListener('message', (event) => {
  const { type, payload } = event.data;

  switch (type) {
    case 'SKIP_WAITING':
      self.skipWaiting();
      break;
    
    case 'CACHE_UPDATE':
      // Update cache with new data
      caches.open(CACHE_NAME).then((cache) => {
        cache.put(payload.url, payload.response);
      });
      break;
    
    case 'DELETE_CACHE':
      // Clear cache
      if (payload.cacheName) {
        caches.delete(payload.cacheName);
      } else {
        caches.keys().then((cacheNames) => {
          cacheNames.forEach((cacheName) => caches.delete(cacheName));
        });
      }
      break;
  }
});

// Background sync for offline actions
self.addEventListener('sync', (event) => {
  if (event.tag === 'background-sync') {
    event.waitUntil(
      // Handle queued offline actions
      handleOfflineActions()
    );
  }
});

// Handle offline actions when back online
async function handleOfflineActions() {
  try {
    // Get queued actions from IndexedDB
    const actions = await getQueuedActions();
    
    // Process each action
    for (const action of actions) {
      try {
        await fetch(action.url, {
          method: action.method,
          headers: action.headers,
          body: action.body
        });
        
        // Remove processed action from queue
        await removeQueuedAction(action.id);
      } catch (error) {
        console.error('[SW] Failed to process offline action:', error);
      }
    }
  } catch (error) {
    console.error('[SW] Error handling offline actions:', error);
  }
}

// IndexedDB helpers for offline queue
async function getQueuedActions() {
  // Implementation would depend on your IndexedDB setup
  // This is a placeholder - you'd need to implement actual IndexedDB operations
  return [];
}

async function removeQueuedAction(id) {
  // Implementation would depend on your IndexedDB setup
  // This is a placeholder - you'd need to implement actual IndexedDB operations
  return true;
}
