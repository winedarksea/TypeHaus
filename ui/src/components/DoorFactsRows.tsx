// What a door is bought as and how it hangs (→ server/model_json_catalog._door_facts): core,
// function, leaf, bottom, closer, and the pocket kit or bypass set. Bare `.kv` siblings, like
// ProductRows, so they land in the opening's open block.
import { Fragment } from "react";
import { productFor } from "../model/products";
import type { Catalog, DoorSizing, DoorTypeSpec } from "../model/types";

const M_PER_IN = 0.0254;

/** Inches to the nearest 1/16" ("1 3/8\""). */
export function formatInches(meters: number): string {
  const sixteenths = Math.round((meters / M_PER_IN) * 16);
  const whole = Math.floor(sixteenths / 16);
  let num = sixteenths % 16;
  let den = 16;
  while (num > 0 && num % 2 === 0) { num /= 2; den /= 2; }
  const frac = num ? `${num}/${den}` : "";
  return `${whole && frac ? `${whole} ${frac}` : whole ? whole : frac || 0}"`;
}

/** The bottom row: a sealed bottom, else the hung undercut (a relief door's is 3/4"). */
export function doorBottom(type: DoorTypeSpec): string | null {
  if (type.bottom_seal) return "Sealed — sweep/automatic bottom";
  if (type.bypass_door) return `${formatInches(type.bypass_door.floor_clearance_m)} over the floor`;
  if (type.undercut_m == null) return null;
  const relief = type.undercut_m >= 0.75 * M_PER_IN - 1e-6;
  return `${formatInches(type.undercut_m)} undercut${relief ? " (relief)" : ""}`;
}

export function DoorFactsRows({ type, sizing, catalog }: {
  type: DoorTypeSpec | undefined; sizing?: DoorSizing | null; catalog?: Catalog;
}) {
  if (!type) return null;
  const bottom = doorBottom(type);
  const kit = sizing?.pocket_kit;
  const bypass = type.bypass_door;
  const set = bypass ? productFor(catalog, bypass.product_ref) : null;
  return <Fragment>
    {type.core && <><span className="k">Core</span><span>{type.core}</span></>}
    {type.function && <><span className="k">Function</span>
      <span>{type.function.replace(/_/g, " ")}</span></>}
    {type.leaf_thickness_m != null && <><span className="k">Leaf thickness</span>
      <span>{formatInches(type.leaf_thickness_m)}</span></>}
    {bottom && <><span className="k">Bottom</span><span>{bottom}</span></>}
    {type.self_closing && <><span className="k">Self-closing</span><span>yes</span></>}
    {kit && <><span className="k">Pocket frame kit</span>
      <span>{kit[0]} {kit[1]} <span className="prov">{kit[2]}</span></span></>}
    {bypass && <><span className="k">Bypass hardware</span>
      <span>{set ? `${set.brand} ${set.model}` : "bypass set"}, {formatInches(bypass.overlap_m)}
        {" "}overlap</span></>}
  </Fragment>;
}
