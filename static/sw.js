// Service Worker para PWA - Analizador Deportivo de Fútbol
const CACHE_NAME = 'football-analyzer-v1';
const urlsToCache = [
  '/',
  '/dashboard',
  '/static/css/style.css',
  '/static/js/dashboard.js',
  'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
  'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
  'https://cdn.jsdelivr.net/npm/aos@2.3.4/dist/aos.css'
];

// Instalación del Service Worker
self.addEventListener('install', function(event) {
  event.waitUntil(
    caches.open(CACHE_NAME)
      .then(function(cache) {
        console.log('Cache abierto');
        return cache.addAll(urlsToCache);
      })
  );
});

// Activación del Service Worker
self.addEventListener('activate', function(event) {
  event.waitUntil(
    caches.keys().then(function(cacheNames) {
      return Promise.all(
        cacheNames.map(function(cacheName) {
          if (cacheName !== CACHE_NAME) {
            console.log('Eliminando cache antiguo:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
});

// Interceptar solicitudes de red
self.addEventListener('fetch', function(event) {
  event.respondWith(
    caches.match(event.request)
      .then(function(response) {
        // Cache hit - devolver respuesta desde cache
        if (response) {
          return response;
        }

        return fetch(event.request).then(
          function(response) {
            // Verificar si recibimos una respuesta válida
            if(!response || response.status !== 200 || response.type !== 'basic') {
              return response;
            }

            // Clonar la respuesta
            var responseToCache = response.clone();

            caches.open(CACHE_NAME)
              .then(function(cache) {
                cache.put(event.request, responseToCache);
              });

            return response;
          }
        );
      })
    );
});

// Manejar notificaciones push
self.addEventListener('push', function(event) {
  const options = {
    body: event.data ? event.data.text() : 'Nueva predicción disponible',
    icon: '/static/img/icon-192.png',
    badge: '/static/img/badge-72.png',
    vibrate: [100, 50, 100],
    data: {
      dateOfArrival: Date.now(),
      primaryKey: 1
    },
    actions: [
      {
        action: 'explore',
        title: 'Ver predicción',
        icon: '/static/img/checkmark.png'
      },
      {
        action: 'close',
        title: 'Cerrar',
        icon: '/static/img/xmark.png'
      }
    ]
  };

  event.waitUntil(
    self.registration.showNotification('Analizador Deportivo', options)
  );
});

// Manejar clicks en notificaciones
self.addEventListener('notificationclick', function(event) {
  event.notification.close();

  if (event.action === 'explore') {
    // Abrir la aplicación
    event.waitUntil(
      clients.openWindow('/')
    );
  } else if (event.action === 'close') {
    // Solo cerrar la notificación
    console.log('Notificación cerrada');
  }
});

// Sincronización en segundo plano
self.addEventListener('sync', function(event) {
  if (event.tag === 'background-sync') {
    console.log('Sincronización en segundo plano');
    event.waitUntil(doBackgroundSync());
  }
});

function doBackgroundSync() {
  return fetch('/api/dashboard/stats')
    .then(function(response) {
      return response.json();
    })
    .then(function(data) {
      console.log('Datos sincronizados:', data);
    })
    .catch(function(error) {
      console.log('Error en sincronización:', error);
    });
}
