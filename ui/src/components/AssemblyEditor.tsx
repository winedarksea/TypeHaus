import { useEffect, useMemo, useState } from "react";
import { useStore } from "../state/store";
import type { AssemblySpec, CatalogLayer, Layer } from "../model/types";
import { formatFtIn, parseFtIn } from "../model/geometry";
import { SectionCard } from "./SectionCard";

// The assembly editor (WP2.4d/e, → 21b feature 7): clone-and-tweak over the standard
// journal. Library presets are read-only until duplicated into the project (`editable`
// flag from the catalog, → server _catalog); duplicates and blanks land in plan/assemblies.py
// and can have their layer stack rewritten directly via the edit_assembly_layers macro.

const LAYER_FUNCTIONS = [
  "structure", "sheathing", "membrane", "insulation", "airgap", "furring", "cladding", "finish",
];

export function AssemblyEditor({ onClose }: { onClose: () => void }) {
  const catalog = useStore((s) => s.model?.catalog);
  const runMacro = useStore((s) => s.runMacro);
  const assemblies = catalog?.assemblies ?? [];
  const materials = catalog?.materials ?? [];

  const [selectedTag, setSelectedTag] = useState<string>(assemblies[0]?.tag ?? "");
  const [draft, setDraft] = useState<CatalogLayer[]>([]);
  const [busy, setBusy] = useState(false);
  const [newTag, setNewTag] = useState("");
  const [showNewMaterial, setShowNewMaterial] = useState(false);

  const selected = useMemo(
    () => assemblies.find((a) => a.tag === selectedTag) ?? null,
    [assemblies, selectedTag],
  );

  // Reset the working draft whenever the selected assembly (or its resolved layers) changes.
  useEffect(() => {
    setDraft(selected ? selected.layers.map((l) => ({ ...l })) : []);
  }, [selected]);

  const dirty = useMemo(
    () => JSON.stringify(draft) !== JSON.stringify(selected?.layers ?? []),
    [draft, selected],
  );

  const previewLayers: Layer[] = draft.map((l) => ({
    name: l.name, function: l.function, material: l.material, thickness_m: l.thickness_m,
    polygon: [], control: [],
  }));

  const duplicate = async (source: AssemblySpec) => {
    const tag = window.prompt(`New tag for a copy of ${source.tag}:`, `${source.tag}_2`);
    if (!tag) return;
    setBusy(true);
    const res = await runMacro({ macro: "duplicate_assembly", source: source.tag, tag });
    setBusy(false);
    if (res) setSelectedTag(tag);
  };

  const createBlank = async () => {
    if (!newTag.trim()) return;
    setBusy(true);
    const res = await runMacro({ macro: "blank_assembly", tag: newTag.trim() });
    setBusy(false);
    if (res) { setSelectedTag(newTag.trim()); setNewTag(""); }
  };

  const save = async () => {
    if (!selected) return;
    setBusy(true);
    const res = await runMacro({
      macro: "edit_assembly_layers", tag: selected.tag,
      layers: draft.map((l) => ({
        name: l.name, material: l.material, function: l.function,
        thickness: formatFtIn(l.thickness_m),
      })),
    });
    setBusy(false);
    if (res) useStore.getState().toast(`${selected.tag} saved`);
  };

  const updateLayer = (i: number, patch: Partial<CatalogLayer>) =>
    setDraft((d) => d.map((l, idx) => (idx === i ? { ...l, ...patch } : l)));
  const moveLayer = (i: number, dir: -1 | 1) =>
    setDraft((d) => {
      const j = i + dir;
      if (j < 0 || j >= d.length) return d;
      const copy = [...d];
      [copy[i], copy[j]] = [copy[j], copy[i]];
      return copy;
    });
  const removeLayer = (i: number) => setDraft((d) => d.filter((_, idx) => idx !== i));
  const addLayer = () => setDraft((d) => [...d, {
    name: `layer-${d.length + 1}`, material: materials[0]?.tag ?? "", function: "structure",
    thickness_m: 0.0127,
  }]);

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal assembly-editor" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 style={{ margin: 0 }}>Assemblies</h3>
          <button className="btn" onClick={onClose}>✕</button>
        </div>
        <div className="assembly-editor-body">
          <div className="assembly-list">
            {assemblies.map((a) => (
              <div key={a.tag} className={`finding info${a.tag === selectedTag ? " selected" : ""}`}
                onClick={() => setSelectedTag(a.tag)}>
                <div style={{ display: "flex", justifyContent: "space-between" }}>
                  <span>{a.tag}</span>
                  {!a.editable && <span className="badge">library</span>}
                </div>
                <span className="muted">{a.layers.length} layers{a.stc != null ? ` · STC ${a.stc}` : ""}</span>
              </div>
            ))}
            <div style={{ marginTop: 10, display: "flex", gap: 6 }}>
              <input placeholder="new tag" value={newTag} onChange={(e) => setNewTag(e.target.value)}
                style={{ flex: 1, minWidth: 0 }} />
              <button className="btn" disabled={busy || !newTag.trim()} onClick={() => void createBlank()}>
                + Blank
              </button>
            </div>
          </div>
          <div className="assembly-detail">
            {!selected ? (
              <div className="muted">Select an assembly.</div>
            ) : !selected.editable ? (
              <div>
                <div className="muted" style={{ marginBottom: 8 }}>
                  {selected.tag} is a shared library preset — duplicate it into the project to edit its layers.
                </div>
                <SectionCard layers={previewLayers} title={selected.tag} />
                <button className="btn" style={{ marginTop: 8 }} disabled={busy}
                  onClick={() => void duplicate(selected)}>
                  Duplicate to edit
                </button>
              </div>
            ) : (
              <div>
                <div className="layer-editor">
                  {draft.map((ly, i) => (
                    <div key={i} className="layer-edit-row">
                      <input value={ly.name} onChange={(e) => updateLayer(i, { name: e.target.value })}
                        style={{ width: 84 }} />
                      <select value={ly.material} onChange={(e) => updateLayer(i, { material: e.target.value })}>
                        {materials.map((m) => <option key={m.tag} value={m.tag}>{m.tag}</option>)}
                      </select>
                      <select value={ly.function} onChange={(e) => updateLayer(i, { function: e.target.value })}>
                        {LAYER_FUNCTIONS.map((f) => <option key={f} value={f}>{f}</option>)}
                      </select>
                      <input value={formatFtIn(ly.thickness_m)} style={{ width: 70 }}
                        onChange={(e) => {
                          const m = parseFtIn(e.target.value);
                          if (m !== null) updateLayer(i, { thickness_m: m });
                        }} />
                      <button className="btn" onClick={() => moveLayer(i, -1)} disabled={i === 0}>↑</button>
                      <button className="btn" onClick={() => moveLayer(i, 1)} disabled={i === draft.length - 1}>↓</button>
                      <button className="btn" onClick={() => removeLayer(i)}>✕</button>
                    </div>
                  ))}
                </div>
                <div style={{ display: "flex", gap: 6, marginTop: 8 }}>
                  <button className="btn" onClick={addLayer}>+ Layer</button>
                  <button className="btn" onClick={() => setShowNewMaterial((v) => !v)}>+ Material</button>
                  <div style={{ flex: 1 }} />
                  <button className="btn" disabled={busy || !dirty || draft.length === 0}
                    style={{ background: dirty ? "var(--accent)" : undefined, color: dirty ? "#fff" : undefined }}
                    onClick={() => void save()}>
                    Save
                  </button>
                </div>
                {showNewMaterial && <NewMaterialForm onDone={() => setShowNewMaterial(false)} />}
                <div style={{ marginTop: 10 }}>
                  <SectionCard layers={previewLayers} title={`${selected.tag} (preview)`} />
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

function NewMaterialForm({ onDone }: { onDone: () => void }) {
  const runMacro = useStore((s) => s.runMacro);
  const [tag, setTag] = useState("");
  const [name, setName] = useState("");
  const [rPerInch, setRPerInch] = useState("");
  const [busy, setBusy] = useState(false);

  const add = async () => {
    if (!tag.trim() || !name.trim()) return;
    setBusy(true);
    const material: { tag: string; name: string; r_per_inch?: number } = { tag: tag.trim(), name: name.trim() };
    const r = Number(rPerInch);
    if (rPerInch && Number.isFinite(r)) material.r_per_inch = r;
    const res = await runMacro({ macro: "add_material", material });
    setBusy(false);
    if (res) onDone();
  };

  return (
    <div className="section-card" style={{ marginTop: 8, display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap" }}>
      <input placeholder="tag" value={tag} onChange={(e) => setTag(e.target.value)} style={{ width: 90 }} />
      <input placeholder="name" value={name} onChange={(e) => setName(e.target.value)} style={{ width: 110 }} />
      <input placeholder="R/in" value={rPerInch} onChange={(e) => setRPerInch(e.target.value)} style={{ width: 56 }} />
      <button className="btn" disabled={busy || !tag.trim() || !name.trim()} onClick={() => void add()}>Add</button>
    </div>
  );
}
