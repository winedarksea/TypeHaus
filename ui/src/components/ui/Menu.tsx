import { useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { Icon } from "../../icons/Icon";
import type { IconName } from "../../icons/names";

export interface MenuItemSpec {
  id: string;
  label: string;
  icon?: IconName;
  hint?: string;
  /** Rendered right-aligned — shortcuts, or the current value of a setting. */
  trailing?: ReactNode;
  selected?: boolean;
  disabled?: boolean;
  danger?: boolean;
  onSelect: () => void;
}

export interface MenuSection {
  id: string;
  label?: string;
  items: MenuItemSpec[];
}

const MENU_VIEWPORT_MARGIN_PX = 8;

/**
 * An anchored popup menu: trigger button plus the surface it opens.
 *
 * Exists because the top bar had roughly twenty controls in a 44px flex row with no overflow
 * handling at all, so anything past the halfway point was simply clipped away and unreachable
 * — at 1024px, not just on a phone. Collapsing groups behind a menu is what makes the bar fit.
 *
 * Closes on outside pointerdown (not click, so it dismisses before the underlying control
 * activates), on Escape, and on select. Arrow keys move a roving focus; the trigger keeps
 * aria-expanded/aria-haspopup so the whole thing is operable without a pointer.
 */
export function Menu({ label, icon, items, sections, align = "end", triggerClassName, showLabel = true, title }: {
  label: string;
  icon?: IconName;
  items?: MenuItemSpec[];
  sections?: MenuSection[];
  /** Which edge of the trigger the surface lines up with. */
  align?: "start" | "end";
  triggerClassName?: string;
  showLabel?: boolean;
  title?: string;
}) {
  const [open, setOpen] = useState(false);
  const [focusIndex, setFocusIndex] = useState(-1);
  const rootRef = useRef<HTMLDivElement>(null);
  const surfaceRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  const resolved: MenuSection[] = sections ?? [{ id: "default", items: items ?? [] }];
  const flat = resolved.flatMap((section) => section.items);

  useEffect(() => {
    if (!open) return;
    const onPointerDown = (e: PointerEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();   // don't also trip App's Esc hierarchy
        setOpen(false);
        rootRef.current?.querySelector("button")?.focus();
      }
    };
    window.addEventListener("pointerdown", onPointerDown);
    window.addEventListener("keydown", onKey, true);
    return () => {
      window.removeEventListener("pointerdown", onPointerDown);
      window.removeEventListener("keydown", onKey, true);
    };
  }, [open]);

  // Nudge the surface back inside the viewport. The top bar's trailing controls sit hard
  // against the right edge, so an end-aligned menu would otherwise hang off-screen —
  // exactly the failure this component exists to fix.
  useLayoutEffect(() => {
    if (!open) return;
    const surface = surfaceRef.current;
    if (!surface) return;
    surface.style.transform = "";
    const rect = surface.getBoundingClientRect();
    const overflowRight = rect.right - (window.innerWidth - MENU_VIEWPORT_MARGIN_PX);
    const overflowLeft = MENU_VIEWPORT_MARGIN_PX - rect.left;
    if (overflowRight > 0) surface.style.transform = `translateX(${-overflowRight}px)`;
    else if (overflowLeft > 0) surface.style.transform = `translateX(${overflowLeft}px)`;
  }, [open]);

  const move = (delta: number) => {
    const enabled = flat.map((item, i) => (item.disabled ? -1 : i)).filter((i) => i >= 0);
    if (enabled.length === 0) return;
    const current = enabled.indexOf(focusIndex);
    const next = current === -1
      ? enabled[delta > 0 ? 0 : enabled.length - 1]
      : enabled[(current + delta + enabled.length) % enabled.length];
    setFocusIndex(next);
    const node = surfaceRef.current?.querySelectorAll<HTMLButtonElement>("[role='menuitem']")[next];
    node?.focus();
  };

  return (
    <div className="menu-root" ref={rootRef}>
      <button
        className={triggerClassName ?? "btn"}
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        title={title ?? label}
        onClick={() => { setOpen(!open); setFocusIndex(-1); }}
        onKeyDown={(e) => {
          if (e.key === "ArrowDown") { e.preventDefault(); setOpen(true); requestAnimationFrame(() => move(1)); }
        }}
      >
        {icon && <Icon name={icon} />}
        {showLabel && <span className="menu-trigger-label">{label}</span>}
        {showLabel && <Icon name="chevron-down" size={16} className="menu-trigger-caret" />}
      </button>

      {open && (
        <div
          id={menuId}
          ref={surfaceRef}
          className={`menu-surface menu-align-${align}`}
          role="menu"
          aria-label={label}
          onKeyDown={(e) => {
            if (e.key === "ArrowDown") { e.preventDefault(); move(1); }
            else if (e.key === "ArrowUp") { e.preventDefault(); move(-1); }
          }}
        >
          {resolved.map((section) => (
            <div className="menu-section" key={section.id}>
              {section.label && <div className="menu-section-label">{section.label}</div>}
              {section.items.map((item) => (
                <button
                  key={item.id}
                  role="menuitem"
                  className={`menu-item${item.selected ? " selected" : ""}${item.danger ? " danger" : ""}`}
                  disabled={item.disabled}
                  title={item.hint}
                  aria-checked={item.selected}
                  onClick={() => { item.onSelect(); setOpen(false); }}
                >
                  {item.icon
                    ? <Icon name={item.icon} className="menu-item-icon" />
                    : <span className="menu-item-icon" aria-hidden />}
                  <span className="menu-item-label">{item.label}</span>
                  {item.trailing && <span className="menu-item-trailing">{item.trailing}</span>}
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
