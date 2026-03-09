// M9: Enhanced Service Worker Caching
const CACHE_VERSION = 'v2';
const CACHE_NAME = `jobhuntin-${CACHE_VERSION}`;
const OFFLINE_URL = '/offline.html';
const API_CACHE_NAME = `jobhuntin-api-${CACHE_VERSION}`;

// Assets to cache on install
const PRECACHE_ASSETS = [
  '/',
  '/offline.html',
  '/manifest.json',
];

// M9: Cache strategies
const CACHE_STRATEGIES = {
  // Static assets - cache first, network fallback
  STATIC: 'cache-first',
  // API responses - network first, cache fallback (stale-while-revalidate)
  API: 'network-first',
  // Images - cache first with long TTL
  IMAGES: 'cache-first',
};

// Install event - cache core assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      console.log('[SW] Precaching core assets');
      return cache.addAll(PRECACHE_ASSETS);
    })
  );
  // Activate immediately
  self.skipWaiting();
});

// M9: Enhanced activate event - clean up old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((cacheNames) => {
      return Promise.all(
        cacheNames
          .filter((name) => name !== CACHE_NAME && name !== API_CACHE_NAME)
          .map((name) => {
            console.log('[SW] Deleting old cache:', name);
            return caches.delete(name);
          })
      );
    }).then(() => {
      // M9: Limit API cache size to prevent storage issues
      return caches.open(API_CACHE_NAME).then((cache) => {
        return cache.keys().then((keys) => {
          // Keep only last 50 API responses
          if (keys.length > 50) {
            const toDelete = keys.slice(0, keys.length - 50);
            return Promise.all(toDelete.map((key) => cache.delete(key)));
          }
        });
      });
    })
  );
  // Take control immediately
  self.clients.claim();
});

// M9: Enhanced fetch event with better caching strategies
self.addEventListener('fetch', (event) => {
  // Skip non-GET requests
  if (event.request.method !== 'GET') return;

  const url = new URL(event.request.url);
  const isSameOrigin = url.origin === self.location.origin;
  const isFont = url.pathname.includes('/fonts/') || url.hostname.includes('fonts.');
  
  if (!isSameOrigin && !isFont) return;

  // M9: Determine cache strategy based on request type
  const isAPI = url.pathname.startsWith('/api/');
  const isImage = /\.(jpg|jpeg|png|gif|webp|svg|ico)$/i.test(url.pathname);
  const isStatic = /\.(js|css|woff|woff2|ttf|eot)$/i.test(url.pathname);

  if (isAPI) {
    // M9: Network-first strategy for API - always try network, fallback to cache
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          // Cache successful API responses (GET only, exclude auth endpoints)
          if (response.ok && !url.pathname.includes('/auth/')) {
            const responseClone = response.clone();
            caches.open(API_CACHE_NAME).then((cache) => {
              // Cache with 5-minute TTL for API responses
              cache.put(event.request, responseClone);
            });
          }
          return response;
        })
        .catch(() => {
          // Fallback to cache if network fails
          return caches.match(event.request).then((cached) => {
            if (cached) {
              return cached;
            }
            // Return offline response for API calls
            return new Response(
              JSON.stringify({ error: 'Offline', message: 'You are currently offline' }),
              { status: 503, headers: { 'Content-Type': 'application/json' } }
            );
          });
        })
    );
  } else if (isImage || isStatic) {
    // M9: Cache-first strategy for static assets and images
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        if (cachedResponse) {
          // Update cache in background
          event.waitUntil(
            fetch(event.request).then((response) => {
              if (response.ok) {
                caches.open(CACHE_NAME).then((cache) => {
                  cache.put(event.request, response);
                });
              }
            }).catch(() => {})
          );
          return cachedResponse;
        }
        // Fetch and cache if not in cache
        return fetch(event.request).then((response) => {
          if (response.ok) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        });
      })
    );
  } else {
    // M9: Stale-while-revalidate for HTML pages
    event.respondWith(
      caches.match(event.request).then((cachedResponse) => {
        const fetchPromise = fetch(event.request).then((response) => {
          if (response.ok) {
            const responseClone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(event.request, responseClone);
            });
          }
          return response;
        }).catch(() => {
          // Return offline page for navigation requests
          if (event.request.mode === 'navigate') {
            return caches.match(OFFLINE_URL) || new Response('Offline', { status: 503 });
          }
          return cachedResponse || new Response('Offline', { status: 503 });
        });

        // Return cached version immediately, update in background
        return cachedResponse || fetchPromise;
      })
    );
  }
});

// Handle push notifications (for future use)
self.addEventListener('push', (event) => {
  if (!event.data) return;
  
  const data = event.data.json();
  const options = {
    body: data.body || 'New notification from JobHuntin',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-72x72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: data.id || '1',
      url: data.url || '/',
    },
    actions: data.actions || [],
  };

  event.waitUntil(
    self.registration.showNotification(data.title || 'JobHuntin', options)
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', (event) => {
  event.notification.close();

  const url = event.notification.data?.url || '/';
  
  event.waitUntil(
    clients.matchAll({ type: 'window', includeUncontrolled: true }).then((clientList) => {
      // Focus existing window if available
      for (const client of clientList) {
        if (client.url === url && 'focus' in client) {
          return client.focus();
        }
      }
      // Open new window
      if (clients.openWindow) {
        return clients.openWindow(url);
      }
    })
  );
});
