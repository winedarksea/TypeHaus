import type { ReactNode } from "react";

// The chrome the two full-width readers share (assembly details, bill of materials). Same
// focus-mode treatment as the Workbench — canvas dims behind a breadcrumb back — because both
// are read-and-return surfaces, not inspectors you keep open while editing.
export function ReaderShell({ title, subtitle, onClose, toolbar, children }: {
  title: string;
  subtitle: string;
  onClose: () => void;
  toolbar?: ReactNode;
  children: ReactNode;
}) {
  return (
    <div className="workbench-backdrop">
      <div className="workbench" role="dialog" aria-label={title}>
        <div className="workbench-bread">
          <button className="btn" onClick={onClose} title="Back to canvas">← Back</button>
          <span className="workbench-title">{title}</span>
          <span className="muted reader-subtitle">{subtitle}</span>
          <span className="spacer" style={{ flex: 1 }} />
          {toolbar}
        </div>
        <div className="workbench-body">{children}</div>
      </div>
    </div>
  );
}

// A labelled block inside a reader. `count` is shown next to the heading so a section that is
// empty for this house says so rather than looking broken.
export function ReaderSection({ title, note, count, children }: {
  title: string;
  note: string;
  count: number;
  children: ReactNode;
}) {
  return (
    <section className="reader-section">
      <h3 className="reader-section-title">
        {title} <span className="muted">· {count}</span>
      </h3>
      <p className="muted reader-section-note">{note}</p>
      {count === 0 ? <div className="muted">Nothing in this model.</div> : children}
    </section>
  );
}
