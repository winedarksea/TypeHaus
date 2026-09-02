// How a resolved solid's category is spelled for a reader.
//
// Split out of three/solidMaterials.ts, which is about how a solid is *shaded*: this is a
// naming table with no geometry in it, and the Inspector that needs it (DerivedInspectors) is
// on the 2D side, where importing the material module dragged all of three.js into the entry
// bundle for the sake of a string lookup.

// Solid category → what a person calls it. The raw category reads fine for `slab` and badly
// for anything with an underscore — worst of all for a family name: "pipe accessory" is true
// of a shutoff, a backflow preventer and a can of foam alike, telling a reader nothing about
// the thing they just clicked. Categories are per-device (see SOLID_CATEGORY_TRADE above);
// this map gives the rest of them sentence case too.
//
// Anything absent falls back to the category with its underscores opened out, so a new
// category is readable on the day it lands and gets a proper name when someone has one.
const SOLID_CATEGORY_LABEL: Record<string, string> = {
  main_shutoff: "Main shutoff valve",
  shutoff: "Isolation valve",
  backflow_preventer: "Backflow preventer",
  vacuum_breaker: "Vacuum breaker",
  water_hammer_arrestor: "Water-hammer arrestor",
  ro_stub: "RO tap provision (capped)",
  penetration_seal: "Envelope penetration seal",
  pipe_drain: "Waste pipe",
  pipe_vent: "Vent pipe",
  pipe_water_hot: "Hot water pipe",
  pipe_water_cold: "Cold water pipe",
  pipe_gas: "Gas pipe",
  pipe_radon: "Radon pipe",
  pipe_sleeve: "Cast-in sleeve",
  conduit_power: "Power conduit",
  conduit_data: "Data conduit",
  duct_supply: "Supply duct",
  duct_return: "Return duct",
  duct_exhaust: "Exhaust duct",
  duct_dryer: "Dryer exhaust duct",
  duct_transfer: "Transfer opening",
  duct_outdoor_air: "Outdoor-air duct",
  drain_tile: "Drain tile",
  french_drain: "French drain",
  drywell: "Drywell",
  downspout: "Downspout",
  sump: "Sump pit",
  thermal_break: "Thermal break",
  bug_screen: "Rainscreen base closure",
  glazing_trim: "Glazing trim",
  window_trim: "Window casing",
  opening_frame: "Opening frame",
  ridge_cap: "Ridge cap",
  corner_trim: "Corner trim",
};

export function solidCategoryLabel(category: string | null | undefined): string {
  if (!category) return "Solid";
  const key = category.trim().toLowerCase();
  const known = SOLID_CATEGORY_LABEL[key];
  if (known) return known;
  const opened = key.replace(/_/g, " ");
  return opened.charAt(0).toUpperCase() + opened.slice(1);
}
