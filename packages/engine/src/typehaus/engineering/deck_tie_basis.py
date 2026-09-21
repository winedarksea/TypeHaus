"""What ties a deck to a concrete wall, and what the tie is asked to carry.

Two readers, one derivation. ``pier_basis._base_moments`` asks whether a deck is braced by a
wall — and if it is, its cast columns lean and grade no base moment. ``deck_tie`` asks what
that bracing costs the tie. Deriving "braced" twice is how the two would come to disagree
about the same landing, so both read :func:`wall_ties`.

**Braced is derived from hardware, never declared.** A deck is tied when an authored
``Connector`` joins a member of its framing — a beam it bears on, a beam bearing on one of
those, or a wall standing on it — to a CONCRETE wall or a framed wall OFF the deck (another
structure's). A bearing standoff is not a tie (it holds a soffit off a pour and transfers
nothing sideways), nor is a tie block (it joins nothing to the other structure). Whether the
tie is ENOUGH is ``deck_tie``'s question, answered against the part's published allowables;
a tie that is not enough is an OVER record, never an unbraced deck.

**Loads, each placed where it acts in plan** (the tie's torsion depends on it):

* the deck's own wind, ``balcony_wind``'s storey shear per axis, at the sheet's centroid;
* the in-plane share of every shear panel standing on the deck, from the roof frame case
  that loads it (``roof_moment``), at the panel's midpoint along its line;
* wind on the FACE of every framed wall standing on the deck, ``0.6 q G C_f A`` at the
  same C_f ceiling the deck uses, at the wall's midpoint — a wall the deck carries is a
  sail the deck carries;
* IRC R301.5's 200 lb guard load at each end of every guard standing on the deck.

Oracle: ``houses/catlin/notes/north_entry_piers.md`` §10.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from typehaus.engineering.registry import EngineeringContext

_FT = 0.3048
#: IRC R301.5 / Table R301.5 note f — the same 200 lb ``pier_basis`` puts on a column base.
GUARD_LOAD_LB = 200.0
#: A wall stands on a deck when its plan line lies inside the deck's sheet grown by this. A
#: skirt hung on the deck edge sits outboard of the sheet by its own build-up (catlin's
#: ``W-BW-SCREEN-SKIRT``, 2.8"); six inches admits that and nothing a foot away.
ON_DECK_PLAN_TOLERANCE_FT = 0.5


@dataclass(frozen=True)
class TieJoint:
    """One member-to-wall joint: the parts at it and where it is."""

    member: str
    wall: str
    parts: tuple[str, ...]
    model: str
    x_ft: float
    y_ft: float
    #: The wall's run direction, "x" or "y".
    wall_axis: str
    #: The parts' heel in plan (``Connector.axis``): "x"/"y", ``None`` for a vertical heel,
    #: "mixed" where the parts disagree. Only an angle's capacity reads it.
    heel_axis: str | None = None
    #: The tied-to wall is concrete (an anchor side to grade) rather than framing.
    on_concrete: bool = True
    #: The parts' authored ``Connector.service`` condition ("dry"/"wet"), ``None`` where none
    #: is authored (read wet), "mixed" where they disagree; and its stated basis.
    service_condition: str | None = None
    service_basis: str = ""


@dataclass(frozen=True)
class Load:
    """A plan force (lb, ASD) acting through ``(x_ft, y_ft)``."""

    label: str
    fx: float
    fy: float
    x_ft: float
    y_ft: float


def _xy_ft(point: Any) -> tuple[float, float]:
    x, y = point.xy_m
    return x / _FT, y / _FT


def _concrete_walls(ctx: EngineeringContext) -> dict[str, Any]:
    from typehaus.model.elements import Wall
    from typehaus.resolve.assembly_material import assembly_structure_material

    return {e.tag: e for e in ctx.plan.all_elements() if isinstance(e, Wall)
            and assembly_structure_material(ctx.plan, e.assembly) == "concrete"}


def framing_of(ctx: EngineeringContext, deck: Any) -> set[str]:
    """The beams a deck bears on, and every beam bearing on one of those or on the deck."""
    from typehaus.model.structure import Beam

    beams = {t for t in deck.joists.bearing_refs or ()
             if isinstance(ctx.plan.by_tag(t), Beam)}
    carried = {e.tag for e in ctx.plan.all_elements() if isinstance(e, Beam)
               and set(e.bearing_refs or ()) & (beams | {deck.tag})}
    return beams | carried


def _tie_targets(ctx: EngineeringContext, on_deck: set[str]) -> dict[str, Any]:
    """Walls a deck may be tied TO: concrete, or framing that does not stand on the deck."""
    from typehaus.model.elements import Wall

    return {e.tag: e for e in ctx.plan.all_elements()
            if isinstance(e, Wall) and e.tag not in on_deck}


def wall_ties(ctx: EngineeringContext, deck: Any) -> list[TieJoint]:
    """Every joint tying this deck to another structure's wall, one per (member, wall)."""
    from typehaus.model.enums import ConnectorKind
    from typehaus.model.structure import Connector

    on_deck = {w.tag for w, _a, _b in walls_on_deck(ctx, deck)}
    framing = framing_of(ctx, deck) | on_deck
    walls = _tie_targets(ctx, on_deck)
    concrete = _concrete_walls(ctx)
    groups: dict[tuple[str, str], list[Any]] = {}
    for part in ctx.plan.all_elements():
        if not isinstance(part, Connector) or part.kind in (
                ConnectorKind.BEARING_STANDOFF, ConnectorKind.TIE_BLOCK):
            continue
        members = [t for t in part.connects if t in framing]
        targets = [t for t in part.connects if t in walls and t not in framing]
        if members and targets:
            groups.setdefault((members[0], targets[0]), []).append(part)
    out = []
    for (member, wall_tag), parts in sorted(groups.items()):
        points = [_xy_ft(p.position) for p in parts]
        wall = walls[wall_tag]
        (x0, y0), (x1, y1) = (_xy_ft(ctx.plan.by_tag(wall.start_node).position),
                              _xy_ft(ctx.plan.by_tag(wall.end_node).position))
        heels = {p.axis for p in parts}
        services = {(p.service.condition, p.service.basis) if p.service else (None, "")
                    for p in parts}
        service = next(iter(services)) if len(services) == 1 else ("mixed", "")
        out.append(TieJoint(
            member=member, wall=wall_tag, parts=tuple(sorted(p.tag for p in parts)),
            model=parts[0].size, x_ft=sum(p[0] for p in points) / len(points),
            y_ft=sum(p[1] for p in points) / len(points),
            wall_axis="x" if abs(x1 - x0) >= abs(y1 - y0) else "y",
            heel_axis=next(iter(heels)) if len(heels) == 1 else "mixed",
            on_concrete=wall_tag in concrete, service_condition=service[0],
            service_basis=service[1]))
    return out


