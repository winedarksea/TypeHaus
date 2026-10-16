// Millwork: window stools, base runs and door casings (resolved geometry, drawn in their own
// material — oak boards, or a painted or stone piece's flat colour) and the stair members
// whose material declares a board recipe (oak treads and winders; a landing's plank field).
import * as THREE from "three";
import type {
  BaseRun, Countertop, DoorCasing, Member, Vec2, WindowStool,
} from "../../model/types";
import {
  authoredAppearance, materialColor, type MaterialAppearance, type ResolvedNordicPalette,
} from "../../nordic/palette";
import { composeMemberBoxMatrix, isRakedMember } from "../memberBox";
import { memberColor } from "../members";
import { createPlanPrismGeometry, projectPointToScene, type PlanCenter } from "../planGeometry";
import {
  createPlankMaterial, planLongAxis, plankStyleOrNull,
  type PlankStyle,
} from "../plankMaterial";
import { makeSurfaceMesh, standardMaterial } from "../surfaces";
import { applyPieceGrainUv, boardBoxGeometry, pieceSeed, woodMaterialsForGeometry } from "../woodPiece";
import { registerSelectable } from "./registry";

/** The board recipe a material declares (or infers), for a solid-wood piece; else null. */
export function boardStyleFor(ref: string | null | undefined,
  materials: readonly MaterialAppearance[] | undefined): PlankStyle | null {
  const appearance = authoredAppearance(ref, materials);
  return ref ? plankStyleOrNull(ref, appearance?.finish, appearance?.species) : null;
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
    applyPieceGrainUv(geometry, new THREE.Vector3(x1 - x0, 0, -(y1 - y0)),
      style, pieceSeed(stool.uid));
  }
  const material = style ? createPlankMaterial(mode, style, color, undefined,
    authoredAppearance(stool.material_ref, materials)) : standardMaterial(color, mode);
  parent.add(makeSurfaceMesh(geometry, woodMaterialsForGeometry(material, geometry)));
  registerSelectable(parent, firstChildIndex, stool.opening_uid, "opening", picks, byUid);
}

/**
 * One rectangular trim board (a base piece, a casing leg or head) as a textured box: the grain
 * runs its longest way, so a leg's grain stands up and a head's runs across.
 */
function trimBoardGeometry(outline: readonly Vec2[], z0: number, z1: number,
  center: PlanCenter, style: PlankStyle | null, seed: number): THREE.BufferGeometry | null {
  if (!style || outline.length !== 4) {
    return createPlanPrismGeometry(outline as Vec2[], z0, z1, [], center);
  }
  const origin = projectPointToScene(outline[0], z0, center);
  const along = projectPointToScene(outline[1], z0, center).sub(origin);
  const across = projectPointToScene(outline[3], z0, center).sub(origin);
  const up = new THREE.Vector3(0, z1 - z0, 0);
  let matrix = new THREE.Matrix4().makeBasis(along, up, across);
  if (matrix.determinant() < 0) matrix = new THREE.Matrix4().makeBasis(across, up, along);
  matrix.setPosition(origin.clone().addScaledVector(along, 0.5).addScaledVector(across, 0.5)
    .addScaledVector(up, 0.5));
  const axes = [new THREE.Vector3(), new THREE.Vector3(), new THREE.Vector3()];
  matrix.extractBasis(axes[0], axes[1], axes[2]);
  // A short offcut still runs along the trim, even when its height exceeds its length.
  return boardBoxGeometry(matrix, style, seed, axes[0].length() >= axes[2].length() ? 0 : 2);
}

