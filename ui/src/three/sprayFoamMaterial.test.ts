import * as THREE from "three";
import { applySprayFoamUv, buildSprayFoamMaps, createSprayFoamMaterial,
  disposeSprayFoamTextures, isSprayFoamFinish, sprayFoamSample, SPRAY_FOAM_SURFACE } from "./sprayFoamMaterial";
import { buildMembers } from "./members";
import { resolveMemberPickUid } from "./memberPicking";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import type { Member } from "../model/types";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runSprayFoamMaterialTests(): void {
  assert(isSprayFoamFinish("spray-foam") && !isSprayFoamFinish("closed-cell-spray-foam")
    && !isSprayFoamFinish("rigid") && !isSprayFoamFinish(null), "Only the declared finish selects sprayed skin");
  for (const t of [0, 0.131, 0.5, 0.873]) {
    for (const [u, v] of [[0, t], [t, 0], [0.279, t]]) {
      const sample = sprayFoamSample(u, v);
      for (const [du, dv] of [[1, 0], [0, 1]]) {
        const wrapped = sprayFoamSample(u + du, v + dv);
        assert(Math.abs(sample.height - wrapped.height) < 1e-12
          && Math.abs(sample.luminance - wrapped.luminance) < 1e-9, "Height and color repeat seamlessly");
      }
    }
  }
  const maps = buildSprayFoamMaps();
  assert(maps === buildSprayFoamMaps(), "Maps are generated once and shared");
  assert(maps.color.colorSpace === THREE.SRGBColorSpace && maps.normal.colorSpace === THREE.NoColorSpace,
    "Color and normal data use the correct color spaces");
  assert(maps.normal.generateMipmaps && maps.normal.wrapS === THREE.RepeatWrapping, "Distant surfaces filter and tile");
  const pixels = maps.normal.image.data!;
  let minimumNormalX = 255, maximumNormalX = 0;
  for (let i = 0; i < pixels.length; i += 4) {
    const x = Number(pixels[i]) / 255 * 2 - 1;
    const y = Number(pixels[i + 1]) / 255 * 2 - 1;
    const z = Number(pixels[i + 2]) / 255 * 2 - 1;
    assert(Math.abs(Math.hypot(x, y, z) - 1) < 0.015 && z > 0.7, "Normals are unit length with restrained relief");
    minimumNormalX = Math.min(minimumNormalX, Number(pixels[i]));
    maximumNormalX = Math.max(maximumNormalX, Number(pixels[i]));
  }
  assert(maximumNormalX - minimumNormalX > 20, "Relief produces a visible lighting cue");
  const textured = createSprayFoamMaterial("nordic", "#e8d9b5");
  const schematic = createSprayFoamMaterial("schematic", "#e8d9b5");
  assert(textured.normalMap === maps.normal && textured.color.getHexString() === "e8d9b5"
    && textured.roughness > 0.9 && textured.metalness === 0, "Foam keeps its authored tint and matte surface");
  assert(!schematic.map && !schematic.normalMap && schematic.flatShading, "Schematic mode stays flat");

  const box = new THREE.BoxGeometry(1.2, 0.3, 0.6);
  const before = Array.from(box.getAttribute("position").array);
  applySprayFoamUv(box, [5, 7]);
  const uv = box.getAttribute("uv"), normals = box.getAttribute("normal");
  for (const axis of [0, 1, 2]) {
    const us: number[] = [], vs: number[] = [];
    for (let i = 0; i < uv.count; i++) if (Math.abs(normals.getComponent(i, axis)) > 0.9) {
      us.push(uv.getX(i)); vs.push(uv.getY(i));
    }
    assert(Math.max(...us) > Math.min(...us) && Math.max(...vs) > Math.min(...vs), "All box faces have usable UVs");
  }
  assert(before.every((value, i) => value === box.getAttribute("position").array[i]), "Mapping leaves geometry unchanged");
  const topUs = Array.from({ length: uv.count }, (_, i) => i)
    .filter(i => normals.getY(i) > 0.9).map(i => uv.getX(i));
  assert(Math.abs(Math.max(...topUs) - Math.min(...topUs) - 1.2 / SPRAY_FOAM_SURFACE.tileSizeM) < 1e-5,
    "Texture scale follows physical dimensions");

  const member = (key: string, material: string, x: number): Member => ({
    key, material, category: "insulation", profile: "foam", parent_uid: null, p0: [x, 0], p1: [x + 1, 0],
    z0_m: 0, z1_m: 0.2, length_m: 1, z0_end_m: null, z1_end_m: null, shape: "rect",
    width_m: 0.1, depth_m: 0.1, flange_width_m: null, flange_thickness_m: null,
    web_thickness_m: null, plies: 1, orient: [1, 0], connection: null, trade: null,
  });
  const group = new THREE.Group();
  buildMembers(group, [member("a", "custom", 0), member("b", "custom", 1), member("c", "xps", 2)],
    [0, 0], "nordic", RESOLVED_NORDIC_PALETTE.light, "W", [{ tag: "custom", finish: "spray-foam", color: "#e8d9b5" }]);
  const foam = group.children[0] as THREE.Mesh<THREE.BufferGeometry, THREE.MeshStandardMaterial>;
  assert(foam.material.normalMap === maps.normal && foam.geometry.getAttribute("uv"), "Closure members receive the same texture");
  assert(resolveMemberPickUid(foam, null, 0) === "W::a" && resolveMemberPickUid(foam, null, 12) === "W::b",
    "Merged foam closures retain individual picking");
  assert(group.children.length === 2, "Foam stays batched separately from rigid insulation");
  let disposed = 0;
  Object.values(maps).forEach(map => map.addEventListener("dispose", () => disposed++));
  disposeSprayFoamTextures();
  assert(disposed === 2 && buildSprayFoamMaps() !== maps, "Both shared maps can be disposed and regenerated");
  disposeSprayFoamTextures();
  textured.dispose(); schematic.dispose(); box.dispose();
}
