// Orbit-camera framing and input normalization for the 3D panel — the arithmetic behind
// "reset the view", the arrow-key pan step, and one wheel notch.
//
// Split out of components/Panel3D.tsx: none of it touches a scene, a store or React, and all of
// it is exactly the kind of thing that has to be provable in a unit test rather than by eye
// (the default-zoom fit was wrong for years because it was buried in a 1700-line component).
import * as THREE from "three";

export type PanDirection = "left" | "right" | "up" | "down";

// Default / reset framing (→ TODO: "the 'default zoom' for reset is poorly calculated").
// The old fit dollied back far enough to contain the building's bounding *sphere*, which for a
// house — long, wide, and comparatively low — is a ball roughly the plan diagonal across, so
// the model landed small and the operator had to pan and dolly their way back in. These frame
// the eight box corners against the real frustum instead, which is exact for any proportions.
export const VIEW_FIT_MARGIN = 1.06; // breathing room around the tightest exact fit
export const VIEW_FIT_MIN_RADIUS_M = 2;
// Polar angle from +Y. ~0.34π puts the eye about 29° above the horizon: high enough to read
// the roof planes and the storey stack, low enough that elevations stay legible.
export const VIEW_FIT_POLAR_ANGLE = Math.PI * 0.34;
// Arrow-key / on-screen pan step as a fraction of the current dolly distance, so one tap moves
// the same *apparent* amount whether you are framing the whole house or one corner of it.
export const VIEW_PAN_STEP_FRACTION = 0.22;
// Wheel deltas are wildly inconsistent (a line-mode mouse notch vs. a pixel-mode trackpad
// flick), so they are normalized to pixels and then clamped before they reach the dolly. This
// is what stops one trackpad gesture from crossing the whole zoom range.
export const WHEEL_LINE_HEIGHT_PX = 16;
export const WHEEL_MAX_STEP_PX = 90;
export const WHEEL_DOLLY_SENSITIVITY = 0.0016;
export const MIN_DOLLY_RADIUS_M = 0.8;
export const MAX_DOLLY_RADIUS_M = 400;

/** Normalize one wheel event to a clamped pixel delta (see WHEEL_* constants). */
export function normalizedWheelDeltaPx(deltaY: number, deltaMode: number): number {
  const pixels = deltaMode === 1 ? deltaY * WHEEL_LINE_HEIGHT_PX : deltaY;
  return Math.max(-WHEEL_MAX_STEP_PX, Math.min(WHEEL_MAX_STEP_PX, pixels));
}

/**
 * The dolly distance at which every corner of `box` sits inside the frustum, looking at
 * `target` from the orbit angles given. Exact rather than sphere-conservative: each corner is
 * projected onto the camera basis and required to fall within the horizontal and vertical
 * half-angles at its own depth.
 */
export function frameRadiusForBounds(
  box: THREE.Box3,
  target: THREE.Vector3,
  theta: number,
  phi: number,
  verticalFovRadians: number,
  aspect: number,
  margin: number = VIEW_FIT_MARGIN,
): number {
  const eyeDirection = new THREE.Vector3(
    Math.sin(phi) * Math.cos(theta), Math.cos(phi), Math.sin(phi) * Math.sin(theta));
  const forward = eyeDirection.clone().negate();
  const right = new THREE.Vector3().crossVectors(forward, new THREE.Vector3(0, 1, 0)).normalize();
  const up = new THREE.Vector3().crossVectors(right, forward).normalize();
  const tanVertical = Math.tan(verticalFovRadians / 2);
  const tanHorizontal = tanVertical * Math.max(1e-3, aspect);
  let radius = 0;
  const offset = new THREE.Vector3();
  for (const x of [box.min.x, box.max.x]) {
    for (const y of [box.min.y, box.max.y]) {
      for (const z of [box.min.z, box.max.z]) {
        offset.set(x, y, z).sub(target);
        const depth = offset.dot(forward); // positive = further from the eye than the target
        radius = Math.max(radius,
          Math.abs(offset.dot(right)) / tanHorizontal - depth,
          Math.abs(offset.dot(up)) / tanVertical - depth);
      }
    }
  }
  return Math.max(VIEW_FIT_MIN_RADIUS_M, radius * margin);
}
