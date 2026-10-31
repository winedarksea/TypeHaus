// Draw-call merge for a multi-part massing (→ builders/site.ts buildCanvasObjectParts).
//
// A product is a dozen boxes in two or three colours, and catlin places hundreds of them: one
// mesh per part made furniture and devices the two biggest buckets of an orbit frame. Parts of
// one object that share an opaque material draw as one mesh instead. Every merged mesh still
// carries the object's uid and material, so picking and highlight are unchanged.
import * as THREE from "three";
import { mergeGeometries } from "three/examples/jsm/utils/BufferGeometryUtils.js";

export interface PartDraw {
  geometry: THREE.BufferGeometry;
  material: THREE.Material | THREE.Material[];
  /** Local offset the mesh carries (a centred box); null when baked into the geometry. */
  offset: [number, number, number] | null;
  /** Names the geometry when it is the type's, shared by every instance; null when the
   *  instance owns it (a board's seeded grain). */
  shareKey: string | null;
}

/** Shared merged geometries, keyed by the parts folded in (→ PartGeometries). */
export interface MergedGeometryCache {
  merged(key: string, make: () => THREE.BufferGeometry | null): THREE.BufferGeometry | null;
}

// A transparent part sorts on its own, and a multi-material (end-grain) part needs its groups. A
// single material ignores groups (a BoxGeometry always carries six).
const mergeable = (draw: PartDraw): draw is PartDraw & { material: THREE.Material } =>
  !Array.isArray(draw.material) && !draw.material.transparent;

// mergeGeometries needs the same attributes and indexing on every input. A plain material reads
// only position and normal, so its parts merge whatever else they carry (a box's uv).
const plain = (material: THREE.Material) => !(material as THREE.MeshStandardMaterial).vertexColors
  && !Object.values(material).some((value) => value instanceof THREE.Texture);
const layout = (geometry: THREE.BufferGeometry) =>
  `${Object.keys(geometry.attributes).sort().join(",")}|${geometry.index ? "i" : "n"}`;

// One input as the merge wants it: in the object's frame, with only the attributes every input
// shares, de-indexed when any input is not. Never mutates a geometry it was handed.
function prepare(draw: PartDraw, shared: ReadonlySet<string>, deindex: boolean): THREE.BufferGeometry {
  let geometry = draw.geometry;
  const own = () => { if (geometry === draw.geometry) geometry = geometry.clone(); };
  if (deindex && geometry.index) geometry = geometry.toNonIndexed();
  for (const name of Object.keys(geometry.attributes)) {
    if (!shared.has(name)) { own(); geometry.deleteAttribute(name); }
  }
  if (draw.offset) { own(); geometry.translate(...draw.offset); }
  return geometry;
}

function mergeBucket(bucket: PartDraw[], cache?: MergedGeometryCache): PartDraw[] {
  if (bucket.length === 1) return bucket;
  const make = () => {
    const names = bucket.map((draw) => Object.keys(draw.geometry.attributes));
    const shared = new Set(names[0].filter((name) => names.every((list) => list.includes(name))));
    const deindex = bucket.some((draw) => !draw.geometry.index);
    const inputs = bucket.map((draw) => prepare(draw, shared, deindex));
    const merged = mergeGeometries(inputs, false);
    // Clones are dropped either way; an instance-owned input only once it is folded in.
    inputs.forEach((geometry, i) => {
      if (geometry !== bucket[i].geometry || (merged && !bucket[i].shareKey)) geometry.dispose();
    });
    return merged;
  };
  const shareable = cache && bucket.every((draw) => draw.shareKey);
  const geometry = shareable
    ? cache.merged(bucket.map((draw) => draw.shareKey).join("+"), make) : make();
  return geometry ? [{ geometry, material: bucket[0].material, offset: null, shareKey: null }] : bucket;
}

/** The draws to make, in part order: a merged bucket sits where its first part did. */
export function mergePartDraws(draws: PartDraw[], cache?: MergedGeometryCache): PartDraw[] {
  const slots: PartDraw[][] = [];
  const buckets = new Map<string, PartDraw[]>();
  for (const draw of draws) {
    if (!mergeable(draw)) { slots.push([draw]); continue; }
    const key = `${draw.material.uuid}|${plain(draw.material) ? "plain" : layout(draw.geometry)}`;
    const bucket = buckets.get(key);
    if (bucket) bucket.push(draw);
    else { const fresh = [draw]; buckets.set(key, fresh); slots.push(fresh); }
  }
  return slots.flatMap((slot) => mergeBucket(slot, cache));
}
