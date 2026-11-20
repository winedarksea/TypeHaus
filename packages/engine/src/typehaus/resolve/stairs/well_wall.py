"""Frame the rest of a face-only well wall standing on a U-stair's partition line.

``u_split`` frames the partition between the flights, up to the landing's corner post. An
authored wall on that line with no framing of its own (``STAIRWELL_PARTITION_4H``) may run
on past it, into the landing zone. This pass frames that remainder once: plates where the
base and top lines are free, studs at each free bay's ends and on 16" between, each cut
around whatever crosses the line there (posts, landing rims, decks, risers) so it bears on
a plate, a rim or a post. A bay narrower than a stud takes none; a plate that meets the
stair's own plate end to end extends it.
"""

from __future__ import annotations

from dataclasses import replace

from typehaus.model.spatial import Stair
from typehaus.resolve.framing.footprint import member_footprint
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.framing.solver import frames_as_members, structure_layer
from typehaus.resolve.model import FramedMember, ResolvedModel
from typehaus.resolve.stairs.bearing import _authored_post_spans
from typehaus.resolve.stairs.common import _FRAMING_SPACING_M

_ON_LINE_M = 0.003  # a wall axis this close to the partition centreline is on it
_MIN_STUD_M = 0.15  # a free height shorter than this takes no stud
_TOL = 1e-4


def _subtract(spans: list[tuple[float, float]], cut: tuple[float, float]
              ) -> list[tuple[float, float]]:
    out = []
    for lo, hi in spans:
        if cut[1] <= lo + _TOL or cut[0] >= hi - _TOL:
            out.append((lo, hi))
            continue
        if cut[0] > lo + _TOL:
            out.append((lo, cut[0]))
        if cut[1] < hi - _TOL:
            out.append((cut[1], hi))
    return out


