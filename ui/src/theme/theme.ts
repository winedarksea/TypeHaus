import { useEffect, useState, useSyncExternalStore } from "react";

export type ThemePreference = "system" | "light" | "dark";
export type ResolvedTheme = Exclude<ThemePreference, "system">;

// Density profile drives --hit, row heights, and padding via a data-density attribute,
// mirroring the data-theme mechanism (Phase 1). Desktop-pointer first → default comfortable.
export type Density = "compact" | "comfortable" | "touch";

export const THEME_STORAGE_KEY = "typehaus.theme-preference";
export const DENSITY_STORAGE_KEY = "typehaus.density-profile";
const DARK_MEDIA_QUERY = "(prefers-color-scheme: dark)";

export function parseDensity(value: string | null): Density {
  return value === "compact" || value === "comfortable" || value === "touch"
    ? value
    : "comfortable";
}

export function savedDensity(): Density {
  try {
    return parseDensity(window.localStorage.getItem(DENSITY_STORAGE_KEY));
  } catch {
    return "comfortable";
  }
}

export function applyDensity(density: Density): Density {
  document.documentElement.dataset.density = density;
  return density;
}

// Called before React mounts so the cached density does not flash the wrong metrics.
export function initializeDensity(): Density {
  return applyDensity(savedDensity());
}

export function useDensity(): {
  density: Density;
  setDensity: (density: Density) => void;
} {
  const [density, setDensityState] = useState<Density>(savedDensity);

  useEffect(() => {
    applyDensity(density);
  }, [density]);

  const setDensity = (next: Density) => {
    try {
      window.localStorage.setItem(DENSITY_STORAGE_KEY, next);
    } catch {
      // Private browsing may reject storage; the in-memory choice still applies.
    }
    setDensityState(next);
  };

  return { density, setDensity };
}

export function parseThemePreference(value: string | null): ThemePreference {
  return value === "light" || value === "dark" || value === "system" ? value : "system";
}

export function resolveTheme(preference: ThemePreference, systemPrefersDark: boolean): ResolvedTheme {
  return preference === "system" ? (systemPrefersDark ? "dark" : "light") : preference;
}

function systemPrefersDark(): boolean {
  return typeof window !== "undefined" && window.matchMedia(DARK_MEDIA_QUERY).matches;
}

export function savedThemePreference(): ThemePreference {
  try {
    return parseThemePreference(window.localStorage.getItem(THEME_STORAGE_KEY));
  } catch {
    return "system";
  }
}

function updateThemeColor(theme: ResolvedTheme): void {
  const color = theme === "dark" ? "#2E3440" : "#f4f2ed";
  for (const tag of document.querySelectorAll<HTMLMetaElement>('meta[name="theme-color"]')) tag.content = color;
}

export function applyTheme(preference: ThemePreference): ResolvedTheme {
  const theme = resolveTheme(preference, systemPrefersDark());
  document.documentElement.dataset.theme = theme;
  document.documentElement.style.colorScheme = theme;
  updateThemeColor(theme);
  return theme;
}

// Called before React mounts so cached overrides do not flash the wrong palette.
export function initializeTheme(): ThemePreference {
  const preference = savedThemePreference();
  applyTheme(preference);
  return preference;
}

/**
 * The theme is ONE piece of state with several readers, so it lives in a module store rather
 * than in each hook call's useState.
 *
 * It was per-instance useState, and that made every caller its own island: the overflow menu
 * flipped the preference and re-rendered itself, `applyTheme` wrote data-theme on <html> so the
 * whole stylesheet followed — and Panel3D, whose useTheme() is a separate useState, was never
 * told. Its three.js scene kept the palette it had mounted with, so a runtime toggle left the
 * 3D backdrop, the schematic material tints and the selection highlight on the old theme while
 * every CSS surface around them changed. Reloading the page "fixed" it because the fresh mount
 * read the stored preference.
 *
 * useSyncExternalStore is the primitive for exactly this: one value, every reader re-rendered
 * on a write. Any future useTheme() caller is correct by construction.
 */
interface ThemeState {
  readonly preference: ThemePreference;
  readonly theme: ResolvedTheme;
}

// Cached, and replaced wholesale on a change: getSnapshot must return a referentially stable
// value between writes or useSyncExternalStore re-renders forever.
let themeState: ThemeState | null = null;
const themeListeners = new Set<() => void>();

function themeSnapshot(): ThemeState {
  if (!themeState) {
    const preference = savedThemePreference();
    themeState = { preference, theme: resolveTheme(preference, systemPrefersDark()) };
  }
  return themeState;
}

function publishThemeState(next: ThemeState): void {
  themeState = next;
  for (const listener of themeListeners) listener();
}

// The OS preference moving only matters while the preference is "system"; resolveTheme already
// encodes that, so this is a no-op write for an explicit light/dark and publishes nothing.
function refreshResolvedTheme(): void {
  const { preference, theme } = themeSnapshot();
  const resolved = applyTheme(preference);
  if (resolved !== theme) publishThemeState({ preference, theme: resolved });
}

function subscribeTheme(listener: () => void): () => void {
  themeListeners.add(listener);
  // One media listener for the whole app, attached with the first subscriber rather than per
  // hook instance — the old code added one per caller.
  if (themeListeners.size === 1) {
    window.matchMedia(DARK_MEDIA_QUERY).addEventListener("change", refreshResolvedTheme);
  }
  return () => {
    themeListeners.delete(listener);
    if (themeListeners.size === 0) {
      window.matchMedia(DARK_MEDIA_QUERY).removeEventListener("change", refreshResolvedTheme);
    }
  };
}

export function useTheme(): {
  preference: ThemePreference;
  theme: ResolvedTheme;
  setPreference: (preference: ThemePreference) => void;
} {
  const { preference, theme } = useSyncExternalStore(subscribeTheme, themeSnapshot);

  const setPreference = (next: ThemePreference) => {
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, next);
    } catch {
      // Private browsing may reject storage; the in-memory choice still applies.
    }
    // applyTheme does the DOM side of the switch and hands back what "system" resolved to.
    publishThemeState({ preference: next, theme: applyTheme(next) });
  };

  return { preference, theme, setPreference };
}
