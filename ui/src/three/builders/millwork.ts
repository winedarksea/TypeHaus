// Solid-wood millwork: window stools (resolved geometry, drawn as their oak) and the stair
// members whose material declares a board recipe (oak treads, winders, landings).
import * as THREE from "three";
import type { Member, WindowStool } from "../../model/types";
import {
  authoredAppearance, materialColor, type MaterialAppearance, type ResolvedNordicPalette,
} from "../../nordic/palette";
import { composeMemberBoxMatrix, isRakedMember } from "../memberBox";
import { memberColor } from "../members";
import { createPlanPrismGeometry, type PlanCenter } from "../planGeometry";
import {
  applyPlankPlaneUv, createPlankMaterial, planLongAxis, plankStyleOrNull, plankTileSizeM,
  type PlankStyle,
} from "../plankMaterial";
import { makeSurfaceMesh, standardMaterial } from "../surfaces";
import { boardBoxGeometry, pieceSeed, seatPieceUv } from "../woodPiece";
import { registerSelectable } from "./registry";

/** The board recipe a material declares (or infers), for a solid-wood piece; else null. */
export function boardStyleFor(ref: string | null | undefined,
  materials: readonly MaterialAppearance[] | undefined): PlankStyle | null {
  return ref ? plankStyleOrNull(ref, authoredAppearance(ref, materials)?.finish) : null;
}

export function buildWindowStool(parent: THREE.Group, stool: WindowStool, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  materials: readonly MaterialAppearance[] | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  if (stool.outline.length < 3 || stool.z1_m <= stool.z0_m) return;
  const geometry = createPlanPrismGeometry(stool.outline, stool.z0_m, stool.z1_m, [], center);
  if (!geometry) return;
  const firstChildIndex = parent.children.length;
  const color = materialColor(stool.material_ref, palette, materials);
  const style = boardStyleFor(stool.material_ref, materials);
  if (style) {
    // The front edge (outline[0] → outline[1]) runs along the wall: that is the grain.
    const [[x0, y0], [x1, y1]] = stool.outline;
    applyPlankPlaneUv(geometry, center, [x1 - x0, y1 - y0], plankTileSizeM(style));
    seatPieceUv(geometry, style, pieceSeed(stool.uid));
  }
  parent.add(makeSurfaceMesh(geometry, style
    ? createPlankMaterial(mode, style, color) : standardMaterial(color, mode)));
  registerSelectable(parent, firstChildIndex, stool.opening_uid, "opening", picks, byUid);
}

/**
 * Draw the members whose material is a solid board (a stair's oak treads) one textured mesh
 * each, and return the rest for the ordinary member buckets — an instanced box has no UVs.
 */
export function buildBoardMembers(parent: THREE.Group, members: readonly Member[],
  center: PlanCenter, mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  materials: readonly MaterialAppearance[] | undefined, ownerUid: string): Member[] {
  const rest: Member[] = [];
  const cache = new Map<string, THREE.Material>();
  for (const m of members) {
    const style = isRakedMember(m) ? null : boardStyleFor(m.material, materials);
    if (!style) { rest.push(m); continue; }
    const seed = pieceSeed(`${ownerUid}|${m.key}`);
    let geometry: THREE.BufferGeometry | null;
    if (m.plan_outline && m.plan_outline.length >= 3) {
      geometry = createPlanPrismGeometry(m.plan_outline, m.z0_m, m.z1_m, [], center);
      if (geometry) {
        applyPlankPlaneUv(geometry, center, planLongAxis(m.plan_outline), plankTileSizeM(style));
        seatPieceUv(geometry, style, seed);
      }
    } else {
      geometry = boardBoxGeometry(composeMemberBoxMatrix(new THREE.Matrix4(), m, center),
        style, seed);
    }
    if (!geometry) { rest.push(m); continue; }
    const color = memberColor(m, palette, materials);
    const key = `${style.key}|${color}`;
    let material = cache.get(key);
    if (!material) {
      material = createPlankMaterial(mode, style, color);
      cache.set(key, material);
    }
    const mesh = makeSurfaceMesh(geometry, material);
    mesh.userData.memberKey = m.key;
    parent.add(mesh);
  }
  return rest;
}
