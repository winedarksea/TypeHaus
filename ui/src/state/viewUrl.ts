// Deep links: the view a person is looking at, as query params on the app's own URL, so a
// link like `/app/?preset=framer` opens 3D with only the structure showing.
//
// Query, not path: `/app/` is a static copy of ui/dist with relative assets, so a path route
// would need host rewrites. The hash keeps its one job (the surface, → route.ts). Every value
// is validated and an unknown one is dropped, so a stale link degrades to the default view.
import type { Model } from "../model/types";
import { levelsOf } from "../model/levels";
import {
  ALL_VISIBILITY_KEYS, DEFAULT_OFF_KEYS, defaultVisibleTrades, expandRolePreset, ROLE_PRESETS, TRADE_GROUPS,
  type VisibilityKey, type VisibleTrades,
} from "../model/tradeVisibility";
import type {
  DetailView, LabelMode, Lens, ThreeMode, ViewMode, Workspace,
} from "./vocabulary";

export interface ViewParams {
  viewMode?: ViewMode;
  threeMode?: ThreeMode;
  /** Exactly these keys on, everything else off. */
  visible?: VisibilityKey[];
  activeStorey?: string;
  /** Level keys hidden in 3D; checked against the model on apply. */
  hiddenLevels?: string[];
  labelMode?: LabelMode;
  activeLens?: Lens;
  activeWorkspace?: Workspace;
  detailView?: DetailView;
}

const MODES: ViewMode[] = ["2d", "split", "3d"];
const THREE: ThreeMode[] = ["nordic", "schematic"];
const LABELS: LabelMode[] = ["all", "hover", "off"];
const LENSES: Lens[] = ["none", "air", "water", "thermal", "vapor"];
const WORKSPACES: Workspace[] = ["design", "analyze", "document"];
const READERS: DetailView[] = [
  "assembly", "bom", "circuits", "lighting", "hvac", "plumbing", "data", "estimate", "documents",
];

/** The store's initial values (store.ts). A param equal to one of these is not printed. */
const DEFAULTS = {
  viewMode: "2d", threeMode: "nordic", labelMode: "hover",
  activeLens: "none", activeWorkspace: "design", detailView: "none",
} as const;

/** Every query key this module owns; anything else in the search string is left alone. */
const OWN_KEYS = [
  "preset", "mode", "three", "show", "group", "storey", "hideLevels", "labels", "lens", "ws", "reader",
];

const structure = () => expandRolePreset(ROLE_PRESETS.Structure);
// A framer looks at the sticks: the stand-in bands would seal them in a box.
const sticks = () => structure().filter((k) => !(DEFAULT_OFF_KEYS as readonly string[]).includes(k));

/** Named bundles. Explicit params override a preset's. */
export const URL_PRESETS: Record<string, () => ViewParams> = {
  framer: () => ({ viewMode: "3d", visible: sticks() }),
  architecture: () => ({ visible: expandRolePreset(ROLE_PRESETS.Architecture) }),
  structure: () => ({ visible: structure() }),
  mep: () => ({ visible: expandRolePreset(ROLE_PRESETS.MEP) }),
  site: () => ({ visible: expandRolePreset(ROLE_PRESETS.Site) }),
};

function pick<T extends string>(value: string | null, allowed: readonly T[]): T | undefined {
  return value !== null && (allowed as readonly string[]).includes(value) ? value as T : undefined;
}

const list = (value: string | null) =>
  (value ?? "").split(",").map((v) => v.trim()).filter(Boolean);

/** A group id first, else a role preset by lower-cased name (`mep`). */
function groupKeys(id: string): VisibilityKey[] {
  const group = TRADE_GROUPS.find((g) => g.id === id);
  if (group) return expandRolePreset({ groups: [group.id] });
  const role = Object.keys(ROLE_PRESETS).find((name) => name.toLowerCase() === id.toLowerCase());
  return role ? expandRolePreset(ROLE_PRESETS[role]) : [];
}

export function parseViewParams(search: string): ViewParams {
  const q = new URLSearchParams(search);
  const out: ViewParams = URL_PRESETS[q.get("preset")?.toLowerCase() ?? ""]?.() ?? {};
  const set = <K extends keyof ViewParams>(key: K, value: ViewParams[K] | undefined) => {
    if (value !== undefined) out[key] = value;
  };
  set("viewMode", pick(q.get("mode"), MODES));
  set("threeMode", pick(q.get("three"), THREE));
  set("labelMode", pick(q.get("labels"), LABELS));
  set("activeLens", pick(q.get("lens"), LENSES));
  set("activeWorkspace", pick(q.get("ws"), WORKSPACES));
  set("detailView", pick(q.get("reader"), READERS));
  set("activeStorey", q.get("storey") || undefined);
  const hidden = list(q.get("hideLevels"));
  if (hidden.length) out.hiddenLevels = hidden;
  if (q.has("show") || q.has("group")) {
    const known = new Set<string>(ALL_VISIBILITY_KEYS);
    const keys = new Set<VisibilityKey>(
      list(q.get("show")).filter((k) => known.has(k)) as VisibilityKey[]);
    for (const id of list(q.get("group"))) groupKeys(id).forEach((k) => keys.add(k));
    // A link naming nothing we know shows the default, not an empty model.
    if (keys.size) out.visible = ALL_VISIBILITY_KEYS.filter((k) => keys.has(k));
  }
  return out;
}

