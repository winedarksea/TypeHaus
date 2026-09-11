// The site surface's slice: the two payloads, the writers, and the cache that keeps the
// board readable when the server is not there.
//
// Deliberately NOT part of the design surface's state. `surface` is a top-level switch in
// App.tsx — the design workbench OR the site pages, never both — so a phone on a job site
// mounts no canvas, no WebGL and no three.js chunk. The two are one app because they share
// the model and the click-to-locate path, not because they share a screen.
//
// Three rules this slice exists to hold.
//
// **Writes are item-level and queued one at a time.** Posting the whole `checked` array
// from possibly stale client state is how two thumbs on two checklist items delete each
// other's tick; `tick_handoff` names one item. The queue is a promise chain rather than
// parallel fetches so the engine's `if_revision` check sees one writer.
//
// **An offline board takes no writes at all.** A tick recorded against a cached payload
// lands nowhere, and an optimistic paint would tell the owner they had recorded something.
// `writable` is false while the payloads came from the cache, and every control reads it.
//
// **A failed save stays visible until it is dismissed.** The optimistic paint reverts, the
// error does not.

import type { StateCreator } from "zustand";
import type {
  AddAttemptOp,
  Inspection,
  InspectionOp,
  InspectionsPayload,
  SchedulePayload,
  SetInspectionOp,
  SetVisitOp,
  Visit,
  VisitOp,
} from "../model/scheduleTypes";

export type Surface = "design" | "site";
export type SitePage = "board" | "inspections";

const CACHE_PREFIX = "typehaus.site-cache";

interface SiteCache {
  schedule: SchedulePayload | null;
  inspections: InspectionsPayload | null;
  /** When this device last heard from the engine. Shown beside the stale banner. */
  at: number;
}

/**
 * The cache key is the house plus the server origin.
 *
 * Two engines on one laptop — `haus serve houses/catlin` and `haus serve houses/starter`,
 * or the same house on two ports — wrote over each other's board under one key, and the
 * failure looked exactly like an engine bug: the wrong house's visits under the right
 * house's title.
 */
export function cacheKey(house: string, origin: string): string {
  return `${CACHE_PREFIX}:${origin}:${house}`;
}

function readCache(key: string): SiteCache {
  try {
    const raw = localStorage.getItem(key);
    if (!raw) return { schedule: null, inspections: null, at: 0 };
    return JSON.parse(raw) as SiteCache;
  } catch {
    // A private window, cleared site data, or a browser refusing storage. The board still
    // works; it just starts empty.
    return { schedule: null, inspections: null, at: 0 };
  }
}

function writeCache(key: string, cache: SiteCache): void {
  try {
    localStorage.setItem(key, JSON.stringify(cache));
  } catch {
    /* storage full or blocked — the cache is a convenience, never a requirement */
  }
}

export interface SiteSlice {
  surface: Surface;
  sitePage: SitePage;
  schedule: SchedulePayload | null;
  inspections: InspectionsPayload | null;
  siteLoading: boolean;
  /** Set when the payloads on screen came from the cache, not from the engine. */
  siteStale: boolean;
  /** Epoch ms of the cached payloads, so the banner can say how old they are. */
  siteCachedAt: number;
  siteError: string | null;
  /** False while the board is an offline snapshot: every write control is disabled. */
  writable: boolean;

  setSurface: (surface: Surface) => void;
  setSitePage: (page: SitePage) => void;
  loadSite: () => Promise<void>;
  dismissSiteError: () => void;

  /** One visit op, folded through the engine's single write path. */
  sendVisitOp: (op: VisitOp) => Promise<boolean>;
  sendInspectionOp: (op: InspectionOp) => Promise<boolean>;

  setVisit: (op: Omit<SetVisitOp, "op">) => Promise<boolean>;
  setInspection: (op: Omit<SetInspectionOp, "op">) => Promise<boolean>;
  addAttempt: (op: Omit<AddAttemptOp, "op">) => Promise<boolean>;
  /** Tick or untick one handoff item on a visit — by item, never by array. */
  tickItem: (slug: string, itemId: string, next: boolean) => Promise<boolean>;
  skipItem: (slug: string, itemId: string, reason: string) => Promise<boolean>;
  setCheckpoint: (slug: string, checkpoint: string,
                  status: "todo" | "in_progress" | "done") => Promise<boolean>;
  /** Tick or untick one on-site document on an inspection. */
  tickOnSite: (id: string, label: string, next: boolean) => Promise<boolean>;
  /** Clear (or un-clear) one authored hold on a visit. */
  clearConstraint: (slug: string, label: string, date: string | null) => Promise<boolean>;
  addException: (slug: string, hold: string, note: string) => Promise<boolean>;
}

