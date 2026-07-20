import * as THREE from "three";
import { createPlanPrismGeometry, projectPointToScene } from "./planGeometry";

function closeTo(actual: number, expected: number, message: string) {
  if (Math.abs(actual - expected) > 1e-6) {
    throw new Error(`${message}: expected ${expected}, received ${actual}`);
  }
}

function boundsFor(geometry: THREE.BufferGeometry): THREE.Box3 {
  geometry.computeBoundingBox();
  if (!geometry.boundingBox) throw new Error("Expected geometry bounds");
  return geometry.boundingBox;
}

// Called by scripts/run-geometry-tests.mjs. This stays framework-free because the UI does
// not otherwise need a browser-test dependency for these deterministic geometry checks.
export function runPlanGeometryTests() {
  const projectPoint = projectPointToScene([3.25, 8.5], 1.75);
  closeTo(projectPoint.x, 3.25, "Project X maps to scene X");
  closeTo(projectPoint.y, 1.75, "Project elevation maps to scene Y");
  closeTo(projectPoint.z, 8.5, "Project +Y maps to positive scene Z");

  const outline: [number, number][] = [[3, 7], [8, 7], [8, 11], [3, 11]];
  const geometry = createPlanPrismGeometry(outline, 1.25, 2.75);
  if (!geometry) throw new Error("Expected a prism for a valid outline");
  const bounds = boundsFor(geometry);
  closeTo(bounds.min.x, 3, "Prism preserves minimum project X");
  closeTo(bounds.max.x, 8, "Prism preserves maximum project X");
  closeTo(bounds.min.z, 7, "Prism preserves minimum project Y as scene Z");
  closeTo(bounds.max.z, 11, "Prism preserves maximum project Y as scene Z");
  closeTo(bounds.min.y, 1.25, "Prism starts at authored z0");
  closeTo(bounds.max.y, 2.75, "Prism ends at authored z1");
  geometry.dispose();
}
