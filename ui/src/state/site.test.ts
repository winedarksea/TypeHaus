// The optimistic write and its revert, and the cache that keeps the board readable in a
// basement. Pure functions only — the slice's async half is exercised through them.
import type { InspectionsPayload, SchedulePayload } from "../model/scheduleTypes";
import {
  makeConstraint,
  makeInspection,
  makeInspections,
  makeSchedule,
  makeVisit,
} from "../model/scheduleFixtures";
import { applyInspectionLocally, applyVisitLocally, cacheKey } from "./site";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const SCHEDULE: SchedulePayload = makeSchedule({
  visits: [makeVisit({
    slug: "task/concrete/building/footings", package: "task/concrete/building",
    label: "Footings", status: "scheduled", scheduled: "2027-05-04", implicit: false,
    constraints: [
      makeConstraint({ label: "rebar delivered" }),
      makeConstraint({ kind: "visit", ref: "task/earth/building",
                       label: "earth complete" }),
    ],
    handoff: [
      { id: "sleeves:SL-B-FLOOR", label: "5 sleeves", count: 5, element_tags: [],
        sheet_ref: "S-100", derived: "", checked: false },
      { id: "holdowns", label: "12 holdowns", count: 12, element_tags: [],
        sheet_ref: "S-100", derived: "", checked: false },
    ],
  })],
});

const INSPECTIONS: InspectionsPayload = makeInspections({
  inspections: [makeInspection({
    id: "footing", label: "Footing", sequence: 1,
    on_site: [{ label: "permit card posted", checked: false },
              { label: "forms braced", checked: false }],
  })],
});

export function runSiteStoreTests(): void {
  const slug = "task/concrete/building/footings";

  const onSite = applyVisitLocally(SCHEDULE, { op: "set_visit", slug,
                                               status: "in_progress" });
  assert(onSite.visits[0].status === "in_progress", "status paints immediately");
  assert(SCHEDULE.visits[0].status === "scheduled",
    "and the payload it came from is untouched, so a failed write can revert to it");

  // Item-level, not a whole array: two thumbs on two items used to post each other's
  // stale `checked` list and delete a tick nobody unticked.
  const ticked = applyVisitLocally(SCHEDULE, { op: "tick_handoff", slug,
                                               item: "holdowns" });
  assert(ticked.visits[0].checked.join() === "holdowns", "the item joins the tick list");
  assert(ticked.visits[0].handoff.find((i) => i.id === "holdowns")!.checked === true,
    "and the handoff item shows it under the thumb that pressed it");
  assert(ticked.visits[0].handoff.find((i) => i.id.startsWith("sleeves"))!.checked === false,
    "without disturbing the others");

  const skipped = applyVisitLocally(SCHEDULE, {
    op: "skip_handoff", slug, item: "holdowns", reason: "supplied by the next sub" });
  assert(skipped.visits[0].skipped[0].reason === "supplied by the next sub",
    "a skip records its reason — removing evidence silently is what this prevents");

  const cleared = applyVisitLocally(SCHEDULE, {
    op: "set_visit", slug, cleared: { "rebar delivered": "2027-04-28" } });
  assert(cleared.visits[0].constraints[0].cleared === "2027-04-28", "a hold clears");
  assert(cleared.visits[0].constraints[1].cleared === null,
    "and a DERIVED constraint is never touched by an authored clearance");

  const other = applyVisitLocally(SCHEDULE, { op: "set_visit",
                                              slug: "task/earth/building",
                                              status: "done" });
  assert(other.visits[0].status === "scheduled", "an op for another visit changes nothing");

  const requested = applyInspectionLocally(INSPECTIONS, {
    op: "set_inspection", id: "footing", requested: "2027-05-04" });
  assert(requested.inspections[0].state === "requested", "the obvious transition paints");
  const passed = applyInspectionLocally(INSPECTIONS, {
    op: "add_attempt", id: "footing", date: "2027-05-05", result: "pass" });
  assert(passed.inspections[0].state === "passed", "and so does a pass");
  assert(passed.inspections[0].attempts.length === 1, "which ARRIVES as an attempt");
  const failed = applyInspectionLocally(passed, {
    op: "add_attempt", id: "footing", date: "2027-05-08", result: "partial",
    approved: ["FT-B-*"] });
  assert(failed.inspections[0].state === "failed", "partial is a failed visit, not a pass");
  assert(failed.inspections[0].attempts.length === 2,
    "and the first attempt is still there — a second call used to overwrite it");

  const oneTick = applyInspectionLocally(INSPECTIONS, {
    op: "set_inspection", id: "footing", checked: ["permit card posted"] });
  assert(oneTick.inspections[0].on_site[0].checked === true, "the tick lands");
  assert(oneTick.inspections[0].on_site[1].checked === false, "and only that one");
  assert(INSPECTIONS.inspections[0].on_site[0].checked === false,
    "the original payload survives for the revert");

  // The cache key carries the origin as well as the house: two engines on one laptop wrote
  // over each other's board, and it looked exactly like an engine bug.
  assert(cacheKey("catlin", "http://localhost:8765")
    !== cacheKey("catlin", "http://localhost:8766"),
    "two servers do not share a cache entry");

  console.log("Site optimistic-write tests passed.");
}
