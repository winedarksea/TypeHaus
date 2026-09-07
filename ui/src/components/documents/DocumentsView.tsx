import { useRef, useState } from "react";
import { useStore } from "../../state/store";
import { ReaderFilter, ReaderShell } from "../ReaderShell";
import type { DocumentsTab } from "../../state/vocabulary";
import { DrawingsTab } from "./DrawingsTab";
import { NotesTab } from "./NotesTab";
import { ReportsTab } from "./ReportsTab";

/**
 * The Documents hub — one destination for everything the house has to *read*, as opposed to
 * everything it has to draw.
 *
 * Three tabs rather than three rail destinations: the drawings, the notes and the reports are
 * three answers to one question a contractor asks ("what am I building to?"), and a reader
 * who came for a sheet number and finds it in a note should not have to navigate to get from
 * one to the other — hence the note's "on sheet A-401" chips, which cross the tabs.
 *
 * It reuses `ReaderShell` rather than inventing a shell: the Back-to-canvas breadcrumb, the
 * dimmed canvas and the body scroll are exactly the reader treatment, and the hub is one.
 */

const TABS: { id: DocumentsTab; label: string }[] = [
  { id: "drawings", label: "Drawings" },
  { id: "notes", label: "Notes" },
  { id: "reports", label: "Reports" },
];

export function DocumentsView() {
  const model = useStore((s) => s.model);
  const tab = useStore((s) => s.documentsTab);
  const setDocumentsTab = useStore((s) => s.setDocumentsTab);
  const setDetailView = useStore((s) => s.setDetailView);
  const [filter, setFilter] = useState("");
  const stripRef = useRef<HTMLDivElement>(null);

  // Roving arrow keys across the strip, per the WAI-ARIA tabs pattern: the tabs are one stop
  // in the tab order and Left/Right move between them.
  const onStripKey = (event: React.KeyboardEvent) => {
    const delta = event.key === "ArrowRight" ? 1 : event.key === "ArrowLeft" ? -1 : 0;
    if (!delta) return;
    event.preventDefault();
    const index = TABS.findIndex((t) => t.id === tab);
    const next = TABS[(index + delta + TABS.length) % TABS.length];
    setDocumentsTab(next.id);
    // Move focus with the selection, or a keyboard user's next arrow starts from the old tab.
    const buttons = stripRef.current?.querySelectorAll<HTMLButtonElement>(".doc-tab");
    buttons?.[TABS.indexOf(next)]?.focus();
  };

  return (
    <ReaderShell
      wide
      title="Documents"
      subtitle={model ? model.project.name : "—"}
      onClose={() => setDetailView("none")}
      toolbar={
        <>
          {tab === "notes" && (
            <ReaderFilter value={filter} onChange={setFilter}
              placeholder="Filter notes…" label="Filter notes" />
          )}
          <div className="doc-tabs" role="tablist" aria-label="Documents"
            ref={stripRef} onKeyDown={onStripKey}>
            {TABS.map((spec) => (
              <button
                key={spec.id}
                role="tab"
                id={`doc-tab-${spec.id}`}
                aria-selected={tab === spec.id}
                aria-controls={`doc-panel-${spec.id}`}
                tabIndex={tab === spec.id ? 0 : -1}
                className={`doc-tab${tab === spec.id ? " active" : ""}`}
                onClick={() => setDocumentsTab(spec.id)}
              >
                {spec.label}
              </button>
            ))}
          </div>
        </>
      }
    >
      <div role="tabpanel" id={`doc-panel-${tab}`} aria-labelledby={`doc-tab-${tab}`}>
        {tab === "drawings" && <DrawingsTab />}
        {tab === "notes" && <NotesTab filter={filter} />}
        {tab === "reports" && <ReportsTab />}
      </div>
    </ReaderShell>
  );
}
