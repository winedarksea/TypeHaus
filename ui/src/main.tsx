import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import { registerPwa } from "./pwa/register";
import { initializeTheme, initializeDensity } from "./theme/theme";
import { useStore } from "./state/store";
import { installRouteSync } from "./state/route";
import { installViewUrlSync } from "./state/viewUrl";
import "./styles/index.css";

initializeTheme();
initializeDensity();
registerPwa();

// A tab that outlived a rebuild asks for chunk names that no longer exist. Reload once for the
// current entry bundle; `?reader=` survives it. Time-guarded, not flag-guarded: a reader opened
// from the URL fails again on every boot, and a flag cleared at boot would loop.
window.addEventListener("vite:preloadError", () => {
  const key = "haus:chunk-reload";
  try {
    const last = Number(sessionStorage.getItem(key) ?? 0);
    if (Date.now() - last < 10_000) return;
    sessionStorage.setItem(key, String(Date.now()));
  } catch {
    return; // no storage, no loop guard: leave it to the reader error boundary
  }
  window.location.reload();
});

// Screenshot-harness control surface (scripts/shoot.mjs). There is no Playwright and no UI
// test runner here, so the shot rig is the only automated gate — and driving it by clicking
// chrome would make it break every time the chrome is refactored, which is exactly when the
// gate matters most. Posing states through the store instead keeps the harness stable across
// the layout work. Read-only from the harness's side; ships in prod because `haus serve`
// serves the production build and there is nothing here a user cannot already do in the UI.
(window as unknown as { __haus?: unknown }).__haus = { store: useStore };

// Before the first render, so a cold load of `#/site/board` never paints the design
// workbench first — which would mount the canvas and fetch the three.js chunk on a phone
// that is not going to use either.
installRouteSync(useStore);
// Query params name the design view (`?preset=framer`); the address bar stays a shareable link.
installViewUrlSync(useStore);

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
