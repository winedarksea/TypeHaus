"""The milling schedule — what to cut, at what finished size, from what rough stock.

A *view*, exactly like ``wood_surfaces``: every quantity here is already billed somewhere
else, and every row says where (``also_in_framing`` / ``also_in_stair_finish`` /
``also_in_wood_surfaces``). Nothing sums it into the cost estimate a second time; see
``takeoff/wood_surfaces.py``'s header for the contract this follows.

What it adds that no existing section does is **rough stock**. Every other section reports
the finished quantity a house consumes. A sawyer is asked a different question: how much
tree, at what thickness, before the planer takes its cut. So each row carries the finished
piece (T x W x L), the nominal stock it comes out of (4/4, 8/4), and the rough board feet
*and* rough surface square feet the mill has to produce — both, because "$2 a square foot"
is ambiguous between the two the moment stock is thicker than 4/4.

The ``glue_up`` column is the flag that catches what the rest of the model cannot say: a
piece whose finished width is past the widest board the supply can produce, or whose
finished thickness is past the stock it is cut from. The first is a 24"-deep pantry shelf
against 18" boards; the second is a 6-1/8" post out of 8/4 elm, which is how the reference
house's tudor posts are really made.
"""

from __future__ import annotations

import math
from collections.abc import Mapping

from typehaus.model.millwork import MillworkStandard
from typehaus.resolve.model import ResolvedModel

_M_TO_IN = 39.37007874
_SQIN_PER_BF_IN = 144.0  # board foot = T(in) x W(in) x L(in) / 144

# --- rough-stock yield (AGENTS.md §1.3 — named, documented, not inline magic) -----------

#: Finished thickness a nominal quarter-stock thickness dresses down to, in inches. 4/4
#: rough (1") planes to 3/4"; 8/4 (2") to 1-1/2". The loss is two faces of planer skim plus
#: the cup a board dries with, and it is why a "1-inch" shelf is never an inch.
_FINISHED_FROM_QUARTERS: dict[int, float] = {4: 0.75, 5: 1.0, 6: 1.25, 8: 1.5, 12: 2.5}

#: Width lost to straight-lining one edge and jointing the other, in inches. Rough-milled
#: stock arrives with waney or sawn edges; a finished width is what survives both cuts.
_WIDTH_LOSS_IN = 0.75

#: Length allowance on every cut piece — defect (knot, check, sticker stain) plus the trim
#: cut at each end. The band a hardwood mill quotes is 10-15%; the midpoint is used, and a
#: schedule that wants the pessimistic end can read ``_LENGTH_ALLOWANCE`` here rather than
#: hunting a bare 1.125 in the arithmetic.
_LENGTH_ALLOWANCE = 0.125

#: Face width divided by coverage width, by milling profile. A T&G or shiplap board covers
#: less wall than it is wide — the tongue disappears into the next board's groove, the lap
#: under the next board's rabbet — so the mill saws more face than the wall shows. Derived
#: from the profiles this catalog actually runs: a 3-1/2" T&G face over 3-1/8" coverage, a
#: 5-1/2" shiplap face over 5" coverage. A flat profile covers exactly its own width.
_PROFILE_FACE_FACTOR: dict[str, float] = {
    "T&G": 3.5 / 3.125,
    "shiplap": 5.5 / 5.0,
}
_FLAT_FACE_FACTOR = 1.0

#: Order the schedule groups by. A mill reads it top to bottom as one day's work.
_USE_ORDER = ("window stool", "shelf", "stair tread", "stair landing deck", "floor",
              "wainscot", "wall liner", "timber post")


def hardwood_takeoff(model: ResolvedModel) -> list[dict[str, object]]:
    """The milling schedule: one row per (use, material, finished size, profile)."""
    materials = {material.tag: material for material in model.plan.library.materials}
    standard = next((el for el in model.plan.all_elements()
                     if isinstance(el, MillworkStandard)), None)
    max_board_width_in = (standard.max_board_width.inches
                          if standard is not None else None)

    rows: list[dict[str, object]] = []
    rows.extend(_stool_rows(model, materials, max_board_width_in))
    rows.extend(_shelf_rows(model, materials, max_board_width_in))
    rows.extend(_stair_rows(model, materials, standard, max_board_width_in))
    rows.extend(_coverage_rows(model, materials))
    rows.extend(_timber_rows(model, materials, max_board_width_in))
    rows.sort(key=_sort_key)
    return rows


