import * as THREE from "three";
import type { ResolvedNordicPalette } from "../nordic/palette";

// The gradient is authored at 256 steps down and 2px across. three stretches a plain-texture
// `scene.background` to fill the viewport, so the horizontal axis carries no information —
// there is nothing there to sample, and a wider canvas would only cost memory.
const HEIGHT_PX = 256;
const WIDTH_PX = 2;

/**
 * The 3D stage backdrop: `palette.viewport` as a vertical two-stop ramp.
 *
 * Tagged SRGBColorSpace, and that is what keeps tone mapping off it: three's WebGLBackground
 * sets `toneMapped = false` on the background plane exactly when the texture's transfer is sRGB.
 * With it, the ramp renders as the literal hex the palette authors — the same treatment the flat
 * THREE.Color background used to get, so the renderer's NeutralToneMapping (→ Panel3D) is not
 * quietly crushing the darker stop into the lighter one.
 *
 * The caller owns the texture and must dispose it; a Color needed no disposal, a texture does.
 */
export function createViewportBackground(palette: ResolvedNordicPalette): THREE.CanvasTexture {
  const canvas = document.createElement("canvas");
  canvas.width = WIDTH_PX;
  canvas.height = HEIGHT_PX;
  const ctx = canvas.getContext("2d")!;
  const gradient = ctx.createLinearGradient(0, 0, 0, HEIGHT_PX);
  gradient.addColorStop(0, palette.viewport[0]);
  gradient.addColorStop(1, palette.viewport[1]);
  ctx.fillStyle = gradient;
  ctx.fillRect(0, 0, WIDTH_PX, HEIGHT_PX);

  const texture = new THREE.CanvasTexture(canvas);
  texture.colorSpace = THREE.SRGBColorSpace;
  // Nothing ever samples this minified — it is drawn at full viewport size — so mips are pure
  // cost, and clamping keeps the end stops flat rather than wrapping into each other.
  texture.generateMipmaps = false;
  texture.minFilter = THREE.LinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.wrapS = THREE.ClampToEdgeWrapping;
  texture.wrapT = THREE.ClampToEdgeWrapping;
  return texture;
}

/** The same two stops as a CSS gradient, for the DOM behind the canvas. One source, no second table. */
export function viewportBackgroundCss(palette: ResolvedNordicPalette): string {
  return `linear-gradient(${palette.viewport[0]}, ${palette.viewport[1]})`;
}
