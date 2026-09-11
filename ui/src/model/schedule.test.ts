// The board's grouping and its "what is in the way" rules, against a hand-built payload.
import type { SchedulePayload } from "./scheduleTypes";
import {
  makeConstraint,
  makeDates,
  makeInspection,
  makeInspections,
  makeSchedule,
  makeVisit,
} from "./scheduleFixtures";
import {
  actionList,
  attention,
  blockers,
  currentMilestone,
  firstBlockerLabel,
  groupByMilestone,
  holdbacks,
  nextVisit,
  openHandoff,
  statusTransitions,
  visitSheets,
} from "./schedule";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const visit = makeVisit;

const PAYLOAD: SchedulePayload = makeSchedule({
  milestones: [
    { id: "foundation", label: "Foundation", trades: ["concrete"],
      visits: ["task/concrete/building", "task/earth/building"], inspections: ["footing"],
      state: "in_progress" },
    { id: "weathertight", label: "Weathertight", trades: ["framing"],
      visits: ["task/framing/building"], inspections: [], state: "not_started" },
  ],
  visits: [
    visit({ slug: "task/concrete/building", readiness: "blocked", constraints: [
      makeConstraint({ kind: "visit", ref: "task/earth/building",
                       label: "earth complete" }),
      makeConstraint({ kind: "attention", ref: "x", label: "UNKNOWN — no soil class",
                       severity: "attention" }),
    ] }),
    visit({ slug: "task/earth/building", trade: "earth", readiness: "done",
            status: "done" }),
    visit({ slug: "task/framing/building", trade: "framing", milestone: "weathertight",
            readiness: "ready", handoff: [
              { id: "a", label: "A", count: 1, element_tags: [], sheet_ref: "S-201",
                derived: "", checked: true },
              { id: "b", label: "B", count: 2, element_tags: [], sheet_ref: "A-602",
                derived: "", checked: false },
              { id: "c", label: "C", count: null, element_tags: [], sheet_ref: null,
                derived: "", checked: false },
            ] }),
  ],
});

export function runScheduleTests(): void {
  const groups = groupByMilestone(PAYLOAD);
  assert(groups.length === 2, "one group per milestone, in engine order");
  assert(groups[0].milestone.id === "foundation", "engine order is preserved");
  assert(groups[0].blocked.map((v) => v.slug).join() === "task/concrete/building",
    "blocked visits are separated from ready ones");
  assert(groups[0].done.map((v) => v.slug).join() === "task/earth/building",
    "done visits collapse into their own lane");

  assert(groupByMilestone(null).length === 0, "no payload, no groups");

  assert(currentMilestone(PAYLOAD) === "foundation", "the first not-done milestone");
  assert(currentMilestone(null) === null, "no payload, no current milestone");

  const concrete = PAYLOAD.visits[0];
  assert(firstBlockerLabel(concrete) === "earth complete", "the first BLOCKING constraint");
  assert(blockers(concrete).length === 1, "an attention item is not a blocker");
  assert(attention(concrete).length === 1, "and it is still reported");
  assert(firstBlockerLabel(PAYLOAD.visits[1]) === null, "a clear visit has no blocker");

  // A visit the sub called done but nobody walked is the most urgent thing on the site:
  // the crew is still reachable and the work is still visible.
  assert(nextVisit(PAYLOAD)?.slug === "task/earth/building", "done-but-unwalked comes first");
  assert(nextVisit({ ...PAYLOAD, visits: [PAYLOAD.visits[2]] })?.slug
    === "task/framing/building", "otherwise the first ready visit");
  assert(nextVisit({ ...PAYLOAD, visits: [] }) === null, "and null when there is none");
  // Before the first shovel nothing is ready, and "Next: nothing" is the least useful thing
  // this card could say — so it falls back to what to work TOWARD, in the current milestone.
  assert(nextVisit({ ...PAYLOAD, visits: [PAYLOAD.visits[0]] })?.slug
    === "task/concrete/building", "falls back to the first blocked visit");

  const framing = PAYLOAD.visits[2];
  assert(visitSheets(framing).join() === "A-602,S-201", "sheets deduplicated and sorted");
  assert(visitSheets(PAYLOAD.visits[1]).length === 0, "no handoff, no sheets");
  assert(openHandoff(framing).map((i) => i.id).join() === "b,c", "ticked items drop out");

  const transitions = statusTransitions(framing);
  assert(transitions.length === 4, "four status buttons");
  assert(transitions.every((t) => t.disabledBecause === null),
    "with no authored holds, every transition is available");

  const held = visit({ slug: "x", constraints: [
    makeConstraint({ label: "girt screws verified", cleared: null }),
  ] });
  const verified = statusTransitions(held).find((t) => t.status === "verified")!;
  assert(verified.disabledBecause?.includes("girt screws verified"),
    "verified is refused while an owner hold is open, and says which one");
  assert(statusTransitions(held).find((t) => t.status === "done")!.disabledBecause === null,
    "but DONE is the sub's claim and is never refused");

  const cleared = visit({ slug: "x", constraints: [
    makeConstraint({ label: "girt screws verified", cleared: "2027-06-01" }),
  ] });
  assert(statusTransitions(cleared).find((t) => t.status === "verified")!.disabledBecause
    === null, "clearing the hold opens the walk");

  assert(holdbacks(PAYLOAD).length === 0, "no holdback on this payload");
  assert(holdbacks({ ...PAYLOAD, visits: [visit({ slug: "y", holdback_open: true })] })
    .length === 1, "and one when a verified visit still owes money");

  runActionListTests();
  console.log("Build-board grouping tests passed.");
}

