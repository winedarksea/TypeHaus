"""One header per wall opening, chosen before the wall is framed.

Precedence: an authored ``header_spec``; in a NONBEARING host up to 8', the R602.7.4 flat 2x
at the wall's depth where the nailing surface above is within 24" (a 2-2x6 on edge with head
cripples where it is not); in a BEARING host, the smallest R602.7 row at or above
``HeaderStandard.min_bearing_header`` (``header_tables``) with its NJ; anything else draws the
old span ladder as a placeholder and ``structural.header_span`` says why.

``frame_model`` precomputes it the way it does ``jamb_framing``, because the jamb pack is
read three times before the opening is framed.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, replace

from typehaus.model.enums import StructuralRole
from typehaus.quantities import M_PER_IN
from typehaus.quantities import m as _m
from typehaus.resolve.framing.header_tables import TableCondition, header_row, table_condition
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.short_members import MIN_STUD_LINE_M
from typehaus.resolve.framing.tables import (
    flat_header_member,
    header_depth,
    header_profile_from_spec,
    header_size,
    member_actual,
    opening_framing_pattern,
)

#: R602.7.4: the flat nailer serves only where the parallel nailing surface is within 24".
FLAT_HEADER_GAP_MAX_IN = 24.0
#: R602.7.4's opening limit, and the end of R602.7's tables.
PRESCRIPTIVE_SPAN_MAX_IN = 96.0
#: The on-edge member over a nonbearing opening whose head is too far below the plates for
#: a flat nailer: it carries only the head cripples, so it is not graded.
NONSTRUCTURAL_HEADER = "2-2x6"
_FLAT_IN = 1.5
_TOL_M = 1e-6


@dataclass(frozen=True)
class HeaderChoice:
    profile: str
    depth_m: float
    flat: bool = False
    #: The table's NJ; ``None`` leaves the jacks to ``king_jack_counts``.
    jacks: int | None = None
    #: authored | flat | nonstructural | table | ladder
    basis: str = "ladder"


@dataclass(frozen=True)
class HeaderHost:
    """What the solver knows about the opening's wall."""

    role: StructuralRole
    #: The 2x the wall lays flat (its plate member) and its stud depth, inches.
    flat_member: str
    stud_depth_in: float
    #: Plate underside at a station along the wall.
    underside_at: Callable[[float], float]
    #: The table cell its load reads at, or why there is none (BEARING hosts only).
    table: TableCondition | str | None = None
    min_bearing_header: str | None = None


def span_stations(opening) -> tuple[float, float]:
    """The clear span between the trimmers: the RO, plus a pocket's cavity (2W + 1")."""
    lo = opening.center_m - opening.width_m / 2
    hi = opening.center_m + opening.width_m / 2
    pattern = opening_framing_pattern(opening.operation)
    if pattern.pocket_cavity and opening.pocket_run_m > 1e-9 and opening.pocket_sign:
        if opening.pocket_sign > 0:
            hi += opening.pocket_run_m
        else:
            lo -= opening.pocket_run_m
    return lo, hi


def authored_header(spec: str | None) -> HeaderChoice | None:
    """The member an authored ``header_spec`` names; a flat one lies on its 1 1/2" face. An
    unparseable spec is ``None`` and the caller sizes the header: a typo never does."""
    profile = header_profile_from_spec(spec) if spec is not None else None
    if profile is None:
        return None
    section = cross_section(profile)
    flat = flat_header_member(spec) is not None
    return HeaderChoice(profile, section.width_m if flat else section.depth_m, flat,
                        basis="authored")


def ladder_header(opening) -> HeaderChoice:
    """A bare fixture's header, as before R602.7 was read: authored, else the ladder."""
    authored = authored_header(opening.header_spec)
    if authored is not None:
        return authored
    structural = opening_framing_pattern(opening.operation).header_is_structural
    size = header_size(_m(opening.width_m), bearing=structural)
    return HeaderChoice(size, header_depth(size, _m(opening.width_m)).meters)


