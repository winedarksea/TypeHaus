"""The per-wall half of ``mep.run_through_stud``: is a run IN the wall, or merely against it.

The member-by-member reading could only speak about a run that met a stud, so a run between
two studs said nothing about the wall it stands in: ``DU-ERV-RISER-SUP`` was reported against
``W-M-MECH-S`` and ``DU-ERV-RISER-EXH``, 9" away in the same condition, was not. (Part of that
was a riser's z read at its midpoint, fixed in ``mep_bore_geometry.leg_crossings``.)

Every (run, wall) whose envelope meets the wall's **stud plane** — the plates' own plan
rectangles over the framing's z band, less its rough openings — is classified:

* **through** — the centreline crosses a face of the stud plane. A penetration: the members
  it cuts are graded one by one, and a hole in the finish needs no rule. Not reported here.
* **in the cavity** — the centreline stays inside and the whole envelope fits between the
  stud faces. Legal; PASS.
* **too big for the cavity** — the centreline stays inside and the envelope does not fit.
  FAIL with the protrusion.
* **beside the wall** — the centreline never enters, yet the envelope takes part of the stud
  plane: neither in the cavity nor clear of the wall, so studs and plates are notched along
  it and the wall cannot be closed. FAIL, naming how far to move to clear the finished face.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.mep.framing_envelope import (
    TOLERANCE_M,
    at,
    band_over,
    extent_along,
    legs,
    z_overlap,
)
from typehaus.checks.registry import CheckContext
from typehaus.quantities import M_PER_IN

#: How far past a leg's envelope the wall's faces are read.
_LOCAL_M = 0.15


@dataclass(frozen=True)
class CavityVerdict:
    ok: bool
    kind: str  # "cavity" | "oversize" | "beside"
    message: str
    fix: str | None = None


def _wall_planes(ctx: CheckContext) -> list[tuple]:
    """``(wall, stud plane, body, z0, z1, normal)`` for every framed wall with plates."""
    import math

    from shapely.geometry import Polygon

    from typehaus.resolve.framing.profiles import cross_section
    from typehaus.resolve.mep_bore_geometry import member_plan_shape
    from typehaus.resolve.overlay import union_all

    out = []
    for wall in ctx.model.walls:
        plates = [m for m in wall.members if m.category == "plate" and m.p0 != m.p1]
        framing = [m for m in wall.members if m.category in ("plate", "stud", "king")]
        shapes = [member_plan_shape(m, cross_section(m.profile)) for m in plates]
        shapes = [s for s in shapes if s is not None and not s.is_empty]
        if not shapes or len(wall.axis) < 2:
            continue
        body = [Polygon(layer.polygon) for layer in wall.layers if len(layer.polygon) >= 3]
        body = [poly for poly in body if poly.is_valid and not poly.is_empty]
        (ax, ay), (bx, by) = wall.axis[0], wall.axis[-1]
        length = math.hypot(bx - ax, by - ay) or 1.0
        normal = (-(by - ay) / length, (bx - ax) / length)
        z0 = min(m.z0_m for m in framing)
        z1 = max((m.z1_m if m.z1_m is not None else wall.z1_m) for m in framing)
        out.append((wall, union_all(shapes), union_all(body) if body else None,
                    z0, z1, normal))
    return out


def _openings(ctx: CheckContext) -> dict[str, list[tuple]]:
    from typehaus.resolve.mep_envelopes import opening_prisms

    out: dict[str, list[tuple]] = {}
    for _tag, _door, host, footprint, low, high, _for in opening_prisms(ctx.model,
                                                                        erode_m=0.0):
        out.setdefault(host, []).append((footprint, low, high))
    return out


def stud_plane_verdicts(ctx: CheckContext) -> dict[tuple[str, str], CavityVerdict]:
    """``{(run, wall): verdict}`` for every run standing in (not through) a wall's framing."""
    from shapely import STRtree

    planes = _wall_planes(ctx)
    if not planes:
        return {}
    openings = _openings(ctx)
    index = STRtree([plane for _w, plane, _b, _z0, _z1, _n in planes])
    worst: dict[tuple[str, str], tuple[float, CavityVerdict]] = {}
    for leg in legs(ctx.model):
        for position in index.query(leg.footprint):
            wall, plane, body, z0, z1, normal = planes[int(position)]
            band = band_over(leg, plane)
            if band is None or z_overlap(leg, band, z0, z1) <= TOLERANCE_M:
                continue
            axis = leg.axis()
            if not plane.buffer(1e-6).contains(axis) and axis.intersects(plane):
                continue  # through: a penetration, graded member by member
            # Standing in a rough opening is not standing in the framing
            # (``mep.run_through_opening`` owns that).
            for footprint, low, high in openings.get(wall.tag, ()):
                if band[0] - leg.half_z_m < high and band[1] + leg.half_z_m > low:
                    plane = plane.difference(footprint)
            verdict = _classify(leg, wall.tag, plane, body, normal)
            if verdict is None:
                continue
            score, found = verdict
            key = (leg.tag, wall.tag)
            if key not in worst or score > worst[key][0]:
                worst[key] = (score, found)
    return {key: verdict for key, (_s, verdict) in worst.items()}


