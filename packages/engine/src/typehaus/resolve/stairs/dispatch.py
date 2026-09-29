"""Stair validation + layout dispatch — the package's public entry point.

``_resolve_stair`` checks every authored reference and the geometry budget, then hands
member generation to the layout module (straight / u_split / winder) and runs the
structural guard passes from :mod:`typehaus.resolve.stairs.bearing`.
"""

from __future__ import annotations

import math
from dataclasses import replace

from typehaus.findings import Finding
from typehaus.findings import element_error as _error
from typehaus.model.floors import FloorOpening, FloorSystem, Slab
from typehaus.model.spatial import Stair
from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember, ResolvedModel, ResolvedStair
from typehaus.resolve.stairs.bearing import _bear_stair_on_walls, _clip_stair_to_subfloor
from typehaus.resolve.stairs.common import (
    _DEFAULT_NOSING_DEPTH_M,
    _DEFAULT_TREAD_DEPTH_M,
    _MAX_NOSING_DEPTH_M,
    _MAX_RISER_M,
    _MIN_LANDING_DEPTH_M,
    _MIN_NOSING_DEPTH_M,
    _MIN_TREAD_M,
    _WELL_PARTITION_THICKNESS_M,
    _tread_thickness,
)
from typehaus.resolve.stairs.finish import (
    landing_nosing_parts,
    lower_stair_substrates,
    set_landing_stack,
    stair_finish_parts,
    stairhead_nosing_part,
)
from typehaus.resolve.stairs.straight import _straight_stair_members
from typehaus.resolve.stairs.u_split import _u_split_landing_members
from typehaus.resolve.stairs.winder import _winder_stair_members


