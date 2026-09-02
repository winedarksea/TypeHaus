import type { IconName } from "../../icons/names";
import type { DetailView, Tool, ToolGroup } from "../../state/vocabulary";

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
];

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
