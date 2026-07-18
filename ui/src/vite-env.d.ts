/// <reference types="vite/client" />

// Python source imported as a string for the pyodide worker (→ 40 WP4.2).
declare module "*.py?raw" {
  const src: string;
  export default src;
}
