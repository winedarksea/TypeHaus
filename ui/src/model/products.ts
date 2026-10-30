// Resolving a `product_ref` to the product it names (→ engine model/product.py).
//
// A model module rather than part of the component, for the reason every other one here is:
// the arrangement is testable without a DOM, and three inspectors (canvas object, opening,
// solid/member) all need the same two lookups. `components/ProductRows.tsx` is the renderer.
import { pieceLabel, pieceRole } from "./pieceKeys";
import type { Catalog, Model, Opening, ProductSpec } from "./types";

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

/** What a picked piece of an opening is made of, and the product that supplies it. */
export interface PieceProduct {
  label: string;
  product: ProductSpec | null;
  /** The material or hardware role behind the piece, when the model names one. */
  detail: string | null;
}

/**
 * The product behind one piece of an opening (→ `Selection.piece`). Frame, leaf and glass come
 * from the opening's type; hardware from its catalog item; a doorway part from its spec;
 * installation boards, casings and stools from their material.
 */
export function pieceProduct(model: Model, opening: Opening, piece: string): PieceProduct {
  const label = pieceLabel(piece);
  const catalog = model.catalog;
  const role = pieceRole(piece);
  const types = opening.is_door ? catalog?.door_types ?? [] : catalog?.window_types ?? [];
  const typeProduct = () => productFor(catalog,
    types.find((type) => type.tag === opening.type_ref)?.product_ref);
  if (role === "hardware") {
    const part = opening.authored_product_parts?.find((one) => one.key === piece);
    return { label, product: productFor(catalog, part?.name), detail: part?.role ?? null };
  }
  if (role === "doorway") {
    const [, spec] = piece.split(":");
    const component = opening.doorway?.components.find((one) => one.specification.role === spec);
    return { label, product: productFor(catalog, component?.specification.product_ref),
             detail: spec ?? null };
  }
  if (role === "installation") {
    const board = opening.doorway?.exterior_placement?.boards
      .find((one) => one.name === piece.slice("installation:".length));
    return { label, product: productForMaterial(model, board?.material_ref),
             detail: board?.material_ref ?? null };
  }
  // Exterior casing is a trim category, not part of the window product.
  if (role === "exterior_trim") return { label, product: null, detail: "window trim" };
  if (role === "casing" || role === "stool") {
    const uid = piece.split(":")[1];
    const trim = role === "casing"
      ? (model.door_casings ?? []).find((one) => one.uid === uid)
      : (model.window_stools ?? []).find((one) => one.uid === uid);
    return { label: role === "stool" ? "Window stool" : label,
             product: productForMaterial(model, trim?.material_ref),
             detail: trim?.material_ref ?? null };
  }
  return { label, product: typeProduct(), detail: null };
}

/** The manufacturer profile a solid's `product` key names (Metal Sales "PBR Jamb"), or null. */
export function trimProfileFor(catalog: Catalog | undefined, key: string | null | undefined) {
  return key ? catalog?.trim_profiles?.find((profile) => profile.key === key) ?? null : null;
}

/** The product a railing's `RailingType` names, reached from the railing tag its solids carry. */
export function railingProduct(model: Model | null, railingTag: string | null | undefined) {
  const catalog = model?.catalog;
  const typeRef = catalog?.railings?.find((railing) => railing.tag === railingTag)?.type_ref;
  const type = catalog?.railing_types?.find((one) => one.tag === typeRef);
  return { type: type ?? null, product: productFor(catalog, type?.product_ref) };
}
