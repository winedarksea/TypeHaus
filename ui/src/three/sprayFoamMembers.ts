import * as THREE from "three";
import type { Member } from "../model/types";
import { authoredAppearance, materialColor, type MaterialAppearance, type ResolvedNordicPalette } from "../nordic/palette";
import { createPlanPrismGeometry, type PlanCenter } from "./planGeometry";
import { composeMemberBoxMatrix, UNIT_BOX, elevationProfileVertices, pushBoxIndices, pushSweepIndices, rakedBoxVertices, sectionRingVertices, seatedProfileVertices } from "./memberBox";
import { memberUidsFor, tagMergedMemberIdentity } from "./memberPicking";
import { createSurfaceMeshGeometry } from "./surfaceMesh";
import { applySprayFoamUv, createSprayFoamMaterial, isSprayFoamFinish } from "./sprayFoamMaterial";
import { makeSurfaceMesh, type ShadingMode } from "./surfaces";

/** Keep the closure batch and picking identities while giving foam crisp, world-scaled faces. */
export function buildSprayFoamMembers(
  group: THREE.Group, members: Member[], center: PlanCenter, mode: ShadingMode,
  palette: ResolvedNordicPalette, ownerUid: string, materials?: readonly MaterialAppearance[],
): Member[] {
  const remaining: Member[] = [], drawn: Member[] = [];
  const positions: number[] = [], colors: number[] = [], triangleStarts = [0];
  for (const member of members) {
    if (!isSprayFoamFinish(authoredAppearance(member.material, materials)?.finish)) {
      remaining.push(member);
      continue;
    }
    let geometry = member.surface_mesh ? createSurfaceMeshGeometry(member.surface_mesh, center)
      : member.plan_outline?.length ? createPlanPrismGeometry(member.plan_outline, member.z0_m, member.z1_m, [], center)
      : null;
    if (!geometry) {
      const profile = elevationProfileVertices(member, center)
        ?? seatedProfileVertices(member, center) ?? sectionRingVertices(member, center);
      const vertices = profile ?? rakedBoxVertices(member, center);
      if (!vertices) {
        geometry = UNIT_BOX.clone().applyMatrix4(composeMemberBoxMatrix(new THREE.Matrix4(), member, center));
      } else {
        const indices: number[] = [];
        if (profile) pushSweepIndices(indices, 0, vertices.length / 2, vertices);
        else pushBoxIndices(indices, 0);
        geometry = new THREE.BufferGeometry();
        geometry.setAttribute("position", new THREE.Float32BufferAttribute(vertices.flat(), 3));
        geometry.setIndex(indices);
      }
    }
    if (geometry.index) {
      const indexed = geometry;
      geometry = indexed.toNonIndexed();
      indexed.dispose();
    }
    const position = geometry.getAttribute("position");
    const color = new THREE.Color(materialColor(member.material!, palette, materials));
    for (let i = 0; i < position.count; i++) {
      positions.push(position.getX(i), position.getY(i), position.getZ(i));
      colors.push(color.r, color.g, color.b);
    }
    triangleStarts.push(triangleStarts[triangleStarts.length - 1] + position.count / 3);
    drawn.push(member);
    geometry.dispose();
  }
  if (drawn.length) {
    const geometry = new THREE.BufferGeometry();
    geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
    geometry.setAttribute("color", new THREE.Float32BufferAttribute(colors, 3));
    geometry.computeVertexNormals();
    applySprayFoamUv(geometry, center);
    const material = createSprayFoamMaterial(mode, 0xffffff);
    material.vertexColors = true;
    const mesh = makeSurfaceMesh(geometry, material);
    tagMergedMemberIdentity(mesh, memberUidsFor(ownerUid, drawn), triangleStarts);
    group.add(mesh);
  }
  return remaining;
}
