import { useStore } from "../../state/store";
import { Icon } from "../../icons/Icon";
import { REPORTS } from "../shell/navigationConfig";
import { HIDDEN_REPORTS } from "../../state/public";

/**
 * The full-screen readers, as cards.
 *
 * They were a top-bar menu, which put them a click away but gave them no room to say what
 * they were for — seven one-line labels in a dropdown. A card can carry the hint, and the
 * hub is where a reader belongs anyway: an assembly stack and a panel schedule are two more
 * things a contractor reads, beside the drawings and the notes.
 *
 * `readerOrigin` is set before the reader opens so its Back comes here rather than to the
 * canvas — the reader itself is unchanged and does not know where it was opened from.
 */
export function ReportsTab() {
  const setDetailView = useStore((s) => s.setDetailView);
  const setReaderOrigin = useStore((s) => s.setReaderOrigin);

  const shown = REPORTS.filter((report) => !HIDDEN_REPORTS.has(report.id));

  return (
    <div className="doc-card-grid">
      {shown.map((report) => (
        <button
          key={report.id}
          className="doc-card"
          onClick={() => { setReaderOrigin("documents"); setDetailView(report.id); }}
        >
          <span className="doc-card-title">
            <Icon name={report.icon} size={18} />
            {report.label}
          </span>
          <span className="doc-card-hint">{report.hint}</span>
        </button>
      ))}
    </div>
  );
}
