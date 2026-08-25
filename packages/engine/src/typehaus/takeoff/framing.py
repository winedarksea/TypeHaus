"""Sheet-good and framing takeoffs derived from resolved framing and authored assemblies."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

from shapely.geometry import Polygon

from typehaus.model.enums import LayerFunction
from typehaus.model.floors import FloorOpening, FloorSystem, Slab
from typehaus.model.spatial import Room
from typehaus.resolve.assembly_material import assembly_structure_material
from typehaus.resolve.ceiling_over import ceiling_decks_over
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.geometry import length, polygon_area, sub
from typehaus.resolve.model import ResolvedModel

_M2_TO_FT2 = 10.7639104167
_SHEET_AREA_FT2 = 32.0
_M_TO_FT = 3.280839895013123
_M3_TO_FT3 = 35.3146667215
_FT3_PER_CUBIC_YARD = 27.0

# Stock lengths a dimensional-lumber order is placed in; a member is charged to the shortest
# stock it can be cut from, and anything past the longest stock rounds up to the next 2 ft.
_STOCK_LENGTHS_FT = (8, 10, 12, 14, 16, 20)
# Trimmable floor-truss stock: 18' and 20', each trimmable up to 6" from each end (12"
# total), so an 18' truss covers 17'-0"-18'-0" and a 20' covers 19'-0"-20'-0".
_TRUSS_STOCK_FT = (18, 20)
_TRUSS_TRIM_ALLOWANCE_FT = 1.0
# ``[plies-]TxW`` — a leading built-up ply count is optional; a trailing name (LVL, rim,
# I-joist) is ignored. Board-foot rollup is only reported when this matches.
_PROFILE_RE = re.compile(r"^(?:(\d+)-)?(\d+(?:\.\d+)?)x(\d+(?:\.\d+)?)")


def _order_length_ft(length_ft: float, profile: str | None = None) -> int:
    """Round a cut length up to the stock length it would be purchased in.

    A ``floor_truss`` is fabricated, not milled dimensional lumber: it charges to the
    18'/20' trimmable ladder only within each stock's trim window; a length outside both
    windows (or a member clipped short by an opening) is fabricated to its own length and
    buckets at its own whole-foot ceiling rather than the next stock size up.
    """
    if profile is not None and cross_section(profile).shape == "floor_truss":
        for stock in _TRUSS_STOCK_FT:
            if stock - _TRUSS_TRIM_ALLOWANCE_FT - 1e-6 <= length_ft <= stock + 1e-6:
                return stock
        return int(math.ceil(length_ft - 1e-9))
    for stock in _STOCK_LENGTHS_FT:
        if length_ft <= stock + 1e-6:
            return stock
    return int(math.ceil(length_ft / 2.0)) * 2


#: A cut this short — half the shortest stock or less — is nested: several of them come out
#: of one stick, which is what a framer does with blocking, cripples and the 8" truss-wall
#: blocks. Charging each its own 8' stick is the failure this exists to stop: 1,660 blocks
#: at 8" is 1,107 lineal feet of wood ordered as 13,280. Anything longer than the threshold
#: cannot reliably pair with a second piece, so it still buys its own stick — the
#: conservative reading, and the one that leaves every long-member row exactly as it was.
_NEST_FRACTION = 0.5
#: Saw kerf lost at each cut when several pieces come off one stick. 1/8" — a framing blade.
_KERF_FT = 0.125 / 12.0


def _bucket_cut_lengths(lengths: list[float], profile: str | None) -> Counter:
    """The stock sticks one ``(profile, category, material)`` group is actually bought in.

    Long pieces bucket one-for-one, exactly as before. Short ones are packed first-fit-
    decreasing into the shortest stock, kerf included, so the order reflects the sticks a
    framer carries to the saw rather than one per cut. A fabricated member (a floor truss)
    is never nested: it is made to its length, and two of them do not come off one blank.
    """
    buckets: Counter = Counter()
    stock = _STOCK_LENGTHS_FT[0]
    fabricated = profile is not None and cross_section(profile).shape == "floor_truss"
    nestable: list[float] = []
    own_stick: list[float] = []
    for cut_ft in lengths:
        if not fabricated and cut_ft <= stock * _NEST_FRACTION + 1e-9:
            nestable.append(cut_ft)
        else:
            own_stick.append(cut_ft)
    for cut_ft in own_stick:
        buckets[_order_length_ft(cut_ft, profile)] += 1
    remaining: list[float] = []
    for cut_ft in sorted(nestable, reverse=True):
        need = cut_ft + _KERF_FT
        for index, left in enumerate(remaining):
            if left >= need - 1e-9:
                remaining[index] = left - need
                break
        else:
            remaining.append(stock - need)
    if remaining:
        buckets[stock] += len(remaining)
    return buckets


def _board_feet_per_ft(profile: str) -> float | None:
    """Nominal board-feet per lineal foot for a dimensional/built-up profile, or None."""
    match = _PROFILE_RE.match(profile)
    if match is None:
        return None
    plies = int(match.group(1)) if match.group(1) else 1
    thickness, width = float(match.group(2)), float(match.group(3))
    return plies * thickness * width / 12.0


def framing_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Full framing bill of materials: every resolved member grouped by size AND type.

    One row per (profile, category) — e.g. ``2x6`` / ``stud`` — carrying the piece count,
    the summed cut length, the stock length that count is ordered in, and the per-stock
    length buckets a framer or estimator actually buys against. Nothing is silently dropped:
    ``model.all_members()`` is the complete resolved member set (walls, floors, roofs,
    stairs, braces), so the pieces here reconcile 1:1 with what the 3D model frames.
    """
    cuts: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for member in model.all_members():
        cuts[(member.profile, member.category, member.material or "")].append(
            member.length_m * _M_TO_FT)

    rows: list[dict[str, object]] = []
    for (profile, category, material), lengths in sorted(cuts.items()):
        buckets = _bucket_cut_lengths(lengths, profile)
        order_ft_total = sum(length_ft * count for length_ft, count in buckets.items())
        bf_per_ft = _board_feet_per_ft(profile)
        rows.append({
            "profile": profile,
            "category": category,
            # The species/product the member is cut from, when the model knows it — a KDAT
            # outrigger and an SPF stud are both "2x4" and are not the same purchase. ``None``
            # for ordinary framing, which is what every row said before truss walls existed.
            "material": material or None,
            "pieces": len(lengths),
            "cut_length_ft": round(sum(lengths), 1),
            "order_length_ft": order_ft_total,
            "stock": [{"length_ft": length_ft, "count": count}
                      for length_ft, count in sorted(buckets.items())],
            "board_feet": round(bf_per_ft * order_ft_total, 1) if bf_per_ft else None,
        })
    return rows


