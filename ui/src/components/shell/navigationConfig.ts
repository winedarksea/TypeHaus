import type { IconName } from "../../icons/names";
import type { DetailView, DocumentsTab, Tool, ToolGroup } from "../../state/vocabulary";

/**
 * The chrome's contents as data rather than as repeated JSX, so adding a destination or a
 * tool means adding a row here instead of copy-pasting a block.
 */

export interface ReportSpec {
  id: Exclude<DetailView, "none">;
  label: string;
  icon: IconName;
  hint: string;
}

/**
 * The full-screen readers. These are destinations, not toolbar actions, which is the
 * argument for collapsing them behind one trigger rather than a row of buttons.
 */
export const REPORTS: ReportSpec[] = [
  { id: "assembly", label: "Assembly details", icon: "wall",
    hint: "Transitions, resolved conditions, layer stacks" },
  { id: "bom", label: "Bill of materials", icon: "report",
    hint: "Every part in the model" },
  { id: "estimate", label: "Estimate", icon: "report",
    hint: "Priced rows, bid ladder, $/sf" },
  { id: "circuits", label: "Circuits", icon: "report",
    hint: "Panel schedule, service load, conduit, PV" },
  { id: "hvac", label: "HVAC", icon: "report",
    hint: "Heat-pump systems, zone loads, ducts, registers, ERV" },
  { id: "plumbing", label: "Plumbing", icon: "report",
    hint: "Isometric riser, fixture units, pipe takeoff, cast-in sleeves" },
  { id: "lighting", label: "Lighting", icon: "report",
    hint: "Luminaire schedule, controls, LED runs, connected load" },
  // Reachable only from the command palette until the Documents hub: the top bar's Reports
  // menu rendered this list too, so a reader missing from it was a reader with no home.
  { id: "data", label: "Data", icon: "report",
    hint: "Low-voltage devices, comms raceways, PoE budget" },
];

/**
 * The Documents destination, one entry per tab of the hub.
 *
 * It replaced the top bar's Reports menu rather than sitting beside it: the readers above
 * are one of three things a contractor reads (the drawings and the house's notes are the
 * other two). One trigger was one too few, though — "Documents" names the container, not
 * the thing you came for, so reaching a report cost a click into the hub and a second onto
 * its tab strip. The strip stays (a note's "on sheet A-401" chip still has to cross to the
 * drawings), and the rail now enters it at the right tab.
 */
export interface DocumentsDestinationSpec {
  tab: DocumentsTab;
  label: string;
  icon: IconName;
  hint: string;
}

export const DOCUMENT_DESTINATIONS: DocumentsDestinationSpec[] = [
  { tab: "drawings", label: "Drawings", icon: "drawing",
    hint: "The permit set — sheets, details, schedules" },
  { tab: "notes", label: "Notes", icon: "note",
    hint: "Design and product notes for this house" },
  { tab: "reports", label: "Reports", icon: "report",
    hint: "Assembly, bill of materials, circuits, HVAC, plumbing, lighting, data" },
];

/** The hub as one destination — the phone bar has room for a container, not three tabs. */
export const DOCUMENTS_DESTINATION = {
  id: "documents" as const,
  label: "Documents",
  icon: "description" as IconName,
  hint: "Permit drawings, design and product notes, and the model reports",
};

export interface ToolSpec {
  id: Tool;
  icon: IconName;
  label: string;
  hint: string;
}

export interface ToolGroupSpec {
  id: ToolGroup;
  icon: IconName;
  label: string;
  tools: ToolSpec[];
}

/** The rail renders this directly; the flyout drills into it. */
export const TOOL_GROUPS: ToolGroupSpec[] = [
  { id: "select", icon: "cursor", label: "Select", tools: [
    { id: "select", icon: "cursor", label: "Select", hint: "Select and move elements" },
  ] },
  { id: "build", icon: "wall", label: "Build", tools: [
    { id: "wall", icon: "wall", label: "Wall", hint: "Draw wall (tap → tap; Shift = ortho)" },
    { id: "room", icon: "room", label: "Room", hint: "Claim a room" },
    { id: "stair", icon: "stairs", label: "Stair", hint: "Add a stair (tap on a floor)" },
  ] },
  { id: "openings", icon: "opening", label: "Openings", tools: [
    { id: "opening", icon: "opening", label: "Window / Door", hint: "Place a window or door on a wall" },
  ] },
  { id: "components", icon: "component", label: "Components", tools: [
    { id: "placeable", icon: "component", label: "Place", hint: "Place furniture, fixtures, and devices" },
  ] },
  { id: "measure", icon: "measure", label: "Measure", tools: [
    { id: "dimension", icon: "dimension", label: "Dimension", hint: "Drive a wall's length" },
    { id: "measure", icon: "measure", label: "Measure", hint: "Tap two points to measure (Shift = ortho)" },
  ] },
];

/** Which group owns the active tool — drives the rail's active highlight. */
export const GROUP_OF_TOOL: Record<Tool, ToolGroup> = {
  select: "select",
  wall: "build",
  room: "build",
  stair: "build",
  opening: "openings",
  placeable: "components",
  dimension: "measure",
  measure: "measure",
};

export const VIEW_MODES = [
  { id: "2d", label: "2D", icon: "view-2d" as IconName, hint: "Plan only" },
  { id: "split", label: "Split", icon: "view-split" as IconName, hint: "Plan and model side by side" },
  { id: "3d", label: "3D", icon: "view-3d" as IconName, hint: "Model only" },
] as const;
