// The /schedule and /inspections payloads, and the ops that write them.
//
// Types only, no imports: this file is the contract between the engine's
// `schedule/` package and the site surface, and both sides were built against it
// before either existed. Field names mirror the Python `as_dict()` writers exactly.

export type VisitStatus = "todo" | "scheduled" | "in_progress" | "done" | "verified";
export type VisitReadinessState =
  | "ready" | "blocked" | "in_progress" | "done" | "verified";
export type InspectionState =
  | "passed" | "failed" | "scheduled" | "requested" | "ready"
  | "not_ready" | "not_applicable" | "waived";
export type Authority =
  | "building" | "electrical" | "plumbing" | "mechanical" | "report" | "owner";

export interface BomRowRef { section: string; key: string }

/** Where a constraint came from — what lets the UI order them worst-first. */
export type ConstraintKind =
  | "visit" | "inspection" | "authored" | "finding" | "attention";

export interface Constraint {
  kind: ConstraintKind;
  ref: string | null;
  label: string;
  /** Authored clearance date. Non-null means the owner ticked it off. */
  cleared: string | null;
  severity: "blocking" | "attention";
  element_tags: string[];
  /** The three fields that turn a hold into a task. Null on a derived constraint. */
  owner: string | null;
  next_action: string | null;
  follow_up: string | null;
  /** "locate" for a Gopher State One Call ticket; "" on every untyped hold. */
  ticket_kind: string;
  ticket: string | null;
  ticket_start: string | null;
  refresh_agreement: boolean;
  /** Derived from a typed hold: when it arms, when it lapses, and the sentence that says how. */
  armed: string | null;
  expires: string | null;
  derived: string;
}

export interface Checkpoint {
  id: string;
  label: string;
  status: "todo" | "in_progress" | "done";
  /** Refs this checkpoint waits on beyond the visit's own. */
  after: string[];
  /** Calendar days the work sits before the next checkpoint. Authored, never defaulted. */
  cure_days: number | null;
  started: string | null;
  completed: string | null;
}

/** `done` was claimed while a blocking hold was open. The hold stays open. */
export interface VisitException { at: string; hold: string; note: string }

export interface SkippedHandoff { id: string; reason: string }

export interface LogLine { at: string; from: string; to: string; ref: string }

export interface Booking {
  date: string;
  window: string | null;
  confirmed_by: string | null;
  confirmed_at: string | null;
  note: string | null;
}

export interface VisitMaterial {
  id: string;
  label: string;
  /** Authored when quoted. Null is "lead time unknown", never a default. */
  lead_days: number | null;
  order_by: string | null;
  ordered: string | null;
  /** A promise. Only `received` is a fact. */
  expected: string | null;
  received: string | null;
  source: string | null;
  note: string | null;
  on_site?: boolean;
  why?: string;
  ask_now?: boolean;
}

/** Everything `schedule/timing.py` can say about one visit's calendar. */
export interface VisitDates {
  slug: string;
  suggested_start: string | null;
  suggested_finish: string | null;
  planned: string | null;
  booked: string | null;
  /** Days a predecessor overruns a booking. The engine never moves the booking. */
  threatened_by_days: number | null;
  why: string;
  materials: VisitMaterial[];
}

export interface Contractor {
  key: string;
  name: string;
  phone: string | null;
  email: string | null;
  trades: string[];
  licence: string | null;
  coi_expires: string | null;
  w9: string | null;
  contract: string | null;
  note: string | null;
  /** Attention items, never blocks. A sub without digital paperwork stays bookable. */
  missing_documents: string[];
}

export interface HandoffItem {
  id: string;
  label: string;
  count: number | null;
  element_tags: string[];
  /** Manifest sheet number to bring, e.g. "A-301". */
  sheet_ref: string | null;
  /** Where the number came from — including "the model knows the count, not the positions". */
  derived: string;
  checked: boolean;
}

export interface VisitEntry {
  status: VisitStatus;
  scheduled: string | null;
  assignee: string | null;
  contact: string | null;
  note: string | null;
}

