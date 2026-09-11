// The optimistic write and its revert, and the cache that keeps the board readable in a
// basement. Pure functions only — the slice's async half is exercised through them.
import type { InspectionsPayload, SchedulePayload } from "../model/scheduleTypes";
import { applyInspectionLocally, applyVisitLocally } from "./site";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const SCHEDULE: SchedulePayload = {
  profile: "mn-2020", checks_pending: false, proposals: {}, stale: [], milestones: [],
  visits: [{
    slug: "task/concrete/building/footings", id: "x", package: "task/concrete/building",
    label: "Footings", trade: "concrete", storey: "building", milestone: "foundation",
    status: "scheduled", scheduled: "2027-05-04", assignee: null, contact: null,
    note: null, depends_on: [], rows: [], element_tags: [], checked: [],
    estimate_fmt: "", holdback_open: false, implicit: false, readiness: "ready",
    constraints: [
      { kind: "authored", ref: null, label: "rebar delivered", cleared: null,
        severity: "blocking", element_tags: [] },
      { kind: "visit", ref: "task/earth/building", label: "earth complete",
        cleared: null, severity: "blocking", element_tags: [] },
    ],
    handoff: [
      { id: "sleeves:SL-B-FLOOR", label: "5 sleeves", count: 5, element_tags: [],
        sheet_ref: "S-100", derived: "", checked: false },
      { id: "holdowns", label: "12 holdowns", count: 12, element_tags: [],
        sheet_ref: "S-100", derived: "", checked: false },
    ],
  }],
};

const INSPECTIONS: InspectionsPayload = {
  profile: "mn-2020", checks_pending: false, authorities: {},
  inspections: [{
    id: "footing", label: "Footing", authority: "building", sequence: 1, after: [],
    gates: [], applies: true, evidence: "", extra: false, state: "ready", entry: null,
    prerequisites: [], checks: [], milestone: "foundation",
    on_site: [{ label: "permit card posted", checked: false },
              { label: "forms braced", checked: false }],
  }],
};

export function runSiteStoreTests(): void {
  const slug = "task/concrete/building/footings";

  const onSite = applyVisitLocally(SCHEDULE, { slug, status: "in_progress" });
  assert(onSite.visits[0].status === "in_progress", "status paints immediately");
  assert(SCHEDULE.visits[0].status === "scheduled",
    "and the payload it came from is untouched, so a failed write can revert to it");

  const ticked = applyVisitLocally(SCHEDULE, { slug, checked: ["holdowns"] });
  assert(ticked.visits[0].checked.join() === "holdowns", "the tick list is replaced");
  assert(ticked.visits[0].handoff.find((i) => i.id === "holdowns")!.checked === true,
    "and the handoff item shows it under the thumb that pressed it");
  assert(ticked.visits[0].handoff.find((i) => i.id.startsWith("sleeves"))!.checked === false,
    "without disturbing the others");

  const cleared = applyVisitLocally(SCHEDULE, {
    slug, cleared: { "rebar delivered": "2027-04-28" } });
  assert(cleared.visits[0].constraints[0].cleared === "2027-04-28", "a hold clears");
  assert(cleared.visits[0].constraints[1].cleared === null,
    "and a DERIVED constraint is never touched by an authored clearance");

  const other = applyVisitLocally(SCHEDULE, { slug: "task/earth/building",
                                              status: "done" });
  assert(other.visits[0].status === "scheduled", "an op for another visit changes nothing");

  const requested = applyInspectionLocally(INSPECTIONS, { id: "footing",
                                                          requested: "2027-05-04" });
  assert(requested.inspections[0].state === "requested", "the obvious transition paints");
  const passed = applyInspectionLocally(INSPECTIONS, { id: "footing", result: "pass" });
  assert(passed.inspections[0].state === "passed", "and so does a pass");
  const failed = applyInspectionLocally(INSPECTIONS, { id: "footing", result: "partial" });
  assert(failed.inspections[0].state === "failed", "partial is a failed visit, not a pass");

  const oneTick = applyInspectionLocally(INSPECTIONS, {
    id: "footing", checked: ["permit card posted"] });
  assert(oneTick.inspections[0].on_site[0].checked === true, "the tick lands");
  assert(oneTick.inspections[0].on_site[1].checked === false, "and only that one");
  assert(INSPECTIONS.inspections[0].on_site[0].checked === false,
    "the original payload survives for the revert");

  console.log("Site optimistic-write tests passed.");
}