def _resolve_stair(
    model: ResolvedModel, stair: Stair, storey: str
) -> tuple[ResolvedStair | None, list[Finding]]:
    """Resolve an authored stair layout inside its explicitly-owned opening."""
    source = model.plan.storey(stair.from_storey)
    target = model.plan.storey(stair.to_storey)
    if source is None or target is None:
        return None, [_error("integrity.stair_storey", f"stair {stair.tag} references an "
                             "unknown storey", stair.tag)]
    if (stair.base_elevation is None) != (stair.top_elevation is None):
        return None, [_error("integrity.stair_rise", f"stair {stair.tag} authors only one of "
                             "base_elevation/top_elevation; a flight that states its own "
                             "rise must state both ends of it", stair.tag)]
    base, top = stair.base_elevation, stair.top_elevation
    explicit = base is not None and top is not None
    z0 = base.meters if base is not None else source.elevation.meters
    z_top = top.meters if top is not None else target.elevation.meters
    rise = z_top - z0
    if rise <= 0:
        return None, [_error("integrity.stair_rise", f"stair {stair.tag} does not rise to "
                             "its destination", stair.tag)]
    # ``stringer_spacing`` lays out every raked carriage: a straight flight's (or its box
    # tiers'), each U flight's, and a winder's straight flight. Landing joists and winder
    # boxes keep their own rules. ``tread_thickness`` is honoured by every layout.
    if stair.stringer_spacing is not None and stair.stringer_spacing.meters <= 0:
        return None, [_error("integrity.stair_geometry", f"stair {stair.tag} "
                             "stringer_spacing must be positive", stair.tag)]
    if stair.tread_thickness is not None and stair.tread_thickness.meters <= 0:
        return None, [_error("integrity.stair_geometry", f"stair {stair.tag} "
                             "tread_thickness must be positive", stair.tag)]
    finish_thickness_m = 0.0
    if stair.finish_material is not None:
        finish = next((material for material in model.plan.library.materials
                       if material.tag == stair.finish_material), None)
        depth_in = getattr(finish, "finish_thickness_in", None)
        if depth_in is None or depth_in <= 0:
            return None, [_error("integrity.stair_finish", f"stair {stair.tag} finish "
                                 f"{stair.finish_material!r} needs a positive installed "
                                 "finish_thickness_in", stair.tag)]
        finish_thickness_m = inch(depth_in).meters

    if stair.floor_opening is None:
        # A run that passes through no floor — a step-down within one storey. There is no
        # hole to bound it, so the flight bounds itself: its footprint is derived below,
        # once the riser count is known, and it must state where it starts.
        if stair.start is None:
            return None, [_error("integrity.stair_opening", f"stair {stair.tag} has no "
                                 "floor_opening, so it must author start", stair.tag)]
        if not explicit:
            return None, [_error("integrity.stair_rise", f"stair {stair.tag} has no "
                                 "floor_opening, so its rise cannot come from a pair of "
                                 "storey elevations: author base_elevation/top_elevation",
                                 stair.tag)]
        if stair.layout != "straight":
            return None, [_error("integrity.stair_layout", f"stair {stair.tag} has no "
                                 "floor_opening; only a straight flight is bounded without "
                                 "one", stair.tag)]
        opening = None
        outline: list[tuple[float, float]] = []
        xs = ys = []
    else:
        opening = model.plan.by_tag(stair.floor_opening)
        if not isinstance(opening, FloorOpening):
            return None, [_error("integrity.stair_opening", f"stair {stair.tag} references "
                                 f"missing FloorOpening {stair.floor_opening!r}", stair.tag)]
        if stair.to_storey != _element_storey(model, opening.tag):
            return None, [_error("integrity.stair_opening", f"stair {stair.tag} must use an "
                                 "opening on its destination storey", stair.tag)]
        # The destination deck (wood FloorSystem or concrete Slab) must own the opening.
        # Asked of *any* deck on that storey, not of the first one found: a storey may carry
        # several (catlin's main floor is two I-joist bays and a concrete band, plus its
        # breezeway deck), and "the first element that is a FloorSystem or a Slab" would
        # depend on authoring order rather than on which deck the hole is in.
        if not any(isinstance(element, (FloorSystem, Slab))
                   and opening.tag in element.openings
                   for element in model.plan.storey_elements(stair.to_storey)):
            return None, [_error("integrity.stair_opening", f"stair {stair.tag} opening must "
                                 "be owned by the destination FloorSystem/Slab", stair.tag)]
        outline = [point.xy_m for point in opening.outline]
        if len(outline) < 3:
            return None, [_error("integrity.stair_opening", f"stair {stair.tag} opening has "
                                 "no usable outline", stair.tag)]
        xs, ys = [point[0] for point in outline], [point[1] for point in outline]
        along_x = stair.run_direction == "x"
        width = (max(ys) - min(ys)) if along_x else (max(xs) - min(xs))
        if width + 1e-9 < stair.width.meters:
            return None, [_error("integrity.stair_width", f"stair {stair.tag} is wider than "
                                 "its floor opening", stair.tag)]
    along_x = stair.run_direction == "x"
    run = (0.0 if opening is None else
           ((max(xs) - min(xs)) if along_x else (max(ys) - min(ys))))
    if stair.layout not in {"straight", "u_split_landing", "u_level_landing",
                            "right_angle_winder"}:
        return None, [_error("integrity.stair_layout", f"stair {stair.tag} has unknown layout "
                             f"{stair.layout!r}", stair.tag)]
    if stair.layout == "right_angle_winder":
        if stair.turn_direction not in {"left", "right"}:
            return None, [_error("integrity.stair_turn", f"stair {stair.tag} needs a left or "
                                 "right turn direction", stair.tag)]
        if stair.winder_count < 3:
            return None, [_error("integrity.stair_winders", f"stair {stair.tag} needs at least "
                                 "three winders for a quarter turn", stair.tag)]
    elif stair.winder_count:
        return None, [_error("integrity.stair_winders", f"stair {stair.tag} only accepts "
                             "winders in right_angle_winder layout", stair.tag)]
    if (stair.layout in {"u_split_landing", "u_level_landing"}
            and stair.turn_direction is not None
            and stair.turn_direction not in {"left", "right"}):
        return None, [_error("integrity.stair_turn", f"stair {stair.tag} has unknown turn "
                             f"direction {stair.turn_direction!r}", stair.tag)]
    # ``bearing_refs`` grants bearing permission, so a tag naming no wall on the storey the
    # flight springs from would silently grant nothing — that is an authoring error.
    missing_bearing = [tag for tag in stair.bearing_refs
                       if not any(wall.tag == tag and wall.storey == stair.from_storey
                                  for wall in model.walls)]
    if missing_bearing:
        return None, [_error("integrity.stair_bearing", f"stair {stair.tag} references "
                             "missing bearing wall(s) on "
                             f"{stair.from_storey}: {', '.join(missing_bearing)}", stair.tag)]
    physical_tread_m = (stair.tread_depth.meters if stair.tread_depth is not None
                        else _DEFAULT_TREAD_DEPTH_M)
    nosing_m = (stair.nosing_depth.meters if stair.nosing_depth is not None
                else _DEFAULT_NOSING_DEPTH_M)
    going_m = physical_tread_m - nosing_m
    if nosing_m < -1e-9 or (nosing_m > 1e-9 and not
                            _MIN_NOSING_DEPTH_M - 1e-9 <= nosing_m <= _MAX_NOSING_DEPTH_M + 1e-9):
        return None, [_error("integrity.stair_nosing", f"stair {stair.tag} nosing must be "
                             "0 or 3/4\"–1 1/4\"", stair.tag)]
    if physical_tread_m + 1e-9 < inch(11).meters and nosing_m <= 1e-9:
        return None, [_error("integrity.stair_nosing", f"stair {stair.tag} needs a nosing "
                             "when its physical tread is under 11\"", stair.tag)]
    if going_m + 1e-9 < _MIN_TREAD_M:
        return None, [_error("integrity.stair_geometry", f"stair {stair.tag} has "
                             f"{going_m / 0.0254:.1f}\" going; IRC R311.7 requires 10\"",
                             stair.tag)]
    risers = math.ceil(rise / _MAX_RISER_M)
    treads = max(0, risers - 1)
    straight_treads = treads - stair.winder_count
    # Turn-landing depth (in the run direction) for the U-stair. Unset reserves one stair
    # width; an authored value is honoured down to the IRC R311.7.6 direction-of-travel
    # minimum (see ``_MIN_LANDING_DEPTH_M``), which is 36" and *not* the stair width.
    landing_depth_m = (max(stair.landing_depth.meters, _MIN_LANDING_DEPTH_M)
                       if stair.landing_depth is not None else stair.width.meters)
    # A winder turn consumes a square whose side is the stair width. The remaining treads
    # must still meet the 10 in. minimum on their straight walking line.
    if stair.layout in {"u_split_landing", "u_level_landing"}:
        # The paired decks consume one riser on arrival; a split landing also consumes
        # one between them. The destination deck consumes the final riser.
        flight_treads = max(0, risers - (2 if stair.layout == "u_level_landing" else 3))
        lower_treads = (flight_treads + 1) // 2
        straight_run = run - landing_depth_m
        available_going = straight_run / lower_treads if lower_treads else 0.0
    else:
        straight_run = run - stair.width.meters if stair.layout == "right_angle_winder" else run
        available_going = straight_run / straight_treads if straight_treads else 0.0
    # A flight with no opening has no run budget to blow: nothing bounds it overhead, so its
    # footprint is whatever its own risers and going come to, derived below.
    if opening is not None and available_going + 1e-9 < going_m:
        return None, [_error("integrity.stair_geometry", f"stair {stair.tag} needs {risers} "
                             "risers but its opening only permits "
                             f"{available_going / 0.0254:.1f}\" "
                             f"going (needs {going_m / 0.0254:.1f}\")", stair.tag)]
    riser = rise / risers
    if opening is not None and not _stair_fits_opening(
            stair, min(xs), max(xs), min(ys), max(ys), going_m, risers, landing_depth_m):
        return None, [_error("integrity.stair_opening", f"stair {stair.tag} extends outside "
                             f"floor opening {opening.tag!r}", stair.tag)]
    if opening is not None:
        origin_x, origin_y = min(xs), min(ys)
    else:
        # ``start`` is required without an opening — the guard above returns an integrity
        # error when it is missing — but that is two branches back from here.
        assert stair.start is not None
        origin_x, origin_y = stair.start.xy_m
    members = _stair_members(stair, origin_x, origin_y, z0, risers, riser,
                             going_m, physical_tread_m, nosing_m, landing_depth_m,
                             _deck_underside(model, stair, opening), finish_thickness_m)
    members = lower_stair_substrates(members, finish_thickness_m)
    deck = _landing_deck(model, stair)
    if deck is not None:
        if deck.stack_thickness_m > _tread_thickness(stair) + 1e-9:
            return None, [_error("integrity.stair_landing_deck", f"stair {stair.tag}'s landing "
                                 "stack is thicker than its treads", stair.tag)]
        members = set_landing_stack(members, deck.stack_thickness_m, _tread_thickness(stair))
    if opening is None:
        outline = _flight_footprint(stair, going_m, risers)
    # Structural guards: the flight never drops below the subfloor it springs from (so a
    # U-stair well partition cannot poke through the foundation), and every flight is
    # borne on the walls beside it — posted down wherever none reaches.
    members = _clip_stair_to_subfloor(members, z0)
    members = _bear_stair_on_walls(model, stair, members, z0)
    surfaces = _finish_materials(model, stair)
    members = _in_stair_material(stair, members, surfaces)
    finish_parts = (stair_finish_parts(members, stair.finish_material,
                                      finish_thickness_m, _tread_thickness(stair))
                    if stair.finish_material is not None else ())
    # R311.7.5.3 counts the nosings at landings and floors: a lip over each riser that
    # climbs onto one, so the last tread is as deep as the rest.
    lips: tuple = ()
    if nosing_m > 1e-9:
        landing_lip = (deck.nosing_material_ref if deck is not None
                       else stair.finish_material or surfaces[1])
        if landing_lip is not None:
            lips = landing_nosing_parts(members, landing_lip, _tread_thickness(stair),
                                        nosing_m, finish_thickness_m)
        head_material = _head_nosing_material(model, stair)
        head = (stairhead_nosing_part(members, head_material, z_top, nosing_m,
                                      finish_thickness_m)
                if head_material is not None else None)
        lips += (head,) if head is not None else ()
    for lip in lips:
        # A covering on the riser under a lip stops beneath it.
        finish_parts = tuple(
            replace(part, z1_m=lip.z0_m) if part.role == "riser"
            and part.z0_m < lip.z0_m < part.z1_m - 1e-9
            and _same_riser(part, lip) else part for part in finish_parts)
    finish_parts += lips
    # A stair declaration lives with its destination deck so it can own the opening, but
    # its resolved plan-storey identity is the floor it rises *from*.
    return ResolvedStair(stair.uid, stair.tag, stair.from_storey, stair.to_storey, outline,
                         risers, riser,
                         physical_tread_m, stair.run_direction, stair.run_reversed, stair.layout,
                         stair.turn_direction, stair.winder_count, members,
                         going_depth_m=going_m, nosing_depth_m=nosing_m,
                         base_elevation_m=z0, arrival_elevation_m=z_top,
                         finish_material=stair.finish_material,
                         finish_thickness_m=finish_thickness_m,
                         finish_parts=finish_parts), []


