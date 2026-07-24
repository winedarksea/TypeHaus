// House-directory access for the offline PWA via the File System Access API (→ 40 WP4.2).
// Reads a house folder into an in-memory { relpath: text } map that the pyodide worker writes
// into its virtual FS. Read-only: we never write back offline (mutation is the local-serve
// path). Location-independent by construction (→ 02 §Git topology) — any folder with a plan/.

import type { HouseFiles } from "./PyodideEngineClient";

export function fsAccessSupported(): boolean {
  return typeof (window as { showDirectoryPicker?: unknown }).showDirectoryPicker === "function";
}

// Text files the engine's plan loader consumes. Binary (out/*.glb, images) is skipped.
const TEXT_EXT = /\.(py|toml|md|json|txt|cfg|ini)$/i;
// Never descend into build output / caches / vcs.
const SKIP_DIR = new Set(["out", "__pycache__", ".git", "node_modules", ".venv", "dist"]);

interface DirHandle {
  name: string;
  entries(): AsyncIterableIterator<[string, FileSystemHandle]>;
}

async function walk(
  dir: DirHandle,
  prefix: string,
  out: HouseFiles,
): Promise<void> {
  for await (const [name, handle] of dir.entries()) {
    const rel = prefix ? `${prefix}/${name}` : name;
    if (handle.kind === "directory") {
      if (SKIP_DIR.has(name)) continue;
      await walk(handle as unknown as DirHandle, rel, out);
    } else if (TEXT_EXT.test(name)) {
      const file = await (handle as unknown as FileSystemFileHandle).getFile();
      out[rel] = await file.text();
    }
  }
}

export interface OpenedHouse {
  name: string;
  files: HouseFiles;
}

// The Catlin house bundled into the app (built by scripts/build-house-asset.mjs). Loaded by
// default when the PWA runs standalone (no local `haus serve`), so a first-time visitor lands
// in a real house with no folder pick (U9).
export async function loadBundledHouse(
  file = "catlin-house.json",
  name = "Catlin house (demo)",
): Promise<OpenedHouse> {
  const url = new URL(file, document.baseURI).href;
  const res = await fetch(url);
  if (!res.ok) throw new Error(`bundled house ${res.status} @ ${url}`);
  const files = (await res.json()) as HouseFiles;
  if (!Object.keys(files).some((p) => p.includes("plan"))) {
    throw new Error("bundled house asset has no plan/ files");
  }
  return { name, files };
}

export async function pickHouseDirectory(): Promise<OpenedHouse | null> {
  const picker = (window as {
    showDirectoryPicker?: () => Promise<DirHandle>;
  }).showDirectoryPicker;
  if (!picker) throw new Error("File System Access API unavailable in this browser");
  let handle: DirHandle;
  try {
    handle = await picker();
  } catch (err) {
    // AbortError = user cancelled the picker.
    if ((err as DOMException)?.name === "AbortError") return null;
    throw err;
  }
  const files: HouseFiles = {};
  await walk(handle, "", files);
  if (!Object.keys(files).some((p) => p.includes("plan"))) {
    throw new Error(`"${handle.name}" has no plan/ — pick a Type:Haus house directory`);
  }
  return { name: handle.name, files };
}
