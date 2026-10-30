import { pieceProduct, productFor, productForMaterial } from "./products";
import type { Catalog, MaterialSpec, Model, ProductSpec } from "./types";

function assert(condition: unknown, message: string): asserts condition {
  if (!condition) throw new Error(message);
}

const WASHTOWER: ProductSpec = {
  tag: "PROD-LG-WKHC252HBA", brand: "LG", model: "WKHC252HBA",
  name: "WashTower (washer + heat-pump dryer)", sku: "", url: null, source: null,
};

function material(overrides: Partial<MaterialSpec>): MaterialSpec {
  return { tag: "m", name: "M", r_per_inch: null, perm_rating: null, density: null,
    ...overrides };
}

function catalog(overrides: Partial<Catalog>): Catalog {
  return { window_types: [], door_types: [], occupancies: [], materials: [], assemblies: [],
    ...overrides };
}

export function runProductTests() {
  const full = catalog({ products: [WASHTOWER] });

  assert(productFor(full, "PROD-LG-WKHC252HBA") === WASHTOWER, "A ref resolves to its product");
  assert(productFor(full, null) === null, "No ref is no product");
  assert(productFor(full, "") === null, "An empty ref is no product, not a lookup for ''");
  // A dangling ref renders as nothing, exactly like an absent one. The ERROR belongs to
  // `integrity.unknown_product_ref`; a panel that guessed here would print a half-filled
  // block for a product nobody defined.
  assert(productFor(full, "PROD-TYPO") === null, "A dangling ref resolves to null, not a stub");
  // An older engine's payload has no `products` list at all — the rows simply do not render.
  assert(productFor(catalog({}), "PROD-LG-WKHC252HBA") === null, "No catalog is no product");
  assert(productFor(undefined, "PROD-LG-WKHC252HBA") === null, "No model is no product");

  const model = {
    catalog: catalog({
      products: [WASHTOWER],
      materials: [material({ tag: "metal-dark-exterior", product_ref: "PROD-LG-WKHC252HBA" }),
                  material({ tag: "spf" })],
    }),
  } as unknown as Model;

  assert(productForMaterial(model, "metal-dark-exterior") === WASHTOWER,
    "A material's own product_ref is the derived inspectors' route in");
  assert(productForMaterial(model, "spf") === null,
    "A material naming no product is a specification, not a gap");
  assert(productForMaterial(model, "not-a-material") === null,
    "An unknown material tag resolves to null rather than throwing");
  assert(productForMaterial(model, null) === null, "A solid with no material has no product");
  assert(productForMaterial(null, "metal-dark-exterior") === null, "No model, no product");

  // A piece of an opening: boards take the type's product, hardware its own, trim its material.
  const withDoor = {
    catalog: catalog({
      products: [WASHTOWER],
      door_types: [{ tag: "DT-1", product_ref: "PROD-LG-WKHC252HBA" }] as never,
      materials: [material({ tag: "mdf-casing", product_ref: "PROD-LG-WKHC252HBA" })],
    }),
    door_casings: [{ uid: "CA1", material_ref: "mdf-casing" }],
  } as unknown as Model;
  const door = { is_door: true, type_ref: "DT-1", authored_product_parts: [
    { key: "hardware:0", name: "PROD-LG-WKHC252HBA", role: "hinge" }] } as never;
  assert(pieceProduct(withDoor, door, "frame:jamb-left").product === WASHTOWER,
    "A frame board takes the opening type's product");
  assert(pieceProduct(withDoor, door, "hardware:0").detail === "hinge",
    "A hardware piece reports its catalog role");
  assert(pieceProduct(withDoor, door, "casing:CA1:leg_left").product === WASHTOWER
    && pieceProduct(withDoor, door, "casing:CA1:leg_left").label === "Casing, leg left",
  "A casing leg takes its material's product and reads as the leg");
  assert(pieceProduct(withDoor, door, "exterior_trim:head").product === null,
    "Exterior casing is not the window's product");

  console.log("Product reference tests passed.");
}
