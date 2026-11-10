// Project Helix service worker — offline shell + fresh-when-online event data.
// Bump on every app-shell change — a stale v1 cache would keep serving an
// index.html that has no food-resources.js tag.
const CACHE = 'helix-v4';

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
  './Project/static/food-resources.js',
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
  if (url.search) return;
  const assetPath = url.pathname;
  const shellPaths = ASSETS.map((asset) => new URL(asset, self.registration.scope).pathname);
  if (!shellPaths.includes(assetPath) && !assetPath.endsWith('/Project/scraped_events.json') &&
      !assetPath.endsWith('/Project/food_resources.json')) return;

  // Event data: network-first so listings stay fresh, cache as offline fallback.
  if (url.pathname.endsWith('scraped_events.json') || url.pathname.endsWith('food_resources.json')) {
    event.respondWith(
      fetch(req)
        .then((res) => {
          const copy = res.clone();
          if (res.ok) caches.open(CACHE).then((c) => c.put(req, copy));
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
          if (res.ok) caches.open(CACHE).then((c) => c.put(req, copy));
          return res;
        })
        .catch(() => cached);
      return cached || network;
    })
  );
});