def _sort_key(row: dict[str, object]) -> tuple[object, ...]:
    """Use, then recommended size, then profile — the schedule's stated order."""
    use = str(row["use"])
    order = _USE_ORDER.index(use) if use in _USE_ORDER else len(_USE_ORDER)
    quarters = row.get("nominal_quarters")
    return (order, use, -(quarters if isinstance(quarters, int) else 0),
            str(row.get("milling_profile") or ""), str(row.get("material")),
            -_as_float(row.get("finished_width_in")),
            -_as_float(row.get("finished_length_in")))


# --- reading an untyped BOM row -----------------------------------------------------------
#
# ``wood_surfaces`` rows are ``dict[str, object]`` — the BOM's own shape — so every value has
# to be narrowed before it is arithmetic. These two keep that narrowing in one place instead
# of scattering casts through the sources below.

def _as_float(value: object, default: float = 0.0) -> float:
    return float(value) if isinstance(value, (int, float)) else default


def _as_tags(value: object) -> list[str]:
    return [str(tag) for tag in value] if isinstance(value, (list, tuple)) else []


# --- the two row shapes ------------------------------------------------------------------

def _piece_row(use: str, material_ref: str, materials: Mapping[str, object], pieces: int,
               thickness_in: float, width_in: float, length_in: float,
               max_board_width_in: float | None, tags: list[str],
               also: Mapping[str, object], profile: str | None = None) -> dict[str, object]:
    """A discrete board cut to a finished size: a stool, a shelf, a tread, a post.

    ``laminations`` is what makes a post out of board stock: a piece finishing thicker than
    the stock it comes from is glued up from that many layers, and the rough quantity is
    that many times the piece. It is 1 for everything that is really a board.
    """
    material = materials.get(material_ref)
    quarters = getattr(material, "nominal_quarters", None) if material else None
    milling = profile or (getattr(material, "milling_profile", None) if material else None)
    rough_thickness_in = quarters / 4.0 if quarters else None
    # What one board of that stock actually yields dressed — NOT its rough thickness. An
    # 8/4 board is 2" in the rough and 1-1/2" out of the planer, so a 1-3/4" piece needs two
    # of them however close 2" sounds.
    yield_in = _FINISHED_FROM_QUARTERS.get(quarters, rough_thickness_in) if quarters else None
    laminations = (max(1, math.ceil(thickness_in / yield_in - 1e-9)) if yield_in else 1)
    rough_width_in = width_in + _WIDTH_LOSS_IN
    rough_length_in = length_in * (1.0 + _LENGTH_ALLOWANCE)
    rough_sf = pieces * laminations * rough_width_in * rough_length_in / _SQIN_PER_BF_IN
    rough_bf = rough_sf * rough_thickness_in if rough_thickness_in else None
    # The flag tests the ROUGH width, not the finished one. What the mill has to find is a
    # board it can straight-line and joint down to the finished face, so a 18" shelf out of
    # an 18" supply is not a single board — it is 3/4" short of one, and reporting it as
    # clear would send someone to the yard for stock that is not there.
    over_width = (max_board_width_in is not None
                  and rough_width_in > max_board_width_in + 1e-9)
    over_thickness = yield_in is not None and thickness_in > yield_in + 1e-9
    row: dict[str, object] = {
        "use": use,
        "species": getattr(material, "species", None) if material else None,
        "material": material_ref,
        "known": material is not None,
        "pieces": pieces,
        "finished_thickness_in": round(thickness_in, 3),
        "finished_width_in": round(width_in, 3),
        "finished_length_in": round(length_in, 2),
        "finished_board_feet": round(
            pieces * thickness_in * width_in * length_in / _SQIN_PER_BF_IN, 1),
        "nominal_quarters": quarters,
        "nominal_stock": f"{quarters}/4" if quarters else None,
        "laminations": laminations,
        "rough_width_in": round(rough_width_in, 3),
        "rough_surface_sqft": round(rough_sf, 1),
        "rough_board_feet": round(rough_bf, 1) if rough_bf is not None else None,
        "milling_profile": milling,
        "glue_up": bool(over_width or over_thickness),
        "glue_up_reason": (
            f'needs a {rough_width_in:.2f}" rough board; the supply is '
            f'{max_board_width_in:.2f}"' if over_width else
            f'{thickness_in:.2f}" finished is {laminations} laminations of '
            f'{yield_in:.2f}" stock' if over_thickness else None),
        "tags": sorted(set(tags)),
    }
    row.update(also)
    return row


