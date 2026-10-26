import * as THREE from "three";

// A house-sized 2048px shadow map cannot resolve the two faces of 24 ga sheet steel.
// Bias only the shadow lookup, leaving the visible geometry and other finishes untouched.
const SHEET_SHADOW_NORMAL_BIAS_M = 0.01;
const PAINTED_METAL_SURFACE = {
  metalness: 0.05, roughness: 0.45, clearcoat: 0.3, clearcoatRoughness: 0.1,
};

export function createBoardBattenMaterial(
  mode: "nordic" | "schematic", color: number,
): THREE.MeshStandardMaterial {
  const material = mode === "schematic"
    ? new THREE.MeshStandardMaterial({ color, roughness: 1, metalness: 0, flatShading: true })
    : new THREE.MeshPhysicalMaterial({ color, ...PAINTED_METAL_SURFACE });
  material.onBeforeCompile = shader => {
    const shadowChunk = THREE.ShaderChunk.shadowmap_vertex.replace(
      /shadowWorldNormal \* ((?:directional|point|spot)LightShadows\[ i \]\.shadowNormalBias)/g,
      `shadowWorldNormal * max($1, ${SHEET_SHADOW_NORMAL_BIAS_M.toFixed(4)})`,
    );
    shader.vertexShader = shader.vertexShader.replace("#include <shadowmap_vertex>", shadowChunk);
  };
  material.customProgramCacheKey = () => "board-batten-sheet-shadows-v1";
  return material;
}
