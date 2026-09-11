import type { ReactNode } from "react";
import { Sheet } from "../ui/Sheet";
import { Icon } from "../../icons/Icon";
import { useIsCompact } from "../../hooks/useBreakpoint";

/**
 * One detail body, two presentations: a modal bottom sheet on a phone, a fixed side sheet
 * from medium up.
 *
 * The body component is shared rather than duplicated — the visit detail is a long
 * checklist either way, and two copies of it would drift the moment one gained a field.
 */
export function DetailHost({ title, onClose, children }: {
  title: string;
  onClose: () => void;
  children: ReactNode;
}) {
  const compact = useIsCompact();
  if (compact) return <Sheet title={title} onClose={onClose}>{children}</Sheet>;
  return (
    <aside className="site-side-sheet" role="dialog" aria-modal="false" aria-label={title}>
      <header className="site-side-sheet-head">
        <h2 className="site-side-sheet-title">{title}</h2>
        <button className="btn icon-btn" onClick={onClose} aria-label={`Close ${title}`}>
          <Icon name="close" />
        </button>
      </header>
      <div className="site-side-sheet-body">{children}</div>
    </aside>
  );
}
