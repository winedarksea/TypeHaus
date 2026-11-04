import * as THREE from "three";

// Fit the sun's orthographic shadow frustum to the building box; otherwise the default 5m box
// clips every house and the shadow map resolution is wasted on empty space.
export function fitSunToBox(key: THREE.DirectionalLight, box: THREE.Box3) {
  if (box.isEmpty()) return;
  const bounds = box.getBoundingSphere(new THREE.Sphere());
  const cam = key.shadow.camera;
  cam.left = -bounds.radius; cam.right = bounds.radius;
  cam.top = bounds.radius; cam.bottom = -bounds.radius;
  cam.near = 0.1; cam.far = bounds.radius * 6;
  cam.updateProjectionMatrix();
  key.target.position.copy(bounds.center);
  key.position.copy(bounds.center).add(
    new THREE.Vector3(0.6, 1.1, 0.45).normalize().multiplyScalar(bounds.radius * 2.5),
  );
  key.target.updateMatrixWorld();
}