def choose_header(opening, host: HeaderHost, header_bottom_m: float) -> HeaderChoice:
    authored = authored_header(opening.header_spec)
    if authored is not None:
        return authored
    lo, hi = span_stations(opening)
    span_in = (hi - lo) / M_PER_IN

    def gap_m(depth_m: float) -> float:
        # A raked top: the largest gap across the span governs.
        return max(host.underside_at(lo), host.underside_at(hi)) - header_bottom_m - depth_m

    def depth_m(size: str) -> float:
        return member_actual(size.split("-")[-1])[1] * M_PER_IN

    within = span_in <= PRESCRIPTIVE_SPAN_MAX_IN + 1e-6
    if host.role is StructuralRole.NONBEARING and within:
        if gap_m(_FLAT_IN * M_PER_IN) <= FLAT_HEADER_GAP_MAX_IN * M_PER_IN + _TOL_M:
            return HeaderChoice(host.flat_member, _FLAT_IN * M_PER_IN, True, basis="flat")
        return HeaderChoice(NONSTRUCTURAL_HEADER, depth_m(NONSTRUCTURAL_HEADER),
                            basis="nonstructural")
    if (host.role is StructuralRole.BEARING and within
            and isinstance(host.table, TableCondition)):
        row = header_row(
            host.table, span_in, host.stud_depth_in, min_size=host.min_bearing_header,
            unbraced=lambda size: gap_m(depth_m(size)) >= MIN_STUD_LINE_M - 1e-9,
            fits=lambda size: gap_m(depth_m(size)) >= -_TOL_M)
        if row is not None:
            return HeaderChoice(row.size, depth_m(row.size), jacks=row.jacks, basis="table")
    # The placeholder. In a BEARING host a pocket or bifold no longer earns a nonbearing head.
    bearing = host.role is StructuralRole.BEARING
    width = _m(hi - lo) if bearing else _m(opening.width_m)
    structural = bearing or opening_framing_pattern(opening.operation).header_is_structural
    size = header_size(width, bearing=structural)
    return HeaderChoice(size, header_depth(size, width).meters)


def host_table(index, ground_snow_psf, wall, opening) -> TableCondition | str:
    """The R602.7 cell this opening's span reads at, or why there is none."""
    lo, hi = span_stations(opening)
    condition = index.condition(wall, lo, hi)
    if condition.point_loads:
        return f"point load(s) {', '.join(condition.point_loads)} bear inside the span"
    width = condition.building_width_m
    return table_condition(condition.exterior, bool(condition.roofs),
                           tuple(kind for _tag, kind in condition.floors),
                           None if width is None else width / 0.3048, ground_snow_psf)


def plate_underside_at(plan, rw) -> Callable[[float], float] | None:
    """``frame_wall``'s ``top_at``: the underside of the top plates at a station."""
    from typehaus.resolve.framing.solver import (
        _framing_axis,
        _top_plate_count,
        _wall_top_elevations,
        frames_as_members,
        structure_layer,
    )

    layer = structure_layer(plan, rw.assembly)
    if not frames_as_members(layer):
        return None
    (x0, y0), (x1, y1) = _framing_axis(rw)
    axis_len = ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5
    top_start, top_end = _wall_top_elevations(rw)
    plates = (0 if layer.framing.wall_frame == "plate"
              else _top_plate_count(layer.framing)) * _FLAT_IN * M_PER_IN

    def underside(station: float) -> float:
        fraction = station / axis_len if axis_len else 0.0
        return top_start + (top_end - top_start) * fraction - plates

    return underside


def choose_headers(plan, model, by_host: dict[str, list]) -> None:
    """Attach a ``HeaderChoice`` to every opening in ``by_host``, in place."""
    from typehaus.model.framing_standards import HeaderStandard
    from typehaus.resolve.framing.solver import structure_layer
    from typehaus.resolve.header_loads import LoadIndex

    standard = next((el for el in plan.all_elements() if isinstance(el, HeaderStandard)), None)
    min_bearing = standard.min_bearing_header if standard is not None else None
    ground_snow = getattr(getattr(plan.project, "site", None), "ground_snow_load_psf", None)
    index = None
    for wall_tag, openings in by_host.items():
        rw = model.wall(wall_tag)
        underside = plate_underside_at(plan, rw) if rw is not None else None
        if underside is None:
            continue
        framing = structure_layer(plan, rw.assembly).framing
        flat_member = framing.plate_member or framing.member
        role = getattr(plan.by_tag(wall_tag), "structural_role", StructuralRole.UNKNOWN)
        for position, opening in enumerate(openings):
            if opening.header_in_band is not None:
                continue
            table = None
            if role is StructuralRole.BEARING:
                index = index or LoadIndex.of(plan, model)
                table = host_table(index, ground_snow, rw, opening)
            host = HeaderHost(role, flat_member, member_actual(flat_member)[1], underside,
                              table, min_bearing)
            bottom = rw.base_ref_z_m + opening.sill_m + opening.height_m
            openings[position] = replace(opening, header=choose_header(opening, host, bottom))