def _millwork_standard(model: ResolvedModel):
    from typehaus.model.millwork import MillworkStandard

    return next((el for el in model.plan.all_elements()
                 if isinstance(el, MillworkStandard)), None)


def _landing_deck(model: ResolvedModel, stair: Stair):
    """The house's hardwood landing declaration when it names this flight."""
    standard = _millwork_standard(model)
    deck = standard.landing_deck if standard is not None else None
    return deck if deck is not None and stair.tag in deck.stair_refs else None


def _same_riser(face, lip) -> bool:
    """A riser's covering and a lip over it share their plan edge."""
    from shapely.geometry import Polygon

    return Polygon(face.outline).distance(Polygon(lip.outline)) < 1e-4


def _head_nosing_material(model: ResolvedModel, stair: Stair) -> str | None:
    """The authored stairhead nosing, else the house tread stock for a flight it scopes."""
    if stair.head_nosing_material is not None:
        return stair.head_nosing_material
    standard = _millwork_standard(model)
    if standard is not None and stair.tag in standard.tread_stairs:
        return standard.tread_material_ref
    return None


def _finish_materials(model: ResolvedModel,
                      stair: Stair) -> tuple[str | None, str | None, str | None]:
    """``(tread, landing, riser)`` finish refs: the flight's own ``tread_material``, else the house
    ``MillworkStandard`` that scopes it — so the treads the viewer textures are the ones
    ``haus millwork`` cuts, declared once."""
    standard = _millwork_standard(model)
    tread = stair.tread_material
    scoped = standard is not None and stair.tag in standard.tread_stairs
    if tread is None and scoped:
        tread = standard.tread_material_ref
    riser = stair.riser_material
    if riser is None and scoped:
        riser = standard.riser_material_ref
    deck = standard.landing_deck if standard is not None else None
    # A declared landing deck is a floor-board field; its nosing is a millwork detail.
    landing = (deck.field_material_ref if deck is not None and stair.tag in deck.stair_refs
               else tread)
    return tread, landing, riser


