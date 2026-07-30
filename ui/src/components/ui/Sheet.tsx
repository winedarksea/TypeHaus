import { useEffect, useRef, type ReactNode } from "react";
import { Icon } from "../../icons/Icon";

const FOCUSABLE =
  'a[href], button:not(:disabled), input:not(:disabled), select:not(:disabled),'
  + ' textarea:not(:disabled), [tabindex]:not([tabindex="-1"])';

/**
 * A bottom sheet — how the side panels present themselves on a phone.
 *
 * Dismissal is scrim tap, Escape, and an explicit close button. The MD3 drag handle is drawn
 * because it is the affordance people look for, and it is itself a close button — but
 * drag-to-dismiss is deliberately NOT implemented. Arbitrating that gesture against the
 * sheet's own scrolling ("only drag when scrollTop is 0, and only if the gesture started
 * downward") is a pointer state machine with no library and no test runner behind it, and
 * three working dismissal paths are enough. Add the gesture later if it is actually missed.
 *
 * The focus trap is not optional: without it, Tab from a full-screen sheet walks into the
 * SVG behind it and the user is editing a drawing they cannot see.
 */
export function Sheet({ title, onClose, children }: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const panel = panelRef.current;
    panel?.querySelector<HTMLElement>(FOCUSABLE)?.focus();

    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.stopPropagation();
        onClose();
        return;
      }
      if (e.key !== "Tab" || !panel) return;
      const focusable = [...panel.querySelectorAll<HTMLElement>(FOCUSABLE)];
      if (focusable.length === 0) return;
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (e.shiftKey && document.activeElement === first) { e.preventDefault(); last.focus(); }
      else if (!e.shiftKey && document.activeElement === last) { e.preventDefault(); first.focus(); }
    };
    window.addEventListener("keydown", onKey, true);
    return () => window.removeEventListener("keydown", onKey, true);
  }, [onClose]);

  return (
    <div className="sheet-scrim" onPointerDown={onClose}>
      <div
        className="sheet"
        role="dialog"
        aria-modal="true"
        aria-label={title}
        ref={panelRef}
        onPointerDown={(e) => e.stopPropagation()}
      >
        <button className="sheet-handle" onClick={onClose} title={`Close ${title}`} aria-label={`Close ${title}`}>
          <span className="sheet-handle-grip" aria-hidden />
        </button>
        <div className="sheet-head">
          <h2 className="sheet-title">{title}</h2>
          <button className="btn icon-btn" onClick={onClose} aria-label={`Close ${title}`}>
            <Icon name="close" />
          </button>
        </div>
        <div className="sheet-body">{children}</div>
      </div>
    </div>
  );
}
