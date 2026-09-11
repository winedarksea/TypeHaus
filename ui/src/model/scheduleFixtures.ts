// Builders for the site payloads, so a test states the two fields it is about and nothing
// else. Shared by the model tests and the store tests, and kept beside the types rather
// than in a test file because both sides import it.

import type {
  Constraint,
  Inspection,
  InspectionAuthority,
  InspectionsPayload,
  Permit,
  SchedulePayload,
  Visit,
  VisitDates,
} from "./scheduleTypes";

export function makeConstraint(partial: Partial<Constraint> & Pick<Constraint, "label">)
: Constraint {
  return {
    kind: "authored", ref: null, cleared: null, severity: "blocking", element_tags: [],
    owner: null, next_action: null, follow_up: null, ticket_kind: "", ticket: null,
    ticket_start: null, refresh_agreement: false, armed: null, expires: null, derived: "",
    ...partial,
  };
}

export function makeDates(partial: Partial<VisitDates> = {}): VisitDates {
  return {
    slug: partial.slug ?? "", suggested_start: null, suggested_finish: null,
    planned: null, booked: null, threatened_by_days: null, why: "", materials: [],
    ...partial,
  };
}

export function makeVisit(partial: Partial<Visit> & Pick<Visit, "slug">): Visit {
  return {
    id: partial.slug, package: partial.slug, label: partial.slug, trade: "concrete",
    storey: "building", milestone: "foundation", status: "todo", scheduled: null,
    assignee: null, contact: null, note: null, depends_on: [], rows: [], element_tags: [],
    checked: [], estimate_fmt: "", holdback_open: false, implicit: true,
    standalone: false, blocks_successors: true, shared_rows: false, checkpoints: [],
    exceptions: [], skipped: [], log: [], updated: null, needs_rewalk: false,
    orphan_ticks: [], planned: null, booked: null, duration_days: null, materials: [],
    contractor: null, readiness: "ready", constraints: [], handoff: [],
    dates: makeDates({ slug: partial.slug }),
    ...partial,
  };
}

export function makeSchedule(partial: Partial<SchedulePayload> = {}): SchedulePayload {
  return {
    profile: "mn-2020", checks_pending: false, revision: "r0", milestones: [], visits: [],
    proposals: {}, stale: [], errors: [], dropped_gates: [],
    contractors: {},
    ...partial,
  };
}

export function makeAuthority(partial: Partial<InspectionAuthority> = {})
: InspectionAuthority {
  return {
    label: "Authority", phone: null, portal_url: null, window: null, lead_days: null,
    method: null, source_url: null, confirmed: null, ...partial,
  };
}

export function makePermit(partial: Partial<Permit> = {}): Permit {
  return {
    number: null, issued: null, expires: null, code_edition: null, nec_edition: null,
    note: null, ...partial,
  };
}

export function makeInspection(partial: Partial<Inspection> & Pick<Inspection, "id">)
: Inspection {
  return {
    label: partial.id, authority: "building", sequence: 0, spec_id: partial.id,
    scope: [], approved: [], attempts: [], after: [], gates: [], applies: true,
    evidence: "", extra: false, state: "ready", entry: null, prerequisites: [],
    checks: [], on_site: [], milestone: "foundation",
    ...partial,
  };
}

export function makeInspections(partial: Partial<InspectionsPayload> = {})
: InspectionsPayload {
  return {
    profile: "mn-2020", checks_pending: false, revision: "r0", authorities: {},
    permit: makePermit(), errors: [], inspections: [],
    ...partial,
  };
}
