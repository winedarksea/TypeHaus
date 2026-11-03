// Shared static artwork for the 80" x 60" hanging, on the engine's room-facing sheet.
import * as THREE from "three";
import huntArtworkUrl from "../assets/medieval-hunt-tapestry.png";
import tapestryArtworkUrl from "../assets/lady-and-dragon-tapestry.png";

const TAPESTRY_TEXTURE_ANISOTROPY = 4;
const textureReadyListeners = new Set<() => void>();
const tapestryArtworkByType: Record<string, string> = {
  "FT-TAPESTRY-HUNT-80X60": huntArtworkUrl,
};
const cachedTapestryTextures = new Map<string, THREE.Texture>();

export function isTapestry(role: string | null | undefined): boolean {
  return role === "tapestry";
}

/** Render-on-demand viewers need a frame when the static artwork finishes loading. */
export function onTapestryMapReady(listener: () => void): () => void {
  textureReadyListeners.add(listener);
  return () => { textureReadyListeners.delete(listener); };
}

/** Vite bundles the image locally so packaged and offline viewers share the same artwork. */
export function buildTapestryMap(type: string | null = null): THREE.Texture | null {
  if (typeof document === "undefined") return null;
  const artworkUrl = tapestryArtworkByType[type ?? ""] ?? tapestryArtworkUrl;
  const cached = cachedTapestryTextures.get(artworkUrl);
  if (cached) return cached;
  const texture = new THREE.TextureLoader().load(artworkUrl, () => {
    if (cachedTapestryTextures.get(artworkUrl) !== texture) return;
    for (const listener of textureReadyListeners) listener();
  });
  texture.colorSpace = THREE.SRGBColorSpace;
  texture.anisotropy = TAPESTRY_TEXTURE_ANISOTROPY;
  cachedTapestryTextures.set(artworkUrl, texture);
  return texture;
}

/** A matte cloth material around the shared map, or null in headless geometry builds. */
export function createTapestryMaterial(type: string | null = null): THREE.MeshStandardMaterial | null {
  const map = buildTapestryMap(type);
  return map ? new THREE.MeshStandardMaterial({ map, roughness: 1, metalness: 0 }) : null;
}

/** Drop the shared texture — teardown in tests/hot reload only. */
export function disposeTapestryTextures(): void {
  for (const texture of cachedTapestryTextures.values()) texture.dispose();
  cachedTapestryTextures.clear();
}
