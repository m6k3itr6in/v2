const CACHE_NAME = 'coffee-app-v2';
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

self.addEventListener('push', function (event) {
    const data = event.data.json();
    const options = {
        body: data.body,
        icon: '/static/images/icon-192.png',
        badge: '/static/images/icon-192.png',
        data: {
            url: data.url
        }
    };
    event.waitUntil(self.registration.showNotification(data.title, options));
});

self.addEventListener('notificationclick', function (event) {
    event.notification.close();
    event.waitUntil(clients.openWindow(event.notification.data.url));
});