def framing_bom_by_size(model: ResolvedModel) -> list[dict[str, object]]:
    """Roll the framing takeoff up to one row per (size, material), across member types.

    ``material`` splits the row only where the model actually knows one — a KDAT 2x4
    outrigger against an SPF 2x4 stud. Everything the model calls plain lumber carries
    ``None`` and lands in the single row it always did. The price join reads it as a
    qualifier (``cli/prices.QUALIFIED_KEY_FIELD``), so a house that says nothing about
    material still prices ``2x4`` at one rate and nothing changes for it.
    """
    by_size: dict[tuple[str, str], dict[str, object]] = {}
    for row in framing_takeoff(model):
        profile = str(row["profile"])
        material = row["material"]
        key = (profile, str(material or ""))
        size = by_size.get(key)
        if size is None:
            size = by_size[key] = {"profile": profile, "material": material, "pieces": 0,
                                   "cut_length_ft": 0.0, "order_length_ft": 0,
                                   "board_feet": 0.0, "types": []}
        size["pieces"] = int(size["pieces"]) + int(row["pieces"])
        size["cut_length_ft"] = round(
            float(size["cut_length_ft"]) + float(row["cut_length_ft"]), 1)
        size["order_length_ft"] = int(size["order_length_ft"]) + int(row["order_length_ft"])
        if row["board_feet"] is not None:
            size["board_feet"] = round(float(size["board_feet"]) + float(row["board_feet"]), 1)
        types = size["types"]
        assert isinstance(types, list)
        types.append(row["category"])
    for size in by_size.values():
        if not size["board_feet"]:
            size["board_feet"] = None
    return [by_size[key] for key in sorted(by_size)]