/** The visit as it would look after `op` lands. Used for the optimistic paint. */
export function applyVisitLocally(payload: SchedulePayload, op: VisitOp): SchedulePayload {
  return {
    ...payload,
    visits: payload.visits.map((visit): Visit => {
      if (visit.slug !== op.slug) return visit;
      const next: Visit = { ...visit };
      if (op.op === "set_visit") {
        if (op.status !== undefined) next.status = op.status;
        if (op.scheduled !== undefined) next.scheduled = op.scheduled;
        if (op.planned !== undefined) next.planned = op.planned;
        if (op.booked !== undefined) next.booked = op.booked;
        if (op.duration_days !== undefined) next.duration_days = op.duration_days;
        if (op.contractor !== undefined) next.contractor = op.contractor;
        if (op.assignee !== undefined) next.assignee = op.assignee;
        if (op.contact !== undefined) next.contact = op.contact;
        if (op.note !== undefined) next.note = op.note;
        if (op.cleared !== undefined) {
          next.constraints = visit.constraints.map((constraint) =>
            constraint.kind === "authored" && op.cleared![constraint.label] !== undefined
              ? { ...constraint, cleared: op.cleared![constraint.label] }
              : constraint);
        }
      } else if (op.op === "tick_handoff") {
        next.checked = Array.from(new Set([...visit.checked, op.item]));
        next.skipped = visit.skipped.filter((item) => item.id !== op.item);
        next.handoff = visit.handoff.map((item) =>
          item.id === op.item ? { ...item, checked: true } : item);
      } else if (op.op === "skip_handoff") {
        next.checked = visit.checked.filter((id) => id !== op.item);
        next.skipped = [...visit.skipped.filter((x) => x.id !== op.item),
                        { id: op.item, reason: op.reason }];
        next.handoff = visit.handoff.map((item) =>
          item.id === op.item ? { ...item, checked: false } : item);
      } else if (op.op === "set_checkpoint") {
        next.checkpoints = visit.checkpoints.map((point) =>
          point.id === op.checkpoint
            ? { ...point, status: op.status ?? point.status }
            : point);
      } else if (op.op === "clear_hold") {
        next.constraints = visit.constraints.map((constraint) =>
          constraint.label === op.label
            ? { ...constraint, cleared: op.cleared ?? new Date().toISOString() }
            : constraint);
      } else if (op.op === "add_exception") {
        next.exceptions = [...visit.exceptions,
                           { at: new Date().toISOString(), hold: op.hold,
                             note: op.note ?? "" }];
      }
      return next;
    }),
  };
}

export function applyInspectionLocally(payload: InspectionsPayload, op: InspectionOp)
: InspectionsPayload {
  if (op.op !== "set_inspection" && op.op !== "add_attempt") return payload;
  return {
    ...payload,
    inspections: payload.inspections.map((record): Inspection => {
      if (record.id !== op.id) return record;
      const next: Inspection = { ...record };
      if (op.op === "set_inspection") {
        if (op.checked !== undefined) {
          next.on_site = record.on_site.map((item) => ({
            ...item, checked: op.checked!.includes(item.label),
          }));
        }
        // The optimistic state, not the derived one: the engine owns the ladder
        // (requested -> scheduled -> passed) and re-derives it on the response. Guessing
        // more than the obvious here is how an optimistic UI starts disagreeing with its
        // server.
        if (op.scheduled) next.state = "scheduled";
        else if (op.requested) next.state = "requested";
      } else {
        // An attempt is APPENDED. The failure this replaces was a single result slot that
        // the second call overwrote, losing the corrections the reinspection answers.
        next.attempts = [...record.attempts, {
          date: op.date, result: op.result, inspector: op.inspector ?? null,
          corrections: op.corrections ?? [], approved: op.approved ?? [],
          note: op.note ?? null,
        }];
        next.state = op.result === "pass" ? "passed" : "failed";
        if (op.result === "partial") next.approved = [...record.approved, ...(op.approved ?? [])];
        if (op.result === "pass") next.approved = ["*"];
      }
      return next;
    }),
  };
}

interface SiteClient {
  getSchedule: () => Promise<SchedulePayload>;
  getInspections: () => Promise<InspectionsPayload>;
  patchVisits: (ops: VisitOp[], ifRevision?: string) => Promise<SchedulePayload>;
  patchInspections: (ops: InspectionOp[], ifRevision?: string)
    => Promise<InspectionsPayload>;
}

export const createSiteSlice: StateCreator<
  SiteSlice & { client: SiteClient; house?: string }, [], [], SiteSlice
