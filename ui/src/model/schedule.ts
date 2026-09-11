// Pure functions over the /schedule payload. No React, no store, no fetch — so the board's
// grouping and its "what is in the way" sentence are testable without a DOM.

import type {
  Constraint,
  HandoffItem,
  InspectionsPayload,
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


// --- the action list ------------------------------------------------------------------
//
// "Next visit" answered a question the board could not actually answer: on a house with
// nothing ready it showed the first blocked visit, which is where you are GOING, not what
// to do. The action list answers the real one — what is on me today — in the order the
// things cost you if you miss them.

export type ActionUrgency = "now" | "today" | "soon" | "release";

export interface BoardAction {
  id: string;
  urgency: ActionUrgency;
  title: string;
  detail: string;
  /** The visit to open, when there is one. */
  slug: string | null;
  /** True when this action lives on the inspections page. */
  inspection: string | null;
}

function days(from: Date, iso: string | null): number | null {
  if (!iso) return null;
  const when = Date.parse(iso);
  if (Number.isNaN(when)) return null;
  return Math.round((when - from.getTime()) / 86_400_000);
}

/**
 * Everything standing on the owner right now, worst first.
 *
 * 1. exceptions, expired or expiring locates, threatened bookings
 * 2. today: bookings, inspection windows open now, calls to make
 * 3. a lookahead window: visits whose suggested or planned date falls inside it
 * 4. what releases them: holds with an owner, materials to order, owner checks
 */
export function actionList(
  schedule: SchedulePayload | null,
  inspections: InspectionsPayload | null,
  now: Date = new Date(),
  lookaheadDays = 14,
): BoardAction[] {
  if (!schedule) return [];
  const today = now.toISOString().slice(0, 10);
  const out: BoardAction[] = [];

  for (const visit of schedule.visits) {
    for (const item of visit.exceptions) {
      out.push({
        id: `exception:${visit.slug}:${item.hold}`, urgency: "now",
        title: `Went ahead against an open hold — ${visit.label}`,
        detail: `${item.hold}${item.note ? ` · ${item.note}` : ""} (${item.at})`,
        slug: visit.slug, inspection: null,
      });
    }
    for (const hold of visit.constraints) {
      if (hold.ticket_kind !== "locate") continue;
      const left = days(now, hold.expires);
      if (hold.expires && left !== null && left <= 3) {
        out.push({
          id: `locate:${visit.slug}`, urgency: "now",
          title: left < 0 ? `Locate ticket EXPIRED — ${visit.label}`
                          : `Locate ticket expires in ${left} day(s) — ${visit.label}`,
          detail: hold.derived || hold.label, slug: visit.slug, inspection: null,
        });
      } else if (!hold.armed && hold.cleared === null) {
        out.push({
          id: `locate-unset:${visit.slug}`, urgency: "release",
          title: `Locate ticket not called in — ${visit.label}`,
          detail: hold.derived || hold.label, slug: visit.slug, inspection: null,
        });
      }
    }
    if (visit.dates.threatened_by_days) {
      out.push({
        id: `threat:${visit.slug}`, urgency: "now",
        title: `Booking threatened by ${visit.dates.threatened_by_days} day(s) — ${visit.label}`,
        detail: "A predecessor now finishes after this date. The engine will not move it "
                + "for you: call the sub.",
        slug: visit.slug, inspection: null,
      });
    }
    if (visit.booked?.date === today) {
      out.push({
        id: `booked:${visit.slug}`, urgency: "today",
        title: `Booked today — ${visit.label}`,
        detail: [visit.booked.window, visit.assignee].filter(Boolean).join(" · ")
          || "confirmed",
        slug: visit.slug, inspection: null,
      });
    }
    const when = visit.dates.planned ?? visit.dates.suggested_start;
    const ahead = days(now, when);
    if (ahead !== null && ahead > 0 && ahead <= lookaheadDays
        && visit.readiness !== "done" && visit.readiness !== "verified") {
      out.push({
        id: `ahead:${visit.slug}`, urgency: "soon",
        title: `${when} — ${visit.label}`,
        detail: visit.dates.planned ? "planned, not confirmed with the sub"
                                    : "earliest the sequence allows",
        slug: visit.slug, inspection: null,
      });
    }
    for (const item of visit.dates.materials) {
      if (item.received) continue;
      if (item.ask_now) {
        out.push({
          id: `lead:${visit.slug}:${item.id}`, urgency: "release",
          title: `Lead time unknown — ${item.label || item.id}`,
          detail: `${visit.label}: ask the supplier and write it into tasks.toml`,
          slug: visit.slug, inspection: null,
        });
      } else if (item.order_by && (days(now, item.order_by) ?? 99) <= lookaheadDays) {
        out.push({
          id: `order:${visit.slug}:${item.id}`, urgency: "soon",
          title: `Order by ${item.order_by} — ${item.label || item.id}`,
          detail: visit.label, slug: visit.slug, inspection: null,
        });
      }
    }
    for (const hold of visit.constraints) {
      if (hold.kind !== "authored" || hold.cleared !== null) continue;
      if (hold.ticket_kind === "locate") continue;
      if (!hold.owner && !hold.next_action && !hold.follow_up) continue;
      out.push({
        id: `hold:${visit.slug}:${hold.label}`, urgency: "release",
        title: hold.label,
        detail: [visit.label, hold.owner ? `on ${hold.owner}` : "", hold.next_action,
                 hold.follow_up ? `chase ${hold.follow_up}` : ""]
          .filter(Boolean).join(" · "),
        slug: visit.slug, inspection: null,
      });
    }
  }

  for (const record of inspections?.inspections ?? []) {
    if (record.state === "ready" && !record.entry?.requested) {
      out.push({
        id: `call:${record.id}`, urgency: "today",
        title: `Call in — ${record.label}`,
        detail: inspections?.authorities[record.authority]?.label ?? record.authority,
        slug: null, inspection: record.id,
      });
    }
    if (record.entry?.scheduled === today) {
      out.push({
        id: `appointment:${record.id}`, urgency: "today",
        title: `Inspection today — ${record.label}`,
        detail: record.entry.inspector ?? "", slug: null, inspection: record.id,
      });
    }
    const last = record.attempts[record.attempts.length - 1];
    if (last && last.result !== "pass" && !record.entry?.scheduled) {
      out.push({
        id: `reinspect:${record.id}`, urgency: "now",
        title: `Failed and not rebooked — ${record.label}`,
        detail: last.corrections.join("; ") || last.date,
        slug: null, inspection: record.id,
      });
    }
  }

  const rank: Record<ActionUrgency, number> = { now: 0, today: 1, soon: 2, release: 3 };
  return out.sort((a, b) => rank[a.urgency] - rank[b.urgency]
    || a.title.localeCompare(b.title));
}
