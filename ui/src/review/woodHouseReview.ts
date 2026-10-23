import * as THREE from "three";
import type { Model } from "../model/types";
import { assemblyFaceMaterial } from "../model/solidLabels";
import { RESOLVED_NORDIC_PALETTE } from "../nordic/palette";
import { buildBaseRun, buildBoardMembers, buildCountertop, buildDoorCasing } from "../three/builders/millwork";
import { buildPaneling, buildSolid } from "../three/builders/structure";
import { buildCanvasObjectParts } from "../three/builders/site";
import { buildWallSkinMembers } from "../three/builders/wallSkin";
import { runWallCoatingChecks } from "./wallCoatingChecks";

/** Actual resolved Catlin objects, built through the same entrypoints as the editor. */
export async function houseWoodSamples() {
  const model: Model = await (await fetch("/__wood-review-house")).json();
  const palette = RESOLVED_NORDIC_PALETTE.light, materials = model.catalog!.materials;
  const appearanceFor = (ref: string | null | undefined) => materials.find(m => m.tag === ref);
  const isSpecies = (ref: string | null | undefined, species: string) => appearanceFor(ref)?.species === species;
  const groups: { name: string; group: THREE.Group; species: string; surface: string }[] = [];
  const failures: string[] = [];
  const add = (name: string, species: string, surface: string,
    build: (group: THREE.Group, picks: THREE.Mesh[], selected: Map<string, THREE.Material[]>) => void) => {
    const group = new THREE.Group(), picks: THREE.Mesh[] = [], selected = new Map<string, THREE.Material[]>();
    build(group, picks, selected);
    const wood: THREE.Material[] = [];
    group.traverse(object => {
      if (!(object instanceof THREE.Mesh)) return;
      const appearance = Array.isArray(object.material) ? object.material : [object.material];
      wood.push(...appearance.filter(m => m.userData.woodSpecies === species));
      const ends = object.geometry.getAttribute("woodEnd"), uv = object.geometry.getAttribute("uv");
      if (ends && uv) {
        const faceU = Array.from({ length: uv.count }, (_, i) => i).filter(i => !ends.getX(i)).map(i => uv.getX(i));
        if (Math.max(...faceU) - Math.min(...faceU) > 0.25001) failures.push(`${name}: crosses an atlas lane`);
      }
    });
    if (!wood.length || wood.some(m => m.userData.woodSurface !== surface)) failures.push(`${name}: wrong species/finish`);
    if (!picks.length || !selected.size) failures.push(`${name}: missing selection registration`);
    groups.push({ name, group, species, surface });
  };
  const runLength = (run: NonNullable<Model["base_runs"]>[number]) => Math.max(...run.outline.map((p, i) => {
    const next = run.outline[(i + 1) % run.outline.length]; return Math.hypot(next[0] - p[0], next[1] - p[1]);
  }));
  const cherry = model.door_casings!.find(c => isSpecies(c.material_ref, "cherry"))!;
  add("Cherry · casing", "cherry", "natural-clear", (g, p, s) =>
    buildDoorCasing(g, cherry, [0, 0], "nordic", palette, materials, p, s));
  const tableType = model.catalog!.canvas_object_types!.find(t => t.model_parts?.some(p => isSpecies(p.material_ref, "ash")))!;
  const table = model.canvas_objects!.find(o => o.type === tableType.tag)!;
  add("Ash · dining table", "ash", "natural-clear", (g, p, s) =>
    buildCanvasObjectParts(g, table, tableType.model_parts!, [0, 0], "nordic", table.z_m ?? 0, p, s, materials));
  const elm = model.solids!.find(s => isSpecies(s.material ?? assemblyFaceMaterial(model.catalog, s.assembly), "elm"))!;
  add("Elm · suite post", "elm", "natural-clear", (g, p, s) =>
    buildSolid(g, elm, [0, 0], "nordic", palette, model.catalog, p, s, materials));
  const walnut = model.countertops!.find(c => isSpecies(c.material_ref, "walnut"))!;
  add("Walnut · nook top", "walnut", "natural-clear", (g, p, s) =>
    buildCountertop(g, walnut, [0, 0], "nordic", palette, materials, p, s));
  const oakStair = model.stairs!.find(stair => stair.members.some(m => m.category === "tread" && isSpecies(m.material, "oak")))!;
  const tread = oakStair.members.find(m => m.category === "tread" && isSpecies(m.material, "oak"))!;
  add("White oak · tread", "oak", "natural-clear", (g, p, s) => {
    buildBoardMembers(g, [tread], [0, 0], "nordic", palette, materials, oakStair.uid);
    const mesh = g.children[0] as THREE.Mesh; p.push(mesh);
    s.set(oakStair.uid, Array.isArray(mesh.material) ? mesh.material : [mesh.material]);
  });
  const basswood = model.solids!.find(s => isSpecies(s.material, "basswood"))!;
  add("Basswood · sauna ceiling", "basswood", "unfinished", (g, p, s) =>
    buildSolid(g, basswood, [0, 0], "nordic", palette, model.catalog, p, s, materials));
  const locust = model.base_runs!.filter(r => isSpecies(r.material_ref, "locust"))
    .sort((a, b) => runLength(b) - runLength(a))[0];
  add("Locust · sauna trim", "locust", "unfinished", (g, p, s) =>
    buildBaseRun(g, locust, [0, 0], "nordic", palette, materials, p, s));
  const painted = model.panelings!.find(p => isSpecies(p.material_ref, "oak") && appearanceFor(p.material_ref)?.wood_surface === "painted")!;
  add("White oak · painted shiplap", "oak", "painted", (g, p, s) =>
    buildPaneling(g, painted, [0, 0], "nordic", palette, materials, p, s));
  const mudroomWall = model.walls.find(w => w.tag === "W-M-STRW")!;
  add("Douglas fir · mudroom studs", "douglas-fir", "natural-clear", (g, p, s) => {
    buildWallSkinMembers({ framing: g } as Parameters<typeof buildWallSkinMembers>[0], g,
      mudroomWall.uid, mudroomWall.members, [0, 0], "nordic", palette, materials);
    g.traverse(object => {
      if (!(object instanceof THREE.Mesh)) return;
      p.push(object);
      s.set(mudroomWall.uid, Array.isArray(object.material) ? object.material : [object.material]);
    });
  });
  return { groups, checks: { failures, objects: groups.map(({ name, species, surface }) => ({ name, species, surface })) } };
}

