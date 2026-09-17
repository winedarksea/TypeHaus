import { useState } from "react";
import { useStore } from "../state/store";
import type { NewProjectResult } from "../engine/EngineClient";

// The served house's path, and a "New / Open house" disclosure. The server stays single-house:
// a new house is scaffolded on disk and opened by running the `haus serve` command it returns.
export function ProjectHouseSection() {
  const project = useStore((s) => s.project);
  const [open, setOpen] = useState(false);
  if (!project?.house_dir) return null;
  const canCreate = project.capabilities.includes("project_new");
  return (
    <div className="project-house">
      <div className="kv">
        <span className="k">House</span>
        <code style={{ overflowWrap: "anywhere" }}>{project.house_dir}</code>
      </div>
      <button className="btn" aria-expanded={open} onClick={() => setOpen(!open)} style={{ marginTop: 6 }}>
        New / Open house
      </button>
      {open && <HouseForm templates={canCreate ? project.templates : []} />}
    </div>
  );
}

function HouseForm({ templates }: { templates: string[] }) {
  const client = useStore((s) => s.client);
  // New houses land beside the served one, and the server refuses anything outside that
  // folder — so say where that is rather than letting a plausible ~/... path come back 422.
  const houseDir = useStore((s) => s.project?.house_dir ?? null);
  const root = houseDir ? houseDir.replace(/[\\/][^\\/]*$/, "") : null;
  const [directory, setDirectory] = useState("");
  const [name, setName] = useState("");
  const [template, setTemplate] = useState(templates[0] ?? "starter");
  const [created, setCreated] = useState<NewProjectResult | null>(null);
  const [busy, setBusy] = useState(false);
  const command = created?.command ?? (directory.trim() ? `haus serve ${directory.trim()}` : "");

  const create = async () => {
    setBusy(true);
    try {
      setCreated(await client.newProject({ directory: directory.trim(), name: name.trim() || undefined, template }));
    } catch (err) {
      useStore.getState().toast(`Could not create the house: ${(err as Error).message}`, "error");
    } finally {
      setBusy(false);
    }
  };
  const copyCommand = async () => {
    try {
      await navigator.clipboard.writeText(command);
      useStore.getState().toast("Command copied");
    } catch (err) {
      useStore.getState().toast(`Could not copy: ${(err as Error).message}`, "error");
    }
  };

  return (
    <div>
      <label className="field-label">Directory
        <input value={directory} placeholder="my-house" onChange={(e) => { setDirectory(e.target.value); setCreated(null); }} />
      </label>
      {root && <p className="muted" style={{ fontSize: 12, marginTop: 0 }}>Created in {root}.</p>}
      {templates.length > 0 && <>
        <label className="field-label">Name
          <input value={name} placeholder="My House" onChange={(e) => setName(e.target.value)} />
        </label>
        <label className="field-label">Template
          <select value={template} onChange={(e) => setTemplate(e.target.value)}>
            {templates.map((t) => <option key={t} value={t}>{t}</option>)}
          </select>
        </label>
        <button className="btn" style={{ marginTop: 6 }} disabled={!directory.trim() || busy} onClick={() => void create()}>
          {busy ? "Creating…" : "Create house"}
        </button>
      </>}
      {created && <p className="muted" style={{ fontSize: 12 }}>Wrote {created.written.length} files to {created.house_dir}.</p>}
      {command && (
        <p className="muted" style={{ fontSize: 12 }}>
          Open it by stopping this server and running <code>{command}</code>{" "}
          <button className="btn" onClick={() => void copyCommand()}>Copy</button>
        </p>
      )}
    </div>
  );
}
