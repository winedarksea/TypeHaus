import { useCallback, useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";
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
export function Menu({
  label, icon, items, sections, align = "end", placement = "below",
  triggerClassName, showLabel = true, triggerContent, title,
}: {
  label: string;
  icon?: IconName;
  items?: MenuItemSpec[];
  sections?: MenuSection[];
  /** Which edge of the trigger the surface lines up with. */
  align?: "start" | "end";
  /** "below" for bar triggers; "side" opens alongside, for the vertical rail. */
  placement?: "below" | "side";
  triggerClassName?: string;
  showLabel?: boolean;
  /**
   * Custom trigger content. The navigation rail's items are an icon inside an active
   * indicator with a label beneath, which the default flat icon + text cannot express —
   * and a rail item without its label is just an unexplained glyph.
   */
  triggerContent?: ReactNode;
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

  /**
   * Position the surface in viewport coordinates.
   *
   * It is `position: fixed`, not absolute, because a menu must be able to escape its
   * container: the navigation rail scrolls, and a scroll container clips its children on
   * BOTH axes — `overflow-x: visible` alongside `overflow-y: auto` is not a thing the CSS
   * spec allows, it computes to auto. That is what made the Build group's tool palette
   * render at full size, entirely outside the 72px rail, and be 100% invisible.
   *
   * Also keeps the surface inside the viewport: top-bar triggers sit hard against the right
   * edge, and a bottom-anchored trigger has to open upward.
   */
  const place = useCallback(() => {
    const surface = surfaceRef.current;
    const trigger = rootRef.current?.querySelector("button");
    if (!surface || !trigger) return;
    const t = trigger.getBoundingClientRect();
    const { width, height } = surface.getBoundingClientRect();
    const margin = MENU_VIEWPORT_MARGIN_PX;

    if (placement === "side") {
      // Alongside the trigger, so a vertical rail's own labels stay readable instead of
      // being covered by the menu that one of its items opened.
      let left = t.right + 8;
      if (left + width > window.innerWidth - margin) left = t.left - width - 8;
      const top = Math.min(Math.max(margin, t.top), window.innerHeight - height - margin);
      surface.style.left = `${Math.round(Math.max(margin, left))}px`;
      surface.style.top = `${Math.round(top)}px`;
      return;
    }

    let left = align === "end" ? t.right - width : t.left;
    left = Math.min(Math.max(margin, left), window.innerWidth - width - margin);

    // Prefer below; flip above when there is not room and there is room up there.
    const belowTop = t.bottom + 4;
    const flip = belowTop + height > window.innerHeight - margin && t.top - height - 4 > margin;
    const top = flip ? t.top - height - 4 : Math.min(belowTop, window.innerHeight - height - margin);

    surface.style.left = `${Math.round(left)}px`;
    surface.style.top = `${Math.round(Math.max(margin, top))}px`;
  }, [align, placement]);

  useLayoutEffect(() => {
    if (!open) return;
    place();
    // A scroll anywhere in the ancestor chain moves the trigger out from under the surface.
    window.addEventListener("scroll", place, true);
    window.addEventListener("resize", place);
    return () => {
      window.removeEventListener("scroll", place, true);
      window.removeEventListener("resize", place);
    };
  }, [open, place]);

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
        {triggerContent ?? (
          <>
            {icon && <Icon name={icon} />}
            {showLabel && <span className="menu-trigger-label">{label}</span>}
            {showLabel && <Icon name="chevron-down" size={16} className="menu-trigger-caret" />}
          </>
        )}
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
