// PWA runtime glue (→ 40 WP4.2): registers the service worker, tracks online/offline, and
// captures the `beforeinstallprompt` event so the UI can offer an install button. Kept out of
// React so it runs before first paint; components read state via the small event bus below.

export interface PwaState {
  online: boolean;
  installable: boolean;
  installed: boolean;
}

type Listener = (s: PwaState) => void;

let deferredPrompt: BeforeInstallPromptEvent | null = null;
const listeners = new Set<Listener>();

const state: PwaState = {
  online: navigator.onLine,
  installable: false,
  installed:
    window.matchMedia?.("(display-mode: standalone)").matches ||
    // iOS Safari
    (navigator as { standalone?: boolean }).standalone === true,
};

function emit(): void {
  for (const l of listeners) l({ ...state });
}

export function subscribePwa(listener: Listener): () => void {
  listeners.add(listener);
  listener({ ...state });
  return () => listeners.delete(listener);
}

export function getPwaState(): PwaState {
  return { ...state };
}

// Trigger the browser install flow; resolves to true if the user accepted.
export async function promptInstall(): Promise<boolean> {
  if (!deferredPrompt) return false;
  const prompt = deferredPrompt;
  deferredPrompt = null;
  state.installable = false;
  emit();
  await prompt.prompt();
  const choice = await prompt.userChoice;
  return choice.outcome === "accepted";
}

export function registerPwa(): void {
  window.addEventListener("online", () => {
    state.online = true;
    emit();
  });
  window.addEventListener("offline", () => {
    state.online = false;
    emit();
  });

  window.addEventListener("beforeinstallprompt", (e) => {
    e.preventDefault();
    deferredPrompt = e as BeforeInstallPromptEvent;
    state.installable = true;
    emit();
  });

  window.addEventListener("appinstalled", () => {
    state.installed = true;
    state.installable = false;
    deferredPrompt = null;
    emit();
  });

  if ("serviceWorker" in navigator) {
    // Register after load so the SW install doesn't contend with first paint.
    window.addEventListener("load", () => {
      const swUrl = new URL("sw.js", document.baseURI).href;
      navigator.serviceWorker.register(swUrl).catch((err) => {
        console.warn("[pwa] service worker registration failed", err);
      });
    });
  }
}

// The event isn't in the DOM lib yet.
interface BeforeInstallPromptEvent extends Event {
  prompt(): Promise<void>;
  readonly userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}
