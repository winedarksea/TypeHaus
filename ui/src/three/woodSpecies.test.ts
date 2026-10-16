import * as THREE from "three";
import { createPlankMaterial, plankStyleOrNull, WOOD_PLANK_STYLES } from "./plankMaterial";
import { sampleWoodFigure, woodFigureSampler, WOOD_SPECIES_PROFILES, woodSpeciesProfile } from "./woodSpecies";
import { applyPieceGrainUv, boardBoxGeometry, woodMaterialsForGeometry } from "./woodPiece";
import { createPlanPrismGeometry } from "./planGeometry";
import { buildSolid } from "./builders/structure";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import type { Catalog, Solid } from "../model/types";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}
export function runWoodSpeciesTests() {
  const solid = WOOD_PLANK_STYLES["solid-board"];
  assert(Object.keys(WOOD_SPECIES_PROFILES).length === 9, "Nine distinct species");
  assert(woodSpeciesProfile("oak")?.key === "oak", "Existing oak means white oak");
  assert(woodSpeciesProfile("plywood") === null, "No species guess for sheet goods");
  assert(plankStyleOrNull("local-top", "clear-satin-hardwax-oil", "walnut") === solid,
    "An authored species makes a solid piece without changing its construction finish");
  for (const [key, profile] of Object.entries(WOOD_SPECIES_PROFILES)) {
    const figure = sampleWoodFigure(0.05, 0.4, 14, profile);
    assert(JSON.stringify(figure) === JSON.stringify(sampleWoodFigure(0.05, 0.4, 14, profile)),
      `${key}: deterministic figure`);
    assert(JSON.stringify(figure) !== JSON.stringify(sampleWoodFigure(0.05, 0.4, 15, profile)),
      `${key}: distinct boards`);
    const material = createPlankMaterial("nordic", solid, "#b77d60", undefined, { species: key });
    assert(material.map === null && material.color.getHexString() === "b77d60", "SSR retains authored colour");
    const raw = createPlankMaterial("nordic", solid, "#b77d60", undefined,
      { species: key, wood_surface: "unfinished" });
    assert(raw.roughness > material.roughness, "Raw wood is matte");
    const schematic = createPlankMaterial("schematic", solid, "#b77d60", undefined, { species: key });
    assert(schematic.roughness === 1 && !schematic.map, "Schematic remains flat");
  }
  const basswood = WOOD_SPECIES_PROFILES.basswood, ash = WOOD_SPECIES_PROFILES.ash;
  const energy = (profile: typeof ash) => Array.from({ length: 200 }, (_, i) =>
    sampleWoodFigure(i * 0.0009, 0.5, 4, profile).tone).reduce((sum, n) => sum + n * n, 0);
  assert(energy(basswood) < energy(ash) * 0.1, "Basswood is visibly quieter than ash");
  const fine = woodFigureSampler(4, ash, false, 1200)(0.03, 0.4);
  const minified = woodFigureSampler(4, ash, false, 150)(0.03, 0.4);
  assert(minified.pore < fine.pore * 0.1, "Unresolved pores are filtered before texture sampling");
  const shape = boardBoxGeometry(new THREE.Matrix4().makeRotationZ(0.6)
    .scale(new THREE.Vector3(0.9, 0.04, 0.2)), solid, 4);
  const endGroups = shape.groups.filter(g => g.materialIndex === 1);
  assert(endGroups.reduce((n, g) => n + g.count, 0) === 12, "Two crosscut box faces");
  const uv = shape.getAttribute("uv"), ends = shape.getAttribute("woodEnd");
  const us = Array.from({ length: uv.count }, (_, i) => i).filter(i => !ends.getX(i)).map(i => uv.getX(i));
  assert(Math.max(...us) - Math.min(...us) <= 1 / solid.boardsPerTile, "One lane for a rotated piece");
  const offcut = boardBoxGeometry(new THREE.Matrix4().makeScale(0.04, 0.09, 0.02), solid, 4, 0);
  const offcutUv = offcut.getAttribute("uv"), offcutEnds = offcut.getAttribute("woodEnd");
  const offcutV = Array.from({ length: offcutUv.count }, (_, i) => i).filter(i => !offcutEnds.getX(i))
    .map(i => offcutUv.getY(i));
  assert(Math.abs((Math.max(...offcutV) - Math.min(...offcutV)) * solid.tileAlongM - 0.04) < 1e-5,
    "A short trim offcut keeps grain along its run");
  const prism = createPlanPrismGeometry([[0, 0], [1.2, 0], [1.2, 0.3], [0, 0.3]], 0, 0.04)!;
  applyPieceGrainUv(prism, new THREE.Vector3(1, 0, 0), solid, 5);
  assert(prism.groups.some(g => g.materialIndex === 1), "Prism exposes crosscut ends");
  const endMaterial = new THREE.MeshStandardMaterial(), faceMaterial = new THREE.MeshStandardMaterial();
  faceMaterial.userData.endGrainMaterial = endMaterial;
  assert(Array.isArray(woodMaterialsForGeometry(faceMaterial, prism)), "Both materials bind to prism");
  // An assembly-backed elm post must resolve its wood independently of a direct material ref.
  const group = new THREE.Group(), picks: THREE.Mesh[] = [], selected = new Map<string, THREE.Material[]>();
  const catalog = { materials: [{ tag: "elm", color: "#bd9975", species: "elm" }],
    assemblies: [{ tag: "POST", layers: [{ material: "elm", function: "structure" }] }] } as unknown as Catalog;
  const post = { uid: "post", category: "column", assembly: "POST", material: null,
    outline: [[0, 0], [0.16, 0], [0.16, 0.16], [0, 0.16]], z0_m: 0, z1_m: 2.5 } as Solid;
  buildSolid(group, post, [0, 0], "nordic", RESOLVED_NORDIC_PALETTE.light, catalog, picks, selected);
  const mesh = group.children[0] as THREE.Mesh;
  assert(mesh.geometry.getAttribute("woodEnd"), "Assembly-backed elm gets wood UVs");
  const postUv = mesh.geometry.getAttribute("uv"), postEnd = mesh.geometry.getAttribute("woodEnd");
  const faceV = Array.from({ length: postUv.count }, (_, i) => i).filter(i => !postEnd.getX(i))
    .map(i => postUv.getY(i));
  assert(Math.abs((Math.max(...faceV) - Math.min(...faceV)) * solid.tileAlongM - 2.5) < 1e-5,
    "Post grain follows its vertical height");
  console.log("Wood species tests passed.");
}
