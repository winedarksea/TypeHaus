// Visibility FACETS: viewer-only splits of one trade, keyed `<trade>:<name>`.
//
// A trade is a BID (emit/trades.py); a facet is something a person wants to LOOK at
// separately inside one. Nothing below the UI knows them: the engine stamps the bare trade,
// and `tradeVisibility.ts` swaps the facet in from the layer function, member category or
// solid category already on the record. `baseTrade` maps a facet back, so a facet never
// needs a container of its own.
//
// `framing` owns both the sticks and the planes nailed to them, which is right for a bid and
// wrong for looking: the `structure`/`furring` bands are full-height prisms drawn over the
// studs they stand for, and `sheathing` is the sheet across both. All three default OFF —
// interior sandwich layers whose only view was the cutaway that wanted them gone. A furring
// STICK is not a facet (builders/wallSkin.ts puts it on bare `framing` by category).
//
// The connectors default ON: a marker is what somebody asked to see, and cast-in hardware
// splits from the rest because on site it is the concrete sub's scope.
//
// Rebar is concrete's reinforcement (decision #75). Off by default: ~1,200 bars are lazily
// fetched (`/model/rebar`) the first time the chip turns on, and they sit inside the pour.
// Its meshes carry ONLY the facet key, so dropping the `concrete` chip leaves the cage
// standing — the x-ray view.
import type { Trade } from "../state/vocabulary";

export interface FacetSpec {
  key: `${Trade}:${string}`;
  label: string;
  defaultOff: boolean;
  /** Layer functions (and the member categories that continue them) that take this facet. */
  layerFunctions?: readonly string[];
  /** Member categories that take this facet directly. */
  memberCategories?: readonly string[];
  /** Solid categories that take this facet. */
  solidCategories?: readonly string[];
}

export const FACETS = [
  { key: "framing:structure", label: "Structure band", defaultOff: true,
    layerFunctions: ["structure"] },
  { key: "framing:furring", label: "Furring band", defaultOff: true,
    layerFunctions: ["furring"] },
  { key: "framing:sheathing", label: "Sheathing", defaultOff: true,
    layerFunctions: ["sheathing"] },
  { key: "framing:connector", label: "Connectors", defaultOff: false,
    solidCategories: ["connector", "connector_hanger"] },
  { key: "framing:connector-embedded", label: "Cast-in connectors", defaultOff: false,
    solidCategories: ["connector_embedded"] },
  { key: "concrete:rebar", label: "Rebar", defaultOff: true, memberCategories: ["rebar"] },
] as const satisfies readonly FacetSpec[];

export type FacetKey = (typeof FACETS)[number]["key"];

export const FACET_KEYS: FacetKey[] = FACETS.map((facet) => facet.key);

/** The framing facets alone — kept for callers that predate the generic table. */
export const FRAMING_FACETS = FACET_KEYS.filter((key) => key.startsWith("framing:"));
export type FramingFacet = Extract<FacetKey, `framing:${string}`>;

/** The trade a facet key refines. */
export function facetTrade(key: string): Trade {
  return key.split(":", 1)[0] as Trade;
}

/** A trade's facets, in table order. */
export function facetsOf(trade: Trade): FacetKey[] {
  return FACET_KEYS.filter((key) => facetTrade(key) === trade);
}

export const FACET_LABEL: Record<FacetKey, string> = Object.fromEntries(
  FACETS.map((facet) => [facet.key, facet.label])) as Record<FacetKey, string>;

type Kind = "layerFunctions" | "memberCategories" | "solidCategories";

function index(kind: Kind): Map<string, FacetKey> {
  const out = new Map<string, FacetKey>();
  for (const facet of FACETS as readonly FacetSpec[]) {
    for (const name of facet[kind] ?? []) out.set(`${facetTrade(facet.key)}|${name}`, facet.key as FacetKey);
  }
  return out;
}

const BY_KIND: Record<Kind, Map<string, FacetKey>> = {
  layerFunctions: index("layerFunctions"),
  memberCategories: index("memberCategories"),
  solidCategories: index("solidCategories"),
};

/** Swap each bare trade in `trades` for the facet `name` takes under it, where one exists.
 *  The lookup is per trade: a `structure` layer the engine filed as concrete stays concrete. */
export function withFacets(
  trades: readonly string[], name: string, kinds: readonly Kind[],
): string[] {
  return trades.map((trade) => {
    for (const kind of kinds) {
      const facet = BY_KIND[kind].get(`${trade}|${name}`);
      if (facet) return facet;
    }
    return trade;
  });
}
