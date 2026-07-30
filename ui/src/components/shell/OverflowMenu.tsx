import { useStore } from "../../state/store";
import { useTheme, useDensity, type ThemePreference, type Density } from "../../theme/theme";
import { promptInstall, type PwaState } from "../../pwa/register";
import { Menu, type MenuSection } from "../ui/Menu";
import type { IconName } from "../../icons/names";

const DENSITIES: { id: Density; label: string; icon: IconName }[] = [
  { id: "compact", label: "Compact", icon: "density-compact" },
  { id: "comfortable", label: "Comfortable", icon: "density-comfortable" },
  { id: "touch", label: "Touch", icon: "density-touch" },
];

const THEMES: { id: ThemePreference; label: string; icon: IconName }[] = [
  { id: "system", label: "Match system", icon: "theme-system" },
  { id: "light", label: "Light", icon: "theme-light" },
  { id: "dark", label: "Dark", icon: "theme-dark" },
];

/**
 * The top bar's ⋮ menu: preferences and occasional actions.
 *
 * Density and appearance were six always-visible segmented buttons pinned to the right edge
 * — the controls a user touches least, holding the space that the controls they touch most
 * needed, and the first things to fall off a narrow viewport. They belong behind an overflow.
 */
export function OverflowMenu({ pwa }: { pwa: PwaState }) {
  const { preference: themePreference, setPreference: setThemePreference } = useTheme();
  const { density, setDensity } = useDensity();
  const connected = useStore((s) => s.connected);

  const sections: MenuSection[] = [
    {
      id: "density",
      label: "Density",
      items: DENSITIES.map((d) => ({
        id: `density-${d.id}`,
        label: d.label,
        icon: d.icon,
        selected: density === d.id,
        onSelect: () => setDensity(d.id),
      })),
    },
    {
      id: "appearance",
      label: "Appearance",
      items: THEMES.map((t) => ({
        id: `theme-${t.id}`,
        label: t.label,
        icon: t.icon,
        selected: themePreference === t.id,
        onSelect: () => setThemePreference(t.id),
      })),
    },
    {
      id: "app",
      label: "App",
      items: [
        ...(pwa.installable
          ? [{
              id: "install",
              label: "Install Type:Haus",
              icon: "install" as IconName,
              onSelect: () => { void promptInstall(); },
            }]
          : []),
        {
          id: "engine",
          label: connected ? "Engine connected" : "Engine disconnected",
          // Status, not an action. Disabled so it reads as a readout and cannot be "chosen",
          // while still being reachable by a keyboard user who wants to know.
          disabled: true,
          onSelect: () => {},
        },
      ],
    },
  ];

  return (
    <Menu
      label="More"
      title="More — density, appearance, app"
      icon="more-vertical"
      showLabel={false}
      sections={sections}
      align="end"
      triggerClassName="btn icon-btn"
    />
  );
}
