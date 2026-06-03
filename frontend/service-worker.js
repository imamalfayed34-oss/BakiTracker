// Baki Tracker — Service Worker (Phase 0 stub)
// Caches the app shell so it opens even when offline.
// v2 will add IndexedDB + background sync for full offline writes.

const CACHE = 'baki-shell-v1';
const SHELL = [
  '/',
  '/static/css/style.css',
  '/static/js/app.js',
  '/manifest.json',
];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(CACHE).then((c) => c.addAll(SHELL)));
  self.skipWaiting();
});

self.addEventListener('activate', (e) => {
  e.waitUntil(
    caches.keys().then((keys) =>
      Promise.all(keys.filter((k) => k !== CACHE).map((k) => caches.delete(k)))
    )
  );
  self.clients.claim();
});

self.addEventListener('fetch', (e) => {
  const url = new URL(e.request.url);
  // Never cache API calls — always go to network.
  if (url.pathname.startsWith('/api/')) return;
  // Cache-first for shell assets, fall back to network.
  e.respondWith(
    caches.match(e.request).then((cached) => cached || fetch(e.request))
  );
});
