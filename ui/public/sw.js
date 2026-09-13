/* Type:Haus service worker — offline app-shell + pyodide runtime caching (→ 40 WP4.2).
 *
 * Strategy:
 *  - navigations            → network-first, fall back to cached index.html (offline boot)
 *  - hashed build assets    → cache-first (Vite content-hashes /assets/*, so a URL's bytes
 *                              never change; a new deploy simply asks for new URLs)
 *  - runtime bundles        → network-first, falling back to cache. The engine tarball and the
 *                              bundled house keep STABLE urls across deploys while the app JS is
 *                              content-hashed and therefore always the new deploy's. Under
 *                              stale-while-revalidate that pairing was a bug, not an
 *                              optimisation: a returning visitor ran the NEW ui against the
 *                              engine and house cached on their last visit, and a version skew
 *                              between them boots to "Cannot reach engine" — while a browser
 *                              that has never been here works perfectly, which is exactly how it
 *                              presented. Both carry `max-age=0, must-revalidate` (landing/
 *                              _headers) and are byte-deterministic, so the steady-state cost of
 *                              going to the network first is a 304, and offline still falls back
 *                              to the cached copy.
 *  - other same-origin      → stale-while-revalidate (the manifest, the icons): small, and
 *                              nothing pairs with the app build.
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
// v4: evicts every v3 entry, including the stale engine/house pairs the old
// stale-while-revalidate rule left behind, and the now-renamed .tar.
const CACHE_VERSION = "typehaus-v4";
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
// `/sheets` and `/notes` are the served (documents_api.py) reads. The PWA's own bundled copy
// lives at `<base>sheets/…` — a different path — so it falls through to stale-while-revalidate,
// which is what the manifest's content hash on the PDF's query string is there to make visible.
const API_PREFIXES = [
  "/model", "/checks", "/details", "/detail", "/plan", "/preview", "/macro",
  "/build", "/undo", "/redo", "/events", "/underlays", "/sheets", "/notes",
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

// The assets that keep a stable URL across deploys and must match the app build that asks for
// them. Matched by basename so the same worker serves `haus serve` (which mounts the same dist)
// and the published site. In steady state these cost two conditional requests, not their bulk:
// both are `max-age=0, must-revalidate` with a stable ETag, so an unchanged deploy answers 304
// and `fetch` resolves out of the browser's own HTTP cache.
const RUNTIME_BUNDLES = ["typehaus-engine.tar.gz", "typehaus-ifc-ext.tar", "catlin-house.json"];

function isRuntimeBundle(url) {
  return RUNTIME_BUNDLES.some((name) => url.pathname.endsWith("/" + name));
}

// Network-first: the deploy wins whenever we can reach it, the cache answers when we cannot.
// The cache is still written on every success, which is what keeps the offline boot working.
async function networkFirst(request, cacheName) {
  const cache = await caches.open(cacheName);
  try {
    const response = await fetch(request);
    if (response && response.ok) cache.put(request, response.clone());
    return response;
  } catch (err) {
    const cached = await cache.match(request);
    if (cached) return cached;
    throw err;
  }
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
    let strategy = staleWhileRevalidate;
    if (isImmutableBuildAsset(url)) strategy = cacheFirst;
    else if (isRuntimeBundle(url)) strategy = networkFirst;
    event.respondWith(strategy(request, SHELL_CACHE));
    return;
  }

  // Cross-origin (pyodide CDN, wheels): cache-first so the engine loads offline next time.
  event.respondWith(cacheFirst(request, RUNTIME_CACHE));
});