def structural_solids_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Bill the resolved solids the framing take-off cannot see — slabs, footings, pads,
    posts/columns, standalone beams, and the modeled accessories.

    ``framing_takeoff`` reconciles 1:1 with ``model.all_members()``, but a member is a stick
    of lumber; the concrete and the standalone structure are ``ResolvedSolid`` records. Both
    are needed for the BOM to account for everything the model emits. Volume is the plan
    outline (less its voids) extruded through the solid's elevation range, so concrete rows
    can be ordered in cubic yards.
    """
    Row = dict[str, object]
    groups: dict[tuple[str, str], Row] = {}
    for solid in model.solids:
        net_area_m2 = abs(polygon_area(list(solid.outline))) - sum(
            abs(polygon_area(list(void))) for void in solid.voids)
        volume_m3 = max(0.0, net_area_m2) * max(0.0, solid.z1_m - solid.z0_m)
        key = (solid.category, solid.assembly or "")
        row = groups.get(key)
        if row is None:
            # What the assembly's STRUCTURE layer is made of, so a price table can tell a
            # concrete solid from one that merely shares its category. "slab" covers both
            # SL-M-DECK (9" of cast concrete) and SL-SG-DECK (aluminium plank on wood
            # joists); "beam"/"column" cover LVL girders and 12" sonotube piers alike.
            # ``None`` for a solid with no assembly — that is "unknown", not "not concrete".
            row = groups[key] = {"category": solid.category, "assembly": solid.assembly,
                                 "structure_material": assembly_structure_material(
                                     model.plan, solid.assembly),
                                 "count": 0, "plan_area_sqft": 0.0, "volume_cuft": 0.0,
                                 "tags": []}
        row["count"] = int(row["count"]) + 1
        row["plan_area_sqft"] = float(row["plan_area_sqft"]) + max(0.0, net_area_m2) * _M2_TO_FT2
        row["volume_cuft"] = float(row["volume_cuft"]) + volume_m3 * _M3_TO_FT3
        tags = row["tags"]
        assert isinstance(tags, list)
        tags.append(solid.tag)

    rows: list[dict[str, object]] = []
    for key in sorted(groups):
        row = groups[key]
        volume_cuft = round(float(row["volume_cuft"]), 1)
        rows.append({**row, "plan_area_sqft": round(float(row["plan_area_sqft"]), 1),
                     "volume_cuft": volume_cuft,
                     "volume_cubic_yards": round(volume_cuft / _FT3_PER_CUBIC_YARD, 2),
                     "tags": sorted(row["tags"])})
    return rows


def construction_returns_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Bill the pre-framing ConstructionRule returns (#45), one row per take-off category.

    Each authored :class:`~typehaus.model.assembly.ConstructionRule` return
    (:class:`~typehaus.resolve.model.ResolvedConstructionReturn`) contributes its lineal run
    and count to the ``takeoff_category`` it declares — a PT sill plate, the sauna liner
    return, the foundation foam return, the masonry corner return. Rows reconcile 1:1 with
    ``model.construction_returns`` so the BOM matches the geometry the section/3D/IFC render.
    """
    Row = dict[str, object]
    groups: dict[tuple[str, str], Row] = {}
    for ret in model.construction_returns:
        category = ret.takeoff_category or ret.kind
        key = (category, ret.material_ref)
        row = groups.get(key)
        if row is None:
            row = groups[key] = {"category": category, "material": ret.material_ref,
                                 "kind": ret.kind, "count": 0, "length_m": 0.0}
        row["count"] = int(row["count"]) + 1
        row["length_m"] = float(row["length_m"]) + ret.length_m
    return [
        {"category": row["category"], "material": row["material"], "kind": row["kind"],
         "count": int(row["count"]),
         "length_ft": round(float(row["length_m"]) * _M_TO_FT, 1)}
        for row in (groups[key] for key in sorted(groups))
    ]