def deck_storey(ctx: EngineeringContext, deck: Any) -> str | None:
    """The storey a deck is FILED on — see ``balcony_wind.nearest`` for why it matters."""
    return next((st.tag for st in ctx.plan.storeys
                 if any(e is deck for e in ctx.plan.storey_elements(st.tag))), None)


@dataclass(frozen=True)
class DeckWind:
    """``balcony_wind``'s storey shear on one deck, per plan axis."""

    q_h_psf: float
    height_ft: float
    top_ft: float
    ground_ft: float
    shear_lb: dict[str, float]
    basis_text: str
    guard: Any


def deck_wind(ctx: EngineeringContext, deck: Any, anchors: list[Any]) -> DeckWind | None:
    """The deck's own storey shear on each axis, at ``MAX_VERIFIED_CASE_AB``.

    ``anchors`` are the posts the fascia and guard are found near. ``None`` where the deck
    has no guard or the site no wind basis — the same two gaps ``_base_moments`` stops on.
    """
    from typehaus.engineering.balcony_wind import Demand, ground_below_ft, nearest
    from typehaus.engineering.balcony_wind import ft as _bw_ft
    from typehaus.model.structure import Beam, Railing
    from typehaus.model.trim import Fascia
    from typehaus.wind import velocity_pressure_psf, wind_basis
    from typehaus.wind_tables import MAX_VERIFIED_CASE_AB

    storey = deck_storey(ctx, deck)
    fascia = nearest(ctx.plan, anchors, Fascia, storey)
    if fascia is not None and not _on_sheet(deck, fascia.path):
        fascia = None  # the nearest fascia is another deck's: this one shows its own edge
    guard = nearest(ctx.plan, anchors, Railing, storey)
    basis = wind_basis(ctx.plan.project.site)
    if guard is None or basis is None:
        return None
    ground = ground_below_ft(ctx.plan)
    top = _bw_ft(guard.base_elevation) + _bw_ft(guard.height)
    q_h = velocity_pressure_psf(basis, top - ground)
    members = {t for t in deck.joists.bearing_refs or ()
               if isinstance(ctx.plan.by_tag(t), Beam)}
    shear = {axis: Demand(axis=axis, q_h_psf=q_h, height_ft=top - ground,
                          bands=_bands(ctx, deck, axis, members, fascia)
                          ).storey_shear_lb(MAX_VERIFIED_CASE_AB)
             for axis in ("x", "y")}
    return DeckWind(q_h_psf=q_h, height_ft=top - ground, top_ft=top, ground_ft=ground,
                    shear_lb=shear, basis_text=basis.describe(), guard=guard)


