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
  // URL of an ifcopenshell wheel built for pyodide/wasm. When set (or when the build vendors a
  // wheel into public/, served same-origin), the client-side IFC export path activates via
  // ensureIfc → micropip.install → enable_ifc. Unset by default: IFC export cleanly degrades
  // with the RequiresLocalInstall message. See docs/ifc-wasm.md.
  readonly VITE_IFC_WASM_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
