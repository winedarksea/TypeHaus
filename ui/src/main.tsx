import React from "react";
import ReactDOM from "react-dom/client";
import { App } from "./App";
import { registerPwa } from "./pwa/register";
import { initializeTheme } from "./theme/theme";
import "./styles.css";

initializeTheme();
registerPwa();

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);
