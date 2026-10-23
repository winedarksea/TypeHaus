import * as THREE from "three";
import type { Opening } from "../../model/types";
import fixtures from "./doorwayFixtures.json";
import { buildDoorway } from "./doorway";

export function runDoorwayTests() {
  for (const fixture of fixtures) {
    const [[x0, y0], [x1, y1]] = fixture.wall.axis;
    const length = Math.hypot(x1 - x0, y1 - y0);
    const direction = [(x1 - x0) / length, (y1 - y0) / length];
    const opening = fixture.opening as unknown as Opening;
    const position = [x0 + direction[0] * opening.center_along_m,
      y0 + direction[1] * opening.center_along_m];
    const group = new THREE.Group();
    buildDoorway(opening, position, direction, [0, 0], group, () => new THREE.MeshBasicMaterial());
    if (group.children.length !== 1) throw new Error(`${fixture.name}: component count`);
    const mesh = group.children[0] as THREE.Mesh;
    const points = mesh.geometry.getAttribute("position");
    const actual = Array.from({ length: points.count }, (_, i) =>
      [points.getX(i), points.getY(i), points.getZ(i)]);
    const expected = fixture.profile.flatMap(([x, y, z]) =>
      [[x, z, -y], [x + fixture.extrude[0], z + fixture.extrude[2], -y - fixture.extrude[1]]]);
    if (!expected.every(p => actual.some(q => p.every((v, i) => Math.abs(v - q[i]) < 1e-6)))) {
      throw new Error(`${fixture.name}: sourced sweep differs from Python/glTF`);
    }
    if (mesh.userData.doorwayProduct !== "TEST-REDUCER") throw new Error("Product identity lost");
    // A closed prism must have nonzero volume, with consistent outward face winding.
    const index = mesh.geometry.index!;
    let volume = 0;
    for (let i = 0; i < index.count; i += 3) {
      const [a, b, c] = [0, 1, 2].map(j => new THREE.Vector3(...actual[index.getX(i + j)]));
      volume += a.dot(b.cross(c)) / 6;
    }
    if (volume <= 0) throw new Error(`${fixture.name}: inside-out section`);
  }
  console.log("Sourced doorway Python/viewer sweep parity tests passed.");
}