def _on_sheet(deck: Any, path: Any) -> bool:
    from shapely.geometry import Point, Polygon

    grown = Polygon([_xy_ft(p) for p in (deck.subfloor_outline or deck.outline)]).buffer(
        ON_DECK_PLAN_TOLERANCE_FT)
    return all(grown.covers(Point(_xy_ft(p))) for p in path)


def _bands(ctx: EngineeringContext, deck: Any, axis: str, members: set[str],
           fascia: Any) -> tuple[Any, ...]:
    from typehaus.engineering.balcony_wind import deck_edge_band, solid_bands

    bands = solid_bands(ctx.plan, axis, members, fascia)
    edge = None if fascia is not None else deck_edge_band(deck, axis)
    return bands + ((edge,) if edge is not None else ())


def sheet_centroid_ft(deck: Any) -> tuple[float, float]:
    outline = deck.subfloor_outline or deck.outline
    points = [_xy_ft(p) for p in outline]
    return (sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points))


def walls_on_deck(ctx: EngineeringContext, deck: Any) -> list[tuple[Any, tuple, tuple]]:
    """``(wall, start_xy_ft, end_xy_ft)`` for each FRAMED wall standing on this deck.

    On it means: its plan line inside the sheet grown by ``ON_DECK_PLAN_TOLERANCE_FT``, and
    its base no lower than the deck framing's soffit. The second test is what keeps the
    concrete stem the deck is TIED to from reading as a wall the deck carries.
    """
    from shapely.geometry import LineString, Polygon

    from typehaus.engineering.balcony_wind import ft as _bw_ft
    from typehaus.engineering.balcony_wind import member_depth_ft
    from typehaus.model.elements import Wall

    sheet = Polygon([_xy_ft(p) for p in (deck.subfloor_outline or deck.outline)])
    grown = sheet.buffer(ON_DECK_PLAN_TOLERANCE_FT)
    soffits = [_bw_ft(b.top_elevation) - (member_depth_ft(ctx.plan, t) or 0.0)
               for t in framing_of(ctx, deck)
               if (b := ctx.plan.by_tag(t)) is not None and b.top_elevation is not None]
    if not soffits and deck.top_elevation is None:
        return []  # a deck with no datum stands nothing on it this can place
    soffit = min(soffits, default=_bw_ft(deck.top_elevation) if not soffits else 0.0)
    concrete = _concrete_walls(ctx)
    out = []
    for wall in ctx.plan.all_elements():
        if not isinstance(wall, Wall) or wall.tag in concrete:
            continue
        resolved = ctx.model.wall(wall.tag)
        start, end = ctx.plan.by_tag(wall.start_node), ctx.plan.by_tag(wall.end_node)
        if resolved is None or start is None or end is None:
            continue
        a, b = _xy_ft(start.position), _xy_ft(end.position)
        if resolved.z0_m / _FT < soffit - 1e-6 or not grown.covers(LineString([a, b])):
            continue
        out.append((wall, a, b))
    return out


