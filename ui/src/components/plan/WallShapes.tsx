// Wall plan symbols: the layered wall body with its openings punched out, its driven-dimension
// string, and the assembly card a click pops up.
//
// Split out of components/Canvas2D.tsx. WallShape is memoized on purpose — it is the most
// expensive symbol in the plan (one polygon per assembly layer, masked per opening) and it must
// not re-render when an unrelated hover changes.
import { memo } from "react";
import type { Layer, Opening, Vec2, Wall } from "../../model/types";
import { isLayerVisible, type LayerVisibilityGroup } from "../../model/visibility";
import { layerCarriesControl, lensStrokeSpec } from "../LensBar";
import type { Lens } from "../../state/vocabulary";
import { formatFtIn, pointAlong, wallLength } from "../../model/geometry";
import { materialColor, NORDIC_ACCENT, NORDIC_INK, NORDIC_LINE } from "../../nordic/palette";

export const WallShape = memo(function WallShape({ w, openings, project, selected, hovered, showFraming,
  showLayers, visibleLayerGroups, activeLens, onSelect, onHover }: {
  w: Wall;
  openings: Opening[];
  project: (p: Vec2) => Vec2;
  selected: boolean;
  hovered: boolean;
  showFraming: boolean;
  showLayers: boolean; // Walls discipline — off leaves the framing and the axis alone
  visibleLayerGroups: Record<LayerVisibilityGroup, boolean>;
  activeLens: Lens; // draws the control-layer overlay the lens is about
  onSelect: (wall: Wall, event: React.MouseEvent<SVGGElement>) => void;
  onHover: (uid: string | null) => void;
}) {
  const poly = (pts: Vec2[]) => pts.map(project).map((p) => p.join(",")).join(" ");
  const stroke = selected ? NORDIC_ACCENT : hovered ? NORDIC_INK : NORDIC_LINE;
  const [axisStart, axisEnd] = w.axis;
  const axisLength = Math.hypot(axisEnd[0] - axisStart[0], axisEnd[1] - axisStart[1]) || 1;
  const wallNormal: Vec2 = [
    -(axisEnd[1] - axisStart[1]) / axisLength,
    (axisEnd[0] - axisStart[0]) / axisLength,
  ];
  const pixelsPerMeter = Math.abs(project([1, 0])[0] - project([0, 0])[0]);
  // Resolved wall layers are continuous polygons.  Punch openings out of the complete wall
  // stack before drawing their plan symbols so a thick rendered wall cannot cover a door.
  const wallThicknessPx = Math.max(8, ...w.layers.flatMap((layer) => layer.polygon.map((point) =>
    Math.abs((point[0] - axisStart[0]) * wallNormal[0] + (point[1] - axisStart[1]) * wallNormal[1])
      * pixelsPerMeter,
  )));
  const [startX, startY] = project(axisStart);
  const [endX, endY] = project(axisEnd);
  const screenAngleDeg = Math.atan2(endY - startY, endX - startX) * 180 / Math.PI;
  const openingMaskId = `wall-opening-mask-${w.uid}`;
  return (
    <g onClick={(event) => onSelect(w, event)}
      onPointerEnter={() => onHover(w.uid)} onPointerLeave={() => onHover(null)}
      style={{ cursor: "pointer" }}>
      <mask id={openingMaskId} maskUnits="userSpaceOnUse">
        <rect x={-100000} y={-100000} width={200000} height={200000} fill="white" />
        {openings.map((opening) => {
          const [x, y] = project(pointAlong(w, opening.center_along_m));
          const openingWidthPx = opening.width_m * pixelsPerMeter;
          return <rect key={opening.uid} x={x - openingWidthPx / 2 - 1}
            y={y - wallThicknessPx - 1} width={openingWidthPx + 2}
            height={2 * wallThicknessPx + 2} fill="black"
            transform={`rotate(${screenAngleDeg} ${x} ${y})`} />;
        })}
      </mask>
      <g className="wall-fills" mask={`url(#${openingMaskId})`}>
        {/* Layer fills answer to the Walls discipline *and* to the per-layer control, so the
            weather skin can be dropped while the cavity fill behind it stays drawn. */}
        {showLayers && w.layers.map((ly: Layer, i: number) =>
          ly.polygon.length >= 3 && isLayerVisible(ly, visibleLayerGroups) ? (
            <polygon key={i} points={poly(ly.polygon)} fill={materialColor(ly.material)}
              stroke="var(--panel-line)" strokeWidth={0.5} />
          ) : null,
        )}
        {showFraming && w.members.map((m) => {
          const [x0, y0] = project(m.p0);
          const [x1, y1] = project(m.p1);
          return <line key={m.key} x1={x0} y1={y0} x2={x1} y2={y1} stroke="var(--canvas-wood)"
            strokeWidth={1.5} opacity={0.85} />;
        })}
        {showLayers && <line x1={startX} y1={startY} x2={endX} y2={endY} stroke={stroke}
          strokeWidth={selected ? 2.5 : 1.5} strokeDasharray={w.layers.length === 0 ? "4 4" : undefined} />}
      </g>
      {/* Building-science lens overlay. The engine already tags every resolved layer with the
          controls it carries (`Layer.control`); until now the plan drew none of it, which is
          why the air/water/thermal lenses "didn't seem to show much". Drawn outside the opening
          mask and outside the dimmed fills, because a continuity lens is about the path. */}
      {(() => {
        const strokeSpec = lensStrokeSpec(activeLens);
        if (!strokeSpec) return null;
        return w.layers.map((ly: Layer, i: number) =>
          ly.polygon.length >= 3 && layerCarriesControl(ly.control, activeLens) ? (
            <polygon key={`lens-${i}`} points={poly(ly.polygon)} fill="none" pointerEvents="none"
              stroke={`var(${strokeSpec.colorVar})`} strokeWidth={2} strokeDasharray={strokeSpec.pattern} />
          ) : null,
        );
      })()}
    </g>
  );
});

