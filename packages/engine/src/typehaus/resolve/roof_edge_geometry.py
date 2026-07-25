"""Plan geometry shared by the two roof-edge resolvers (→ B2).

:mod:`typehaus.resolve.roof_edge` carries the wall weather skin up to the roof it dies
into; :mod:`typehaus.resolve.roof_trim` hangs the derived fascia / soffit / gutter and the
roof-edge cladding band off the roof plane. Both need the same primitives — the roof's four
edge runs, the wall stack's mating faces, the plane's slope — so they live here rather than
in whichever module happened to need them first.
"""

from __future__ import annotations

import math
from typing import NamedTuple

from typehaus.model.enums import LayerFunction
from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedModel, ResolvedRoof, ResolvedWall
from typehaus.resolve.roof_geometry import roof_height_at
from typehaus.resolve.roof_layer_setbacks import above_structure_layers

# Under this the wall already meets the roof — a sliver band is a rounding artifact, not
# construction. Also the tolerance for "this wall sits under this roof".
CLOSURE_TOLERANCE_M = inch(0.25).meters
FOOTPRINT_TOLERANCE_M = inch(1.0).meters
METERS_PER_INCH = inch(1).meters

# Which `layer_edge_setbacks` key an edge run's outward normal names.
EDGE_NAMES = {(-1.0, 0.0): "west", (1.0, 0.0): "east",
              (0.0, -1.0): "south", (0.0, 1.0): "north"}


def bbox(ring) -> tuple[float, float, float, float]:
    xs = [point[0] for point in ring]
    ys = [point[1] for point in ring]
    return min(xs), min(ys), max(xs), max(ys)


def skin_layers(wall: ResolvedWall):
    """The weather skin: the first SHEATHING layer and everything outboard of it."""
    layers = wall.depth_layers()
    start = next((index for index, layer in enumerate(layers)
                  if layer.function == LayerFunction.SHEATHING.value), None)
    return () if start is None else layers[start:]


def roof_slope(roof: ResolvedRoof) -> float:
    """Rise over run of the roof plane, derived from the resolved envelope.

    ``ResolvedRoof`` carries no pitch — the plane it was solved into is the authority, and a
    gable's run is half its span.
    """
    minx, miny, maxx, maxy = bbox(roof.footprint)
    span = (maxy - miny) if roof.ridge_direction == "x" else (maxx - minx)
    run = span if roof.form == "shed" else span / 2.0
    return 0.0 if run <= 1e-9 else (roof.ridge_z_m - roof.eave_z_m) / run


def wall_face_inset(
    normal: tuple[float, float], edge_point: tuple[float, float],
    walls: tuple[ResolvedWall, ...],
) -> float:
    """How far inboard of the roof edge the wall's outermost face is, along ``normal``.

    Measured from the resolved cladding polygons, so a rainscreen or a thicker cladding
    moves the soffit's inner edge with it instead of being assumed away.
    """
    projections = [
        (point[0] - edge_point[0]) * normal[0] + (point[1] - edge_point[1]) * normal[1]
        for wall in walls for layer in skin_layers(wall) for point in layer.polygon
    ]
    return max(projections) if projections else 0.0


class MatingFaces(NamedTuple):
    """Perpendicular offsets above the roof plane of the faces a wall's skin dies into.

    Straight off the golden eave detail
    (``tests/fixtures/catlin_reference/scripts/roof_wall_eave_detail_ifc.py``): the roof is
    not one face a wall stops under, it is a stack, and each wall layer runs up to *its own*
    counterpart in that stack —

    * wall sheathing + its membrane → the roof plane itself, which the roof deck then laps
      ("roof sheathing extends to overlap wall sheathing/membrane for continuity");
    * wall foam → the underside of the roof foam;
    * wall furring → the underside of the roof furring, which is what makes the vent channel
      continuous wall → eave → ridge;
    * wall cladding → the roof foam underside, with the gutter and drip edge closing the band
      above it.
    """

    foam_under: float
    furring_under: float
    cladding_under: float

    def for_layer(self, function: str, continuous_cladding: bool = False) -> float:
        if function in (LayerFunction.SHEATHING.value, LayerFunction.MEMBRANE.value):
            return 0.0
        if function == LayerFunction.FURRING.value:
            return self.furring_under
        # A wrapped edge (see :func:`continuous_skin_cladding`) has no drip-edge band for the
        # wall cladding to die under: the wall's run of metal continues up the stack edge to
        # the roofing's own underside, so the two skins read as one surface.
        if continuous_cladding and function == LayerFunction.CLADDING.value:
            return self.cladding_under
        return self.foam_under  # insulation and cladding


