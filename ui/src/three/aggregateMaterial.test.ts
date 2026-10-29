import * as THREE from "three";
import {
  aggregateKind, buildAggregateTexture, createAggregateMaterial, isAggregate, isSand,
} from "./aggregateMaterial";
import { createSolidMaterial } from "./solidMaterials";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runAggregateMaterialTests() {
  assert(isAggregate("capillary-break-stone") && isAggregate("footing-crushed-stone")
    && isAggregate("mndot-class-5-base") && isAggregate(null, "drain_column")
    && !isAggregate("concrete-4000") && !isAggregate(null, "slab") && !isAggregate("usga-choker-sand"),
    "Stone aggregate is the named refs and the drain column, not sand or concrete");
  assert(isSand("usga-choker-sand") && isSand("rootzone-sand") && !isSand("capillary-break-stone"),
    "Sand is usga-* and the rootzone mix");
  assert(aggregateKind("usga-choker-sand") === "sand" && aggregateKind(null, "drain_column") === "stone"
    && aggregateKind("eps-foam") === null, "Each ref takes its own recipe, or none");

  assert(buildAggregateTexture("stone") === null, "No 2D canvas: no texture, and no throw");
  const flat = createAggregateMaterial("nordic", "#8f8d88");
  assert(!flat.map && flat.color.getHexString() === "8f8d88" && flat.roughness === 1,
    "Without a canvas the stone is a flat fill in its own colour");
  assert(createAggregateMaterial("schematic", "#8f8d88").flatShading, "Schematic stays flat-shaded");

  const backfill = createSolidMaterial({ category: "backfill_cap", assembly: null, material: null },
    undefined, "nordic", RESOLVED_NORDIC_PALETTE.light) as THREE.MeshStandardMaterial;
  assert(backfill.polygonOffset && backfill.polygonOffsetFactor > 0 && backfill.polygonOffsetUnits > 0,
    "Backfill is pushed behind the coplanar site sheet");
}
