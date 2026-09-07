import { useEffect, type RefObject } from "react";

/**
 * Close a docked panel when the pointer goes down outside it.
 *
 * The Views and Project panels are `position: absolute` over the canvas with no scrim, so
 * every way out of them was the X button in their own header — including for a user who had
 * already moved on and tapped the drawing. That is a modal's exit affordance on a
 * non-modal surface.
 *
 * Two exclusions, both load-bearing:
 *
 *  - the panel itself, obviously; and
 *  - the chrome that *toggles* it. The rail item is a toggle, so a pointerdown on it would
 *    close the panel here and the click would immediately reopen it — the panel would
 *    appear not to close at all.
 *
 * Capture phase for the same reason `ui/Menu.tsx` uses it: a child that stops propagation
 * (the canvas swallows pointer events while drawing) must not also swallow the dismissal.
 */

/** Chrome whose own click already decides what the panel does. */
const TOGGLE_CHROME = ".nav-rail, .topbar, .bottom-nav";

export function useLightDismiss(
  ref: RefObject<HTMLElement>,
  open: boolean,
  onDismiss: () => void,
): void {
  useEffect(() => {
    if (!open) return;
    const onPointerDown = (event: PointerEvent) => {
      const target = event.target as Element | null;
      if (!target) return;
      if (ref.current?.contains(target)) return;
      if (target.closest?.(TOGGLE_CHROME)) return;
      // A menu, popover or dialog that escaped the panel's DOM (they are `position: fixed`
      // precisely so they can) is still part of the panel as far as the user is concerned.
      if (target.closest?.(".menu-surface, [role='dialog'], [role='menu']")) return;
      onDismiss();
    };
    window.addEventListener("pointerdown", onPointerDown, true);
    return () => window.removeEventListener("pointerdown", onPointerDown, true);
  }, [ref, open, onDismiss]);
}