export interface Visit {
  slug: string;
  id: string;
  package: string;
  label: string;
  trade: string;
  storey: string;
  milestone: string;
  status: VisitStatus;
  scheduled: string | null;
  assignee: string | null;
  contact: string | null;
  note: string | null;
  depends_on: string[];
  rows: BomRowRef[];
  element_tags: string[];
  checked: string[];
  estimate_fmt: string;
  /** Verified, gate passed, and some row is billed but unpaid. */
  holdback_open: boolean;
  /** True when nobody authored a split and this visit is the whole package. */
  implicit: boolean;
  /** True for a `site/<label>` visit that draws from no work package at all. */
  standalone: boolean;
  blocks_successors: boolean;
  shared_rows: boolean;
  checkpoints: Checkpoint[];
  exceptions: VisitException[];
  skipped: SkippedHandoff[];
  log: LogLine[];
  updated: string | null;
  needs_rewalk: boolean;
  orphan_ticks: string[];
  planned: string | null;
  booked: Booking | null;
  duration_days: number | null;
  materials: VisitMaterial[];
  contractor: string | null;
  readiness: VisitReadinessState;
  constraints: Constraint[];
  handoff: HandoffItem[];
  dates: VisitDates;
}

export interface Milestone {
  id: string;
  label: string;
  trades: string[];
  visits: string[];
  inspections: string[];
  state: "not_started" | "in_progress" | "done";
}

export interface ProposedVisit {
  slug: string;
  label: string;
  rows: BomRowRef[];
  element_tags: string[];
  depends_on: string[];
  constraints: string[];
  /** Ready-to-paste tasks.toml source — the engine proposes, the person commits. */
  toml: string;
}

export interface SchedulePayload {
  profile: string;
  /** True when the model resolved but checks have not run yet. */
  checks_pending: boolean;
  /** The content hash of both site-state files. Send it back as `if_revision`. */
  revision: string;
  milestones: Milestone[];
  visits: Visit[];
  proposals: Record<string, ProposedVisit[]>;
  stale: string[];
  /** Dependency loops and rule violations. The board shows the last valid state plus these. */
  errors: string[];
  dropped_gates: { trade: string; inspection: string }[];
  contractors: Record<string, Contractor>;
}

export interface Prerequisite {
  kind: "inspection" | "visit" | "check" | "on_site";
  ref: string | null;
  label: string;
  met: boolean;
}

export interface InspectionCheck {
  check_id: string;
  result: "pass" | "fail" | "unknown" | "not_applicable";
  detail: string;
  element_tags: string[];
}

/** One visit by the inspector, and what they wrote on the card. Nothing overwrites one. */
export interface Attempt {
  date: string;
  result: "pass" | "fail" | "partial";
  inspector: string | null;
  /** What has to change before the next attempt. The reinspection answers these. */
  corrections: string[];
  /** On a `partial`: the tag globs and/or visit slugs this attempt released. */
  approved: string[];
  note: string | null;
}

/** A waiver outranks the model's own evidence, so it has to say who granted it. */
export interface Waiver {
  by: string;
  date: string | null;
  ref: string | null;
  note: string | null;
}

export interface InspectionEntry {
  requested: string | null;
  scheduled: string | null;
  inspector: string | null;
  note: string | null;
  /** Tag globs and/or visit slugs this instance covers. Empty is the whole building. */
  scope: string[];
  checked: string[];
  requires: string[];
  attempts: Attempt[];
  waived: Waiver | null;
  /** Derived from the last attempt. Never a slot anybody overwrites. */
  result: "pass" | "fail" | "partial" | null;
  approved: string[];
}

export interface InspectionAuthority {
  label: string;
  phone: string | null;
  portal_url: string | null;
  window: string | null;
  /** Not published by Saint Paul DSI — an open item asked for at permit issuance. */
  lead_days: number | null;
  method: "phone" | "portal" | "email" | null;
  source_url: string | null;
  /** The date the owner last confirmed the number against the source. */
  confirmed: string | null;
}

export interface Permit {
  number: string | null;
  issued: string | null;
  expires: string | null;
  /** A field, not a constant: which cycle this permit was pulled against. */
  code_edition: string | null;
  nec_edition: string | null;
  note: string | null;
}

