// A placeable's plan symbol, drawn at a screen point: an imported plan SVG wins, then the
// engine-generated strokes, then the plain footprint rectangle. Shared by the canvas
// footprint, the placement ghost and the catalog thumbnails so all three draw the same thing.
import type { CanvasObjectType } from "../../model/types";

const DOMAIN_COLORS: Record<string, [string, string]> = {
  furniture: ["var(--canvas-wood-soft)", "var(--canvas-wood)"],
  plumbing: ["var(--canvas-selection)", "var(--accent)"],
  electrical: ["#fff2bd", "#a66f00"],
  mechanical: ["#dceafb", "#37658d"],
  appliance: ["#e5e7eb", "#4b5563"],
};

export const DEFAULT_FOOTPRINT_M: [number, number] = [0.45, 0.45];

export function domainColors(domain: string): [string, string] {
  return DOMAIN_COLORS[domain] ?? ["#e5e7eb", "#4b5563"];
}

export function PlaceableGlyph({ type, domain, x, y, scale, rotation, selected = false }: {
  type: CanvasObjectType | undefined;
  domain: string;
  x: number;
  y: number;
  scale: number; // px per metre
  rotation: number;
  selected?: boolean;
}) {
  const [widthM, depthM] = type?.footprint_m ?? DEFAULT_FOOTPRINT_M;
  const width = widthM * scale;
  const depth = depthM * scale;
  const [fill, stroke] = domainColors(domain);
  const transform = `rotate(${-rotation} ${x} ${y})`;
  if (type?.plan_svg) {
    return <image href={type.plan_svg} x={x - width / 2} y={y - depth / 2} width={width} height={depth}
      transform={transform} />;
  }
  const strokes = type?.plan_strokes ?? [];
  if (!strokes.length) {
    return <rect x={x - width / 2} y={y - depth / 2} width={width} height={depth}
      fill={fill} stroke={selected ? "var(--ink)" : stroke} strokeWidth={selected ? 2.4 : 1.2}
      transform={transform} />;
  }
  return <g transform={transform}>
    {strokes.map((symbolStroke, index) => {
      // The engine owns the geometry; the UI only projects it. Screen y is inverted from
      // plan y, the same handedness doorSymbolPoint uses.
      const points = symbolStroke.points
        .map(([sx, sy]) => `${x + sx * scale},${y - sy * scale}`).join(" ");
      const outline = index === 0; // the first generated stroke is the outline; it carries selection
      return symbolStroke.closed
        ? <polygon key={index} points={points} fill={symbolStroke.fill ?? "none"}
          stroke={selected && outline ? "var(--ink)" : stroke}
          strokeWidth={(selected && outline ? 2.4 : 1.2) * symbolStroke.weight / 0.25} />
        : <polyline key={index} points={points} fill="none" stroke={stroke}
          strokeWidth={1.2 * symbolStroke.weight / 0.25} />;
    })}
  </g>;
}

// px per metre that fits a footprint inside a `size`-px square with a margin, so a 3 m sofa
// and a 0.1 m receptacle both read in a catalog card.
export function thumbScale(footprint: [number, number] | null | undefined, size: number, marginPx = 4): number {
  const [w, d] = footprint ?? DEFAULT_FOOTPRINT_M;
  const longest = Math.max(w, d, 1e-3);
  return Math.max(0, size - marginPx * 2) / longest;
}

export function PlaceableThumb({ type, size }: { type: CanvasObjectType; size: number }) {
  return <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} aria-hidden="true">
    <PlaceableGlyph type={type} domain={type.domain} x={size / 2} y={size / 2}
      scale={thumbScale(type.footprint_m, size)} rotation={0} />
  </svg>;
}
