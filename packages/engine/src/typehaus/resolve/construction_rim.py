"""Rim-cavity foam: the closed-cell fill that carries a wet room's barrier past a floor line.

The rim is where a wood-framed control layer most often fails — the sheathing stops at the
top plate and restarts at the sole plate above, with the floor structure in between — and it
is where a *sheet* barrier cannot go, because there is no continuous plane to lap one onto
between joist ends. In an ordinary room that is an air-sealing problem, and the
``rim-band-air-seal`` detail answers it with a membrane strip and two beads of sealant.

In a room deliberately run wet it is a vapour problem as well, and the only product that is
simultaneously the air barrier, the vapour retarder and the insulation in a cavity that shape
is closed-cell spray foam: bonded, monolithic, no seams. That is material somebody buys, and
until this finder existed the model *drew* it (``TR-CATLIN-PLANT-RIM``) and billed nobody for
it — a Transition documents and cannot put a quantity in a takeoff (#45).

Everything here reads the **plan**, not the resolved rooms and floors, because construction
rules run pre-framing: at that point ``model.walls`` exists but ``model.rooms`` and
``model.floors`` do not. ``construction_ceiling.py`` derives a room's face from plan inputs
for exactly the same reason, and this module reuses that derivation rather than repeating it.
"""

from __future__ import annotations

import math
from collections.abc import Iterator

from typehaus.model.assembly import ConstructionRule
from typehaus.model.floors import FloorSystem
from typehaus.resolve.construction_ceiling import _room_clear_face, _room_storey
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedConstructionReturn, ResolvedModel, ResolvedWall
from typehaus.resolve.room_walls import bounding_walls

# A floor band whose near face is within this of a wall's own base or top is a band that wall
# crosses. Generous enough for the platform-framing offset (#43) between a wall's z extent and
# the joist band it passes, tight enough never to claim a deck a storey away.
_BAND_REACH_M = 0.40
_EPS = 1e-9
#: The product this rule bills. Named here rather than read off a layer because the foam is
#: not *in* any assembly — it fills the cavity between two of them.
_FOAM_MATERIAL = "closed-cell-spray-foam"
_DEFAULT_DEPTH_M = 0.0762  # 3"


def _weather_exposed(wall: ResolvedWall) -> bool:
    """Does this wall face the weather — i.e. is its rim band a cold cavity?

    The rim of an interior partition has conditioned space on both sides and nothing to seal
    against, so foaming it would be a takeoff that invents work. Same test
    ``rim_band_air_seal`` applies before drawing anything.
    """
    return any(layer.function == "cladding" for layer in wall.layers)


def _plan_floor_bands(model: ResolvedModel) -> list[tuple[FloorSystem, float, float]]:
    """Every interior floor deck's joist band, as ``(system, z0, z1)``, from plan inputs.

    A deck's joists top out at its storey datum and hang their own depth below it — the same
    arithmetic ``construction_ceiling`` uses to hang a ceiling off the joist soffit.

    ``service="deck"`` systems are excluded, and that exclusion is the whole reason the
    balcony does not get foamed: an exterior walking surface on posts and beams has outdoor
    air on both sides of its rim, so there is no interior-to-exterior band there to close.
    """
    out: list[tuple[FloorSystem, float, float]] = []
    for storey in model.plan.storeys:
        for system in model.plan.storey_elements(storey.tag):
            if not isinstance(system, FloorSystem) or system.service != "floor":
                continue
            depth = cross_section(system.joists.member).depth_m
            out.append((system, storey.elevation.meters - depth, storey.elevation.meters))
    return out


def _run_outline(wall: ResolvedWall, u0: float, u1: float,
                 depth_m: float) -> list[tuple[float, float]]:
    """A rectangle along ``wall``'s axis from ``u0`` to ``u1``, ``depth_m`` across.

    Drawn on the wall axis rather than on a layer face: the foam fills the framing's own
    depth at the rim, and the axis is the one line that is the same for both floor systems
    the wall crosses.
    """
    (x0, y0), (x1, y1) = wall.axis
    length = math.hypot(x1 - x0, y1 - y0)
    if length <= _EPS:
        return []
    ux, uy = (x1 - x0) / length, (y1 - y0) / length
    nx, ny = -uy * depth_m / 2.0, ux * depth_m / 2.0
    a = (x0 + ux * u0, y0 + uy * u0)
    b = (x0 + ux * u1, y0 + uy * u1)
    return [(a[0] + nx, a[1] + ny), (b[0] + nx, b[1] + ny),
            (b[0] - nx, b[1] - ny), (a[0] - nx, a[1] - ny)]


