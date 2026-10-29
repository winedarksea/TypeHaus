// Stone / sand surfaces for the builders: footing beds, drain columns, under-slab layers.
import * as THREE from "three";
import type { PlanCenter } from "../planGeometry";
import {
  aggregateKind, applyAggregateUv, createAggregateMaterial, type AggregateKind,
} from "../aggregateMaterial";
import type { ShadingMode } from "../surfaces";

/** The stone material for a bed or column of `color`. */
export function stoneMaterial(
  mode: ShadingMode, color: THREE.ColorRepresentation, kind: AggregateKind = "stone",
): THREE.MeshStandardMaterial {
  return createAggregateMaterial(mode, color, kind);
}

/** The speckle recipe a solid takes, judged by its material ref and category alone. */
export function aggregateKindOfSolid(
  solid: { category?: string | null }, materialRef?: string | null,
): AggregateKind | null {
  return aggregateKind(materialRef, solid.category);
}

/** World UVs in the recipe's tile, so a clipped bed stays in phase with its neighbours. */
export function uvForAggregate(
  geometry: THREE.BufferGeometry, center: PlanCenter, kind: AggregateKind = "stone",
): void {
  applyAggregateUv(geometry, center, kind);
}
