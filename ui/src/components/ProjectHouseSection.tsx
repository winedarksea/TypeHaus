import { useState } from "react";
import { useStore } from "../state/store";
import type { NewProjectResult } from "../engine/EngineClient";
import type { Model } from "../model/types";
import { buildHandoff } from "../model/handoff";
import { Icon } from "../icons/Icon";

// Where the house lives, the agent handoff, and a "New / Open house" disclosure. The server
// stays single-house: a new house is scaffolded on disk and opened by running the
// `haus serve` command it returns. The PWA has no house_dir, so it says which engine instead.
export function ProjectHouseSection({ model }: { model: Model }) {
  const project = useStore((s) => s.project);
  const offlineHouse = useStore((s) => s.offlineHouse);
  const toast = useStore((s) => s.toast);
  const [open, setOpen] = useState(false);
  const houseDir = project?.house_dir ?? null;
  const canCreate = project?.capabilities.includes("project_new") ?? false;

  const copy = async (text: string, done: string) => {
    try {
      await navigator.clipboard.writeText(text);
      toast(done);
    } catch (err) {
      toast(`Could not copy: ${(err as Error).message}`, "error");
    }
  };
  const copyHandoff = () => {
    const { sessionEdits, activeStorey } = useStore.getState();
    const text = buildHandoff(model, sessionEdits, { name: model.project.name, houseDir }, activeStorey);
    void copy(text, "Agent handoff copied");
  };

  return (
    <div className="project-house">
      <div className="project-house-where">
        {houseDir ? <>
          <code title={houseDir}>{houseDir.replace(/[\\/]+$/, "").split(/[\\/]/).pop()}</code>
          <button className="btn icon-btn" onClick={() => void copy(houseDir, "Path copied")} title={`Copy path — ${houseDir}`}>
            <Icon name="duplicate" size={18} />
          </button>
        </> : (
          <span className="muted">In-browser engine{offlineHouse ? ` · ${offlineHouse}` : ""}</span>
        )}
      </div>
      <div className="project-house-actions">
        <button className="btn" onClick={copyHandoff} title="Copy a Markdown brief of this session for an agent">
          Copy agent handoff
        </button>
        {houseDir && (
          <button className="btn" aria-expanded={open} onClick={() => setOpen(!open)}>New / Open house…</button>
        )}
      </div>
      {houseDir && open && <HouseForm templates={canCreate ? project!.templates : []} />}
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