export interface ViewSnapshot {
  viewMode: ViewMode;
  threeMode: ThreeMode;
  visibleTrades: VisibleTrades;
  hiddenLevels: string[];
  activeStorey: string | null;
  labelMode: LabelMode;
  activeLens: Lens;
  activeWorkspace: Workspace;
  detailView: DetailView;
  model: Model | null;
}

/** What store.reload picks when nothing is chosen, so it need not be printed. */
function defaultStorey(model: Pick<Model, "storeys"> | null): string | null {
  return model?.storeys.find((s) => s.tag === "main")?.tag ?? model?.storeys[0]?.tag ?? null;
}

/** The query string (no `?`) naming `state`, defaults omitted. */
export function viewParamsFor(state: ViewSnapshot): string {
  const q = new URLSearchParams();
  const put = (key: string, value: string, fallback: string | null) => {
    if (value !== fallback) q.set(key, value);
  };
  put("mode", state.viewMode, DEFAULTS.viewMode);
  put("three", state.threeMode, DEFAULTS.threeMode);
  const base = defaultVisibleTrades();
  if (ALL_VISIBILITY_KEYS.some((k) => (state.visibleTrades[k] !== false) !== base[k])) {
    q.set("show", ALL_VISIBILITY_KEYS.filter((k) => state.visibleTrades[k] !== false).join(","));
  }
  if (state.hiddenLevels.length) q.set("hideLevels", state.hiddenLevels.join(","));
  if (state.activeStorey) put("storey", state.activeStorey, defaultStorey(state.model));
  put("labels", state.labelMode, DEFAULTS.labelMode);
  put("lens", state.activeLens, DEFAULTS.activeLens);
  put("ws", state.activeWorkspace, DEFAULTS.activeWorkspace);
  put("reader", state.detailView, DEFAULTS.detailView);
  // Commas and colons read better unescaped, and both are legal in a query.
  return q.toString().replace(/%2C/gi, ",").replace(/%3A/gi, ":");
}

/** `search` with this module's keys replaced by `params`; foreign keys survive. */
export function mergeSearch(search: string, params: string): string {
  const q = new URLSearchParams(search);
  for (const key of OWN_KEYS) q.delete(key);
  const foreign = q.toString();
  const joined = [foreign, params].filter(Boolean).join("&");
  return joined ? `?${joined}` : "";
}

interface ViewSetters {
  setActiveStorey: (tag: string | null) => void;
  setHiddenLevels: (keys: readonly string[]) => void;
  setThreeMode: (m: ThreeMode) => void;
  showOnlyTrades: (keys: readonly VisibilityKey[]) => void;
  setLabelMode: (m: LabelMode) => void;
  setActiveLens: (l: Lens) => void;
  setActiveWorkspace: (w: Workspace) => void;
  setDetailView: (v: DetailView) => void;
  openDocuments: () => void;
  setViewMode: (v: ViewMode) => void;
}

type ViewStore = {
  getState: () => ViewSnapshot & ViewSetters;
  subscribe: (listener: (state: ViewSnapshot) => void) => () => void;
};

/** Params that stand without a model. */
function applyModelFree(s: ViewSetters, p: ViewParams): void {
  if (p.threeMode) s.setThreeMode(p.threeMode);
  if (p.visible) s.showOnlyTrades(p.visible);
  if (p.labelMode) s.setLabelMode(p.labelMode);
  if (p.activeLens) s.setActiveLens(p.activeLens);
  if (p.activeWorkspace) s.setActiveWorkspace(p.activeWorkspace);
}

/** Storey and reader wait for the model: a storey is checked against it. The view mode goes
 *  last: zoomToUid forces 2D when it moves the storey. */
function applyWithModel(s: ViewSetters, model: Model, p: ViewParams): void {
  const storey = p.activeStorey;
  if (storey && (model.storeys.some((st) => st.tag === storey)
      || levelsOf(model).some((l) => l.key === storey))) {
    s.setActiveStorey(storey);
  }
  if (p.hiddenLevels) {
    const known = new Set(levelsOf(model).map((l) => l.key));
    s.setHiddenLevels(p.hiddenLevels.filter((k) => known.has(k)));
  }
  if (p.detailView === "documents") s.openDocuments();
  else if (p.detailView) s.setDetailView(p.detailView);
  if (p.viewMode) s.setViewMode(p.viewMode);
}

/**
 * Apply the URL once, then keep its search string naming the current view (replaceState, no
 * history, hash untouched), so the address bar is always a shareable link. Writing starts only
 * after the model-dependent params are applied, or the first write would erase them.
 */
export function installViewUrlSync(store: ViewStore): () => void {
  const params = parseViewParams(window.location.search);
  applyModelFree(store.getState(), params);

  let writing: (() => void) | null = null;
  const startWriting = () => {
    const write = (state: ViewSnapshot) => {
      const next = mergeSearch(window.location.search, viewParamsFor(state));
      if (next === window.location.search) return;
      window.history.replaceState(
        window.history.state, "", window.location.pathname + next + window.location.hash);
    };
    write(store.getState());
    writing = store.subscribe(write);
  };

  let waiting: (() => void) | null = null;
  const onModel = (state: ViewSnapshot) => {
    if (!state.model) return false;
    applyWithModel(store.getState(), state.model, params);
    startWriting();
    return true;
  };
  if (!onModel(store.getState())) {
    waiting = store.subscribe((state) => {
      if (!state.model) return;
      waiting?.();
      waiting = null;
      onModel(state);
    });
  }
  return () => {
    waiting?.();
    writing?.();
  };
}
