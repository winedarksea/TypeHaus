// The site surface's slice: the two payloads, the two writers, and the cache that keeps
// the board readable when the server is not there.
//
// Deliberately NOT part of the design surface's state. `surface` is a top-level switch in
// App.tsx — the design workbench OR the site pages, never both — so a phone on a job site
// mounts no canvas, no WebGL and no three.js chunk. The two are one app because they share
// the model and the click-to-locate path, not because they share a screen.
//
// Writes are optimistic with revert, the same shape BomView's paid checkbox uses: a tick on
// a checklist has to land under a thumb immediately, and a failed write has to put the tick
// back rather than leave the owner believing they recorded something.

import type { StateCreator } from "zustand";
import type {
  Inspection,
  InspectionOp,
  InspectionsPayload,
  SchedulePayload,
  SetVisitOp,
  Visit,
} from "../model/scheduleTypes";

export type Surface = "design" | "site";
export type SitePage = "board" | "inspections";

const CACHE_KEY = "typehaus.site-cache";

interface SiteCache {
  schedule: SchedulePayload | null;
  inspections: InspectionsPayload | null;
}

export interface SiteSlice {
  surface: Surface;
  sitePage: SitePage;
  schedule: SchedulePayload | null;
  inspections: InspectionsPayload | null;
  siteLoading: boolean;
  /** Set when the payloads on screen came from the cache, not from the engine. */
  siteStale: boolean;
  siteError: string | null;

  setSurface: (surface: Surface) => void;
  setSitePage: (page: SitePage) => void;
  loadSite: () => Promise<void>;
  setVisit: (op: Omit<SetVisitOp, "op">) => Promise<boolean>;
  setInspection: (op: Omit<Extract<InspectionOp, { op: "set_inspection" }>, "op">)
    => Promise<boolean>;
  /** Tick or untick one handoff item on a visit. */
  tickItem: (slug: string, itemId: string, next: boolean) => Promise<boolean>;
  /** Tick or untick one on-site document on an inspection. */
  tickOnSite: (id: string, label: string, next: boolean) => Promise<boolean>;
  /** Clear (or un-clear) one authored constraint on a visit. */
  clearConstraint: (slug: string, label: string, date: string | null) => Promise<boolean>;
}

function readCache(): SiteCache {
  try {
    const raw = localStorage.getItem(CACHE_KEY);
    if (!raw) return { schedule: null, inspections: null };
    return JSON.parse(raw) as SiteCache;
  } catch {
    // A private window, cleared site data, or a browser refusing storage. The board still
    // works; it just starts empty.
    return { schedule: null, inspections: null };
  }
}

function writeCache(cache: SiteCache): void {
  try {
    localStorage.setItem(CACHE_KEY, JSON.stringify(cache));
  } catch {
    /* storage full or blocked — the cache is a convenience, never a requirement */
  }
}

/** The visit as it would look after `op` lands. Used for the optimistic paint. */
export function applyVisitLocally(payload: SchedulePayload, op: Omit<SetVisitOp, "op">)
: SchedulePayload {
  return {
    ...payload,
    visits: payload.visits.map((visit): Visit => {
      if (visit.slug !== op.slug) return visit;
      const next: Visit = { ...visit };
      if (op.status !== undefined) next.status = op.status;
      if (op.scheduled !== undefined) next.scheduled = op.scheduled;
      if (op.assignee !== undefined) next.assignee = op.assignee;
      if (op.contact !== undefined) next.contact = op.contact;
      if (op.note !== undefined) next.note = op.note;
      if (op.checked !== undefined) {
        next.checked = op.checked;
        next.handoff = visit.handoff.map((item) => ({
          ...item, checked: op.checked!.includes(item.id),
        }));
      }
      if (op.cleared !== undefined) {
        next.constraints = visit.constraints.map((constraint) =>
          constraint.kind === "authored" && op.cleared![constraint.label] !== undefined
            ? { ...constraint, cleared: op.cleared![constraint.label] }
            : constraint);
      }
      return next;
    }),
  };
}

