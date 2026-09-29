// Caching here is shaped by one rule: this is a live household journal,
// so the network always wins when it is reachable. Nothing is served from
// the cache that could have changed without the page knowing it is
// looking at a saved copy — the app shows an offline bar for that.
//
// The page shell is fetched network-first, because it carries the ?v=
// asset version; serving a saved shell first would pin an installed app
// to an old build forever. Everything under /static/ is the opposite:
// its URL already changes on every deploy and it is immutable for a
// year, so it is safe to take from the cache and never revalidate.
const SHELL_CACHE = "infabula-shell-v1";
const API_CACHE = "infabula-api-v1";
const CACHES = [SHELL_CACHE, API_CACHE];

// Streaming, downloads and private media: pass straight through. An SSE
// stream in particular must never be buffered into a cache. Avatars are
// matched by suffix, not prefix — the real route is /api/users/{id}/avatar,
// so a literal "/api/avatar" prefix here never actually matched it.
const API_BYPASS_PREFIXES = ["/api/events", "/api/export"];
function bypassApi(pathname) {
  return API_BYPASS_PREFIXES.some((p) => pathname.startsWith(p))
    || pathname.endsWith("/avatar");
}

function offlineResponse() {
  // Shaped like the app's own error payloads, so every existing caller
  // reports it through the usual "the server said no" path instead of
  // throwing an unhandled rejection at a tap that appeared to work.
  return new Response(JSON.stringify({ error: "offline" }), {
    status: 503,
    headers: { "Content-Type": "application/json", "X-Offline": "1" },
  });
}

function cacheable(response) {
  return response && response.ok && response.type === "basic";
}

// A deploy changes ?v=, so old copies of the same file would pile up
// forever otherwise.
async function dropOtherVersions(cache, url) {
  for (const req of await cache.keys()) {
    const other = new URL(req.url);
    if (other.pathname === url.pathname && other.search !== url.search) {
      await cache.delete(req);
    }
  }
}

async function handleAsset(request, url) {
  const cache = await caches.open(SHELL_CACHE);
  const hit = await cache.match(request);
  if (hit) return hit;
  const response = await fetch(request);
  if (cacheable(response)) {
    await cache.put(request, response.clone());
    await dropOtherVersions(cache, url);
  }
  return response;
}

async function handleNavigation(request) {
  const cache = await caches.open(SHELL_CACHE);
  try {
    const response = await fetch(request);
    if (cacheable(response)) await cache.put(request, response.clone());
    return response;
  } catch (err) {
    const hit = await cache.match(request, { ignoreSearch: true });
    if (hit) return hit;
    throw err;
  }
}

// A saved copy is returned with the same marker a failed write gets, so
// the page can tell "this is the household's log right now" apart from
// "this is what it looked like last time we had a network".
async function asSavedCopy(hit) {
  const headers = new Headers(hit.headers);
  headers.set("X-Offline", "1");
  return new Response(await hit.blob(), {
    status: hit.status,
    statusText: hit.statusText,
    headers,
  });
}

async function handleApi(request) {
  const cache = await caches.open(API_CACHE);
  try {
    const response = await fetch(request);
    if (cacheable(response)) await cache.put(request, response.clone());
    return response;
  } catch (err) {
    const hit = await cache.match(request);
    if (hit) return asSavedCopy(hit);
    return offlineResponse();
  }
}

self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", (event) =>
  event.waitUntil(
    (async () => {
      const names = await caches.keys();
      await Promise.all(
        names.filter((n) => n.startsWith("infabula-") && !CACHES.includes(n))
             .map((n) => caches.delete(n))
      );
      await self.clients.claim();
    })()
  )
);

// Logging out drops the cached journal with the session: on a shared
// phone the next person must not be able to read it back offline.
self.addEventListener("message", (event) => {
  if (event.data === "clear-cache") {
    event.waitUntil(Promise.all(CACHES.map((n) => caches.delete(n))));
  }
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;

  if (request.method !== "GET") {
    event.respondWith(fetch(request).catch(() => offlineResponse()));
    return;
  }
  if (request.mode === "navigate") {
    event.respondWith(handleNavigation(request));
    return;
  }
  if (url.pathname.startsWith("/static/") || url.pathname.startsWith("/app-icon/")) {
    event.respondWith(handleAsset(request, url));
    return;
  }
  if (url.pathname.startsWith("/api/")) {
    if (bypassApi(url.pathname)) return;
    event.respondWith(handleApi(request));
  }
});

self.addEventListener("push", (event) => {
  let data = {};
  try {
    data = event.data ? event.data.json() : {};
  } catch (e) {
    data = { title: "infabula", body: event.data ? event.data.text() : "" };
  }
  event.waitUntil(
    self.registration.showNotification(data.title || "infabula", {
      body: data.body || "",
      tag: data.tag || "infabula",
      renotify: true,
      icon: "/static/icon.svg",
      badge: "/static/icon.svg",
      data: { url: data.url || "/" },
    })
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const url = (event.notification.data && event.notification.data.url) || "/";
  event.waitUntil(
    self.clients.matchAll({ type: "window", includeUncontrolled: true }).then((wins) => {
      for (const w of wins) {
        if ("focus" in w) {
          w.navigate(url);
          return w.focus();
        }
      }
      return self.clients.openWindow(url);
    })
  );
});
