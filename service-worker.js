// Project Helix service worker — offline shell + fresh-when-online event data.
const CACHE = 'helix-v1';

// App shell — cached on install for instant repeat loads and offline use.
const ASSETS = [
  './',
  './index.html',
  './manifest.webmanifest',
  './Project/static/style.css',
  './Project/static/google-config.js',
  './Project/static/event-utils.js',
  './Project/static/browse-events.js',
  './Project/static/script.js',
  './Project/static/export.js',
  './Project/static/calendar-connect.js',
  './Project/static/manual-event-parser.js',
  './Project/static/manual-event-handler.js',
  './Project/static/images/favicon.png',
  './Project/static/images/Illinois_Block_I.png'
];

self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE)
      .then((cache) => cache.addAll(ASSETS))
      .then(() => self.skipWaiting())
  );
});

self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys()
      .then((keys) => Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k))))
      .then(() => self.clients.claim())
  );
});

self.addEventListener('fetch', (event) => {
  const req = event.request;
  if (req.method !== 'GET') return;

  const url = new URL(req.url);
  // Only manage same-origin traffic; Google APIs / CDNs pass straight through.
  if (url.origin !== self.location.origin) return;

  // Event data: network-first so listings stay fresh, cache as offline fallback.
  if (url.pathname.endsWith('scraped_events.json')) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
          return res;
        })
        .catch(() => caches.match(req))
    );
    return;
  }

  // Static assets: cache-first with background revalidation (stale-while-revalidate).
  event.respondWith(
    caches.match(req).then((cached) => {
      const network = fetch(req)
        .then((res) => {
          const copy = res.clone();
          caches.open(CACHE).then((c) => c.put(req, copy));
          return res;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