> = (set, get) => {
  const origin = typeof location === "undefined" ? "local" : location.origin;
  const key = cacheKey("house", origin);
  const cached = readCache(key);
  // One promise chain, so two thumbs on two controls do not race the engine's revision
  // check. Failures are swallowed here and reported by the caller that queued the write.
  let queue: Promise<unknown> = Promise.resolve();

  function enqueue<T>(work: () => Promise<T>): Promise<T> {
    const next = queue.then(work, work);
    queue = next.catch(() => undefined);
    return next;
  }

  function fail(cause: unknown): false {
    set({ siteError: cause instanceof Error ? cause.message : String(cause) });
    return false;
  }

  return {
    surface: "design",
    sitePage: "board",
    schedule: cached.schedule,
    inspections: cached.inspections,
    siteLoading: false,
    siteStale: cached.schedule !== null || cached.inspections !== null,
    siteCachedAt: cached.at,
    siteError: null,
    writable: false,

    setSurface: (surface) => {
      set({ surface });
      if (surface === "site") void get().loadSite();
    },
    setSitePage: (sitePage) => set({ sitePage }),
    dismissSiteError: () => set({ siteError: null }),

    loadSite: async () => {
      set({ siteLoading: true });
      try {
        // Both at once: the board links to inspections and the inspections page names
        // visits, so one arriving without the other renders half a screen of dashes.
        const [schedule, inspections] = await Promise.all([
          get().client.getSchedule(),
          get().client.getInspections(),
        ]);
        const at = Date.now();
        set({ schedule, inspections, siteLoading: false, siteStale: false,
              siteCachedAt: at, writable: true, siteError: null });
        writeCache(key, { schedule, inspections, at });
      } catch (cause) {
        // The last good payload stays on screen with the stale flag raised, and the board
        // goes read-only. A board that blanked itself when the laptop went to sleep would
        // be useless in a basement; one that took ticks it could not send would be worse.
        set({
          siteLoading: false,
          siteStale: get().schedule !== null || get().inspections !== null,
          writable: false,
          siteError: cause instanceof Error ? cause.message : String(cause),
        });
      }
    },

    sendVisitOp: (op) => enqueue(async () => {
      if (!get().writable) return fail(new Error(
        "This board is an offline snapshot — reconnect before recording anything."));
      const before = get().schedule;
      if (before) set({ schedule: applyVisitLocally(before, op) });
      try {
        const schedule = await get().client
          .patchVisits([op], before?.revision ?? undefined);
        set({ schedule, siteStale: false, siteError: null, siteCachedAt: Date.now() });
        writeCache(key, { schedule, inspections: get().inspections, at: Date.now() });
        return true;
      } catch (cause) {
        set({ schedule: before });
        return fail(cause);
      }
    }),

    sendInspectionOp: (op) => enqueue(async () => {
      if (!get().writable) return fail(new Error(
        "This board is an offline snapshot — reconnect before recording anything."));
      const before = get().inspections;
      if (before) set({ inspections: applyInspectionLocally(before, op) });
      try {
        const inspections = await get().client
          .patchInspections([op], before?.revision ?? undefined);
        set({ inspections, siteStale: false, siteError: null });
        writeCache(key, { schedule: get().schedule, inspections, at: Date.now() });
        // A passed inspection un-blocks visits, so the board is stale the moment this lands.
        const schedule = await get().client.getSchedule().catch(() => null);
        if (schedule) set({ schedule });
        return true;
      } catch (cause) {
        set({ inspections: before });
        return fail(cause);
      }
    }),

    setVisit: (op) => get().sendVisitOp({ op: "set_visit", ...op }),
    setInspection: (op) => get().sendInspectionOp({ op: "set_inspection", ...op }),
    addAttempt: (op) => get().sendInspectionOp({ op: "add_attempt", ...op }),

    // Unticking records a SKIP with a reason rather than silently deleting the evidence
    // that somebody walked the item. That is the whole difference between a checklist and
    // an audit trail, and it is why the vocabulary has no "untick".
    tickItem: (slug, itemId, next) => next
      ? get().sendVisitOp({ op: "tick_handoff", slug, item: itemId })
      : get().skipItem(slug, itemId, "unticked on the walk"),

    skipItem: (slug, itemId, reason) =>
      get().sendVisitOp({ op: "skip_handoff", slug, item: itemId, reason }),

    setCheckpoint: (slug, checkpoint, status) =>
      get().sendVisitOp({ op: "set_checkpoint", slug, checkpoint, status }),

    tickOnSite: (id, label, next) => {
      const record = get().inspections?.inspections.find((r) => r.id === id);
      if (!record) return Promise.resolve(false);
      const current = record.on_site.filter((item) => item.checked).map((item) => item.label);
      const checked = next
        ? Array.from(new Set([...current, label]))
        : current.filter((one) => one !== label);
      return get().setInspection({ id, checked });
    },

    clearConstraint: (slug, label, date) => date === null
      ? get().setVisit({ slug, cleared: { [label]: null } })
      : get().sendVisitOp({ op: "clear_hold", slug, label, cleared: date }),

    addException: (slug, hold, note) =>
      get().sendVisitOp({ op: "add_exception", slug, hold, note }),
  };
};