def mating_faces(layers) -> MatingFaces:
    total = 0.0
    foam_under = furring_under = None
    cladding_under = 0.0
    for layer in layers:
        if layer.function is LayerFunction.INSULATION and foam_under is None:
            foam_under = total
        elif (layer.function in (LayerFunction.AIRGAP, LayerFunction.FURRING)
              and furring_under is None):
            furring_under = total
        elif layer.function is LayerFunction.CLADDING:
            cladding_under = total
        total += layer.thickness.meters
    # A roof with no foam and no vent cavity — the garage's deck-and-metal — presents only its
    # cladding underside, so everything below dies there.
    return MatingFaces(foam_under if foam_under is not None else cladding_under,
                       furring_under if furring_under is not None else cladding_under,
                       cladding_under)


class EdgeRun(NamedTuple):
    """One straight roof-edge run at the plane's elevation, plus its corner bookkeeping.

    ``is_eave`` distinguishes the two level eaves from the rake halves; the ``corner_*``
    flags mark the ends that land on one of the four rake corners, where the eave and rake
    trim of the same piece would otherwise claim the same square (see :func:`mitred_span`).
    """

    key: str
    p0: tuple[float, float]
    z0_m: float
    p1: tuple[float, float]
    z1_m: float
    normal: tuple[float, float]  # outward, in plan
    is_eave: bool
    corner_at_p0: bool
    corner_at_p1: bool

    @property
    def edge_name(self) -> str:
        return EDGE_NAMES[self.normal]


def roof_edge_runs(roof: ResolvedRoof) -> tuple[EdgeRun, ...]:
    """The four roof edges as runs at the plane's elevation.

    The two eaves are level; each rake climbs eave→ridge→eave, so it is split at the ridge
    into two straight runs (the same reason the gable closure splits). Only a rake's
    *outboard* end is a corner — its other end is the ridge.
    """
    minx, miny, maxx, maxy = bbox(roof.footprint)
    along_lo, along_hi = (minx, maxx) if roof.ridge_direction == "x" else (miny, maxy)
    span_lo, span_hi = (miny, maxy) if roof.ridge_direction == "x" else (minx, maxx)
    span_mid = (span_lo + span_hi) / 2.0

    def point(along: float, span: float) -> tuple[float, float]:
        return (along, span) if roof.ridge_direction == "x" else (span, along)

    def height(span: float) -> float:
        return roof_height_at(roof, point(along_lo, span))

    runs: list[EdgeRun] = []
    for name, span, sign in (("eave-lo", span_lo, -1.0), ("eave-hi", span_hi, 1.0)):
        runs.append(EdgeRun(name, point(along_lo, span), height(span),
                            point(along_hi, span), height(span), point(0.0, sign),
                            is_eave=True, corner_at_p0=True, corner_at_p1=True))
    for name, along, sign in (("rake-lo", along_lo, -1.0), ("rake-hi", along_hi, 1.0)):
        for half, (a, b) in enumerate(((span_lo, span_mid), (span_mid, span_hi))):
            runs.append(EdgeRun(f"{name}-{half}", point(along, a), height(a),
                                point(along, b), height(b), point(sign, 0.0),
                                is_eave=False, corner_at_p0=(half == 0),
                                corner_at_p1=(half == 1)))
    return tuple(runs)


class RidgeRun(NamedTuple):
    """The level ridge line of a gable roof, in plan, at the ridge elevation.

    Distinct from the four :class:`EdgeRun` records: a ridge is interior to the footprint,
    has no outward normal and no corner bookkeeping — it is simply the line the two roof
    planes meet on, which is what a ridge cap or a ridge vent registers against.
    """

    p0: tuple[float, float]
    p1: tuple[float, float]
    z_m: float