export interface Inspection {
  /** The INSTANCE key: "footing", or "footing/court" for a second one. */
  id: string;
  label: string;
  authority: Authority;
  sequence: number;
  /** The jurisdiction's spec this instance is of. Equal to `id` on the default instance. */
  spec_id: string;
  scope: string[];
  /** The scope released so far — ["*"] on a full pass, the named globs on a partial. */
  approved: string[];
  attempts: Attempt[];
  after: string[];
  gates: string[];
  /** null = applicability unknown. Listed as such, never dropped. */
  applies: boolean | null;
  evidence: string;
  extra: boolean;
  state: InspectionState;
  entry: InspectionEntry | null;
  prerequisites: Prerequisite[];
  checks: InspectionCheck[];
  on_site: { label: string; checked: boolean }[];
  milestone: string;
  /** Derived by `schedule/timing.py` against the house calendar, never by the client. */
  dates?: InspectionDates;
}

export interface InspectionDates {
  lead_days: number | null;
  /** Earliest this could happen, from the authority's own published notice period. */
  earliest_call: string | null;
  /** Last working day to call in for the appointment already booked. */
  latest_request: string | null;
  /** Why there is no date, where there is none. */
  why: string;
}

export interface InspectionsPayload {
  profile: string;
  checks_pending: boolean;
  revision: string;
  authorities: Record<string, InspectionAuthority>;
  permit: Permit;
  errors: string[];
  inspections: Inspection[];
}

// --- write ops ------------------------------------------------------------------------

export interface SetVisitOp {
  op: "set_visit";
  slug: string;
  status?: VisitStatus;
  scheduled?: string | null;
  planned?: string | null;
  booked?: Booking | null;
  duration_days?: number | null;
  contractor?: string | null;
  assignee?: string | null;
  contact?: string | null;
  note?: string | null;
  /** Authored constraint label -> clearance date (null clears the tick). */
  cleared?: Record<string, string | null>;
}

/** Item-level, so two thumbs on two items never post each other's stale array. */
export interface TickHandoffOp { op: "tick_handoff"; slug: string; item: string }
export interface SkipHandoffOp {
  op: "skip_handoff"; slug: string; item: string; reason: string;
}
export interface SetCheckpointOp {
  op: "set_checkpoint";
  slug: string;
  checkpoint: string;
  status?: "todo" | "in_progress" | "done";
  started?: string | null;
  completed?: string | null;
}
export interface ClearHoldOp {
  op: "clear_hold"; slug: string; label: string; cleared?: string | null;
}
export interface AddHoldOp {
  op: "add_hold";
  slug: string;
  label: string;
  severity?: "blocking" | "attention";
  owner?: string | null;
  next_action?: string | null;
  follow_up?: string | null;
}
export interface AddExceptionOp {
  op: "add_exception"; slug: string; hold: string; note?: string;
}

export type VisitOp =
  | SetVisitOp | TickHandoffOp | SkipHandoffOp | SetCheckpointOp
  | ClearHoldOp | AddHoldOp | AddExceptionOp;

export interface SetInspectionOp {
  op: "set_inspection";
  id: string;
  requested?: string | null;
  scheduled?: string | null;
  inspector?: string | null;
  scope?: string[];
  checked?: string[];
  requires?: string[];
  waived?: Waiver | null;
  note?: string | null;
}

/** A result only ever ARRIVES; it never overwrites. */
export interface AddAttemptOp {
  op: "add_attempt";
  id: string;
  date: string;
  result: "pass" | "fail" | "partial";
  inspector?: string | null;
  corrections?: string[];
  approved?: string[];
  note?: string | null;
}

export interface SetInstanceOp { op: "set_instance"; id: string; scope: string[] }

export interface SetPermitOp {
  op: "set_permit";
  number?: string | null;
  issued?: string | null;
  expires?: string | null;
  code_edition?: string | null;
  nec_edition?: string | null;
  note?: string | null;
}

export interface SetExtraInspectionOp {
  op: "set_extra_inspection";
  id: string;
  label: string;
  authority: Authority;
  after?: string[];
  gates?: string[];
}

export interface RemoveExtraInspectionOp {
  op: "remove_extra_inspection";
  id: string;
}

export type InspectionOp =
  | SetInspectionOp | AddAttemptOp | SetInstanceOp | SetPermitOp
  | SetExtraInspectionOp | RemoveExtraInspectionOp;

export type SiteOp = VisitOp | InspectionOp;
