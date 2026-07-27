// Plan chrome: the things drawn *around* the model rather than from it — the background grid,
// the storey tabs, the current tool's hint line — plus the small graph predicates the editor
// asks about the wall network it just drew.
//
// Split out of components/Canvas2D.tsx with the rest of the presentational layer.
import { useStore } from "../../state/store";
import type { Model, PlanNode, Vec2, Wall } from "../../model/types";
import { deriveNodes, type Node as GeoNode } from "../../model/geometry";

export function ToolHint({ tool, draft, assembly, assemblies, onAssembly, onSplit }: {
  tool: string;
  draft: boolean;
  assembly: string | null;
  assemblies: string[];
  onAssembly: (tag: string) => void;
  onSplit: (() => void) | null;
}) {
  const hints: Record<string, string> = {
    wall: draft ? "Tap the next corner · Shift = ortho · type a length for exact · Esc ends" : "Tap to start a wall (snaps to nodes / grid)",
    opening: "Tap a wall to place a window or door",
    room: "Tap inside an enclosed area to claim a room",
    stair: "Tap on a floor to add a stair up to the next level",
    dimension: "Tap a wall to drive its length",
    measure: "Tap two points to measure · Shift = ortho · Esc clears",
  };
  return (
    <div>
      <div style={{ fontWeight: 600, textTransform: "capitalize", marginBottom: 4 }}>{tool} tool</div>
      <div className="muted">{hints[tool]}</div>
      {tool === "wall" && assembly != null && (
        <label style={{ display: "block", marginTop: 6, fontSize: 12 }}>Assembly{" "}
          <select value={assembly} onChange={(e) => onAssembly(e.target.value)}>
            {assemblies.map((a) => <option key={a} value={a}>{a}</option>)}
          </select>
        </label>
      )}
      {tool === "dimension" && onSplit && (
        <button className="btn" style={{ marginTop: 6 }} onClick={onSplit}>Split at midpoint</button>
      )}
    </div>
  );
}

// A draggable wall endpoint. Captures the pointer so the drag survives leaving the circle.
export function clampScale(s: number): number {
  return Math.min(2000, Math.max(8, s));
}

export function BackgroundGrid({ view }: { view: { scale: number; tx: number; ty: number } }) {
  const ftPx = view.scale * 0.3048;
  if (ftPx < 6) return <rect width="100%" height="100%" fill="none" />;
  const size = ftPx;
  const id = "grid";
  return (
    <>
      <defs>
        <pattern id={id} width={size} height={size} patternUnits="userSpaceOnUse"
          patternTransform={`translate(${view.tx % size},${view.ty % size})`}>
          <path d={`M ${size} 0 L 0 0 0 ${size}`} fill="none" stroke="var(--canvas-grid)" strokeWidth={1} />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${id})`} />
    </>
  );
}

export function StoreyTabs({ model }: { model: Model }) {
  const activeStorey = useStore((s) => s.activeStorey);
  const setActiveStorey = useStore((s) => s.setActiveStorey);
  if (model.storeys.length <= 1) return null;
  return (
    <div className="hud" style={{ display: "flex", gap: 6, flexWrap: "wrap" }}>
      {model.storeys.map((s) => (
        <button key={s.tag} className={`seg-btn${activeStorey === s.tag ? " active" : ""}`}
          onClick={() => setActiveStorey(s.tag)}>
          {s.tag}
        </button>
      ))}
    </div>
  );
}

export function openEndKeys(walls: Wall[]): Set<string> {
  const nodes = deriveNodes(walls);
  const open = new Set<string>();
  for (const n of nodes.values()) if (n.walls.length < 2) open.add(n.id);
  return open;
}

// Whether the two walls meeting at a derived node are (near-)collinear — a healable joint.
export function collinearAt(n: GeoNode, model: Model): boolean {
  if (n.walls.length !== 2) return false;
  const dirs: Vec2[] = [];
  for (const uid of n.walls) {
    const w = model.walls.find((x) => x.uid === uid);
    if (!w) return false;
    const [a, b] = w.axis;
    const far: Vec2 = Math.hypot(a[0] - n.p[0], a[1] - n.p[1]) < 1e-4 ? b : a;
    const dx = far[0] - n.p[0];
    const dy = far[1] - n.p[1];
    const len = Math.hypot(dx, dy) || 1;
    dirs.push([dx / len, dy / len]);
  }
  const cross = dirs[0][0] * dirs[1][1] - dirs[0][1] * dirs[1][0];
  return Math.abs(cross) < 0.02;
}

export function nodeTagMatches(tag: string, world: Vec2, nodes: PlanNode[]): boolean {
  const n = nodes.find((x) => x.tag === tag);
  return n ? Math.hypot(n.x_m - world[0], n.y_m - world[1]) < 1e-4 : false;
}