def _in_stair_material(stair: Stair, members: tuple[FramedMember, ...],
                       finish: tuple[str | None, str | None, str | None] = (None, None, None),
                       ) -> tuple[FramedMember, ...]:
    """Stamp the flight's materials onto every member it generated.

    Applied here, once, rather than threaded through twenty ``FramedMember`` constructions
    across ``straight`` / ``u_split`` / ``winder`` / ``bearing``: the material is a property
    of the flight, not of any one stringer, and a member the *bearing* pass posts down under
    a PT flight is PT for the same reason its stringers are. A generator that has already
    named a material for a member keeps it — nothing here overrides a more specific answer.
    Walking surfaces and risers take ``finish`` (tread, landing, riser) where declared.
    """
    tread, landing, riser = finish
    if (stair.material is None and stair.stringer_material is None and tread is None
            and landing is None and riser is None):
        return members

    def material(member: FramedMember) -> str | None:
        if member.category in ("tread", "winder"):
            return tread or stair.material
        if member.category == "landing":
            return landing or stair.material
        if member.category == "stringer":
            return stair.stringer_material or stair.material
        if member.category == "riser":
            return riser or stair.material
        return stair.material

    return tuple(member if member.material is not None
                 else replace(member, material=material(member)) for member in members)


def _flight_footprint(stair: Stair, going_m: float, risers: int) -> list[tuple[float, float]]:
    """The plan rectangle a flight with no floor opening occupies.

    Every consumer of ``ResolvedStair.outline`` — the plan drawing, the room-area deduction,
    the UI's stair pick — reads the *opening* outline where one exists. A within-storey run
    bounds itself instead: ``start``, the authored width across, and ``going x treads``
    along the run.
    """
    assert stair.start is not None  # only reached for a flight that authored one
    start_x, start_y = stair.start.xy_m
    sign = -1 if stair.run_reversed else 1
    span = sign * going_m * (risers - 1)
    width = stair.width.meters
    if stair.run_direction == "x":
        x0, x1 = sorted((start_x, start_x + span))
        y0, y1 = start_y, start_y + width
    else:
        x0, x1 = start_x, start_x + width
        y0, y1 = sorted((start_y, start_y + span))
    return [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def _element_storey(model: ResolvedModel, tag: str) -> str | None:
    for storey, elements in model.plan.elements.items():
        if any(element.tag == tag for element in elements):
            return storey
    return None


def _deck_underside(model: ResolvedModel, stair: Stair,
                    opening: FloorOpening | None) -> float | None:
    """Underside of the framed deck that owns the stair's opening, or ``None``.

    Stairs resolve before floors, so this reads the authored FloorSystem, exactly as
    ``resolve/floors.py`` places its joists. A slab-owned opening returns ``None``.
    """
    if opening is None:
        return None
    for element in model.plan.storey_elements(stair.to_storey):
        if isinstance(element, FloorSystem) and opening.tag in element.openings:
            storey = model.plan.storey(stair.to_storey)
            top = (element.top_elevation.meters if element.top_elevation is not None
                   else storey.elevation.meters)
            return top - cross_section(element.joists.member).depth_m
    return None


def _stair_members(stair: Stair, minx: float, miny: float, z0: float, risers: int,
                   riser: float, going: float, tread_depth: float, nosing: float,
                   landing_depth_m: float,
                   head_z: float | None = None,
                   finish_m: float = 0.0) -> tuple[FramedMember, ...]:
    if stair.layout == "right_angle_winder":
        return _winder_stair_members(stair, minx, miny, z0, risers, riser, going,
                                     tread_depth, nosing)
    if stair.layout in {"u_split_landing", "u_level_landing"}:
        return _u_split_landing_members(stair, minx, miny, z0, risers, riser, going,
                                        tread_depth, nosing,
                                        landing_depth_m, head_z, finish_m)
    return _straight_stair_members(stair, minx, miny, z0, risers, riser, going,
                                  tread_depth, nosing)


def _stair_fits_opening(stair: Stair, minx: float, maxx: float, miny: float, maxy: float,
                        tread: float, risers: int, landing_depth_m: float) -> bool:
    """Keep the generated flight entirely within its destination deck opening.

    The opening is the structural headroom contract shared by both storeys.  Resolving a
    flight from a shifted start without checking its cross-flight edge could generate treads
    under intact deck, even when its scalar run and width each fit the opening in isolation.
    """
    start_x, start_y = stair.start.xy_m if stair.start is not None else (minx, miny)
    if stair.layout in {"u_split_landing", "u_level_landing"}:
        # Mirrors _u_split_landing_members: the longer flight takes an odd extra tread,
        # and the two lanes are held apart
        # by the well partition — so the cross-run budget is 2 flights *plus* partition.
        flight_treads = max(0, risers - (2 if stair.layout == "u_level_landing" else 3))
        lower_treads = (flight_treads + 1) // 2
        required_run = landing_depth_m + tread * lower_treads
        required_cross = 2 * stair.width.meters + _WELL_PARTITION_THICKNESS_M
        if stair.run_direction == "x":
            return (required_cross <= maxy - miny + 1e-9
                    and required_run <= maxx - minx + 1e-9)
        return (required_cross <= maxx - minx + 1e-9
                and required_run <= maxy - miny + 1e-9)
    if stair.layout == "right_angle_winder":
        straight_treads = risers - 1 - stair.winder_count
        cross_end = (start_y + (1 if stair.turn_direction != "right" else -1) * stair.width.meters
                     if stair.run_direction == "x" else
                     start_x + (1 if stair.turn_direction != "right" else -1) * stair.width.meters)
        if stair.run_direction == "x":
            end_x = start_x + (-1 if stair.run_reversed else 1) * (
                stair.width.meters + tread * straight_treads)
            return (min(start_x, end_x) >= minx - 1e-9 and max(start_x, end_x) <= maxx + 1e-9
                    and min(start_y, cross_end) >= miny - 1e-9
                    and max(start_y, cross_end) <= maxy + 1e-9)
        end_y = start_y + (-1 if stair.run_reversed else 1) * (
            stair.width.meters + tread * straight_treads)
        return (min(start_y, end_y) >= miny - 1e-9 and max(start_y, end_y) <= maxy + 1e-9
                and min(start_x, cross_end) >= minx - 1e-9
                and max(start_x, cross_end) <= maxx + 1e-9)
    run = (-1 if stair.run_reversed else 1) * tread * max(0, risers - 1)
    if stair.run_direction == "x":
        return (min(start_x, start_x + run) >= minx - 1e-9
                and max(start_x, start_x + run) <= maxx + 1e-9
                and miny - 1e-9 <= start_y
                and start_y + stair.width.meters <= maxy + 1e-9)
    return (min(start_y, start_y + run) >= miny - 1e-9
            and max(start_y, start_y + run) <= maxy + 1e-9
            and minx - 1e-9 <= start_x
            and start_x + stair.width.meters <= maxx + 1e-9)