def frame_well_walls(model: ResolvedModel, stair: Stair,
                     members: tuple[FramedMember, ...]) -> tuple[FramedMember, ...]:
    """``members`` plus the framing a face-only well wall still needs past the partition."""
    plates = {m.child_key: m for m in members
              if m.child_key in ("well-partition-plate-bottom", "well-partition-plate-top")}
    if len(plates) != 2:
        return members
    bottom, top = plates["well-partition-plate-bottom"], plates["well-partition-plate-top"]
    along = 1 if stair.run_direction == "y" else 0
    cross = bottom.p0[1 - along]
    stud = cross_section("2x4")
    half, depth_half, plate = stud.width_m / 2.0, stud.depth_m / 2.0, stud.width_m
    base_z, top_z = bottom.z0_m, top.z1_m
    partition = [m for m in members if m.category == "partition"]
    framed = (min(min(m.p0[along], m.p1[along]) - (half if m.p0 == m.p1 else 0.0)
                  for m in partition),
              max(max(m.p0[along], m.p1[along]) + (half if m.p0 == m.p1 else 0.0)
                  for m in partition))
    spans: list[tuple[float, float]] = []
    for wall in model.walls:
        (a, b) = wall.axis
        layer = structure_layer(model.plan, wall.assembly)
        if (layer is None or frames_as_members(layer) or layer.masonry is not None
                or abs(a[1 - along] - cross) > _ON_LINE_M
                or abs(b[1 - along] - cross) > _ON_LINE_M
                or wall.z1_m <= base_z + _TOL or wall.z0_m >= top_z - _TOL):
            continue
        spans += _subtract([tuple(sorted((a[along], b[along])))], framed)
    if not spans:
        return members
    # What crosses the stud plane, as (s_lo, s_hi, z_lo, z_hi).
    obstacles = []
    for box, z0, z1 in _authored_post_spans(model):
        if box[1 - along] < cross + depth_half and box[3 - along] > cross - depth_half:
            obstacles.append((box[along], box[2 + along], z0, z1))
    for m in members:
        if m.category == "partition":
            continue
        ring, z0, z1 = member_footprint(m)
        cs = [p[1 - along] for p in ring]
        if min(cs) < cross + depth_half - _TOL and max(cs) > cross - depth_half + _TOL:
            ss = [p[along] for p in ring]
            obstacles.append((min(ss), max(ss), z0, z1))

    def blocked(lo: float, hi: float, z_lo: float, z_hi: float) -> list[tuple]:
        return [o for o in obstacles if o[0] < hi - _TOL and o[1] > lo + _TOL
                and o[2] < z_hi - _TOL and o[3] > z_lo + _TOL]

    def free_runs(lo: float, hi: float, z_lo: float, z_hi: float) -> list[tuple]:
        runs = [(lo, hi)]
        for o in blocked(lo, hi, z_lo, z_hi):
            runs = _subtract(runs, (o[0], o[1]))
        return runs

    def bays(lo: float, hi: float) -> list[tuple]:
        """Runs of cells where some stud-worthy height stays free between the plates."""
        edges = sorted({lo, hi} | {e for o in obstacles for e in o[:2] if lo < e < hi})
        out: list[tuple] = []
        for c_lo, c_hi in zip(edges, edges[1:], strict=False):
            heights = [(base_z + plate, top_z - plate)]
            for o in blocked(c_lo, c_hi, *heights[0]):
                heights = _subtract(heights, (o[2], o[3]))
            if not any(hi_z - lo_z >= _MIN_STUD_M for lo_z, hi_z in heights):
                continue
            if out and abs(out[-1][1] - c_lo) < _TOL:
                out[-1] = (out[-1][0], c_hi)
            else:
                out.append((c_lo, c_hi))
        return out

    def at(s: float) -> tuple[float, float]:
        return (s, cross) if along == 0 else (cross, s)

    orient = (1.0, 0.0) if along == 0 else (0.0, 1.0)
    out = list(members)
    extended: dict[str, FramedMember] = {}
    new: list[FramedMember] = []
    bottom_runs, top_runs = [], []
    for lo, hi in spans:
        for key, z_lo, runs in (("bottom", base_z, bottom_runs),
                                ("top", top_z - plate, top_runs)):
            for r_lo, r_hi in free_runs(lo, hi, z_lo, z_lo + plate):
                runs.append((r_lo, r_hi))
                own = extended.get(key, plates[f"well-partition-plate-{key}"])
                ends = (own.p0[along], own.p1[along])
                if any(abs(e - r_lo) < _TOL or abs(e - r_hi) < _TOL for e in ends):
                    far = r_hi if abs(max(ends) - r_lo) < _TOL else r_lo
                    near = min(ends) if far == r_hi else max(ends)
                    extended[key] = replace(own, p0=at(near), p1=at(far),
                                            length_m=abs(far - near))
                    continue
                new.append(FramedMember(stair.uid, f"well-partition-ext-plate-{key}-"
                                        f"{len(new):03d}", "partition", "2x4", at(r_lo),
                                        at(r_hi), z_lo, z_lo + plate, r_hi - r_lo))
        # Studs: each free bay's two ends, and 16" between.
        for b_lo, b_hi in bays(lo, hi):
            if b_hi - b_lo < stud.width_m - _TOL:
                continue
            positions = [b_lo + half]
            while positions[-1] + _FRAMING_SPACING_M < b_hi - half - stud.width_m:
                positions.append(positions[-1] + _FRAMING_SPACING_M)
            if b_hi - half - positions[-1] >= stud.width_m - _TOL:
                positions.append(b_hi - half)
            for s in positions:
                z_lo = base_z + (plate if any(r[0] - _TOL <= s - half and s + half
                                              <= r[1] + _TOL for r in bottom_runs) else 0.0)
                z_hi = top_z - (plate if any(r[0] - _TOL <= s - half and s + half
                                             <= r[1] + _TOL for r in top_runs) else 0.0)
                heights = [(z_lo, z_hi)]
                for o in blocked(s - half, s + half, z_lo, z_hi):
                    heights = _subtract(heights, (o[2], o[3]))
                for h_lo, h_hi in heights:
                    if h_hi - h_lo < _MIN_STUD_M:
                        continue
                    new.append(FramedMember(stair.uid, f"well-partition-ext-stud-"
                                            f"{len(new):03d}", "partition", "2x4", at(s),
                                            at(s), h_lo, h_hi, h_hi - h_lo, orient=orient))
    out = [extended.get(m.child_key.rsplit("-", 1)[-1], m)
           if m.child_key in plates else m for m in out]
    return tuple(out) + tuple(new)
