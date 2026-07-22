import { useEffect, useState } from "react";

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

export function useTheme(): {
  preference: ThemePreference;
  theme: ResolvedTheme;
  setPreference: (preference: ThemePreference) => void;
} {
  const [preference, setPreferenceState] = useState<ThemePreference>(savedThemePreference);
  const [theme, setTheme] = useState<ResolvedTheme>(() => applyTheme(savedThemePreference()));

  useEffect(() => {
    const media = window.matchMedia(DARK_MEDIA_QUERY);
    const refresh = () => setTheme(applyTheme(preference));
    refresh();
    media.addEventListener("change", refresh);
    return () => media.removeEventListener("change", refresh);
  }, [preference]);

  const setPreference = (next: ThemePreference) => {
    try {
      window.localStorage.setItem(THEME_STORAGE_KEY, next);
    } catch {
      // Private browsing may reject storage; the in-memory choice still applies.
    }
    setPreferenceState(next);
  };

  return { preference, theme, setPreference };
}
