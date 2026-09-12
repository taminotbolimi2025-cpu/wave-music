/**
 * Wave Music Service Worker - Subway Offline Cache
 * Caches HTML, CSS, JavaScript, and fonts so the Mini App opens with ZERO internet connection.
 */

const CACHE_NAME = 'wave-music-shell-v3.5.0';

const ASSETS_TO_CACHE = [
  '/',
  '/index.html',
  '/style.css?v=3.5.0',
  '/app.js?v=3.5.0',
  '/offline_db.js?v=3.5.0',
  '/tracks.json',
  'https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap'
];

self.addEventListener('install', (event) => {
  self.skipWaiting();
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(ASSETS_TO_CACHE).catch((err) => {
        console.warn('[SW] Pre-caching non-fatal warning:', err);
      });
    })
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.map((key) => {
          if (key !== CACHE_NAME && key.startsWith('wave-music-')) {
            return caches.delete(key);
          }
        })
      );
    }).then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const url = new URL(event.request.url);

  // Never cache audio streaming endpoints or API requests in SW (IndexedDB handles audio blobs)
  if (url.pathname.startsWith('/api/stream') || url.pathname.startsWith('/api/debug_stream')) {
    return;
  }

  // Network-first with cache fallback for HTML pages
  if (event.request.mode === 'navigate' || url.pathname === '/' || url.pathname === '/index.html') {
    event.respondWith(
      fetch(event.request)
        .then((response) => {
          if (response.status === 200) {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => cache.put(event.request, clone));
          }
          return response;
        })
        .catch(() => {
          return caches.match('/index.html') || caches.match('/');
        })
    );
    return;
  }

  // Cache-first with network background revalidate for static styles, scripts, fonts
  if (
    url.pathname.endsWith('.css') ||
    url.pathname.endsWith('.js') ||
    url.pathname.endsWith('.json') ||
    url.hostname.includes('fonts.gstatic.com') ||
    url.hostname.includes('fonts.googleapis.com')
  ) {
    event.respondWith(
      caches.match(event.request).then((cached) => {
        if (cached) {
          // Revalidate in background
          fetch(event.request)
            .then((res) => {
              if (res.status === 200) {
                caches.open(CACHE_NAME).then((c) => c.put(event.request, res));
              }
            })
            .catch(() => {});
          return cached;
        }

        return fetch(event.request).then((res) => {
          if (res.status === 200) {
            const clone = res.clone();
            caches.open(CACHE_NAME).then((c) => c.put(event.request, clone));
          }
          return res;
        });
      })
    );
    return;
  }

  // Default fetch
  event.respondWith(fetch(event.request).catch(() => caches.match(event.request)));
});
