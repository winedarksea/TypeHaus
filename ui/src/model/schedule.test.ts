// The board's grouping and its "what is in the way" rules, against a hand-built payload.
import type { SchedulePayload } from "./scheduleTypes";
import { makeConstraint, makeSchedule, makeVisit } from "./scheduleFixtures";
import {
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

  console.log("Build-board grouping tests passed.");
}