export function applyInspectionLocally(
  payload: InspectionsPayload,
  op: Omit<Extract<InspectionOp, { op: "set_inspection" }>, "op">,
): InspectionsPayload {
  return {
    ...payload,
    inspections: payload.inspections.map((record): Inspection => {
      if (record.id !== op.id) return record;
      const next: Inspection = { ...record };
      if (op.checked !== undefined) {
        next.on_site = record.on_site.map((item) => ({
          ...item, checked: op.checked!.includes(item.label),
        }));
      }
      // The optimistic state, not the derived one: the engine owns the ladder
      // (requested -> scheduled -> passed) and re-derives it on the response. Guessing more
      // than the obvious here is how an optimistic UI starts disagreeing with its server.
      if (op.result === "pass") next.state = "passed";
      else if (op.result === "fail" || op.result === "partial") next.state = "failed";
      else if (op.scheduled) next.state = "scheduled";
      else if (op.requested) next.state = "requested";
      return next;
    }),
  };
}

export const createSiteSlice: StateCreator<
  SiteSlice & { client: { getSchedule: () => Promise<SchedulePayload>;
                          getInspections: () => Promise<InspectionsPayload>;
                          patchVisits: (ops: SetVisitOp[]) => Promise<SchedulePayload>;
                          patchInspections: (ops: InspectionOp[])
                            => Promise<InspectionsPayload> } },
  [], [], SiteSlice
> = (set, get) => {
  const cached = readCache();
  return {
    surface: "design",
    sitePage: "board",
    schedule: cached.schedule,
    inspections: cached.inspections,
    siteLoading: false,
    siteStale: cached.schedule !== null || cached.inspections !== null,
    siteError: null,

    setSurface: (surface) => {
      set({ surface });
      if (surface === "site") void get().loadSite();
    },
    setSitePage: (sitePage) => set({ sitePage }),

    loadSite: async () => {
      set({ siteLoading: true, siteError: null });
      try {
        // Both at once: the board links to inspections and the inspections page names
        // visits, so one arriving without the other renders half a screen of dashes.
        const [schedule, inspections] = await Promise.all([
          get().client.getSchedule(),
          get().client.getInspections(),
        ]);
        set({ schedule, inspections, siteLoading: false, siteStale: false });
        writeCache({ schedule, inspections });
      } catch (cause) {
        // The last good payload stays on screen with the stale flag raised. A board that
        // blanked itself when the laptop went to sleep would be useless in a basement.
        set({
          siteLoading: false,
          siteStale: get().schedule !== null || get().inspections !== null,
          siteError: cause instanceof Error ? cause.message : String(cause),
        });
      }
    },

    setVisit: async (op) => {
      const before = get().schedule;
      if (before) set({ schedule: applyVisitLocally(before, op) });
      try {
        const schedule = await get().client.patchVisits([{ op: "set_visit", ...op }]);
        set({ schedule, siteStale: false, siteError: null });
        writeCache({ schedule, inspections: get().inspections });
        return true;
      } catch (cause) {
        set({ schedule: before, siteError: cause instanceof Error ? cause.message : String(cause) });
        return false;
      }
    },

    setInspection: async (op) => {
      const before = get().inspections;
      if (before) set({ inspections: applyInspectionLocally(before, op) });
      try {
        const inspections = await get().client
          .patchInspections([{ op: "set_inspection", ...op }]);
        set({ inspections, siteStale: false, siteError: null });
        writeCache({ schedule: get().schedule, inspections });
        // A passed inspection un-blocks visits, so the board is stale the moment this lands.
        const schedule = await get().client.getSchedule().catch(() => null);
        if (schedule) set({ schedule });
        return true;
      } catch (cause) {
        set({ inspections: before, siteError: cause instanceof Error ? cause.message : String(cause) });
        return false;
      }
    },

    tickItem: (slug, itemId, next) => {
      const visit = get().schedule?.visits.find((v) => v.slug === slug);
      if (!visit) return Promise.resolve(false);
      const checked = next
        ? Array.from(new Set([...visit.checked, itemId]))
        : visit.checked.filter((id) => id !== itemId);
      return get().setVisit({ slug, checked });
    },

    tickOnSite: (id, label, next) => {
      const record = get().inspections?.inspections.find((r) => r.id === id);
      if (!record) return Promise.resolve(false);
      const current = record.on_site.filter((item) => item.checked).map((item) => item.label);
      const checked = next
        ? Array.from(new Set([...current, label]))
        : current.filter((one) => one !== label);
      return get().setInspection({ id, checked });
    },

    clearConstraint: (slug, label, date) =>
      get().setVisit({ slug, cleared: { [label]: date } }),
  };
};
