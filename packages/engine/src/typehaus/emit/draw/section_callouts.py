"""A-301's detail callouts: a bubble for every starred detail this cut shows (D2-003)."""

from __future__ import annotations

from typehaus.emit.draw.scene import Scene
from typehaus.quantities import M_PER_IN
from typehaus.resolve.geometry_slice import CutPlane
from typehaus.resolve.model import ResolvedModel


def _detail_callouts(model: ResolvedModel, scene: Scene, plane: CutPlane,
                     crop: tuple[tuple[float, float], tuple[float, float]] | None = None,
                     ) -> list:
    """A split-circle callout on the section for every detail this cut passes through.

    A set with details in it and no way to reach them is a set of unrelated drawings, and
    that is what this one was: 76 detail sheets and not one reference to any of them. The
    callout is the half of the cross-reference a reader starts from — they are looking at
    the building, they see a junction, and the bubble says which sheet draws it.

    A bubble points at a wall this cut shows: the condition's own wall when the detail's cut
    is perpendicular and crosses it, else a wall of the same condition (storey + assembly
    pair) standing on one line of the cut. Anything else points at nothing (D2-003).
    """
    from typehaus.emit.draw.callouts import callout_nodes, detail_sheet_numbers
    from typehaus.emit.draw.details import derive_detail_slices

    sheets = detail_sheet_numbers(model)
    placed: list[tuple[float, float]] = []
    out: list = []
    for derived in derive_detail_slices(model):
        sheet = sheets.get(derived.key)
        # Star is the curation the house has already done — the details a builder actually
        # opens. Bubbling all 76 would put more callouts on the section than section.
        if not sheet or derived.transition is None \
                or not derived.transition.stars(derived.key):
            continue
        anchor = _condition_point(model, derived, plane)
        if anchor is None or _too_close(anchor, placed):
            continue
        # A bubble points AT a condition, so one outside the crop points at nothing: on
        # catlin's fireplace cut four of them stood in open sheet twenty feet west of the
        # only thing the drawing shows.
        if crop is not None:
            (cu0, cz0), (cu1, cz1) = crop
            if not (cu0 / M_PER_IN <= anchor[0] <= cu1 / M_PER_IN
                    and cz0 / M_PER_IN <= anchor[1] <= cz1 / M_PER_IN):
                continue
        placed.append(anchor)
        number = "1"  # each detail sheet carries one drawing (not the sheet's last digit)
        out.extend(callout_nodes(anchor, number, sheet, scene.frame.scale
                                 if scene.frame is not None else None))
    return out


def _condition_point(model: ResolvedModel, derived, plane: CutPlane):
    """Where this detail's condition lands in the section's own frame, or ``None``.

    The section's in-plane coordinate is world **y** for an ``x`` cut, and the derived
    detail's ``station`` is a coordinate on ITS cut axis — which, for a perpendicular
    detail, is exactly that y. The elevation comes from the walls the condition names.
    """
    from typehaus.emit.draw.detail_components.geometry import condition_walls

    named = condition_walls(model, derived.condition)
    # A detail cut parallel to this section has a station on the section's own depth axis,
    # so it is located only through a wall of its condition that this cut shows.
    walls = ([w for w in named if _crosses(w, plane)]
             if derived.direction != plane.axis else [])
    u = derived.station
    if not walls and derived.condition.kind.value == "opening_perimeter":
        return None  # an opening detail points at its opening, which this cut misses
    if not walls:
        # The detail was derived at a wall off this cut (D2-003: garage bubbles in the living
        # room). Point at a wall OF THE SAME CONDITION that the cut does show, or at nothing.
        kinds = {(w.storey, w.assembly) for w in named}
        walls = [w for w in model.walls
                 if (w.storey, w.assembly) in kinds and _crosses(w, plane)
                 and abs(w.axis[0][plane.u_index] - w.axis[1][plane.u_index]) < 0.05]
        # Every wall of the condition must stand on one line of the cut, or it is another one.
        lines: dict[float, set] = {}
        for w in walls:
            lines.setdefault(round(w.axis[0][plane.u_index], 1), set()).add((w.storey, w.assembly))
        hit = next((line for line, got in sorted(lines.items()) if got == kinds), None)
        if hit is None:
            return None
        walls = [w for w in walls if round(w.axis[0][plane.u_index], 1) == hit]
        u = walls[0].axis[0][plane.u_index]
    tops = [w.top_z1_m if w.top_z1_m is not None else w.z1_m for w in walls]
    # A stacked junction is at the LOWER wall's top; an eave at the wall's own top.
    pick = max if derived.condition.kind.value in ("wall_roof", "opening_perimeter") else min
    return (u / M_PER_IN, pick(tops) / M_PER_IN)


def _crosses(wall, plane: CutPlane) -> bool:
    """Whether the wall's footprint spans the cut station (to half its depth)."""
    i = plane.perp_index
    (a, b) = wall.axis
    pad = wall.thickness_m / 2.0 + 0.01
    return min(a[i], b[i]) - pad <= plane.station_m <= max(a[i], b[i]) + pad


#: Two callouts closer than this (model inches) would overprint each other's bubble.
_CALLOUT_MIN_GAP_IN = 30.0


def _too_close(point, placed) -> bool:
    return any(abs(point[0] - p[0]) < _CALLOUT_MIN_GAP_IN
               and abs(point[1] - p[1]) < _CALLOUT_MIN_GAP_IN for p in placed)