def roof_ridge_run(roof: ResolvedRoof) -> RidgeRun | None:
    """The ridge line spanning the footprint's full ridge-axis extent, or ``None``.

    Only a gable has a ridge both planes drain toward; a shed's high edge is an eave/rake
    condition and is already covered by :func:`roof_edge_runs`. The run spans the whole
    footprint — rake overhangs included — because a cap stopping at the gable wall would
    leave the overhung ridge open.
    """
    if roof.form != "gable":
        return None
    minx, miny, maxx, maxy = bbox(roof.footprint)
    if roof.ridge_direction == "x":
        mid = (miny + maxy) / 2.0
        return RidgeRun((minx, mid), (maxx, mid), roof.ridge_z_m)
    mid = (minx + maxx) / 2.0
    return RidgeRun((mid, miny), (mid, maxy), roof.ridge_z_m)


def continuous_skin_cladding(
    model: ResolvedModel, roof: ResolvedRoof, walls: tuple[ResolvedWall, ...]
) -> bool:
    """Whether the walls' cladding and the roofing are one continuous skin over a flush edge.

    The catlin house is the motivating case: standing-seam siding, zero overhang, and
    standing-seam roofing — in the real build the panels run essentially unbroken from grade
    up the wall, over the edge, and across the roof, with only a corner trim piece over the
    joint. That reading holds when *every* wall under the roof finishes in the roofing's own
    cladding material and the roof has no overhang for a fascia/soffit assembly to occupy.
    A mixed-material or overhung edge keeps the conventional fascia + edge-band detail.
    """
    element = model.plan.by_tag(roof.tag)
    overhang = getattr(element, "overhang", None)
    if overhang is not None and overhang.meters > CLOSURE_TOLERANCE_M:
        return False
    assembly = model.plan.library.resolve_assembly(roof.assembly) if roof.assembly else None
    layers = above_structure_layers(assembly)
    roofing = next((layer for layer in reversed(layers)
                    if layer.function is LayerFunction.CLADDING), None)
    if roofing is None:
        return False
    materials = set()
    for wall in walls:
        cladding = next((layer for layer in reversed(skin_layers(wall))
                         if layer.function == LayerFunction.CLADDING.value), None)
        if cladding is not None:
            materials.add(cladding.material_ref)
    return bool(materials) and materials == {roofing.material_ref}


class MitredSpan(NamedTuple):
    """A trim piece's run after the rake corners are resolved."""

    p0: tuple[float, float]
    z0_m: float
    p1: tuple[float, float]
    z1_m: float


def mitred_span(
    run: EdgeRun, outer_inboard_m: float, inner_inboard_m: float
) -> MitredSpan | None:
    """Cut a trim piece's run back so the eave and rake runs tile the corner exactly once.

    ``outer_inboard_m`` / ``inner_inboard_m`` are the piece's own faces as distances *inboard*
    of the footprint edge (a board hung outboard of the edge has negative values). At each of
    the four corners the eave piece and the rake piece cross in a square: left alone both
    solids claim it, which is the doubled trim at every rake corner.

    A true compound miter is a 45° end cut, and the lightweight member IR is a box with
    square ends — it cannot carry one. So the corner is resolved as the lap the miter would
    otherwise hide: the eave run is cut back to *its own outer face* and the rake run stops at
    the eave piece's *inner face*, which tiles the square once, with no overlap and no gap.
    Returns ``None`` when the cuts consume the whole run.
    """
    shift = outer_inboard_m if run.is_eave else inner_inboard_m
    dx, dy = run.p1[0] - run.p0[0], run.p1[1] - run.p0[1]
    length = math.hypot(dx, dy)
    if length < 1e-9:
        return None
    start = shift if run.corner_at_p0 else 0.0
    end = shift if run.corner_at_p1 else 0.0
    if start + end >= length - CLOSURE_TOLERANCE_M:
        return None
    t0, t1 = start / length, 1.0 - end / length

    def at(fraction: float) -> tuple[tuple[float, float], float]:
        return ((run.p0[0] + dx * fraction, run.p0[1] + dy * fraction),
                run.z0_m + (run.z1_m - run.z0_m) * fraction)

    (p0, z0), (p1, z1) = at(t0), at(t1)
    return MitredSpan(p0, z0, p1, z1)
