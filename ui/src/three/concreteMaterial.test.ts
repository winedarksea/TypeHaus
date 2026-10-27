import * as THREE from "three";
import { applyConcreteUv, buildConcreteMap, concreteLuminance, createConcreteMaterial,
  disposeConcreteTexture, isCastConcreteFinish } from "./concreteMaterial";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

export function runConcreteMaterialTests(): void {
  assert(isCastConcreteFinish("cast-concrete") && !isCastConcreteFinish("silicate-wash")
    && !isCastConcreteFinish(null), "Only the declared finish selects cast concrete");
  for (const t of [0, 0.131, 0.5, 0.873]) {
    for (const [u, v] of [[0, t], [t, 0], [0.279, t]]) {
      const sample = concreteLuminance(u, v);
      assert(Math.abs(sample - concreteLuminance(u + 1, v)) < 1e-9
        && Math.abs(sample - concreteLuminance(u, v + 1)) < 1e-9, "Luminance repeats seamlessly");
    }
  }
  const map = buildConcreteMap();
  assert(map === buildConcreteMap() && map.colorSpace === THREE.SRGBColorSpace, "Map is shared sRGB");
  const pixels = map.image.data!;
  let sum = 0, min = 255, max = 0;
  for (let i = 0; i < pixels.length; i += 4) {
    sum += Number(pixels[i]); min = Math.min(min, Number(pixels[i])); max = Math.max(max, Number(pixels[i]));
  }
  const mean = sum / (pixels.length / 4) / 255;
  assert(mean > 0.85 && mean < 0.99, "Mean tone stays near the authored colour");
  assert(max - min > 50, "Pits and cloud give visible variation");
  const textured = createConcreteMaterial("nordic", "#a9a9a9");
  const schematic = createConcreteMaterial("schematic", "#a9a9a9");
  assert(textured.map === map && textured.roughness > 0.85 && textured.metalness === 0, "Matte tinted map");
  assert(!schematic.map, "Schematic stays flat");
  const box = new THREE.BoxGeometry(1.2192, 0.3, 0.6);
  applyConcreteUv(box, [0, 0]);
  assert(box.getAttribute("uv").count === box.getAttribute("position").count, "UVs assigned");
  disposeConcreteTexture();
  assert(buildConcreteMap() !== map, "Map regenerates after dispose");
  disposeConcreteTexture();
  textured.dispose(); schematic.dispose(); box.dispose();
}
