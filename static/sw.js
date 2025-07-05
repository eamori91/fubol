/**
 * Service Worker para optimización y soporte offline
 * Caché de recursos estáticos y estrategia offline-first
 */

const CACHE_NAME = 'fubol-cache-v1';
const ASSETS = [
    '/',
    '/static/css/styles.css',
    '/static/js/main.js',
    '/static/images/logo.png',
    '/index',
    '/historico',
    '/proximo',
    '/futuro'
];

// Instalación del Service Worker y caché de recursos
self.addEventListener('install', event => {
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('Caché abierta');
                return cache.addAll(ASSETS);
            })
            .then(() => self.skipWaiting())
    );
});

// Limpieza de cachés antiguas
self.addEventListener('activate', event => {
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.filter(name => name !== CACHE_NAME)
                    .map(name => caches.delete(name))
            );
        }).then(() => self.clients.claim())
    );
});

// Estrategia de caché: Network first, fallback to cache
self.addEventListener('fetch', event => {
    event.respondWith(
        fetch(event.request)
            .then(response => {
                // Clonar la respuesta para almacenarla en caché
                const responseClone = response.clone();
                caches.open(CACHE_NAME)
                    .then(cache => {
                        // Solo cachear GET requests
                        if (event.request.method === 'GET') {
                            cache.put(event.request, responseClone);
                        }
                    });
                return response;
            })
            .catch(() => caches.match(event.request))
    );
});