def _find_rim_cavity_foam(model: ResolvedModel, rule: ConstructionRule) \
        -> Iterator[ResolvedConstructionReturn]:
    """Closed-cell foam in every floor band the scoped room's exterior walls cross.

    One return per (bounding weather-exposed wall, floor band), so a room on a framed storey
    yields two per wall — the deck under it and the deck over it. Both are needed, and for
    the same reason: joists run one way, so one wall takes their *ends* while the wall at
    right angles takes a parallel rim bay, and each is a direct path from a floor cavity into
    the coldest part of an exterior wall.

    ``length_m`` is the shared run of wall and room, not the wall's whole length: a wall that
    borders the room over part of its run is foamed over that part. ``thickness_m`` is the
    authored ``dimension`` — the depth specified, which is what turns lineal feet into the
    board-feet a sprayer quotes.

    ``scope_ref`` is required. A predicate that fired on "every exterior wall of every room"
    would foam the whole house; which rooms are run wet is a room decision, exactly as the
    resilient channel under one living-room ceiling is.
    """
    if rule.scope_ref is None:
        return
    storey = _room_storey(model.plan, rule.scope_ref)
    if storey is None:
        return
    face = _room_clear_face(model.plan, storey.tag, rule.scope_ref)
    if face is None:
        return
    depth_m = rule.dimension.meters if rule.dimension is not None else _DEFAULT_DEPTH_M
    bands = _plan_floor_bands(model)
    room = _RoomProbe(storey.tag, list(face.exterior.coords[:-1]))

    for wall, (u0, u1) in bounding_walls(model, room):
        if not _weather_exposed(wall) or u1 - u0 <= _EPS:
            continue
        outline = _run_outline(wall, u0, u1, depth_m)
        if not outline:
            continue
        for system, band_z0, band_z1 in bands:
            near_base = abs(band_z1 - wall.z0_m) <= _BAND_REACH_M
            near_top = abs(band_z0 - wall.z1_m) <= _BAND_REACH_M
            if not (near_base or near_top):
                continue
            yield ResolvedConstructionReturn(
                uid=f"CR-{wall.uid}-{system.tag}-rimfoam",
                tag=rule.tag, storey=wall.storey, kind=rule.kind,
                applies_to=rule.applies_to, takeoff_category=rule.takeoff_category,
                material_ref=_FOAM_MATERIAL,
                element_tags=(wall.tag, system.tag, rule.scope_ref),
                outline=outline,
                z0_m=band_z0, z1_m=band_z1,
                thickness_m=depth_m, length_m=u1 - u0,
                lap_m=depth_m,
                # It is the insulation, the air barrier and the vapour retarder at once —
                # which is the entire reason it is specified here instead of a batt plus a
                # strip of membrane.
                thermal_continuity=True,
                air_vapor_continuity=True,
                sealant="foam-to-sheathing bond (no seam)",
                returning_layer=_FOAM_MATERIAL,
                # The rim band is already a derived storey-stack condition, so this joins the
                # Transition that documents it rather than inventing a key of its own.
                condition_key=None,
            )


class _RoomProbe:
    """The two fields :func:`bounding_walls` reads, for a room that is not resolved yet.

    Not a ``ResolvedRoom``: that record carries an occupancy, an area and a floor finish
    which do not exist at the construction stage, and inventing them to satisfy a
    constructor would put three fabricated values into the one place a reader would trust
    them.
    """

    __slots__ = ("storey", "clear_face")

    def __init__(self, storey: str, clear_face: list[tuple[float, float]]) -> None:
        self.storey = storey
        self.clear_face = clear_face


__all__ = ["_find_rim_cavity_foam"]
