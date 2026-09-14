// The gap the Connectors toggle falls through without the `scene.ts::tagNew` fix.
//
// Facets were built for layer bands and only ever derived from a layer FUNCTION. A solid has
// no layer function, and `tagNew` force-tags everything that lands in the framing container
// with the bare `framing` token — so a connector marker arrived correctly routed and was
// immediately relabelled, and the toggle silently did nothing.
//
// These are the three properties that have to hold together, and the middle one is the one
// that was broken: the marker is IN the framing container (so it needs no container of its
// own), it is TAGGED with its facet (so its own toggle reaches it), and hiding the whole
// framing trade still hides it (so a facet is a refinement, never an escape).
import * as THREE from "three";
import { describe, expect, it } from "vitest";

import {
  ALL_VISIBILITY_KEYS,
  DEFAULT_OFF_KEYS,
  baseTrade,
  primaryTrade,
  solidTrades,
  solidVisibilityKeys,
  type VisibilityKey,
  type VisibleTrades,
} from "../model/tradeVisibility";
import { applyTradeVisibility, tagTrades } from "./builders/registry";

const allVisible = (): VisibleTrades =>
  Object.fromEntries(ALL_VISIBILITY_KEYS.map((key) => [key, true])) as VisibleTrades;

/** One tagged child standing in for a built marker, routed the way `scene.ts` routes one. */
function routed(category: string) {
  const solid = { category, trades: undefined };
  const keys = solidVisibilityKeys(solid);
  const container = new THREE.Group();
  container.add(new THREE.Object3D());
  tagTrades(container, 0, keys);
  return { keys, container, child: container.children[0] };
}

describe("a derived connector marker routes to framing, tagged with its own facet", () => {
  it("lands in the framing container", () => {
    for (const category of ["connector", "connector_hanger", "connector_embedded"]) {
      expect(primaryTrade(solidTrades({ category, trades: undefined }))).toBe("framing");
    }
  });

  it("is tagged framing:connector, not the bare framing token", () => {
    expect(routed("connector").keys).toEqual(["framing:connector"]);
    expect(routed("connector_hanger").keys).toEqual(["framing:connector"]);
    expect(routed("connector_embedded").keys).toEqual(["framing:connector-embedded"]);
  });

  it("every facet still answers to the framing trade", () => {
    for (const category of ["connector", "connector_hanger", "connector_embedded"]) {
      for (const key of solidVisibilityKeys({ category, trades: undefined })) {
        expect(baseTrade(key)).toBe("framing");
      }
    }
  });

  it("hiding framing hides it; hiding framing:structure does not", () => {
    const { container, child } = routed("connector");
    const visible = allVisible();

    applyTradeVisibility(container, visible);
    expect(child.visible).toBe(true);

    applyTradeVisibility(container, { ...visible, "framing:structure": false });
    expect(child.visible).toBe(true);

    applyTradeVisibility(container, { ...visible, "framing:connector": false });
    expect(child.visible).toBe(false);
  });

  it("cast-in connectors toggle independently of the rest", () => {
    const framer = routed("connector");
    const concrete = routed("connector_embedded");
    const visible = { ...allVisible(), "framing:connector-embedded": false };

    applyTradeVisibility(framer.container, visible);
    applyTradeVisibility(concrete.container, visible);
    expect(framer.child.visible).toBe(true);
    expect(concrete.child.visible).toBe(false);
  });

  it("both connector facets start ON — they are what was asked for", () => {
    expect(DEFAULT_OFF_KEYS).not.toContain("framing:connector" as VisibilityKey);
    expect(DEFAULT_OFF_KEYS).not.toContain("framing:connector-embedded" as VisibilityKey);
  });
});