def sheet_goods_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """Return net-area and whole-sheet quantities for wall, roof, and subfloor sheathing.

    Every row is explicitly tied to its material and thickness; this makes a 4x8-sheet
    estimate auditable instead of silently grouping unlike panel products.
    """
    areas: dict[tuple[str, str, float], float] = defaultdict(float)
    openings_by_wall: dict[str, float] = defaultdict(float)
    for opening in model.openings:
        openings_by_wall[opening.host_wall] += opening.width_m * opening.height_m

    for wall in model.walls:
        exterior = any(layer.function == "cladding" for layer in wall.layers)
        if not exterior:
            continue
        wall_area = length(sub(wall.axis[1], wall.axis[0])) * (
            ((wall.top_z0_m or wall.z1_m) + (wall.top_z1_m or wall.z1_m)) / 2 - wall.z0_m
        ) - openings_by_wall[wall.tag]
        for layer in wall.layers:
            if layer.function == "sheathing":
                areas[("exterior wall", layer.material_ref, layer.thickness_m)] += max(0.0, wall_area)

    for roof in model.roofs:
        assembly = model.plan.library.resolve_assembly(roof.assembly)
        if assembly is None:
            continue
        for layer in assembly.layers:
            if layer.function is LayerFunction.SHEATHING:
                areas[("roof", layer.material_ref, layer.thickness.meters)] += roof.surface_area_m2

    for storey in model.plan.storeys:
        for system in model.plan.storey_elements(storey.tag):
            if not isinstance(system, FloorSystem) or system.subfloor is None:
                continue
            floor = next((item for item in model.floors if item.tag == system.tag), None)
            if floor is None or not floor.members:
                continue
            points = [point for member in floor.members for point in (member.p0, member.p1)]
            gross = (max(point[0] for point in points) - min(point[0] for point in points)) * (
                max(point[1] for point in points) - min(point[1] for point in points)
            )
            openings = sum(abs(polygon_area([point.xy_m for point in opening.outline]))
                           for opening in model.plan.storey_elements(storey.tag)
                           if isinstance(opening, FloorOpening) and opening.tag in system.openings)
            areas[("subfloor", system.subfloor.material_ref, system.subfloor.thickness.meters)] += gross - openings
            # ``FloorSystem.ceiling_below`` is the same kind of sheet on the underside of
            # the same deck, and was simply never read here — a whole storey of ceiling
            # drywall silently absent from the order.
            for layer in system.ceiling_below:
                areas[("ceiling", layer.material_ref, layer.thickness.meters)] += gross - openings

    # A structural Slab's own ceiling_below (a room sitting under a cast deck) bills the
    # same way, net of its floor openings — meaningless, and left unauthored, on a
    # slab-on-grade with no occupied space below it.
    for storey in model.plan.storeys:
        for slab in model.plan.storey_elements(storey.tag):
            if (not isinstance(slab, Slab) or not slab.ceiling_below
                    or slab.datum != "structure"):
                continue
            net = max(0.0, abs(polygon_area([point.xy_m for point in slab.outline])) - sum(
                abs(polygon_area([point.xy_m for point in opening.outline]))
                for opening in model.plan.storey_elements(storey.tag)
                if isinstance(opening, FloorOpening) and opening.tag in slab.openings))
            for layer in slab.ceiling_below:
                areas[("ceiling", layer.material_ref, layer.thickness.meters)] += net

    # A room's own ``ceiling_lining`` override replaces the covering deck's generic
    # billing over just its own clear face — the same clip-and-rebill ``FinishZone``/
    # ``WallPaneling.replaces_wall_finish`` apply to a base billing they only partly cover.
    for room in model.rooms:
        plan_room = model.plan.by_tag(room.tag)
        if not isinstance(plan_room, Room) or not plan_room.ceiling_lining:
            continue
        face = Polygon(room.clear_face)
        for _deck_storey, deck in ceiling_decks_over(model.plan, room.storey, face):
            for layer in deck.ceiling_below:
                areas[("ceiling", layer.material_ref, layer.thickness.meters)] -= room.area_m2
        for layer in plan_room.ceiling_lining:
            areas[("ceiling", layer.material_ref, layer.thickness.meters)] += room.area_m2

    return [
        {"scope": scope, "material": material, "thickness_in": round(thickness / 0.0254, 3),
         "net_area_sqft": round(area * _M2_TO_FT2, 1),
         "sheets_4x8": math.ceil(area * _M2_TO_FT2 / _SHEET_AREA_FT2)}
        for (scope, material, thickness), area in sorted(areas.items())
    ]
