// Deliberately does no caching. This app is a live household journal —
// serving a stale page after a deploy, or stale data offline, is worse
// than no offline support at all. The only reason this file exists is
// that Chrome's install-eligibility check wants an active service
// worker with a fetch handler; a plain passthrough satisfies that
// without changing any actual request behavior.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) => event.waitUntil(self.clients.claim()));
self.addEventListener("fetch", (event) => {
  event.respondWith(fetch(event.request));
});
