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
 * The earliest date an inspection could happen, as a *date only* and only from what the
 * authority itself stated.
 *
 * `lead_days` is a number the jurisdiction publishes ("one business day's notice"), not a
 * duration this app invented — the engine computes no dates at all, and this is the one
 * place a date is derived, from an authored number, on the client, for a phone call.
 */
export function nextCallDate(now: Date, authority: InspectionAuthority | undefined)
: string | null {
  if (!authority || authority.lead_days === null) return null;
  const date = new Date(now.getTime());
  let remaining = Math.max(0, authority.lead_days);
  while (remaining > 0) {
    date.setDate(date.getDate() + 1);
    if (date.getDay() !== 0 && date.getDay() !== 6) remaining -= 1;
  }
  while (date.getDay() === 0 || date.getDay() === 6) date.setDate(date.getDate() + 1);
  return date.toISOString().slice(0, 10);
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
