/// <reference types="vite/client" />

// Python source imported as a string for the pyodide worker (→ 40 WP4.2).
declare module "*.py?raw" {
  const src: string;
  export default src;
}

interface ImportMetaEnv {
  // "1" in the standalone PWA build (type-house.com/app): boot the bundled Catlin house in the
  // offline pyodide engine by default. Unset for local `haus serve` builds.
  readonly VITE_PWA_STANDALONE?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