def _coverage_row(use: str, source: Mapping[str, object], materials: Mapping[str, object],
                  also: Mapping[str, object]) -> dict[str, object]:
    """A material bought by the square foot of wall or floor it covers.

    Quantities come straight off the ``wood_surfaces`` row rather than being re-derived, so
    the two sections reconcile to the digit. Board feet likewise: ``stock_bf_per_sqft`` is
    the material's own coverage factor and already carries whatever the profile loses.
    Rough *surface* is the one number added here — the face area a mill actually saws,
    which exceeds the coverage area by the tongue or the lap.
    """
    material_ref = str(source["material"])
    material = materials.get(material_ref)
    milling = getattr(material, "milling_profile", None) if material else None
    order_sqft = _as_float(source.get("order_area_sqft"))
    face_factor = _PROFILE_FACE_FACTOR.get(milling or "", _FLAT_FACE_FACTOR)
    quarters = getattr(material, "nominal_quarters", None) if material else None
    row: dict[str, object] = {
        "use": use,
        "species": source.get("species"),
        "material": material_ref,
        "known": bool(source.get("known", True)),
        "pieces": None,
        "coverage_sqft": order_sqft,
        "net_coverage_sqft": source.get("net_area_sqft"),
        "nominal_quarters": quarters,
        "nominal_stock": f"{quarters}/4" if quarters else None,
        "laminations": 1,
        "rough_surface_sqft": round(order_sqft * face_factor, 1),
        "rough_board_feet": source.get("board_feet"),
        "milling_profile": milling,
        "glue_up": False,
        "glue_up_reason": None,
        "tags": _as_tags(source.get("tags")),
    }
    row.update(also)
    return row


# --- sources -----------------------------------------------------------------------------

def _stool_rows(model: ResolvedModel, materials: Mapping[str, object],
                max_board_width_in: float | None) -> list[dict[str, object]]:
    """One row per distinct finished stool size — the cut list, not 39 near-copies."""
    # (material, profile, thickness, depth, length) -> the window tags at that size
    groups: dict[tuple[str, str, float, float, float], list[str]] = {}
    for stool in model.window_stools:
        if stool.depth_m is None:
            continue  # UNKNOWN depth: nothing to cut to (#32), and the resolver said so
        key = (stool.material_ref, stool.profile,
               round(stool.thickness_m * _M_TO_IN, 3),
               round(stool.depth_m * _M_TO_IN, 3),
               round(stool.length_m * _M_TO_IN, 2))
        groups.setdefault(key, []).append(stool.window_ref)
    rows = []
    for (material_ref, profile, thickness, depth, length), tags in groups.items():
        rows.append(_piece_row(
            "window stool", material_ref, materials, len(tags), thickness, depth, length,
            max_board_width_in, tags, {"also_in_openings": False}, profile=profile))
    return rows


def _shelf_rows(model: ResolvedModel, materials: Mapping[str, object],
                max_board_width_in: float | None) -> list[dict[str, object]]:
    # (material, profile, thickness, depth, length) -> (board count, bank tags)
    groups: dict[tuple[str, str, float, float, float], tuple[int, list[str]]] = {}
    for bank in model.shelf_banks:
        for shelf in bank.shelves:
            if shelf.depth_m is None:
                continue
            key = (bank.material_ref, bank.profile,
                   round(bank.thickness_m * _M_TO_IN, 3),
                   round(shelf.depth_m * _M_TO_IN, 3),
                   round(shelf.width_m * _M_TO_IN, 2))
            count, tags = groups.get(key, (0, []))
            groups[key] = (count + shelf.count, tags + [bank.tag])
    rows = []
    for (material_ref, profile, thickness, depth, bay_width), (count, tags) in groups.items():
        # Grain runs the LONGER of the two plan dimensions, so the board's width is the
        # shorter one. Usually that is the depth and this is a no-op; where a shelf is
        # deeper than it is wide (RM-S-BATH1's alcove: 18-1/2" wide in a 30" deep carcass)
        # it is the difference between gluing up an 18-1/2" panel and a 30" one.
        width, length = sorted((depth, bay_width))
        rows.append(_piece_row(
            "shelf", material_ref, materials, count, thickness, width, length,
            max_board_width_in, tags, {}, profile=profile))
    return rows


