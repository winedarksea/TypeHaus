"""Where a wall's framing stops at an L corner, and the supplemental corner studs (→ 11).

Two walls meeting at an L share a square of plan the size of one structure band, and only
one wall's framing may occupy it. The junction solver already names that wall
(``ResolvedJunction.framing_owner``) and mitres the two structure-layer polygons across the
square, so the mitre edge carries exactly the two numbers this module needs: projected onto
the wall axis it spans from the *far* face of the neighbour's band (where the owner's
framing runs to) to its *near* face (where the butting wall has to stop).

Why this module exists at all: the framing axis is the datum axis translated onto the
structure layer, but its *endpoints* stayed on the datum node. Both walls' end studs
therefore sat on the node — overhanging the building corner by half a stud and pinwheeling
through each other — and the supplemental corner stud landed outside the corner square. The
3-stud corner pack existed as records but never read as a corner in plan or in 3D.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.resolve.model import ResolvedModel, Ring

#: This wall's framing runs through the shared corner square (the junction's framing owner).
CORNER_ROLE_OWNER = "owner"
#: This wall's framing stops at the near face of the owner's band and butts it.
CORNER_ROLE_BUTTING = "butting"

_MIDPOINT_FRACTION = 0.5  # framing may never be inset past the wall's own midpoint


@dataclass(frozen=True)
class WallEndFraming:
    """Along-axis stations (m from the framing axis start) for one end of a wall.

    ``plate_station_m`` is where the plates are cut; ``end_stud_station_m`` is the centre of
    the stud that closes the run, one half thickness inboard so the stud's end face is flush
    with the plate cut rather than half of it hanging past the corner.
    """

    plate_station_m: float
    end_stud_station_m: float


def invert_corner_role(role: str | None) -> str | None:
    """Owner <-> butting. The cap plate of a double top plate laps the *opposite* way from
    the wall below it — that reversal is what ties two walls together at a corner, so the
    plate that runs through at one course must stop short at the other."""
    if role == CORNER_ROLE_OWNER:
        return CORNER_ROLE_BUTTING
    if role == CORNER_ROLE_BUTTING:
        return CORNER_ROLE_OWNER
    return None


def neighbour_band_insets(neighbour_polygon: Ring, axis_start, direction,
                          axis_len_m: float, at_start: bool) -> tuple[float, float] | None:
    """(far-face, near-face) insets of the *neighbour's* band, read off its own polygon.

    The mitre-edge reading in :func:`_neighbour_band_insets` is only exact when both walls
    carry the same structure depth: the bisector then crosses each band at its own half
    depth, which is also the other's. Where the depths differ — a 2x4 partition dying into
    the end of a 2x6 bearing wall — the bisector leaves the thinner wall's mitre wedge
    reaching *into* the thicker band, and a rectangular end stud placed on that reading
    pokes through the owner's corner pack. Projecting the neighbour's band directly gives
    the two face stations the corner rule actually wants, for any pair of depths and for
    either wall's ``alignment``. Returns ``None`` when the neighbour has no usable polygon.
    """
    if not neighbour_polygon or len(neighbour_polygon) < 3:
        return None
    insets = []
    for point in neighbour_polygon:
        station = ((point[0] - axis_start[0]) * direction[0]
                   + (point[1] - axis_start[1]) * direction[1])
        insets.append(station if at_start else axis_len_m - station)
    return min(insets), max(insets)


def wall_end_framing(structure_polygon: Ring, axis_start, direction, axis_len_m: float,
                     role: str | None, stud_thickness_m: float,
                     at_start: bool,
                     neighbour_insets: tuple[float, float] | None = None) -> WallEndFraming:
    """Framing limit + end-stud station for one wall end under its corner ``role``.

    ``role`` of ``None`` (an open end, a tee branch, a collinear run) keeps the historical
    behaviour — framing runs to the datum endpoint — because only an L corner has a shared
    square to divide.

    ``neighbour_insets`` is the (far, near) pair from :func:`neighbour_band_insets` when the
    caller could resolve the neighbouring wall; without it the mitre edge is read instead,
    which agrees with it wherever the two bands are the same depth.
    """
    if role is None:
        return WallEndFraming(0.0, 0.0) if at_start \
            else WallEndFraming(axis_len_m, axis_len_m)

    outer_inset, inner_inset = neighbour_insets if neighbour_insets is not None else (
        _neighbour_band_insets(
            structure_polygon, axis_start, direction, axis_len_m, at_start
        )
    )
    inset = outer_inset if role == CORNER_ROLE_OWNER else inner_inset
    # A junction the solver could not resolve leaves a square end (outer == inner); both
    # walls then frame to the same station, which is no worse than the datum-node behaviour
    # it replaces. Clamping at the midpoint keeps a very short wall from inverting.
    # A *negative* inset is legitimate and deliberately kept: where the datum axis names a
    # face rather than the band centre, the structure polygon runs past the axis endpoint,
    # and that is exactly where the corner square is.
    #
    # ``neighbour_insets`` (when given) is a real measurement of the *other* wall's band,
    # not a guess — on a short jog wall (e.g. a 6" stub between two junctions) it can
    # legitimately exceed this wall's own midpoint without inverting, because what fixes
    # the inset is the neighbour's thickness, not this wall's length. Only the mitre-edge
    # estimate (no neighbour available) needs the tighter midpoint guard against a skewed
    # or unresolved corner inverting the pack.
    if neighbour_insets is not None:
        inset = min(inset, axis_len_m - stud_thickness_m)
    else:
        inset = min(inset, axis_len_m * _MIDPOINT_FRACTION - stud_thickness_m)
    stud_inset = inset + stud_thickness_m / 2.0
    if at_start:
        return WallEndFraming(inset, stud_inset)
    return WallEndFraming(axis_len_m - inset, axis_len_m - stud_inset)


def corner_stud_stations(end: WallEndFraming, at_start: bool, stud_thickness_m: float,
                         corner_style: str, axis_len_m: float) -> tuple[float, ...]:
    """Supplemental corner-stud stations, packed face-to-face inboard of the end stud.

    One for the default 3-stud corner (end stud + this one + the neighbour's end stud), two
    for the ``4-stud`` box-corner variant. They are deliberately off the regular module: the
    module studs keep their continuity for sheathing, standing-seam panels and floor framing.
    """
    count = 2 if corner_style == "4-stud" else 1
    direction_sign = 1.0 if at_start else -1.0
    midpoint = axis_len_m * _MIDPOINT_FRACTION
    stations = []
    for index in range(1, count + 1):
        station = end.end_stud_station_m + direction_sign * index * stud_thickness_m
        # Never past the wall's own midpoint: on a stub wall the two ends would otherwise
        # pack studs through each other.
        if (station <= midpoint) == at_start:
            stations.append(station)
    return tuple(stations)


@dataclass(frozen=True)
class CornerJunctions:
    """Which (wall, endpoint) pairs sit at an L corner, and who else is there.

    Shared topology, read off ``model.junctions`` once rather than re-derived per layer:
    the stud module (``solver.frame_model``) and the outrigger/furring corner box
    (``furring.frame_furring``) ask the same question — *does this wall own or butt an L
    corner at this end, and which wall is on the other side of it* — about two different
    bands on the same wall pair, and the junction reading itself does not vary by layer.
    """

    #: wall tag -> the ends where this wall OWNS the L corner (its framing runs through it).
    owner: dict[str, set[str]]
    #: wall tag -> the ends where this wall BUTS an L corner another wall owns.
    butting: dict[str, set[str]]
    #: (wall tag, endpoint) -> (the other wall's tag, the other wall's OWN endpoint at this
    #: same corner) — a caller that needs to measure or frame the neighbour's own end (the
    #: corner box's second rip) needs both, not just which wall it is.
    neighbours: dict[tuple[str, str], tuple[str, str]]


def corner_junctions(model: ResolvedModel) -> CornerJunctions:
    """Every L-corner (wall, endpoint) pair in the model, owner and butting alike.

    Purely topological — no assembly, no authored style — so it is correct for any band a
    caller measures off it (a stud layer's structure polygon, a furring layer's outrigger
    band): only which wall owns which corner, and who its neighbour is, ever changes, and
    that is a property of the junction, not of the layer reading it.
    """
    owner: dict[str, set[str]] = {}
    butting: dict[str, set[str]] = {}
    neighbours: dict[tuple[str, str], tuple[str, str]] = {}
    for junction in model.junctions:
        if junction.kind != "l" or not junction.framing_owner:
            continue
        for item in junction.incidents:
            owned = item.wall_tag == junction.framing_owner
            target = owner if owned else butting
            target.setdefault(item.wall_tag, set()).add(item.endpoint)
            other = next(o for o in junction.incidents if o is not item)
            neighbours[(item.wall_tag, item.endpoint)] = (other.wall_tag, other.endpoint)
    return CornerJunctions(owner=owner, butting=butting, neighbours=neighbours)


def _neighbour_band_insets(structure_polygon: Ring, axis_start, direction,
                           axis_len_m: float, at_start: bool) -> tuple[float, float]:
    """(far-face, near-face) inset of the neighbouring wall's band, from the mitre edge.

    The resolved structure polygon is mitred across the shared corner square, so the two
    vertices at this end project onto the axis at the square's two faces. On a square (or
    unresolved) end both project to the same station and the caller degrades gracefully.
    """
    if not structure_polygon:
        return 0.0, 0.0
    insets = []
    for point in structure_polygon:
        station = ((point[0] - axis_start[0]) * direction[0]
                   + (point[1] - axis_start[1]) * direction[1])
        near_start = station <= axis_len_m * _MIDPOINT_FRACTION
        if near_start == at_start:
            insets.append(station if at_start else axis_len_m - station)
    if not insets:
        return 0.0, 0.0
    return min(insets), max(insets)
