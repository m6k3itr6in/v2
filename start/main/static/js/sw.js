const CACHE_NAME = 'coffee-app-v1';
const urlsToCache = [
    '/',
    '/static/css/base.css',
    '/static/css/mobile.css',
    '/static/bootstrap/css/bootstrap.min.css'
];

self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => cache.addAll(urlsToCache))
    );
});

self.addEventListener('fetch', event => {
    event.respondWith(
        caches.match(event.request)
            .then(response => response || fetch(event.request))
    );
});