def _stair_rows(model: ResolvedModel, materials: Mapping[str, object],
                standard: MillworkStandard | None,
                max_board_width_in: float | None) -> list[dict[str, object]]:
    """Treads and landing decks for the flights the house says are hardwood.

    Counted off the resolved members, exactly as ``takeoff/stairs.py`` does, so a stair with
    winders schedules the winder blanks it really generated. A winder bills at its wide end:
    that is the blank the shop cuts the taper from.
    """
    if standard is None or standard.tread_material_ref is None or not standard.tread_stairs:
        return []
    from typehaus.resolve.framing.profiles import cross_section

    material_ref = standard.tread_material_ref
    scope = set(standard.tread_stairs)
    also = {"also_in_framing": True, "also_in_stair_finish": True}
    tread_groups: dict[tuple[float, ...], tuple[int, list[str]]] = {}
    deck_groups: dict[tuple[float, ...], tuple[int, list[str]]] = {}
    for stair in model.stairs:
        if stair.tag not in scope:
            continue
        for member in stair.members:
            if member.category not in ("tread", "winder", "landing"):
                continue
            # A walking surface lies FLAT, so its thickness is the narrow face of its
            # section and the board's own width is the wide one, whichever order the
            # profile string happens to name them in ("deck 11x1.5" vs "tapered tread").
            section = cross_section(member.profile)
            thickness_in = min(section.width_m, section.depth_m) * _M_TO_IN
            board_in = max(section.width_m, section.depth_m) * _M_TO_IN
            key = (round(thickness_in, 3), round(board_in, 2),
                   round(member.length_m * _M_TO_IN, 2))
            groups = deck_groups if member.category == "landing" else tread_groups
            count, tags = groups.get(key, (0, []))
            groups[key] = (count + 1, tags + [stair.tag])
    rows = []
    for (thickness, run, width), (count, tags) in tread_groups.items():
        rows.append(_piece_row("stair tread", material_ref, materials, count,
                               thickness, run, width, max_board_width_in, tags, also))
    for (thickness, depth, length), (count, tags) in deck_groups.items():
        rows.append(_piece_row("stair landing deck", material_ref, materials, count,
                               thickness, depth, length, max_board_width_in, tags, also))
    return rows


#: ``wood_surfaces`` kinds this schedule re-presents, and the use each becomes.
_COVERAGE_KINDS = {
    "floor": ("floor", {"also_in_floor_finishes": True, "also_in_wood_surfaces": True}),
    "paneling": ("wainscot", {"also_in_wood_surfaces": True}),
    "override": ("wainscot", {"also_in_wood_surfaces": True}),
    "wall-assembly-finish": ("wall liner", {"also_in_envelope_layers": True,
                                            "also_in_wood_surfaces": True}),
}


def _coverage_rows(model: ResolvedModel,
                   materials: Mapping[str, object]) -> list[dict[str, object]]:
    from typehaus.takeoff.wood_surfaces import wood_surfaces_takeoff

    rows = []
    for source in wood_surfaces_takeoff(model):
        entry = _COVERAGE_KINDS.get(str(source.get("kind")))
        if entry is None or source.get("species") is None:
            # ``wood_surfaces`` carries every WallPaneling band, species or not, because a
            # tile splash is what it subtracts the liner behind. A milling schedule is only
            # about wood, and ``Material.species`` is the same admission test that section
            # uses for its other three sources.
            continue
        use, also = entry
        rows.append(_coverage_row(use, source, materials, also))
    return rows


def _timber_rows(model: ResolvedModel, materials: Mapping[str, object],
                 max_board_width_in: float | None) -> list[dict[str, object]]:
    """Species posts, scheduled as the glue-up blanks they are.

    ``wood_surfaces`` bills a timber as a section over an ordered length, which is the right
    answer for an estimator and the wrong one for a mill: a clear 6" hardwood timber would
    check badly drying, so it is laminated from board stock. ``_piece_row`` derives the
    lamination count from the material's own nominal stock, so the schedule says "five
    layers of 8/4" instead of "four timbers".
    """
    from typehaus.takeoff.wood_surfaces import wood_surfaces_takeoff

    rows = []
    for source in wood_surfaces_takeoff(model):
        if source.get("kind") != "timber":
            continue
        profile = str(source.get("profile") or "")
        try:
            width_in, depth_in = (float(part) for part in profile.split("x"))
        except ValueError:
            continue
        pieces = int(_as_float(source.get("count")))
        length_in = _as_float(source.get("order_length_ft")) * 12.0 / max(pieces, 1)
        rows.append(_piece_row(
            "timber post", str(source["material"]), materials, pieces,
            depth_in, width_in, length_in, max_board_width_in,
            _as_tags(source.get("tags")),
            {"also_in_structural_solids": True, "also_in_wood_surfaces": True}))
    return rows
