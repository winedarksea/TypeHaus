// "Pin start / Pin end" for the selected wall (P5): toggles Node.anchored, which move_nodes
// honours — a pinned end holds while the wall body is dragged.
import type { Model, PlanNode, Wall } from "../../model/types";
import { useStore } from "../../state/store";

function endNode(model: Model, w: Wall, i: 0 | 1): PlanNode | undefined {
  const [x, y] = w.axis[i];
  return (model.nodes ?? []).find((n) => n.storey === w.storey && Math.hypot(n.x_m - x, n.y_m - y) < 1e-4);
}

export function WallPinControls({ model, w }: { model: Model; w: Wall }) {
  const applyOps = useStore((s) => s.applyOps);
  const toast = useStore((s) => s.toast);
  const ends = [endNode(model, w, 0), endNode(model, w, 1)] as const;
  if (!ends[0] && !ends[1]) return null;
  const toggle = async (node: PlanNode, anchored: boolean) => {
    const ok = await applyOps([{ op: "update", type: "Node", tag: node.tag, fields: { anchored } }]);
    if (ok) toast(`${node.tag} ${anchored ? "pinned" : "unpinned"}`);
  };
  return (
    <div style={{ display: "flex", gap: 12, marginTop: 6 }}>
      {ends.map((node, i) => node && (
        <label key={i} className="ctx-check" title={`Node ${node.tag}: a pinned end holds when the wall is dragged`}>
          <input type="checkbox" checked={node.anchored ?? false}
            onChange={(e) => void toggle(node, e.target.checked)} />
          {" "}{i === 0 ? "Pin start" : "Pin end"}
        </label>
      ))}
    </div>
  );
}