/**
 * The action list, which replaced "Next visit".
 *
 * The old card answered a question the board could not answer: with nothing ready it showed
 * the first BLOCKED visit — where you are going, not what to do — and mid-build it showed
 * one thing while four others were on fire.
 */
function runActionListTests(): void {
  const now = new Date("2027-05-10T08:00:00Z");
  const today = "2027-05-10";

  const payload = makeSchedule({
    visits: [
      visit({
        slug: "task/concrete/building/footings", label: "Footings",
        readiness: "in_progress",
        exceptions: [{ at: "2027-05-09", hold: "rebar delivered", note: "went ahead" }],
      }),
      visit({
        slug: "site/dig", label: "Excavation", readiness: "blocked",
        constraints: [makeConstraint({
          label: "locate ticket", ticket_kind: "locate", ticket_start: "2027-04-28",
          armed: "2027-04-30", expires: "2027-05-12", derived: "216D.04",
        })],
      }),
      visit({
        slug: "task/concrete/basement/walls", label: "Walls", readiness: "blocked",
        booked: { date: today, window: "07:00", confirmed_by: "Nordic", confirmed_at: null,
                  note: null },
        dates: makeDates({ slug: "task/concrete/basement/walls", booked: today,
                           threatened_by_days: 4 }),
      }),
      visit({
        slug: "task/framing/building", label: "Framing", readiness: "blocked",
        dates: makeDates({ slug: "task/framing/building", suggested_start: "2027-05-20",
                           materials: [{ id: "trusses", label: "Roof trusses",
                                         lead_days: null, order_by: null, ordered: null,
                                         expected: null, received: null, source: null,
                                         note: null, ask_now: true, why: "lead time unknown" }] }),
        constraints: [makeConstraint({
          label: "sealed truss drawings on site", owner: "owner",
          next_action: "chase the fabricator", follow_up: "2027-05-12" })],
      }),
    ],
  });

  const inspections = makeInspections({
    authorities: {},
    inspections: [
      makeInspection({ id: "erosion", label: "Erosion", state: "ready" }),
      makeInspection({ id: "footing", label: "Footing", state: "failed",
                       attempts: [{ date: "2027-05-06", result: "fail", inspector: null,
                                    corrections: ["bolts off layout"], approved: [],
                                    note: null }] }),
    ],
  });

  const actions = actionList(payload, inspections, now, 14);
  const at = (id: string) => actions.findIndex((a) => a.id.startsWith(id));

  assert(actions[0].urgency === "now", "the worst thing is first");
  assert(at("exception:") >= 0, "an exception is on the list");
  assert(at("threat:") >= 0, "so is a threatened booking");
  assert(at("locate:") >= 0, "and a locate two days from lapsing");
  assert(at("reinspect:") >= 0, "and an inspection that failed and was never rebooked");
  assert(at("booked:") > at("threat:"), "today sits under now");
  assert(at("ahead:") > at("booked:"), "the lookahead sits under today");
  assert(at("lead:") > at("ahead:"), "and what releases them is last");
  assert(at("hold:") > at("ahead:"), "a hold with an owner is a release item");

  // A lookahead of one week drops the 17th, which is exactly what the control is for.
  const tight = actionList(payload, inspections, now, 7);
  assert(tight.findIndex((a) => a.id.startsWith("ahead:")) === -1,
    "the lookahead window is the owner's, not the engine's");

  assert(actionList(null, null, now).length === 0, "no payload, no actions");
}
