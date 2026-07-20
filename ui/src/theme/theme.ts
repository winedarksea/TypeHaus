import { useEffect, useState } from "react";

export type ThemePreference = "system" | "light" | "dark";
export type ResolvedTheme = Exclude<ThemePreference, "system">;

export const THEME_STORAGE_KEY = "typehaus.theme-preference";
const DARK_MEDIA_QUERY = "(prefers-color-scheme: dark)";

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
