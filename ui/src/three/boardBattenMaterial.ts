import * as THREE from "three";

// A house-sized 2048px shadow map cannot resolve the two faces of 24 ga sheet steel.
// Bias only the shadow lookup, leaving the visible geometry and other finishes untouched.
const SHEET_SHADOW_NORMAL_BIAS_M = 0.01;
// The pans/valleys sit only one sheet thickness ahead of their backing. Fixed depth
// steps keep it from bleeding through at house-view distances; slope bias can hide trim.
export const PROFILED_METAL_SKIN_POLYGON_OFFSET = {
  polygonOffset: true, polygonOffsetFactor: 0, polygonOffsetUnits: -3,
};
const PAINTED_METAL_SURFACE = {
  metalness: 0.05, roughness: 0.45, clearcoat: 0.3, clearcoatRoughness: 0.1,
};

export function createProfiledMetalSkinMaterial(
  mode: "nordic" | "schematic", color: number, offset = PROFILED_METAL_SKIN_POLYGON_OFFSET,
): THREE.MeshStandardMaterial {
  const material = mode === "schematic"
    ? new THREE.MeshStandardMaterial({ color, roughness: 1, metalness: 0, flatShading: true,
      ...offset })
    : new THREE.MeshPhysicalMaterial({ color, ...PAINTED_METAL_SURFACE, ...offset });
  material.onBeforeCompile = shader => {
    const shadowChunk = THREE.ShaderChunk.shadowmap_vertex.replace(
      /shadowWorldNormal \* ((?:directional|point|spot)LightShadows\[ i \]\.shadowNormalBias)/g,
      `shadowWorldNormal * max($1, ${SHEET_SHADOW_NORMAL_BIAS_M.toFixed(4)})`,
    );
    shader.vertexShader = shader.vertexShader.replace("#include <shadowmap_vertex>", shadowChunk);
  };
  material.customProgramCacheKey = () => "profiled-metal-sheet-shadows-v1";
  return material;
}

export const createBoardBattenMaterial = createProfiledMetalSkinMaterial;