export function WallAssemblyPopupCard({ wall, screen, viewport, onClose }: {
  wall: Wall;
  screen: Vec2;
  viewport: DOMRect | null;
  onClose: () => void;
}) {
  const totalThickness = wall.layers.reduce((sum, layer) => sum + layer.thickness_m, 0);
  // Keep the card in the pane even when the click is close to an edge. The CSS height cap
  // makes this conservative vertical allowance work for long assemblies on small screens.
  const left = Math.max(12, Math.min(screen[0] + 12, Math.max(12, (viewport?.width ?? 0) - 292)));
  const top = Math.max(12, Math.min(screen[1] + 12, Math.max(12, (viewport?.height ?? 0) - 372)));

  return (
    <aside className="wall-assembly-popup" style={{ left, top }} aria-label={`${wall.tag} wall assembly`}>
      <div className="wall-assembly-popup-header">
        <div>
          <div className="wall-assembly-popup-title">Wall · {wall.tag}</div>
          <div className="wall-assembly-popup-assembly">{wall.assembly || "UNCONFIGURED"}</div>
        </div>
        <button className="wall-assembly-popup-close" onClick={onClose} aria-label="Close wall assembly popup">×</button>
      </div>
      <div className="wall-assembly-popup-dimensions">
        <span><b>Length</b>{formatFtIn(wallLength(wall))}</span>
        <span><b>Height</b>{formatFtIn(wall.z1_m - wall.z0_m)}</span>
        <span><b>Thickness</b>{formatFtIn(totalThickness)}</span>
      </div>
      <div className="wall-assembly-popup-layers">
        <div className="wall-assembly-popup-layer-heading">Resolved layers</div>
        {wall.layers.length > 0 ? wall.layers.map((layer, index) => (
          <div className="layer-row" key={`${layer.name}-${index}`}>
            <span className="swatch" style={{ background: materialColor(layer.material) }} />
            <span className="wall-assembly-popup-layer-name">{layer.name}</span>
            <span>{formatFtIn(layer.thickness_m)}</span>
            <span className="wall-assembly-popup-layer-material">{layer.material}</span>
          </div>
        )) : <div className="muted">No resolved layers.</div>}
      </div>
    </aside>
  );
}

export function WallDimension({ w, project }: { w: Wall; project: (p: Vec2) => Vec2 }) {
  const [a, b] = w.axis;
  const mid: Vec2 = [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];
  const [mx, my] = project(mid);
  return (
    <text x={mx} y={my - 8} fill={NORDIC_INK} fontSize={12} textAnchor="middle">
      {formatFtIn(wallLength(w))}
    </text>
  );
}
