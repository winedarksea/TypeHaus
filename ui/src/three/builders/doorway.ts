/** Exact manufacturer sections supplied by the engine, swept along the doorway. */
import * as THREE from "three";
import type { Opening } from "../../model/types";
import { projectPointToScene } from "../planGeometry";


export function buildDoorway(
  opening: Opening, position: readonly number[], direction: readonly number[],
  center: Parameters<typeof projectPointToScene>[2], parent: THREE.Object3D,
  materialFor: (ref: string, materialKey: string) => THREE.Material,
) {
  const designSections = (opening.doorway?.exterior_placement?.sections ?? []).map(section => ({
    ...section, normal_m: 0, base_z_m: 0,
    specification: { product_ref: "Project sill design (schematic)", positive_normal_sign: 1,
      parts: [{ ...section }] },
  }));
  for (const component of [...(opening.doorway?.components ?? []), ...designSections]) {
    const spec = component.specification;
    for (const part of spec.parts) {
      const points = part.polygon_m.map(([x, z]) => new THREE.Vector2(x, z));
      const triangles = THREE.ShapeUtils.triangulateShape(points, []);
      const count = points.length;
      const positions: number[] = [];
      for (const along of [component.along_m - component.span_m / 2,
        component.along_m + component.span_m / 2]) {
        for (const [x, z] of part.polygon_m) {
          const normal = component.normal_m + spec.positive_normal_sign * x;
          const point = projectPointToScene([
            position[0] + direction[0] * along - direction[1] * normal,
            position[1] + direction[1] * along + direction[0] * normal,
          ], component.base_z_m + z, center);
          positions.push(point.x, point.y, point.z);
        }
      }
      const indices = triangles.flatMap(([a, b, c]) => [a, c, b, a + count, b + count, c + count]);
      for (let a = 0; a < count; a++) {
        const b = (a + 1) % count;
        indices.push(a, b, b + count, a, b + count, a + count);
      }
      // The installed normal may mirror a section; orient all faces consistently outward.
      const signedArea = points.reduce((sum, p, i) => {
        const q = points[(i + 1) % count]; return sum + p.x * q.y - q.x * p.y;
      }, 0);
      if (signedArea * spec.positive_normal_sign < 0) {
        for (let i = 0; i < indices.length; i += 3) {
          [indices[i], indices[i + 1]] = [indices[i + 1], indices[i]];
        }
      }
      const geometry = new THREE.BufferGeometry();
      geometry.setAttribute("position", new THREE.Float32BufferAttribute(positions, 3));
      geometry.setIndex(indices); geometry.computeVertexNormals();
      const mesh = new THREE.Mesh(geometry, materialFor(part.material_ref, part.material_key ?? "door_hardware"));
      mesh.userData.doorwayProduct = spec.product_ref;
      mesh.userData.doorwayPart = part.name;
      parent.add(mesh);
    }
  }
}
