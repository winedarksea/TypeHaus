/* Type:Haus service worker — offline app-shell + pyodide runtime caching (→ 40 WP4.2).
 *
 * Strategy:
 *  - navigations            → network-first, fall back to cached index.html (offline boot)
 *  - same-origin static     → cache-first (Vite content-hashes filenames, so they're immutable)
 *  - pyodide/CDN cross-origin→ cache-first (stale-while-revalidate); makes the in-browser
 *                              engine work fully offline after the first successful load
 *  - engine API paths       → network-only, never cached (the local `haus serve` path stays
 *                              authoritative; a stale model.json must never be served)
 *
 * CACHE_VERSION is bumped by the build (see scripts/build-pwa-assets.mjs) so a new deploy
 * evicts the old shell on activate.
 */
const CACHE_VERSION = "typehaus-v2";
const SHELL_CACHE = `${CACHE_VERSION}-shell`;
const RUNTIME_CACHE = `${CACHE_VERSION}-runtime`;

// Relative to the SW scope so the ./ base (portable wheel-served build) works.
const SHELL_ASSETS = [
  "./",
  "./index.html",
  "./manifest.webmanifest",
  "./icons/icon.svg",
  "./icons/icon-maskable.svg",
];

// Engine API surface (server/app.py) — never cached; these belong to `haus serve`.
const API_PREFIXES = [
  "/model", "/checks", "/details", "/detail", "/plan", "/preview", "/macro",
  "/build", "/undo", "/redo", "/events", "/underlays",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL_CACHE).then((cache) => cache.addAll(SHELL_ASSETS)).then(() =>
      self.skipWaiting(),
    ),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((k) => !k.startsWith(CACHE_VERSION))
            .map((k) => caches.delete(k)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

function isApiRequest(url) {
  return url.origin === self.location.origin &&
    API_PREFIXES.some((p) => url.pathname === p || url.pathname.startsWith(p + "/"));
}

async function cacheFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  if (cached) return cached;
  const response = await fetch(request);
  // Cache successful and opaque (cross-origin CDN) responses for offline reuse.
  if (response && (response.ok || response.type === "opaque")) {
    cache.put(request, response.clone());
  }
  return response;
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);

  // Engine API + WebSocket: always go to network, never cache.
  if (isApiRequest(url)) return;

  // Navigations: network-first so a live deploy wins, offline falls back to the shell.
  if (request.mode === "navigate") {
    event.respondWith(
      fetch(request).catch(() =>
        caches.match("./index.html", { ignoreSearch: true }).then(
          (r) => r || caches.match("./"),
        ),
      ),
    );
    return;
  }

  // Same-origin hashed static assets: cache-first.
  if (url.origin === self.location.origin) {
    event.respondWith(cacheFirst(request, SHELL_CACHE));
    return;
  }

  // Cross-origin (pyodide CDN, wheels): cache-first so the engine loads offline next time.
  event.respondWith(cacheFirst(request, RUNTIME_CACHE));
});
