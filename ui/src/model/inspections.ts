// Pure functions over the /inspections payload — grouping, the readiness wording, and the
// one piece of arithmetic on this whole surface: whether the AHJ is taking calls right now.

import type {
  Inspection,
  InspectionAuthority,
  InspectionsPayload,
  InspectionState,
  Prerequisite,
} from "./scheduleTypes";

export interface InspectionGroup {
  milestone: string;
  inspections: Inspection[];
}

/** In profile order, grouped by milestone, first-seen milestone first. */
export function groupInspectionsByMilestone(payload: InspectionsPayload | null)
: InspectionGroup[] {
  const groups: InspectionGroup[] = [];
  for (const record of payload?.inspections ?? []) {
    const existing = groups.find((group) => group.milestone === record.milestone);
    if (existing) existing.inspections.push(record);
    else groups.push({ milestone: record.milestone, inspections: [record] });
  }
  return groups;
}

const LABELS: Record<InspectionState, string> = {
  passed: "Passed",
  failed: "Failed — reinspection needed",
  scheduled: "Scheduled",
  requested: "Requested",
  ready: "Ready to request",
  not_ready: "Not ready",
  // Two different sentences, and keeping them apart is the point: the first is the AHJ
  // saying it is not required here, the second is this building not having the condition.
  waived: "Waived by the authority",
  not_applicable: "Does not apply to this building",
};

export function readinessLabel(record: Inspection): string {
  if (record.applies === null && record.state !== "passed") {
    return `${LABELS[record.state]} — applicability unknown`;
  }
  return LABELS[record.state];
}

export function unmet(record: Inspection): Prerequisite[] {
  return record.prerequisites.filter((prerequisite) => !prerequisite.met);
}

/** Inspections you could phone in right now. What the extended FAB offers. */
export function requestable(payload: InspectionsPayload | null): Inspection[] {
  return (payload?.inspections ?? []).filter((record) => record.state === "ready");
}

/**
 * Is the authority taking calls at `now`?
 *
 * `window` is the jurisdiction's own wording, authored in inspections.toml — "7:30-9:00
 * M-F". Anything this cannot parse returns null, which the UI renders as the raw string:
 * showing an AHJ's own sentence is always right, and guessing at one is not.
 */
export function callWindowOpen(now: Date, window: string | null): boolean | null {
  if (!window) return null;
  const match = /(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})/.exec(window);
  if (!match) return null;
  const weekdaysOnly = /M-F/i.test(window);
  const day = now.getDay();
  if (weekdaysOnly && (day === 0 || day === 6)) return false;
  const minutes = now.getHours() * 60 + now.getMinutes();
  const from = Number(match[1]) * 60 + Number(match[2]);
  const to = Number(match[3]) * 60 + Number(match[4]);
  return minutes >= from && minutes <= to;
}

/**
 * The earliest date an inspection could happen — read off the record, not computed here.
 *
 * This used to count weekends on the client, which meant it could not see the house's own
 * `[calendar]`: a holiday the owner authored was a working day to this function, and the
 * one date on that screen was the one date that was wrong. `schedule/timing.py` derives it
 * now, from the authority's own published `lead_days` and the house calendar, and an
 * authority that has published no lead time gets no date and a sentence saying so.
 */
export function nextCallDate(record: Inspection): string | null {
  return record.dates?.earliest_call ?? null;
}

/** The last working day to call in for the appointment already booked, or null. */
export function latestRequest(record: Inspection): string | null {
  return record.dates?.latest_request ?? null;
}

export function authorityOf(payload: InspectionsPayload | null, record: Inspection)
: InspectionAuthority | undefined {
  return payload?.authorities[record.authority];
}

/** `tel:` href for an authority, or null when there is nobody to call (owner, report). */
export function telHref(authority: InspectionAuthority | undefined): string | null {
  if (!authority?.phone) return null;
  return `tel:${authority.phone.replace(/[^\d+]/g, "")}`;
}
