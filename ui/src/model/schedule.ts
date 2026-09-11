// Pure functions over the /schedule payload. No React, no store, no fetch — so the board's
// grouping and its "what is in the way" sentence are testable without a DOM.

import type {
  Constraint,
  HandoffItem,
  Milestone,
  SchedulePayload,
  Visit,
  VisitStatus,
} from "./scheduleTypes";

export interface MilestoneGroup {
  milestone: Milestone;
  ready: Visit[];
  blocked: Visit[];
  done: Visit[];
}

/** Visits grouped under their milestone, in engine order, split by what you can act on. */
export function groupByMilestone(payload: SchedulePayload | null): MilestoneGroup[] {
  if (!payload) return [];
  const bySlug = new Map(payload.visits.map((visit) => [visit.slug, visit]));
  return payload.milestones.map((milestone) => {
    const visits = milestone.visits
      .map((slug) => bySlug.get(slug))
      .filter((visit): visit is Visit => visit !== undefined);
    return {
      milestone,
      ready: visits.filter((v) => v.readiness === "ready" || v.readiness === "in_progress"),
      blocked: visits.filter((v) => v.readiness === "blocked"),
      done: visits.filter((v) => v.readiness === "done" || v.readiness === "verified"),
    };
  });
}

/** The milestone to expand: the first that is not done. */
export function currentMilestone(payload: SchedulePayload | null): string | null {
  if (!payload || payload.milestones.length === 0) return null;
  const open = payload.milestones.find((milestone) => milestone.state !== "done");
  return (open ?? payload.milestones[payload.milestones.length - 1]).id;
}

/** The first thing standing in this visit's way, or null. Attention items never count. */
export function firstBlockerLabel(visit: Visit): string | null {
  const blocker = visit.constraints.find(
    (constraint) => constraint.severity === "blocking" && constraint.cleared === null);
  return blocker ? blocker.label : null;
}

export function blockers(visit: Visit): Constraint[] {
  return visit.constraints.filter(
    (constraint) => constraint.severity === "blocking" && constraint.cleared === null);
}

export function attention(visit: Visit): Constraint[] {
  return visit.constraints.filter((constraint) => constraint.severity === "attention");
}

/**
 * The one visit to put at the top of the board.
 *
 * Priority is what the owner has to do *next*, which is not the same as what comes next in
 * the build: a visit the sub has called done but nobody has walked is the most urgent thing
 * on the site, because the crew is still reachable and the work is still visible.
 */
export function nextVisit(payload: SchedulePayload | null): Visit | null {
  if (!payload) return null;
  const order: Visit["readiness"][] = ["done", "in_progress", "ready"];
  for (const state of order) {
    const found = payload.visits.find((visit) => visit.readiness === state);
    if (found) return found;
  }
  // Nothing is ready — which is the state of every house before the first shovel, and the
  // one where "Next" showing nothing at all is least useful. Fall back to the first blocked
  // visit in the first unfinished milestone: what to work TOWARD, with its blocker under it.
  const current = currentMilestone(payload);
  const blocked = payload.visits.filter((visit) => visit.readiness === "blocked");
  return blocked.find((visit) => visit.milestone === current) ?? blocked[0] ?? null;
}

/** Sheets to bring to a visit: the handoff items' manifest numbers, deduplicated. */
export function visitSheets(visit: Visit): string[] {
  const sheets = visit.handoff
    .map((item) => item.sheet_ref)
    .filter((sheet): sheet is string => Boolean(sheet));
  return Array.from(new Set(sheets)).sort();
}

/** Handoff items still unticked — what the walk is actually for. */
export function openHandoff(visit: Visit): HandoffItem[] {
  return visit.handoff.filter((item) => !item.checked);
}

export interface StatusTransition {
  status: VisitStatus;
  label: string;
  /** Non-null when this transition cannot be taken, and why. */
  disabledBecause: string | null;
}

/**
 * The four buttons on a visit, and which of them the owner may press right now.
 *
 * `verified` is the only one that is ever refused, and the refusal is the point: the engine
 * rejects the write while a hold the owner put on themselves is still open, so disabling the
 * button here is the same rule stated where a thumb can see it rather than after a round
 * trip. Every other transition is legal in both directions — work goes backwards on a site.
 */
export function statusTransitions(visit: Visit): StatusTransition[] {
  const open = visit.constraints.filter(
    (constraint) => constraint.kind === "authored" && constraint.cleared === null);
  return [
    { status: "scheduled", label: "Scheduled", disabledBecause: null },
    { status: "in_progress", label: "On site", disabledBecause: null },
    { status: "done", label: "Done", disabledBecause: null },
    {
      status: "verified",
      label: "Verified",
      disabledBecause: open.length
        ? `${open.length} hold${open.length > 1 ? "s" : ""} still open: ${open[0].label}`
        : null,
    },
  ];
}

/** Visits whose money is done but whose walk is not — the holdback list. */
export function holdbacks(payload: SchedulePayload | null): Visit[] {
  return (payload?.visits ?? []).filter((visit) => visit.holdback_open);
}
