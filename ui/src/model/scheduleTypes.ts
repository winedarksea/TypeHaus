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
  readiness: VisitReadinessState;
  constraints: Constraint[];
  handoff: HandoffItem[];
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
  milestones: Milestone[];
  visits: Visit[];
  proposals: Record<string, ProposedVisit[]>;
  stale: string[];
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

export interface InspectionEntry {
  requested: string | null;
  scheduled: string | null;
  inspector: string | null;
  result: "pass" | "fail" | "partial" | null;
  result_date: string | null;
  reinspect: string | null;
  history: string[];
  checked: string[];
  requires: string[];
  waived: string | null;
  note: string | null;
}

export interface InspectionAuthority {
  label: string;
  phone: string | null;
  window: string | null;
  lead_days: number | null;
}

export interface Inspection {
  id: string;
  label: string;
  authority: Authority;
  sequence: number;
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
}

export interface InspectionsPayload {
  profile: string;
  checks_pending: boolean;
  authorities: Record<string, InspectionAuthority>;
  inspections: Inspection[];
}

// --- write ops ------------------------------------------------------------------------

export interface SetVisitOp {
  op: "set_visit";
  slug: string;
  status?: VisitStatus;
  scheduled?: string | null;
  assignee?: string | null;
  contact?: string | null;
  note?: string | null;
  /** Handoff item ids the owner has ticked. */
  checked?: string[];
  /** Authored constraint label -> clearance date (null clears the tick). */
  cleared?: Record<string, string | null>;
}

export interface SetInspectionOp {
  op: "set_inspection";
  id: string;
  requested?: string | null;
  scheduled?: string | null;
  inspector?: string | null;
  result?: "pass" | "fail" | "partial" | null;
  result_date?: string | null;
  reinspect?: string | null;
  checked?: string[];
  waived?: string | null;
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
  | SetInspectionOp | SetExtraInspectionOp | RemoveExtraInspectionOp;