/** Full-size cutaway context for checking grain minification across the suite's oak floor. */
export async function houseWoodRoom(renderer: THREE.WebGLRenderer) {
  const model: Model = await (await fetch("/__wood-review-house")).json();
  const materials = model.catalog!.materials;
  const materialSpecies = (ref?: string | null) => materials.find(m => m.tag === ref)?.species;
  const band = model.panelings!.find(p => p.tag === "WP-S-SUITE-HEADBOARD")!;
  const room = model.rooms.find(r => r.tag === band.room)!;
  const storey = model.storeys.find(s => s.tag === room.storey)!;
  const group = new THREE.Group(), picks: THREE.Mesh[] = [], selected = new Map<string, THREE.Material[]>();
  const palette = RESOLVED_NORDIC_PALETTE.light;
  const { buildRoomFloor, storeyFloorTopM } = await import("../three/builders/structure");
  buildRoomFloor(group, room, storeyFloorTopM(model.floors ?? [], storey.tag, storey.elevation_m),
    [0, 0], "nordic", palette, materials, picks, selected);
  for (const panel of model.panelings!.filter(p => p.room === room.tag))
    buildPaneling(group, panel, [0, 0], "nordic", palette, materials, picks, selected);
  for (const base of model.base_runs!.filter(r => r.room === room.tag))
    buildBaseRun(group, base, [0, 0], "nordic", palette, materials, picks, selected);
  for (const casing of model.door_casings!.filter(c => c.room === room.tag))
    buildDoorCasing(group, casing, [0, 0], "nordic", palette, materials, picks, selected);
  for (const post of model.solids!.filter(s => s.storey === room.storey
    && materialSpecies(s.material ?? assemblyFaceMaterial(model.catalog, s.assembly)) === "elm"))
    buildSolid(group, post, [0, 0], "nordic", palette, model.catalog, picks, selected, materials);
  const species = new Set<string>();
  group.traverse(object => {
    if (!(object instanceof THREE.Mesh)) return;
    for (const material of Array.isArray(object.material) ? object.material : [object.material])
      if (material.userData.woodSpecies) species.add(material.userData.woodSpecies);
  });
  return { group, checks: { failures: [
    ...["cherry", materialSpecies(room.floor_finish) ?? "oak", "elm"].filter(s => !species.has(s))
      .map(s => `Room context missing ${s}`),
    ...runWallCoatingChecks(model, renderer),
  ], room: room.tag, species: [...species] } };
}
