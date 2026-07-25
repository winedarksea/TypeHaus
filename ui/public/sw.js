/* Type:Haus service worker — offline app-shell + pyodide runtime caching (→ 40 WP4.2).
 *
 * Strategy:
 *  - navigations            → network-first, fall back to cached index.html (offline boot)
 *  - hashed build assets    → cache-first (Vite content-hashes /assets/*, so a URL's bytes
 *                              never change; a new deploy simply asks for new URLs)
 *  - other same-origin      → stale-while-revalidate. The engine tarball, the bundled house,
 *                              the manifest and the icons keep STABLE urls across deploys, so
 *                              cache-first would pin a returning visitor to whatever engine
 *                              they first loaded. Serve the cached copy instantly, then
 *                              refresh it in the background for the next boot.
 *  - pyodide/CDN cross-origin→ cache-first; the URLs are version-pinned, and this is what makes
 *                              the in-browser engine work offline after the first load
 *  - engine API paths       → network-only, never cached (the local `haus serve` path stays
 *                              authoritative; a stale model.json must never be served)
 *
 * Note that CACHE_VERSION is NOT bumped per deploy: the browser only reinstalls this worker when
 * sw.js itself changes, so a version constant nobody edits cannot be the freshness mechanism.
 * Correctness comes from the per-request strategies above; bump it by hand only to force-evict
 * every cache after a breaking change.
 */
const CACHE_VERSION = "typehaus-v3";
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

// Serve the cached copy at once, refresh it in the background. Used for same-origin assets whose
// URL is stable across deploys (engine tarballs, the bundled house, manifest, icons) — offline
// still works, and the *next* boot picks up whatever the last deploy published.
async function staleWhileRevalidate(request, cacheName) {
  const cache = await caches.open(cacheName);
  const cached = await cache.match(request);
  const networked = fetch(request)
    .then((response) => {
      if (response && response.ok) cache.put(request, response.clone());
      return response;
    })
    // Offline (or the host is down) is the expected case here, not an error: fall back to cache.
    .catch(() => cached);
  return cached ?? networked;
}

// Vite writes content-hashed filenames into this directory, so these URLs are immutable.
function isImmutableBuildAsset(url) {
  return url.pathname.includes("/assets/");
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

  if (url.origin === self.location.origin) {
    event.respondWith(
      isImmutableBuildAsset(url)
        ? cacheFirst(request, SHELL_CACHE)
        : staleWhileRevalidate(request, SHELL_CACHE),
    );
    return;
  }

  // Cross-origin (pyodide CDN, wheels): cache-first so the engine loads offline next time.
  event.respondWith(cacheFirst(request, RUNTIME_CACHE));
});
