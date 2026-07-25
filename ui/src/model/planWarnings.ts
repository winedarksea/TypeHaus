// Plan-marker diagnostics (→ TODO "there is a glowing red dot ... you can't click on it to
// tell what it is, so it isn't very helpful in this form").
//
// The 2D plan draws two kinds of marker that carry meaning but no explanation: the pulsing dot
// at an unjoined wall end, and any junction the resolver could only resolve with a fallback.
// This module turns each into a *nameable* record — id, tier, message, the elements involved,
// and the server findings that mention them — so a click can say what it is instead of just
// glowing. Pure over model.json; the canvas only positions what comes back.

import type { Finding, Junction, Model, Severity, Vec2, Wall } from "./types";

export interface PlanWarningMarker {
  key: string; // React key / marker identity
  id: string; // the identifier a person can search for — a node tag where one exists
  code: string; // check-style code, so this reads like the findings it sits beside
  tier: Severity;
  title: string;
  message: string;
  position: Vec2;
  elementTags: string[]; // walls/nodes involved — clickable in the popover
  findings: Finding[]; // server findings that mention any of the above
}

const OPEN_END_CODE = "plan.open_wall_end";
const JUNCTION_FALLBACK_CODE = "plan.junction_diagnostic";

// Findings address elements by uid, but a junction/node names authored *tags*, so both are
// matched. Passing findings that already resolve elsewhere is harmless — the popover is the
// only consumer and it is opened by an explicit click.
export function findingsForElements(model: Model, tags: string[], uids: string[]): Finding[] {
  const wanted = new Set([...tags, ...uids]);
  if (wanted.size === 0) return [];
  return model.findings.filter((finding) => {
    if (finding.result === "pass") return false;
    const referenced = [finding.element, ...(finding.elements ?? [])];
    return referenced.some((value) => typeof value === "string" && wanted.has(value));
  });
}

// The authored node record, when the plan has one at this point. A node that declares
// `open_end: true` is a *deliberate* free end (a stair-well return, a garden wall stub), not a
// modelling mistake — which is exactly the distinction the undifferentiated red dot was hiding.
function nodeAt(model: Model, storey: string | null, point: Vec2, toleranceM: number) {
  return (model.nodes ?? []).find((node) =>
    (!storey || node.storey === storey) &&
    Math.hypot(node.x_m - point[0], node.y_m - point[1]) <= toleranceM);
}

/**
 * Explain one unjoined wall end. `walls` are the walls meeting at the point (one, by
 * definition of an open end); `toleranceM` matches the canvas's own node-snap tolerance.
 */
export function openEndMarker(
  model: Model, storey: string | null, point: Vec2, walls: Wall[], toleranceM: number,
): PlanWarningMarker {
  const node = nodeAt(model, storey, point, toleranceM);
  const declared = node?.open_end === true;
  const wallTags = walls.map((wall) => wall.tag);
  const id = node?.tag ?? `${point[0].toFixed(3)},${point[1].toFixed(3)}`;
  const where = wallTags.length ? ` of ${wallTags.join(", ")}` : "";
  return {
    key: `open-end-${id}`,
    id,
    code: OPEN_END_CODE,
    tier: declared ? "info" : "warn",
    title: declared ? "Declared open wall end" : "Unjoined wall end",
    message: declared
      ? `${id} is authored with open_end = true, so this free end${where} is intentional. Nothing to fix.`
      : `No second wall meets ${id}${where}. Either the run is unfinished, or the node should be declared open_end = true.`,
    position: point,
    elementTags: [...(node ? [node.tag] : []), ...wallTags],
    findings: findingsForElements(model, [...(node ? [node.tag] : []), ...wallTags],
      walls.map((wall) => wall.uid)),
  };
}

function junctionMarker(model: Model, junction: Junction): PlanWarningMarker {
  const wallTags = junction.incidents.map((incident) => incident.wall);
  const wallUids = model.walls.filter((wall) => wallTags.includes(wall.tag)).map((wall) => wall.uid);
  return {
    key: `junction-${junction.storey}-${junction.node}`,
    id: junction.node,
    code: JUNCTION_FALLBACK_CODE,
    tier: junction.supported ? "warn" : "error",
    title: `${junction.kind.toUpperCase()} junction fallback`,
    message: junction.diagnostic ?? "The resolver fell back to conservative geometry here.",
    position: junction.point,
    elementTags: [junction.node, ...wallTags],
    findings: findingsForElements(model, [junction.node, ...wallTags], wallUids),
  };
}

/** Every junction on `storey` the resolver annotated with a diagnostic. */
export function junctionDiagnosticMarkers(model: Model, storey: string | null): PlanWarningMarker[] {
  return (model.junctions ?? [])
    .filter((junction) => junction.diagnostic && (!storey || junction.storey === storey))
    .map((junction) => junctionMarker(model, junction));
}
