// The inspections page's grouping, wording, and the one date this app is allowed to derive.
import type { Inspection, InspectionsPayload } from "./scheduleTypes";
import {
  authorityOf,
  callWindowOpen,
  groupInspectionsByMilestone,
  nextCallDate,
  readinessLabel,
  requestable,
  telHref,
  unmet,
} from "./inspections";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

function record(partial: Partial<Inspection> & Pick<Inspection, "id">): Inspection {
  return {
    label: partial.id, authority: "building", sequence: 0, after: [], gates: [],
    applies: true, evidence: "", extra: false, state: "not_ready", entry: null,
    prerequisites: [], checks: [], on_site: [], milestone: "foundation", ...partial,
  };
}

const PAYLOAD: InspectionsPayload = {
  profile: "mn-2020", checks_pending: false,
  authorities: {
    building: { label: "Saint Paul DSI", phone: "651-266-9002",
                window: "7:30-9:00 M-F", lead_days: 1 },
    owner: { label: "Owner's own hold", phone: null, window: null, lead_days: 0 },
  },
  inspections: [
    record({ id: "erosion", state: "passed" }),
    record({ id: "footing", state: "ready", prerequisites: [
      { kind: "inspection", ref: "erosion", label: "Erosion resolved", met: true },
      { kind: "on_site", ref: null, label: "permit card posted", met: false },
    ] }),
    record({ id: "lath", milestone: "weathertight", state: "not_applicable",
             applies: false, evidence: "no cement plaster" }),
    record({ id: "fireplace", milestone: "weathertight", state: "not_ready",
             applies: null, evidence: "no fireplace element kind" }),
    record({ id: "girt_screws", milestone: "weathertight", authority: "owner",
             extra: true, state: "not_ready" }),
  ],
};

export function runInspectionTests(): void {
  const groups = groupInspectionsByMilestone(PAYLOAD);
  assert(groups.length === 2, "grouped by milestone, first-seen first");
  assert(groups[0].milestone === "foundation" && groups[0].inspections.length === 2,
    "profile order is preserved inside a group");
  assert(groups[1].inspections.length === 3, "the house's own extra joins its milestone");
  assert(groupInspectionsByMilestone(null).length === 0, "no payload, no groups");

  assert(readinessLabel(PAYLOAD.inspections[0]) === "Passed", "a plain state");
  assert(readinessLabel(PAYLOAD.inspections[2]) === "Does not apply to this building",
    "N/A says what it means — not 'skipped'");
  assert(readinessLabel(PAYLOAD.inspections[3]).endsWith("applicability unknown"),
    "an inconclusive probe is SAID, never dropped");
  assert(readinessLabel(record({ id: "w", state: "waived" }))
    === "Waived by the authority",
    "waived and not_applicable are different sentences");

  assert(unmet(PAYLOAD.inspections[1]).length === 1, "only the unmet prerequisites");
  assert(requestable(PAYLOAD).map((r) => r.id).join() === "footing",
    "only 'ready' inspections can be phoned in");
  assert(requestable(null).length === 0, "no payload, nothing to request");

  const dsi = authorityOf(PAYLOAD, PAYLOAD.inspections[1]);
  assert(dsi?.label === "Saint Paul DSI", "the authority row is looked up by id");
  assert(telHref(dsi) === "tel:6512669002", "punctuation is stripped from the tel: href");
  assert(telHref(PAYLOAD.authorities.owner) === null,
    "a hold the owner put on themselves has nobody to call");

  // 2026-09-09 is a Wednesday.
  const wednesdayEarly = new Date(2026, 8, 9, 8, 0);
  const wednesdayLate = new Date(2026, 8, 9, 14, 0);
  const saturday = new Date(2026, 8, 12, 8, 0);
  assert(callWindowOpen(wednesdayEarly, "7:30-9:00 M-F") === true, "inside the window");
  assert(callWindowOpen(wednesdayLate, "7:30-9:00 M-F") === false, "after it");
  assert(callWindowOpen(saturday, "7:30-9:00 M-F") === false, "M-F excludes the weekend");
  assert(callWindowOpen(wednesdayEarly, null) === null, "no window stated, no claim");
  assert(callWindowOpen(wednesdayEarly, "call the area inspector") === null,
    "an AHJ's own prose is shown, never guessed at");

  // One business day from a Wednesday is Thursday; from a Friday it is Monday.
  assert(nextCallDate(wednesdayEarly, dsi) === "2026-09-10", "one business day ahead");
  assert(nextCallDate(new Date(2026, 8, 11, 8, 0), dsi) === "2026-09-14",
    "the weekend does not count as notice");
  assert(nextCallDate(wednesdayEarly, PAYLOAD.authorities.owner) === "2026-09-09",
    "zero lead days is today, rolled off a weekend");
  assert(nextCallDate(wednesdayEarly, undefined) === null,
    "no authority row, no derived date");

  console.log("Inspection readiness tests passed.");
}