function buildTrimPieces(parent: THREE.Group, uid: string, materialRef: string,
  pieces: readonly { outline: Vec2[]; z0_m: number; z1_m: number }[], center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  materials: readonly MaterialAppearance[] | undefined) {
  const color = materialColor(materialRef, palette, materials);
  const style = boardStyleFor(materialRef, materials);
  const material = style ? createPlankMaterial(mode, style, color, undefined, authoredAppearance(materialRef, materials)) : standardMaterial(color, mode);
  for (const [index, piece] of pieces.entries()) {
    if (piece.outline.length < 3 || piece.z1_m <= piece.z0_m) continue;
    const geometry = trimBoardGeometry(piece.outline, piece.z0_m, piece.z1_m, center, style,
      pieceSeed(`${uid}|${index}`));
    if (geometry) parent.add(makeSurfaceMesh(geometry, woodMaterialsForGeometry(material, geometry)));
  }
}

/** A derived base run: one board on the room's finish face. It selects as its room. */
export function buildBaseRun(parent: THREE.Group, run: BaseRun, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  materials: readonly MaterialAppearance[] | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  const firstChildIndex = parent.children.length;
  buildTrimPieces(parent, run.uid, run.material_ref, [run], center, mode, palette, materials);
  registerSelectable(parent, firstChildIndex, run.room_uid, "room", picks, byUid);
}

/** A door face's casing: legs and head. It selects as its door, as a stool as its window. */
export function buildDoorCasing(parent: THREE.Group, casing: DoorCasing, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  materials: readonly MaterialAppearance[] | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  const firstChildIndex = parent.children.length;
  buildTrimPieces(parent, casing.uid, casing.material_ref, casing.pieces, center, mode, palette,
    materials);
  registerSelectable(parent, firstChildIndex, casing.opening_uid, "opening", picks, byUid);
}

/**
 * A countertop slab in its own material: oak takes plank grain along the slab's long axis,
 * stone its flat colour. It selects its first host cabinet, as a stool selects its window.
 */
export function buildCountertop(parent: THREE.Group, top: Countertop, center: PlanCenter,
  mode: "nordic" | "schematic", palette: ResolvedNordicPalette,
  materials: readonly MaterialAppearance[] | undefined,
  picks: THREE.Mesh[], byUid: Map<string, THREE.Material[]>) {
  if (top.z1_m <= top.z0_m) return;
  const firstChildIndex = parent.children.length;
  const color = materialColor(top.material_ref, palette, materials);
  const style = boardStyleFor(top.material_ref, materials);
  const material = style ? createPlankMaterial(mode, style, color, undefined, authoredAppearance(top.material_ref, materials)) : standardMaterial(color, mode);
  for (const [index, part] of top.parts.entries()) {
    const geometry = createPlanPrismGeometry(part.outline, top.z0_m, top.z1_m, part.holes,
      center);
    if (!geometry) continue;
    if (style) {
      const [gx, gy] = planLongAxis(part.outline);
      applyPieceGrainUv(geometry, new THREE.Vector3(gx, 0, -gy), style,
        pieceSeed(`${top.uid}|${index}`));
    }
    parent.add(makeSurfaceMesh(geometry, woodMaterialsForGeometry(material, geometry)));
  }
  if (top.host_uid) {
    registerSelectable(parent, firstChildIndex, top.host_uid, "canvas_object", picks, byUid);
  }
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
        const grainAxis: [number, number] = m.nosing_line
          ? [m.nosing_line[1][0] - m.nosing_line[0][0], m.nosing_line[1][1] - m.nosing_line[0][1]]
          : planLongAxis(m.plan_outline);
        applyPieceGrainUv(geometry, new THREE.Vector3(grainAxis[0], 0, -grainAxis[1]), style, seed);
      }
    } else {
      geometry = boardBoxGeometry(composeMemberBoxMatrix(new THREE.Matrix4(), m, center),
        style, seed);
    }
    if (!geometry) { rest.push(m); continue; }
    const color = memberColor(m, palette, materials);
    const key = `${style.key}|${color}|${m.material}`;
    let material = cache.get(key);
    if (!material) {
      material = createPlankMaterial(mode, style, color, undefined, authoredAppearance(m.material, materials));
      cache.set(key, material);
    }
    const mesh = makeSurfaceMesh(geometry, woodMaterialsForGeometry(material, geometry));
    mesh.userData.memberKey = m.key;
    parent.add(mesh);
  }
  return rest;
}
