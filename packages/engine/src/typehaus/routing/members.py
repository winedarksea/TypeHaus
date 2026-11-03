"""Which framing members a lattice edge cuts, whether each cut is legal, and what it costs.

A plumber prices a lane by its holes: every stud bored along a wall, every plate cut by a
riser, every joist bored across a floor. This reads them off the RESOLVED framing — the
studs where the solver put them, never a spacing — and grades each with the same verdicts
the checks use (``resolve/mep_bores``, ``resolve/mep_crossings.member_window``), so the
search cannot propose a hole a check refuses:

* along a wall inside its stud plane, each stud is a bore — ``stud_bore`` at this run's OD,
  bearing or not (``resolve/mep_bore_scope``) — and an envelope that does not keep 5/8" of
  stud either side, or straddles the plane, is refused outright;
* across a wall, an edge that lands on a stud would cut it in two and is refused;
* a riser crosses plates; over half a plate's width it needs R602.6.1's tie and pays twice;
* across a floor, each joist line is a bore: solid-sawn by R502.8.1 (D/3, 2" edges), an
  I-joist inside its flange-clear window at the fabricator's chart price, an open-web truss
  free inside its chord window (that is what it is for).

Members are kept as SORTED STATIONS per line, so an edge's crossings are a bisect.
``notes/framing_bore_limits.md`` §"The router" works one wall and one joist by hand.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from typehaus.quantities import M_PER_IN

if TYPE_CHECKING:  # pragma: no cover - typing only
    from typehaus.resolve.model import ResolvedModel

_STUD_CATEGORIES = ("stud", "king", "jack", "cripple")
_PLATE_CATEGORIES = ("plate", "sill")
#: Bucket width for the perpendicular lookup: the 1/16" grid the repo authors on, x 16.
_BUCKET_M = 0.0254
_EDGE_M = 0.625 * M_PER_IN  # R602.6: 5/8" of stud either side of a bore


@dataclass
class _Wall:
    tag: str
    axis: str  # the wall runs along this axis
    bearing: bool
    z0: float
    z1: float
    perp: tuple[float, float]  # the stud plane across the wall
    along: tuple[float, float]
    stations: list[float] = field(default_factory=list)
    studs: list[tuple[float, float, float, float, str, float]] = field(default_factory=list)
    plates: list[tuple[float, float, str, float]] = field(default_factory=list)  # z0 z1 prof w


@dataclass
class _Floor:
    tag: str
    across: str  # an edge along this axis crosses the member lines
    kind: str    # "open_web" | "i_joist" | "solid_sawn"
    window: tuple[float, float]
    stations: list[float] = field(default_factory=list)
    joists: list[tuple[float, float, float, float, str]] = field(default_factory=list)


class Penetrations:
    """Every wall's studs and plates and every floor's member lines inside one bbox."""

    def __init__(self, model: ResolvedModel, bbox: tuple[float, float, float, float],
                 radius_m: float, *, cavity_radius_m: float | None = None) -> None:
        from typehaus.resolve.mep_bore_scope import r602_6_roles

        self.radius_m = radius_m
        self.cavity_radius_m = cavity_radius_m if cavity_radius_m is not None else radius_m
        roles = r602_6_roles(model)
        self.walls: dict[tuple[str, int], list[_Wall]] = {}
        self.floors: list[_Floor] = []
        minx, miny, maxx, maxy = bbox
        for wall in model.walls:
            built = _wall(wall, wall.tag in roles)
            if built is None or not _overlaps(built, minx, miny, maxx, maxy):
                continue
            grow = radius_m + _BUCKET_M
            for key in range(int((built.perp[0] - grow) / _BUCKET_M),
                             int((built.perp[1] + grow) / _BUCKET_M) + 1):
                self.walls.setdefault((built.axis, key), []).append(built)
        for floor in model.floors:
            built = _floor(floor)
            if built is not None:
                self.floors.append(built)

    def cuts(self, a: tuple[float, float, float], b: tuple[float, float, float], axis: str,
             band: tuple[float, float] | None = None) -> dict[str, int] | None:
        """``{kind: count}`` for one edge, or None when it would need an illegal cut.

        ``band`` replaces the edge's own z for a falling run searched in one nominal plane:
        its real height is not known here, so a floor in its band is crossed, and its member
        windows are ``gravity_search``'s to grade.
        """
        out: dict[str, int] = {}
        r = self.radius_m
        if axis == "z":
            low, high = sorted((a[2], b[2]))
            cav = self.cavity_radius_m
            for wall in self._walls_at("x", a[1]) + self._walls_at("y", a[0]):
                along = a[0] if wall.axis == "x" else a[1]
                across = a[1] if wall.axis == "x" else a[0]
                if not (wall.along[0] <= along <= wall.along[1]
                        and wall.perp[0] - cav < across < wall.perp[1] + cav):
                    continue
                if high > wall.z0 and low < wall.z1 and not (
                        wall.perp[0] + cav - 1e-6 <= across <= wall.perp[1] - cav + 1e-6):
                    # Proud of the stud plane, or a hub the cavity cannot hold (a 3" stack in
                    # a 2x4): every stud and plate along it notched (``mep.run_through_stud``).
                    return None
                for z0, z1, _profile, width in wall.plates:
                    if high > z0 + 1e-6 and low < z1 - 1e-6:
                        kind = "plate_tie" if 2 * r > 0.5 * width else "plate"
                        out[kind] = out.get(kind, 0) + 1
            for floor in self.floors:
                if _riser_on_member(floor, a, low, high, r):
                    return None  # through a joist or chord: not a hole, the member's removal
            return out
        lo, hi = sorted((a[0], b[0]) if axis == "x" else (a[1], b[1]))
        station = a[1] if axis == "x" else a[0]
        z = (a[2] + b[2]) / 2.0
        other = "y" if axis == "x" else "x"
        for wall in self._walls_at(axis, station):
            if wall.perp[0] - r >= station or station >= wall.perp[1] + r:
                continue
            if band is not None:
                # Straddles and plates are banded prisms (``wall_prisms``); a lane wholly
                # inside the cavity at some height in the band pays for its studs.
                if band[1] > wall.z0 and band[0] < wall.z1:
                    count = self._inside_count(wall, station, lo, hi)
                    if count:
                        out["stud"] = out.get("stud", 0) + count
                continue
            if not (wall.z0 < z < wall.z1):
                continue
            if not (wall.perp[0] + r - 1e-6 <= station <= wall.perp[1] - r + 1e-6):
                return None  # proud of the stud plane: in the cavity or clear of it
            if any(z0 - r < z < z1 + r for z0, z1, _p, _w in wall.plates):
                return None  # running along inside a plate
            verdict = self._along(wall, station, lo, hi, z)
            if verdict is None:
                return None
            if verdict:
                out["stud"] = out.get("stud", 0) + verdict
        for wall in self._walls_crossed(other, lo, hi):
            if wall.along[0] <= station <= wall.along[1] and wall.z0 < z < wall.z1 \
                    and _hits_a_stud(wall, station, z, r):
                return None
        for floor in self.floors:
            if floor.across != axis:
                continue
            count = _floor_crossings(floor, station, lo, hi, z, band)
            if not count:
                continue
            if band is None and not (floor.window[0] + r <= z <= floor.window[1] - r):
                return None  # through a chord, a flange or a solid joist's 2" edge
            kind = _FLOOR_KIND[floor.kind]
            if kind == "joist" and not _solid_bore_ok(floor, 2 * r):
                return None
            if kind:
                out[kind] = out.get(kind, 0) + count
        return out

    def riser_blocker(self, x: float, y: float, low: float, high: float
                      ) -> tuple[str, float] | None:
        """``(tag, z)`` of the first wall or floor member a riser here meets, for a refusal."""
        hits = []
        for floor in self.floors:
            if floor.joists and _riser_on_member(floor, (x, y, 0.0), low, high, self.radius_m):
                hits.append((max(low, min(j[3] for j in floor.joists)), floor.tag))
        step = 0.5 * M_PER_IN
        z = low
        while z < high and not hits:
            if self.cuts((x, y, z), (x, y, z + step), "z") is None:
                tags = [w.tag for w in self._walls_at("x", y) + self._walls_at("y", x)]
                hits.append((z, tags[0] if tags else "a stud plane"))
            z += step
        if not hits:
            return None
        z, tag = min(hits)
        return tag, z

    def wall_prisms(self) -> list[Any]:
        """Each wall's illegal zones as hard prisms, for a FALLING run's banded set.

        A drain searches one nominal plane, so the studs and plates at its real height are
        graded the way any partial-height obstacle is (``gravity_band``): a strip along each
        face where the envelope would leave under 5/8" of stud or straddle the plane, the
        whole plane where the pipe cannot fit a stud at all, and every plate.
        """
        from shapely.geometry import box

        from typehaus.routing.obstacles import HardPrism

        r = self.radius_m
        out = []
        seen: set[int] = set()
        for walls in self.walls.values():
            for wall in walls:
                if id(wall) in seen or not wall.studs:
                    continue
                seen.add(id(wall))
                centre = (wall.perp[0] + wall.perp[1]) / 2.0
                half = (wall.perp[1] - wall.perp[0]) / 2.0
                legal = half - r - _EDGE_M
                spans = ([(centre - half - r, centre - legal), (centre + legal, centre + half + r)]
                         if legal > 0 else [(centre - half - r, centre + half + r)])
                for lo, hi in spans:
                    out.append(HardPrism(tag=wall.tag, kind="member",
                                         footprint=_strip(wall, lo, hi, box),
                                         z0_m=wall.z0, z1_m=wall.z1,
                                         applies=frozenset({wall.axis, "z"})))
                for z0, z1, _profile, _width in wall.plates:
                    # A riser cuts a plate (priced); a level lane through one severs it.
                    out.append(HardPrism(tag=wall.tag, kind="member",
                                         footprint=_strip(wall, wall.perp[0] - r,
                                                          wall.perp[1] + r, box),
                                         z0_m=z0 - r, z1_m=z1 + r,
                                         applies=frozenset({"x", "y"})))
        return out

    def _walls_at(self, axis: str, station: float) -> list[_Wall]:
        return self.walls.get((axis, int(station / _BUCKET_M)), [])

    def _walls_crossed(self, axis: str, lo: float, hi: float) -> list[_Wall]:
        """Walls running along ``axis`` whose stud plane an edge from lo to hi crosses."""
        found: dict[int, _Wall] = {}
        for key in range(int(lo / _BUCKET_M), int(hi / _BUCKET_M) + 1):
            for wall in self.walls.get((axis, key), ()):
                if wall.perp[1] > lo and wall.perp[0] < hi:
                    found[id(wall)] = wall
        return list(found.values())

    def _inside_count(self, wall: _Wall, station: float, lo: float, hi: float) -> int:
        """Studs a lane wholly inside the cavity bores, its z unknown (a falling run)."""
        r = self.radius_m
        return sum(1 for i in range(bisect_left(wall.stations, lo),
                                    bisect_right(wall.stations, hi))
                   if abs(station - wall.studs[i][1]) <= wall.studs[i][2] - r - _EDGE_M)

    def _along(self, wall: _Wall, station: float, lo: float, hi: float,
               z: float) -> int | None:
        """Studs bored running along ``wall``; None if any bore is illegal."""
        from typehaus.resolve.mep_bores import stud_bore

        r = self.radius_m
        count = 0
        for i in range(bisect_left(wall.stations, lo), bisect_right(wall.stations, hi)):
            at, centre, half_depth, top, profile, base = wall.studs[i]
            if not (base < z < top):
                continue
            if abs(station - centre) >= half_depth + r:
                continue  # a staggered row's stud on the other face
            if abs(station - centre) > half_depth - r - _EDGE_M + 1e-9:
                return None  # straddles the stud plane or leaves under 5/8" of stud
            verdict = stud_bore(profile, 2 * r / M_PER_IN, bearing=wall.bearing)
            if verdict.ok is not True:
                return None
            count += 1
        return count


_FLOOR_KIND = {"open_web": "", "i_joist": "unpublished", "solid_sawn": "joist"}


def _wall(wall: Any, bearing: bool) -> _Wall | None:
    from typehaus.resolve.framing.profiles import cross_section

    if len(wall.axis) < 2 or not wall.members:
        return None
    (ax, ay), (bx, by) = wall.axis[0], wall.axis[-1]
    if min(abs(bx - ax), abs(by - ay)) > 1e-6:
        return None  # raked or angled: no rectilinear lane rides it
    axis = "x" if abs(bx - ax) >= abs(by - ay) else "y"
    structure = next((ly for ly in wall.layers if ly.function == "structure"), None)
    if structure is None or len(structure.polygon) < 3:
        return None
    across = [p[1] if axis == "x" else p[0] for p in structure.polygon]
    along = sorted((ax, bx) if axis == "x" else (ay, by))
    base = getattr(wall, "frame_base_z_m", None) or wall.z0_m
    out = _Wall(tag=wall.tag, axis=axis, bearing=bearing, z0=base, z1=wall.z1_m,
                perp=(min(across), max(across)), along=(along[0], along[1]))
    studs = []
    for member in wall.members:
        section = cross_section(member.profile)
        if section is None or member.z0_m is None:
            continue
        top = member.z1_m if member.z1_m is not None else wall.z1_m
        if member.category in _STUD_CATEGORIES and member.p0 == member.p1:
            at = member.p0[0] if axis == "x" else member.p0[1]
            centre = member.p0[1] if axis == "x" else member.p0[0]
            studs.append((at, centre, max(section.depth_m, section.width_m) / 2.0, top,
                          member.profile, member.z0_m))
        elif member.category in _PLATE_CATEGORIES and member.p0 != member.p1:
            out.plates.append((member.z0_m, top, member.profile,
                               max(section.depth_m, section.width_m)))
    studs.sort()
    out.studs = studs
    out.stations = [s[0] for s in studs]
    return out


def _floor(floor: Any) -> _Floor | None:
    from typehaus.resolve.mep_crossings import is_member_line, member_window

    window = member_window(floor)
    if window is None:
        return None
    along_x = floor.direction == "x"
    joists = []
    for member in floor.members:
        if member.z0_m is None or not is_member_line(member):
            continue
        p0 = member.p0[1] if along_x else member.p0[0]
        p1 = member.p1[1] if along_x else member.p1[0]
        if abs(p1 - p0) > 1e-6:
            continue
        extent = sorted((member.p0[0], member.p1[0]) if along_x
                        else (member.p0[1], member.p1[1]))
        top = getattr(member, "z1_m", None) or floor.deck_z0_m
        joists.append((p0, extent[0], extent[1], member.z0_m, top, member.profile))
    joists.sort()
    out = _Floor(tag=floor.tag, across="y" if along_x else "x", kind=window.kind,
                 window=(window.z0_m, window.z1_m))
    out.joists = [j[:5] for j in joists]
    out.half_widths = [_half_width(j[5]) for j in joists]  # type: ignore[attr-defined]
    out.stations = [j[0] for j in joists]
    out.profile = joists[0][5] if joists else ""  # type: ignore[attr-defined]
    return out


def _floor_crossings(floor: _Floor, along: float, lo: float, hi: float, z: float,
                     band: tuple[float, float] | None) -> int:
    count = 0
    for i in range(bisect_right(floor.stations, lo), bisect_left(floor.stations, hi)):
        _at, start, end, z0, z1 = floor.joists[i]
        if not start - 1e-6 <= along <= end + 1e-6:
            continue
        if band is None and not z0 <= z <= z1:
            continue
        if band is not None and (band[1] < z0 or band[0] > z1):
            continue
        count += 1
    return count


def _solid_bore_ok(floor: _Floor, diameter_m: float) -> bool:
    from typehaus.resolve.mep_bores import joist_bore

    return joist_bore(getattr(floor, "profile", ""), diameter_m / M_PER_IN).ok is True


def _half_width(profile: str) -> float:
    from typehaus.resolve.framing.profiles import cross_section

    section = cross_section(profile)
    return 0.0 if section is None else min(section.width_m, section.depth_m) / 2.0


def _riser_on_member(floor: _Floor, p: tuple[float, float, float], low: float, high: float,
                     r: float) -> bool:
    """Whether a vertical at ``p`` from ``low`` to ``high`` passes through a member line."""
    across = p[1] if floor.across == "y" else p[0]
    along = p[0] if floor.across == "y" else p[1]
    widths = getattr(floor, "half_widths", ())
    for i, (at, start, end, z0, z1) in enumerate(floor.joists):
        hw = widths[i] if i < len(widths) else 0.0
        if (abs(across - at) < hw + r - 1e-6 and start - 1e-6 <= along <= end + 1e-6
                and high > z0 + 1e-6 and low < z1 - 1e-6):
            return True
    return False


def _hits_a_stud(wall: _Wall, station: float, z: float, radius: float) -> bool:
    """Whether an edge crossing ``wall`` at ``station`` lands on one of its studs."""
    half = 0.75 * M_PER_IN + radius
    for i in range(bisect_left(wall.stations, station - half),
                   bisect_right(wall.stations, station + half)):
        _at, _centre, _half_depth, top, _profile, base = wall.studs[i]
        if base < z < top:
            return True
    return False


def _strip(wall: _Wall, lo: float, hi: float, box: Any) -> Any:
    """A plan rectangle the wall's length by ``[lo, hi]`` across it."""
    if wall.axis == "x":
        return box(wall.along[0], lo, wall.along[1], hi)
    return box(lo, wall.along[0], hi, wall.along[1])


def _overlaps(wall: _Wall, minx: float, miny: float, maxx: float, maxy: float) -> bool:
    if wall.axis == "x":
        return wall.perp[1] >= miny and wall.perp[0] <= maxy and \
            wall.along[1] >= minx and wall.along[0] <= maxx
    return wall.perp[1] >= minx and wall.perp[0] <= maxx and \
        wall.along[1] >= miny and wall.along[0] <= maxy
