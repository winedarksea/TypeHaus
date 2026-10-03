import * as THREE from "three";
import type { CanvasObject, ModelPart } from "../../model/types";
import { buildCanvasObjectParts } from "./site";

function assert(condition: boolean, message: string): void {
  if (!condition) throw new Error(message);
}

export function runMirrorBuilderTests(): void {
  const item = { uid: "mirror", position_m: [0, 0], rotation: 90 } as CanvasObject;
  const part: ModelPart = {
    center: [0, -0.02, 0.381], size: [0.762, 0.004, 0.762], color: "#c7d6de",
    shape: "cylinder-depth", radial_segments: 64, metalness: 1, roughness: 0.08,
  };
  const picks: THREE.Mesh[] = [];
  const byUid = new Map<string, THREE.Material[]>();
  const group = buildCanvasObjectParts(new THREE.Group(), item, [part], [0, 0],
    "nordic", 1, picks, byUid);
  const mesh = group.children[0] as THREE.Mesh;
  mesh.geometry.computeBoundingBox();
  const extent = mesh.geometry.boundingBox!.getSize(new THREE.Vector3());
  assert(Math.abs(extent.x - extent.y) < 1e-6 && Math.abs(extent.z - 0.004) < 1e-6,
    "A round wall mirror keeps its vertical circular face and shallow horizontal depth");
  assert(mesh.geometry instanceof THREE.CylinderGeometry
    && mesh.geometry.parameters.radialSegments === part.radial_segments,
    "Mirror edges use the engine's smooth silhouette resolution");
  assert(mesh.position.z > 0 && Math.abs(group.rotation.y - Math.PI / 2) < 1e-9,
    "The glass faces into the room and placement rotates it onto the perpendicular wall");
  const glass = mesh.material as THREE.MeshStandardMaterial;
  assert(glass.metalness === 1 && glass.roughness < 0.1,
    "Mirror glass reflects the scene environment instead of receiving matte massing paint");
  assert(picks[0] === mesh && byUid.get(item.uid)?.[0] === glass,
    "The round mirror stays selectable and its material participates in highlighting");

  const mixed = buildCanvasObjectParts(new THREE.Group(), item,
    [part, { ...part, metalness: 0, roughness: 0.82 }], [0, 0], "nordic", 0, [], new Map());
  assert((mixed.children[0] as THREE.Mesh).material !== (mixed.children[1] as THREE.Mesh).material,
    "Parts with the same colour and different surface finishes keep separate materials");
  const schematic = buildCanvasObjectParts(new THREE.Group(), item, [part], [0, 0],
    "schematic", 0, [], new Map());
  const diagram = (schematic.children[0] as THREE.Mesh).material as THREE.MeshStandardMaterial;
  assert(diagram.roughness === 1 && diagram.metalness === 0,
    "Schematic mode keeps its readable matte surfaces");
}
