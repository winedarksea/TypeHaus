// One reinforcing bar, picked out of the rebar layer in 3D (→ three/rebar.ts). Like a framing
// member it is derived: the edit lives on the host's reinforcement spec, so the one action is
// getting back to the host.
import type { LocatedMember } from "../model/memberIdentity";
import type { Model, RebarBar } from "../model/types";
import { formatFtIn } from "../model/geometry";
import { useStore } from "../state/store";
import type { SelectionKind } from "../state/vocabulary";

/** A wall host selects as a wall; a footing, pad, slab or post is emitted as a solid. */
export function rebarHostSelectionKind(model: Model | null, hostUid: string): SelectionKind {
  return model?.walls.some((wall) => wall.uid === hostUid) ? "wall" : "solid";
}

function hooksLabel(bar: RebarBar): string {
  const { hook_m, hook_kinds } = bar.rebar;
  if (!hook_m && !hook_kinds.length) return "none";
  const kinds = hook_kinds.length ? ` (${hook_kinds.join(", ")})` : "";
  return `${formatFtIn(hook_m)}${kinds}`;
}

export function RebarInspector({ located, bar }: { located: LocatedMember; bar: RebarBar }) {
  const select = useStore((s) => s.select);
  const model = useStore((s) => s.model);
  const r = bar.rebar;
  return <div>
    <h3>Rebar · {bar.key}</h3>
    <div className="kv">
      <span className="k">Host</span><span>{located.ownerTag}</span>
      <span className="k">Role</span><span>{r.role}{bar.closed ? " (closed)" : ""}</span>
      <span className="k">Bar</span><span>#{r.bar}</span>
      <span className="k">Coating</span><span>{r.coating}</span>
      <span className="k">Spacing</span>
      <span>{r.spacing_in != null ? `${r.spacing_in}" o.c.` : "—"}</span>
      <span className="k">Piece</span><span>{r.piece} of {r.pieces}</span>
      <span className="k">Placed</span><span>{formatFtIn(r.placed_m)}</span>
      <span className="k">Lap</span><span>{r.lap_m ? formatFtIn(r.lap_m) : "—"}</span>
      <span className="k">Hooks</span><span>{hooksLabel(bar)}</span>
      <span className="k">Cut length</span><span>{formatFtIn(r.cut_m)}</span>
      <span className="k">Weight</span><span>{r.weight_lb.toFixed(2)} lb</span>
      {r.note && <><span className="k">Note</span><span>{r.note}</span></>}
      <span className="k">Storey</span><span>{located.storey ?? "—"}</span>
    </div>
    <button className="btn" style={{ marginTop: 8 }}
      onClick={() => select(rebarHostSelectionKind(model, located.ownerUid), located.ownerUid)}>
      Select the host ({located.ownerTag})
    </button>
    <p className="muted" style={{ fontSize: 11, marginTop: 8 }}>
      Derived geometry — laid out from {located.ownerTag}'s reinforcement. Edit that to change it.
    </p>
  </div>;
}