def loads_on(ctx: EngineeringContext, deck: Any, wind: DeckWind
             ) -> tuple[dict[str, list[Load]], list[Load]]:
    """``({axis: wind loads}, guard loads)`` — every force the tie line must take."""
    from typehaus.engineering.roof_moment import frame_cases_of, roof_base_moments
    from typehaus.model.spatial import Roof
    from typehaus.wind import ASD_WIND_FACTOR, velocity_pressure_psf, wind_basis
    from typehaus.wind_tables import GUST_EFFECT_RIGID, MAX_VERIFIED_CASE_AB

    cx, cy = sheet_centroid_ft(deck)
    wind_loads: dict[str, list[Load]] = {
        axis: [Load(f"{deck.tag} deck wind", wind.shear_lb[axis] if axis == "x" else 0.0,
                    wind.shear_lb[axis] if axis == "y" else 0.0, cx, cy)]
        for axis in ("x", "y")}
    guards: list[Load] = []
    basis = wind_basis(ctx.plan.project.site)
    on_deck = walls_on_deck(ctx, deck)
    panels = {w.tag: (a, b) for w, a, b in on_deck if getattr(w, "shear_panel", None)}

    roof_base_moments(ctx)
    for roof in ctx.plan.all_elements():
        if not isinstance(roof, Roof) or roof.diaphragm is None:
            continue
        for case in frame_cases_of(roof.tag):
            for tag, share in case.panels_governing.shares.items():
                if tag not in panels:
                    continue
                (x0, y0), (x1, y1) = panels[tag]
                force = share * case.diaphragm_shear_lb
                wind_loads[case.axis].append(Load(
                    f"{tag} panel share of {roof.tag}",
                    force if case.axis == "x" else 0.0, force if case.axis == "y" else 0.0,
                    (x0 + x1) / 2, (y0 + y1) / 2))

    for wall, (x0, y0), (x1, y1) in on_deck:
        resolved = ctx.model.wall(wall.tag)
        height = (resolved.z1_m - resolved.z0_m) / _FT
        length = math.dist((x0, y0), (x1, y1))
        face_axis = "x" if abs(y1 - y0) > abs(x1 - x0) else "y"
        if basis is not None:
            q = velocity_pressure_psf(basis, resolved.z1_m / _FT - wind.ground_ft)
            force = ASD_WIND_FACTOR * q * GUST_EFFECT_RIGID * MAX_VERIFIED_CASE_AB \
                * length * height
            wind_loads[face_axis].append(Load(
                f"{wall.tag} face wind ({length:.3f}' x {height:.3f}', q {q:.2f} psf)",
                force if face_axis == "x" else 0.0, force if face_axis == "y" else 0.0,
                (x0 + x1) / 2, (y0 + y1) / 2))
        if getattr(wall, "guard", False):
            guards += _guard_loads(wall.tag, ((x0, y0), (x1, y1)))
    for railing in _railings_on(ctx, deck):
        guards += _guard_loads(railing.tag, [_xy_ft(p) for p in railing.path])
    return wind_loads, guards


def _guard_loads(tag: str, points: Any) -> list[Load]:
    """The 200 lb at each end of a guard run, along each axis (the sign is taken later)."""
    return [Load(f"{tag} guard at ({x:.3f}, {y:.3f})", fx, fy, x, y)
            for x, y in points
            for fx, fy in ((GUARD_LOAD_LB, 0.0), (0.0, GUARD_LOAD_LB))]


def _railings_on(ctx: EngineeringContext, deck: Any) -> list[Any]:
    """Guards authored as ``Railing`` whose path lies on the deck's sheet."""
    from shapely.geometry import LineString, Polygon

    from typehaus.engineering.balcony_wind import ft as _bw_ft
    from typehaus.model.structure import Railing

    sheet = Polygon([_xy_ft(p) for p in (deck.subfloor_outline or deck.outline)])
    grown = sheet.buffer(ON_DECK_PLAN_TOLERANCE_FT)
    base = _bw_ft(deck.top_elevation) - ON_DECK_PLAN_TOLERANCE_FT
    return [r for r in ctx.plan.all_elements()
            if isinstance(r, Railing) and len(r.path) >= 2
            and _bw_ft(r.base_elevation) >= base
            and grown.covers(LineString([_xy_ft(p) for p in r.path]))]
