// Resolving a `product_ref` to the product it names (→ engine model/product.py).
//
// A model module rather than part of the component, for the reason every other one here is:
// the arrangement is testable without a DOM, and three inspectors (canvas object, opening,
// solid/member) all need the same two lookups. `components/ProductRows.tsx` is the renderer.
import type { Catalog, Model, ProductSpec } from "./types";

/**
 * The product a `product_ref` names, or null.
 *
 * Null for an ABSENT ref and for a DANGLING one alike: `integrity.unknown_product_ref` is
 * the surface that reports the second as a hard error, and the panel's job is to print
 * nothing rather than a half-filled block naming a product nobody defined.
 */
export function productFor(
  catalog: Catalog | undefined, ref: string | null | undefined,
): ProductSpec | null {
  if (!ref) return null;
  return catalog?.products?.find((product) => product.tag === ref) ?? null;
}

/**
 * The product behind a MATERIAL tag — the derived inspectors' route in.
 *
 * A solid or a framing member names a material, never a product type: the trim-run family
 * (gutters, fascia, soffits, ridge caps, edge cladding, railing parts) carries
 * `Solid.material` directly, and a member carries `Member.material`. So the join is one hop
 * longer than a placeable's: tag → `Material.product_ref` → `Product`.
 */
export function productForMaterial(
  model: Model | null, materialTag: string | null | undefined,
): ProductSpec | null {
  if (!materialTag) return null;
  const material = model?.catalog?.materials?.find((candidate) => candidate.tag === materialTag);
  return productFor(model?.catalog, material?.product_ref);
}
