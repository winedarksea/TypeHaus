// The inspections page's grouping, wording, and the one date this app is allowed to derive.
import type { InspectionsPayload } from "./scheduleTypes";
import { makeAuthority, makeInspection, makeInspections } from "./scheduleFixtures";
import {
  authorityOf,
  callWindowOpen,
  groupInspectionsByMilestone,
  latestRequest,
  nextCallDate,
  readinessLabel,
  requestable,
  telHref,
  unmet,
} from "./inspections";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const record = (partial: Parameters<typeof makeInspection>[0]) =>
  makeInspection({ state: "not_ready", ...partial });

const PAYLOAD: InspectionsPayload = makeInspections({
  authorities: {
    building: makeAuthority({ label: "Saint Paul DSI", phone: "651-266-9002",
                              window: "7:30-9:00 M-F", lead_days: 1 }),
    owner: makeAuthority({ label: "Owner's own hold", lead_days: 0 }),
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
});

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

  // The date is DERIVED BY THE ENGINE against the house calendar and read off the record
  // here. It used to be counted on the client, which could not see an authored holiday —
  // making the one date on this screen the one date that was wrong.
  assert(nextCallDate(record({ id: "x" })) === null, "no derived date, no date");
  assert(nextCallDate(record({ id: "x", dates: { lead_days: 1,
    earliest_call: "2026-09-10", latest_request: "2026-09-09", why: "" } }))
    === "2026-09-10", "the engine's answer is the answer");
  assert(latestRequest(record({ id: "x", dates: { lead_days: 1,
    earliest_call: null, latest_request: "2026-09-09", why: "" } })) === "2026-09-09",
    "and the deadline to call in for a booked appointment comes the same way");

  console.log("Inspection readiness tests passed.");
}
