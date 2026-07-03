// Kill-switch: limpa todos os caches e desregistra o Service Worker.
// Resolvido problema de "carregamento infinito" causado por SW stale.
// PWA sera re-habilitado em producao com estrategia de cache robusta.

self.addEventListener("install", (event) => {
  self.skipWaiting();
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    Promise.all([
      caches.keys().then((keys) =>
        Promise.all(keys.map((k) => caches.delete(k)))
      ),
      self.registration.unregister(),
    ]).then(() => self.clients.claim())
  );
});
