"""What a bid package for one trade looks like: which sections it holds, in what order, how
each row is written, and which drawings it points at.

Judgment, authored once. A recipe never invents a quantity — every number is a BOM row's
own — it only decides how a sub wants to read it: lumber by size with a piece count and
the stock it is cut from, sheet goods by the sheet, concrete by the pour in yards, pipe by
system and size in feet with fittings by the piece.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from typehaus.takeoff.labels import _fraction_in

Row = Mapping[str, Any]


def _lumber(row: Row) -> str:
    pieces = row.get("pieces")
    cut = row.get("cut_length_ft")
    return f"{pieces} pcs, {cut} LF cut" if pieces is not None and cut is not None else ""


def _sheets(row: Row) -> str:
    sheets = row.get("sheets")
    area = row.get("net_area_sqft")
    size = row.get("sheet") or "4x8"
    return f"{sheets} sheets {size} over {area} SF net" if sheets is not None else ""


def _sheet_unit(row: Row) -> str:
    return f"sheets {row.get('sheet') or '4x8'}"


def _solid(row: Row) -> str:
    count = row.get("count")
    area = row.get("plan_area_sqft")
    return f"{count} placed, {area} SF plan" if count is not None else ""


def _bar(row: Row) -> str:
    """Pieces and cut length, laps and hooks in (decision #75): what a fabricator ships."""
    length, pieces = row.get("length_ft"), row.get("pieces")
    if length is None:
        return ""
    return (f"{pieces} pc, {length} LF cut incl. {row.get('lap_length_ft')} LF laps + "
            f"{row.get('hook_length_ft')} LF hooks")


def _runs(row: Row) -> str:
    runs = row.get("runs")
    return f"{runs} run(s)" if runs is not None else ""


def _members(row: Row) -> str:
    beddings = row.get("beddings")
    return f"{beddings} bed(s)" if beddings is not None else ""


def _opening(row: Row) -> str:
    width, height = row.get("width_in"), row.get("height_in")
    return (f"{_fraction_in(width)} x {_fraction_in(height)}"
            if width is not None and height is not None else "")


def _railing(row: Row) -> str:
    posts, brackets = row.get("post_count"), row.get("bracket_count")
    return f"{posts} post(s), {brackets} bracket(s)" if posts is not None else ""


@dataclass(frozen=True)
class Shape:
    """How one estimate section reads in a package: its heading, its unit, and the
    per-row detail a sub wants beside the quantity."""

    heading: str
    detail: Callable[[Row], str] | None = None
    unit: str | None = None  # override the estimate unit's spelling
    unit_of: Callable[[Row], str] | None = None  # ...or spell it per row


SHAPES: dict[str, Shape] = {
    "framing": Shape("Lumber and engineered wood, by size", _lumber, "LF ordered"),
    "sheet_goods": Shape("Sheet goods, by the sheet", _sheets, unit_of=_sheet_unit),
    "hardware": Shape("Connectors and fasteners, by part"),
    "concrete": Shape("Pours, by the yard", _solid),
    "site": Shape("Site solids: stormwater, planting and aggregate", _solid),
    "solids": Shape("Other structural solids", _solid),
    "reinforcement": Shape("Reinforcing steel, by bar", _bar, "lb"),
    "wall_structure": Shape("Wall structure", None),
    "footing_bedding": Shape("Footing bedding", _members, "cy"),
    "pipe_runs": Shape("Pipe, by system and size", _runs, "LF"),
    "pipe_fittings": Shape("Pipe fittings, by the piece"),
    "sleeves": Shape("Cast-in sleeves, by the piece"),
    "plumbing_specialties": Shape("Valves and specialties, by model"),
    "pipe_insulation": Shape("Pipe insulation", _runs, "LF"),
    "install_parts": Shape("Installation kits, by the piece"),
    "ducts": Shape("Ducts, by system and size", _runs, "LF"),
    "duct_fittings": Shape("Duct fittings, by the piece"),
    "duct_insulation": Shape("Duct insulation", _runs, "LF"),
    "placeables": Shape("Fixtures, devices and equipment, by model"),
    "floor_heat": Shape("Radiant floor heat cable"),
    "conduit": Shape("Conduit, by trade size", _runs, "LF"),
    "conductors": Shape("Conductors"),
    "data_raceways": Shape("Data raceways", _runs, "LF"),
    "solar_modules": Shape("PV modules, by the module", None),
    "freeze_protection": Shape("Heat trace"),
    "openings": Shape("Windows and doors, by product", _opening, "ea"),
    "envelope_layers": Shape("Assembly layers, by material", None, "SF net"),
    "edge_trim": Shape("Trim and flashing, by profile", None, "LF"),
    "member_protection": Shape("Member protection tape", None, "LF"),
    "construction_returns": Shape("Construction returns", None, "LF"),
    "sill_gaskets": Shape("Sill gaskets", None, "LF"),
    "drainage": Shape("Stormwater runs", None, "LF"),
    "floor_finishes": Shape("Floor finishes, by area", None, "SF ordered"),
    "wood_surfaces": Shape("Wood surfaces", None, "SF ordered"),
    "shelving": Shape("Purchased shelving", None, "SF ordered"),
    "countertops": Shape("Countertops", None, "SF"),
    "railings": Shape("Guards and handrails", _railing, "LF"),
    "allowances": Shape("Owner allowances"),
    "timber": Shape("Timber", _solid),
    "furnishings": Shape("Furnishings"),
}


@dataclass(frozen=True)
class Recipe:
    """One trade's package: what to say first, which sections lead, which sheets matter."""

    title: str
    intro: str
    #: Sections in the order the sub reads them; anything else follows in estimate order.
    section_order: tuple[str, ...] = ()
    #: Sheet numbers to point at, filtered against the sheets the house actually draws.
    sheets: tuple[str, ...] = ()
    #: Whether the package lists element tags per line (a framer wants them; a painter does
    #: not) — Appendix A.
    tags_appendix: bool = True


GENERIC_RECIPE = Recipe(
    title="Bid package",
    intro="Quantities are taken off the model and are net of waste unless a line says "
          "otherwise. This is a request for quote: price the scope as you would install "
          "it, and say where your count differs.",
)

RECIPES: dict[str, Recipe] = {
    "general": Recipe("General conditions", "Permits, insurance, testing, dumpsters and "
                      "scaffolding — the owner's own lines, listed for the record.",
                      ("allowances",), ("G-001",), tags_appendix=False),
    "earth": Recipe("Earthwork", "Excavation, backfill, grading and the stone placed under the "
                    "footings, with the perimeter tile bedded in it.",
                    ("footing_bedding", "envelope_layers", "allowances"), ("S-100", "C-100")),
    "drainage": Recipe("Drainage", "The stormwater run from the gutter to daylight: leaders, "
                       "tile, drywells and the sump.", ("drainage", "site", "allowances"),
                       ("S-100", "P-101")),
    "landscaping": Recipe("Landscaping", "Final grade, sod, rootzone and the segmental "
                          "retaining block.", ("envelope_layers", "wall_structure", "site"),
                          ("C-100",)),
    "concrete": Recipe("Concrete", "Every pour, by the yard: footings, foundation walls, slabs, "
                       "the cast columns, the reinforcing steel and the cast-in anchors and "
                       "sleeves.", ("concrete", "wall_structure", "reinforcement", "hardware",
                                    "envelope_layers", "allowances"),
                       ("S-100", "S-101", "A-301")),
    "masonry": Recipe("Masonry", "Brick veneer and the fireplace wythe, by the yard.",
                      ("wall_structure", "construction_returns"), ("A-201", "A-301")),
    "framing": Recipe("Framing", "Sticks by size with piece counts, sheet goods by the sheet, "
                      "the structural hardware, the decks, and the tape on every member "
                      "top. Trusses and engineered wood are called out by the profile.",
                      ("framing", "sheet_goods", "hardware", "solids", "timber",
                       "member_protection", "construction_returns", "sill_gaskets",
                       "envelope_layers", "wall_structure"),
                      ("S-100", "S-101", "S-201", "A-301", "A-401")),
    "stairs": Recipe("Stairs and guards", "Stringers, treads, risers and newels, and every "
                     "guard and handrail.", ("framing", "railings", "solids"),
                     ("A-301", "A-401")),
    "roofing": Recipe("Roofing", "Standing seam, underlayment, drip and ridge, and the snow "
                      "retention and clamps fastened into the skin.",
                      ("envelope_layers", "edge_trim", "hardware", "allowances"),
                      ("A-201", "A-401")),
    "siding": Recipe("Siding and trim", "Cladding, the WRB and furring behind it, corners, "
                     "fascia, the eave soffit and the closures.",
                     ("envelope_layers", "edge_trim", "framing", "hardware", "sheet_goods",
                      "wall_structure", "solids", "allowances"),
                     ("A-201", "A-401")),
    "insulation": Recipe("Insulation and air sealing", "Spray foam, batts, blown fill, rigid "
                         "board and the rim foam, plus the air-sealing allowance.",
                         ("envelope_layers", "construction_returns", "sheet_goods", "solids",
                          "allowances"), ("A-301", "A-401")),
    "drywall": Recipe("Drywall", "Board by the sheet and the area behind it, resilient "
                      "channel, and the dropped soffit boxes.",
                      ("sheet_goods", "envelope_layers", "construction_returns", "solids"),
                      ("A-101",)),
    "paint": Recipe("Paint", "Wall and ceiling coats by area, the foundation coating, and the "
                    "trim allowance.", ("envelope_layers", "allowances"), ("A-101",)),
    "openings": Recipe("Windows and doors", "Every product by type and size, the pocket "
                       "frames, and the hardware allowances.",
                       ("openings", "hardware", "solids", "allowances"), ("A-601",)),
    "tile": Recipe("Tile", "Floor and wall tile by area with the uncoupling membrane.",
                   ("floor_finishes", "allowances"), ("A-101",)),
    "flooring": Recipe("Flooring", "Every finish floor by ordered area, with its underlayment.",
                       ("floor_finishes", "allowances"), ("A-101",)),
    "millwork": Recipe("Millwork and casework", "Casework and built-ins by unit, tops by area, "
                       "paneling and interior trim.",
                       ("placeables", "countertops", "shelving", "wood_surfaces", "envelope_layers",
                        "allowances"), ("A-101", "A-501")),
    "plumbing": Recipe("Plumbing", "Pipe by system and size in feet, fittings by the piece, "
                       "the sleeves that go in before the pour, every fixture by model, and "
                       "the water heater.",
                       ("pipe_runs", "pipe_fittings", "sleeves", "plumbing_specialties",
                        "pipe_insulation", "install_parts", "placeables", "solids",
                        "allowances"), ("P-101", "P-201")),
    "electrical": Recipe("Electrical", "Devices and luminaires by model, conduit and "
                         "conductors by the foot, the PV array with its inverter and battery, "
                         "and the appliance control kits.",
                         ("placeables", "conduit", "conductors", "data_raceways",
                          "solar_modules", "hardware", "install_parts", "freeze_protection",
                          "solids", "allowances"), ("E-101", "E-601", "E-602")),
    "mechanical": Recipe("Mechanical", "Ducts by system and size in feet, fittings and "
                         "insulation, every register and the equipment by model, and the "
                         "radiant floor cable.",
                         ("ducts", "duct_fittings", "duct_insulation", "placeables",
                          "floor_heat", "hardware", "solids", "pipe_runs", "allowances"),
                         ("M-101", "M-201")),
    "furniture": Recipe("Furniture and appliances", "Loose furniture and appliances by model; "
                        "the porch enclosure panels.", ("placeables", "furnishings",
                                                        "allowances"),
                        (), tags_appendix=False),
}


def recipe_for(trade: str) -> Recipe:
    return RECIPES.get(trade, GENERIC_RECIPE)


def shape_for(section: str) -> Shape:
    return SHAPES.get(section, Shape(section.replace("_", " ").capitalize()))


#: Every recipe and shape names things that exist. Checked at import so a typo in a section
#: name fails here rather than silently dropping a section from a package.
def _validate(sections: tuple[str, ...] = ()) -> None:
    if not sections:
        from typehaus.cli.prices import ESTIMATE_PLANS

        sections = tuple(plan[0] for plan in ESTIMATE_PLANS)
    unknown = sorted({s for r in RECIPES.values() for s in r.section_order} - set(sections))
    unknown += sorted(set(SHAPES) - set(sections))
    if unknown:
        raise ValueError(f"bid recipes name sections that do not exist: {unknown}")