def _classify(leg, wall_tag: str, plane, body, normal) -> tuple[float, CavityVerdict] | None:
    overlap = leg.footprint.intersection(plane)
    if overlap.is_empty or overlap.area <= 0:
        return None
    axis = leg.axis()
    inside = plane.buffer(1e-6).contains(axis)
    if not inside and axis.intersects(plane):
        return None  # half in an opening: the opening's question, not the framing's
    along = (normal[1], -normal[0])
    c0, c1 = extent_along(axis, along)
    p0, p1 = extent_along(plane, along)
    if not inside and (c1 < p0 + TOLERANCE_M or c0 > p1 - TOLERANCE_M):
        return None  # past the wall's END: the joining wall's run, not this one's
    # Faces read locally, so a wall's far end or a jog does not widen them.
    window = leg.footprint.envelope.buffer(_LOCAL_M)
    e0, e1 = extent_along(leg.footprint, normal)
    s0, s1 = extent_along(plane.intersection(window), normal)
    body = body.intersection(window) if body is not None else None
    if body is not None and body.is_empty:
        body = None
    where = at(leg.a) if leg.plan_m < 1e-9 else f"{at(leg.a)}-{at(leg.b)}"
    size = f'{2 * leg.radius_m / M_PER_IN:.2f}"'
    if inside:
        proud = max(s0 - e0, e1 - s1)
        if proud <= TOLERANCE_M:
            return (0.0, CavityVerdict(True, "cavity", (
                f"{leg.kind} {leg.tag} stands in {wall_tag}'s stud cavity at {where}: its {size} "
                f"envelope fits the {(s1 - s0) / M_PER_IN:.2f}\" stud plane")))
        fits = (e1 - e0) <= (s1 - s0) + TOLERANCE_M
        return (proud, CavityVerdict(False, "oversize", (
            f"{leg.kind} {leg.tag} stands in {wall_tag}'s stud cavity at {where}, but its "
            f"{size} envelope stands {proud / M_PER_IN:.3f}\" proud of the "
            f"{(s1 - s0) / M_PER_IN:.2f}\" stud plane: it does not fit the cavity"),
            fix=(f"centre it in the cavity: move it {proud / M_PER_IN:.3f}\" toward the "
                 "wall's axis" if fits else
                 "drop to a size the cavity holds, fur the wall out, or frame a chase")))
    o0, o1 = extent_along(overlap, normal)
    into = o1 - o0
    if into <= TOLERANCE_M:
        return None
    b0, b1 = extent_along(body, normal) if body is not None else (s0, s1)
    north = (e0 + e1) / 2.0 > (s0 + s1) / 2.0
    clear = (b1 - e0) if north else (e1 - b0)
    return (into, CavityVerdict(False, "beside", (
        f"{leg.kind} {leg.tag} stands beside {wall_tag} at {where} with {into / M_PER_IN:.3f}\" "
        f"of its {size} envelope inside the {(s1 - s0) / M_PER_IN:.2f}\" stud plane: it is "
        "neither in the cavity nor clear of the wall, so every stud and plate along it is "
        "notched and the wall cannot be closed over it"),
        fix=(f"move the run {clear / M_PER_IN:.3f}\" away from the wall to clear its finished "
             "face, or into the cavity at a size that fits it")))
