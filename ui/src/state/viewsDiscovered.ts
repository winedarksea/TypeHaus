// Whether this viewer has ever opened Views: the rail's primary tile pulses until they have.
const DISCOVERED_KEY = "typehaus.viewsDiscovered";

// A per-viewer convenience: storage may be absent or throw (private window, previews).
export function viewsDiscovered(): boolean {
  try {
    return globalThis.localStorage?.getItem(DISCOVERED_KEY) === "1";
  } catch {
    return false;
  }
}

export function markViewsDiscovered(): void {
  try {
    globalThis.localStorage?.setItem(DISCOVERED_KEY, "1");
  } catch {
    // Not remembered; the pulse returns next session.
  }
}
