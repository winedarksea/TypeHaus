import * as THREE from "three";
import type { Opening, Wall } from "../../model/types";
import { RESOLVED_NORDIC_PALETTE } from "../../nordic/palette";
import fixtures from "./doorwayFixtures.json";
import { buildDoorway } from "./doorway";
import { buildOpening } from "./openings";

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
    for (const pocketOffset of [-0.06, 0.06]) {
      const normal = [-direction[1], direction[0]];
      const wall: Wall = {
        uid: "wall", tag: "W-1", storey: "S-1", assembly: "A-1", provenance: null,
        axis: [[x0, y0], [x1, y1]], z0_m: 0, z1_m: 3,
        top_z0_m: null, top_z1_m: null, plate_base_z_m: null, plate_top_z_m: null,
        layout_axis: null, is_foundation: false, members: [],
        layers: [{ name: "stud", material: "spf", function: "structure", thickness_m: 0.18,
          control: [], polygon: [[x0, y0, -0.09], [x1, y1, -0.09],
            [x1, y1, 0.09], [x0, y0, 0.09]].map(([x, y, depth]) =>
            [x + normal[0] * (pocketOffset + depth),
              y + normal[1] * (pocketOffset + depth)] as [number, number]) }],
      };
      const pocket = new THREE.Group();
      buildOpening(pocket, opening, wall, [0, 0], "schematic", RESOLVED_NORDIC_PALETTE.light,
        { operation: "pocket" }, [], new Map());
      const section = pocket.children.find(child => child.userData.doorwayProduct) as THREE.Mesh;
      const pocketPoints = section.geometry.getAttribute("position");
      if (pocketPoints.count !== points.count || actual.some((point, i) =>
        point.some((value, axis) => Math.abs(value - pocketPoints.getComponent(i, axis)) > 1e-6))) {
        throw new Error(`${fixture.name}: pocket offset shifts sourced doorway section`);
      }
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
