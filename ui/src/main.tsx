import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import { registerPwa } from "./pwa/register";
import { initializeTheme, initializeDensity } from "./theme/theme";
import { useStore } from "./state/store";
import "./styles/index.css";

initializeTheme();
initializeDensity();
registerPwa();

// Screenshot-harness control surface (scripts/shoot.mjs). There is no Playwright and no UI
// test runner here, so the shot rig is the only automated gate — and driving it by clicking
// chrome would make it break every time the chrome is refactored, which is exactly when the
// gate matters most. Posing states through the store instead keeps the harness stable across
// the layout work. Read-only from the harness's side; ships in prod because `haus serve`
// serves the production build and there is nothing here a user cannot already do in the UI.
(window as unknown as { __haus?: unknown }).__haus = { store: useStore };

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
