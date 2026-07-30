import { useStore } from "../../state/store";
import { useTheme, useDensity, type ThemePreference, type Density } from "../../theme/theme";
import { promptInstall, type PwaState } from "../../pwa/register";
import { Menu, type MenuSection } from "../ui/Menu";
import { REPORTS } from "./navigationConfig";
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
export function OverflowMenu({ pwa, compact = false }: { pwa: PwaState; compact?: boolean }) {
  const { preference: themePreference, setPreference: setThemePreference } = useTheme();
  const { density, setDensity } = useDensity();
  const connected = useStore((s) => s.connected);
  const detailView = useStore((s) => s.detailView);
  const setDetailView = useStore((s) => s.setDetailView);
  const setCommandPaletteOpen = useStore((s) => s.setCommandPaletteOpen);
  const undo = useStore((s) => s.undo);
  const redo = useStore((s) => s.redo);

  const sections: MenuSection[] = [
    // On a phone these are not overflow in the "rarely used" sense — they are the constant
    // actions the bar no longer has room for, so they come first.
    ...(compact
      ? [
          {
            id: "reports",
            label: "Reports",
            items: REPORTS.map((report) => ({
              id: report.id,
              label: report.label,
              icon: report.icon,
              hint: report.hint,
              selected: detailView === report.id,
              onSelect: () => setDetailView(detailView === report.id ? "none" : report.id),
            })),
          },
          {
            id: "actions",
            label: "Edit",
            items: [
              { id: "undo", label: "Undo", icon: "undo" as IconName, onSelect: () => { void undo(); } },
              { id: "redo", label: "Redo", icon: "redo" as IconName, onSelect: () => { void redo(); } },
              { id: "search", label: "Command palette", icon: "search" as IconName,
                onSelect: () => setCommandPaletteOpen(true) },
            ],
          },
        ]
      : []),
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
