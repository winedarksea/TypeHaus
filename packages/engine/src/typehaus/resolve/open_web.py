"""``OpenWebShape``: the web layout of one open-web floor truss, derived from its published row.

The engine carries a truss as ONE member (chords and webs are the maker's plate layout), and
a service passes through it only where the layout has an opening. This derives that layout
from ``JoistSpec.web_openings`` (``PublishedWebOpenings``) so the viewer, the section drawing,
the router and the checks all read the same truss:

* **Stock and trim.** Stock is a multiple of the row's increment; the member is the stock cut
  down, the trim split EVENLY between the two ends (assumed: the row does not say which end
  is cut). Each stock end carries an OSB TrimEnd block of ``trim_end``; trimming eats into it.
* **Chase.** R1 sits in a framed chase at the STOCK centreline, which is where the even split
  puts it: the member midpoint.
* **Webs.** Warren diagonals, panel points ``pitch`` apart on each chord (a diagonal spans
  pitch/2), anchored at the chase face (or the member start) with a half triangle at each
  end of a web run. The stock remainder is absorbed in the LAST diagonal, at the TrimEnd end
  (assumed). Every pocket between webs is a ``D`` opening: the row's round hole, with R2 as
  its rectangular alternative.

``assumptions`` on the shape prints what the row does not publish; a shop layout replaces it.
Rings are ``(run from p0, z above the member's bottom)``, metres, counter-clockwise.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

_EPS = 1e-9


@dataclass(frozen=True)
class WebStick:
    """One drawn piece. ``trim_end``/``vertical``: the box ``[run0, run1] x [z0, z1]``;
    ``diagonal``: the centreline ``(run0, z0) -> (run1, z1)`` between chord faces."""

    kind: str
    run0_m: float
    z0_m: float
    run1_m: float
    z1_m: float


@dataclass(frozen=True)
class WebOpening:
    """A hole through the truss. ``kind``: ``trim_end`` (passes nothing), ``D`` (a web pocket),
    ``R1`` (the chase). ``round_m`` is the largest published round run; ``rect_m`` the
    published ``(along, height)`` rectangle, if any."""

    key: str
    kind: str
    ring: tuple[tuple[float, float], ...]
    round_m: float
    rect_m: tuple[float, float] | None

    @property
    def run0_m(self) -> float:
        return min(u for u, _z in self.ring)

    @property
    def run1_m(self) -> float:
        return max(u for u, _z in self.ring)


@dataclass(frozen=True)
class OpenWebShape:
    """The derived web layout of one truss member (``FramedMember.web``)."""

    stock_m: float
    trim_lo_m: float
    trim_hi_m: float
    length_m: float
    chase_run_m: float | None
    pitch_m: float
    sticks: tuple[WebStick, ...]
    openings: tuple[WebOpening, ...]
    assumptions: tuple[str, ...]
    #: Where the row's own limits are broken (stock outside its range, trim past the TrimEnd).
    issues: tuple[str, ...] = ()
    #: The window the openings were cut in: ``(bottom chord top, top chord underside)``.
    window_z_m: tuple[float, float] = (0.0, 0.0)
    web_thickness_m: float = 0.0

    def opening_at(self, run_m: float, z_m: float) -> WebOpening | None:
        """The opening containing this point (``z_m`` above the member's bottom), or None."""
        for opening in self.openings:
            if _contains_point(opening.ring, run_m, z_m):
                return opening
        return None

    def solid_bands(self) -> list[tuple[float, float]]:
        """Run bands that are solid at every height a service could pass: TrimEnds, chase
        posts and each diagonal where it crosses mid-depth. The router's reading of the webs
        (a duct threads the pockets by construction); the check grades the exact polygons."""
        out: list[tuple[float, float]] = []
        for stick in self.sticks:
            if stick.kind != "diagonal":
                out.append((stick.run0_m, stick.run1_m))
                continue
            du, dz = abs(stick.run1_m - stick.run0_m), abs(stick.z1_m - stick.z0_m)
            half = self.web_thickness_m * math.hypot(du, dz) / (2.0 * max(dz, _EPS))
            mid = (stick.run0_m + stick.run1_m) / 2.0
            out.append((mid - half, mid + half))
        return sorted(out)


@dataclass(frozen=True)
class RunSize:
    """A run's footprint in the truss plane: full width ALONG the member (already stretched
    by crossing obliquity) and full height; ``round_`` for a pipe or round duct."""

    along_m: float
    height_m: float
    round_: bool


def run_of(member, station_m: float, along_x: bool) -> float:
    """Distance from ``member.p0`` along the member to a plan coordinate on its line."""
    axis = 0 if along_x else 1
    sign = 1.0 if member.p1[axis] >= member.p0[axis] else -1.0
    return (station_m - member.p0[axis]) * sign


def station_of(member, run_m: float, along_x: bool) -> float:
    """The plan coordinate of a run distance (inverse of :func:`run_of`)."""
    axis = 0 if along_x else 1
    sign = 1.0 if member.p1[axis] >= member.p0[axis] else -1.0
    return member.p0[axis] + sign * run_m


# --- derivation -----------------------------------------------------------------------


def open_web_shape(row, section, length_m: float) -> OpenWebShape:
    """Derive one truss's shape from its published ``row`` (``PublishedWebOpenings``)."""
    depth, chord, web = section.depth_m, section.flange_thickness_m, section.web_thickness_m
    z_bot, z_top = chord, depth - chord
    pitch, half = row.panel_pitch.meters, row.panel_pitch.meters / 2.0
    assumptions: list[str] = []
    issues: list[str] = []

    stock, trim_lo, trim_hi, trim_end = length_m, 0.0, 0.0, 0.0
    if row.trim_end is not None:
        trim_end = row.trim_end.meters
        inc = row.stock_increment.meters
        stock = math.ceil(length_m / inc - _EPS) * inc
        stock = max(stock, row.stock_min.meters)
        if stock > row.stock_max.meters + _EPS:
            issues.append(f"stock {stock / 0.0254:.0f}\" is over the {row.stock_max.inches:g}\" "
                          "maximum")
        trim_lo = trim_hi = (stock - length_m) / 2.0
        if trim_lo > trim_end + _EPS:
            issues.append(f"{trim_lo / 0.0254:.2f}\" trim per end is over the "
                          f"{row.trim_end.inches:g}\" TrimEnd")
        assumptions.append("trim is split evenly between the two stock ends (the row does "
                           "not say which end is cut), which puts the chase at the member "
                           "midpoint")
    if row.panel_pitch_assumed:
        assumptions.append(f"panel points every {row.panel_pitch.inches:g}\" are assumed "
                           "until the shop layout arrives")
    if row.r2_width is not None:
        assumptions.append("R2 is taken as the rectangular alternative to D in any web "
                           "pocket (its stations are on the shop layout)")

    ta, tb = max(trim_end - trim_lo, 0.0), max(trim_end - trim_hi, 0.0)
    sticks: list[WebStick] = []
    openings: list[WebOpening] = []
    for key, a, b in (("trim-0", 0.0, ta), ("trim-1", length_m - tb, length_m)):
        if b - a > _EPS:
            sticks.append(WebStick("trim_end", a, z_bot, b, z_top))
            openings.append(WebOpening(key, "trim_end", _rect(a, b, z_bot, z_top), 0.0, None))

    # (start, end, reference node as (offset from the start, top?)): see _warren
    runs: list[tuple[float, float, str]] = []
    chase_run: float | None = None
    if row.chase is not None and row.r1_at_stock_centreline:
        chase_run = stock / 2.0 - trim_lo
        c0, c1 = chase_run - row.chase / 2.0, chase_run + row.chase / 2.0
        for a, b in ((c0 - web, c0), (c1, c1 + web)):
            sticks.append(WebStick("vertical", a, z_bot, b, z_top))
        mid = depth / 2.0
        r1w, r1h = row.r1_width.meters, row.r1_height.meters
        openings.append(WebOpening(
            "R1", "R1", _rect(chase_run - r1w / 2.0, chase_run + r1w / 2.0,
                              mid - r1h / 2.0, mid + r1h / 2.0),
            min(r1w, r1h), (r1w, r1h)))
        runs += [(ta, c0 - web, "chase-end"), (c1 + web, length_m - tb, "chase-start")]
        assumptions.append(f"the {row.chase / 0.0254:g}\" chase sits at the stock centreline, "
                           "its verticals one web thick outside it")
    else:
        runs.append((ta, length_m - tb, "middle"))

    rect = (row.r2_width.meters, row.r2_height.meters) if row.r2_width is not None else None
    pockets: list[WebOpening] = []
    for a, b, anchor in runs:
        if b - a <= _EPS:
            continue
        ref_u = {"chase-start": 0.0, "chase-end": b - a, "middle": (b - a) / 2.0}[anchor]
        diagonals, rings = _warren(b - a, half, z_bot, z_top, web, ref_u,
                                   ref_top=anchor != "middle")
        flip = lambda u, a=a: a + u  # noqa: E731
        for (u0, z0, u1, z1) in diagonals:
            sticks.append(WebStick("diagonal", flip(u0), z0, flip(u1), z1))
        for ring in rings:
            pockets.append(WebOpening("", "D", _ccw(tuple((flip(u), z) for u, z in ring)),
                                      row.round_diameter.meters, rect))
        assumptions.append(f"panel points run from the chase face (from midspan where there "
                           f"is no chase); the remainder is absorbed in the end diagonals "
                           f"({half / 0.0254:g}-{2 * half / 0.0254:g}\" wide)")
    pockets.sort(key=lambda o: (o.run0_m + o.run1_m))
    openings += [WebOpening(f"D{i}", o.kind, o.ring, o.round_m, o.rect_m)
                 for i, o in enumerate(pockets)]
    return OpenWebShape(
        stock_m=stock, trim_lo_m=trim_lo, trim_hi_m=trim_hi, length_m=length_m,
        chase_run_m=chase_run, pitch_m=pitch, sticks=tuple(sticks),
        openings=tuple(openings), assumptions=tuple(dict.fromkeys(assumptions)),
        issues=tuple(issues), window_z_m=(z_bot, z_top), web_thickness_m=web)


def _warren(width: float, half: float, z_bot: float, z_top: float, web: float,
            ref_u: float, ref_top: bool):
    """One web run of local length ``width``, panel points ``half`` apart either side of the
    reference node ``(ref_u, ref_top)`` (a top node at a chase face, a bottom one at a bearing
    end or the middle of a chase-less truss). A node must stand ``half`` clear of each end, so
    the end diagonals take the remainder: between ``half`` and ``2 * half`` wide.

    Returns the diagonals ``(u0, z0, u1, z1)`` and the pocket rings (local ``(u, z)``).
    """
    lo = math.ceil((half - ref_u) / half - _EPS)
    hi = math.floor((width - half - ref_u) / half + _EPS)
    nodes = [(ref_u + k * half, ref_top != (k % 2 == 1)) for k in range(lo, hi + 1)]
    if not nodes:  # too short for a node: one diagonal end to end
        nodes = [(0.0, not ref_top)]
    verts = list(nodes)
    if verts[0][0] > _EPS:
        verts.insert(0, (0.0, not verts[0][1]))
    if verts[-1][0] < width - _EPS:
        verts.append((width, not verts[-1][1]))
    z_of = lambda top: z_top if top else z_bot  # noqa: E731
    diagonals = [(verts[i][0], z_of(verts[i][1]), verts[i + 1][0], z_of(verts[i + 1][1]))
                 for i in range(len(verts) - 1)]
    rings = []
    for j, (u, top) in enumerate(verts):
        left = verts[j - 1][0] if j > 0 else verts[0][0]
        right = verts[j + 1][0] if j < len(verts) - 1 else width
        base_z, apex_z = z_of(not top), z_of(top)
        ring = _inset_triangle([(left, base_z), (right, base_z), (u, apex_z)], web / 2.0)
        if ring is not None:
            rings.append(ring)
    return diagonals, rings


def _rect(u0: float, u1: float, z0: float, z1: float) -> tuple[tuple[float, float], ...]:
    return ((u0, z0), (u1, z0), (u1, z1), (u0, z1))


def _area(ring) -> float:
    return 0.5 * sum(ring[i][0] * ring[(i + 1) % len(ring)][1]
                     - ring[(i + 1) % len(ring)][0] * ring[i][1] for i in range(len(ring)))


def _ccw(ring):
    return ring if _area(ring) >= 0 else tuple(reversed(ring))


def _inset_triangle(points, inset: float):
    """The triangle with every SLANTED edge moved inward by ``inset`` (chord and vertical
    edges stay on their faces), or None where nothing is left."""
    ring = list(_ccw(tuple(points)))
    n = len(ring)
    lines = []
    for i in range(n):
        (x0, z0), (x1, z1) = ring[i], ring[(i + 1) % n]
        dx, dz = x1 - x0, z1 - z0
        length = math.hypot(dx, dz)
        if length < _EPS:
            return None
        nx, nz = -dz / length, dx / length
        slanted = abs(dx) > _EPS and abs(dz) > _EPS
        lines.append((nx, nz, nx * x0 + nz * z0 + (inset if slanted else 0.0)))
    out = []
    for i in range(n):
        (a1, b1, c1), (a2, b2, c2) = lines[i - 1], lines[i]
        det = a1 * b2 - a2 * b1
        if abs(det) < _EPS:
            return None
        out.append(((c1 * b2 - c2 * b1) / det, (a1 * c2 - a2 * c1) / det))
    return tuple(out) if _area(out) > 1e-8 else None


def _contains_point(ring, u: float, z: float, tol: float = 1e-9) -> bool:
    n = len(ring)
    for i in range(n):
        (x0, z0), (x1, z1) = ring[i], ring[(i + 1) % n]
        if (x1 - x0) * (z - z0) - (z1 - z0) * (u - x0) < -tol:
            return False
    return True


# --- grading --------------------------------------------------------------------------


@dataclass(frozen=True)
class CrossingGrade:
    opening: WebOpening | None
    ok: bool
    why: str = ""


def grade_crossing(shape: OpenWebShape, run_m: float, z_m: float, size: RunSize) -> CrossingGrade:
    """A run centred at ``(run_m, z_m)`` against the opening it lands in.

    D takes the row's round (or its R2 rectangle), R1 its rectangle, a TrimEnd nothing; the
    run's whole outline must also sit inside the opening's polygon.
    """
    opening = shape.opening_at(run_m, z_m)
    inch = 0.0254
    if opening is None:
        return CrossingGrade(None, False, "it lands on a web or a chord, which nobody bores")
    if opening.kind == "trim_end":
        return CrossingGrade(opening, False, "it lands in the OSB TrimEnd, which passes nothing")
    if size.round_:
        limit = opening.round_m
        if size.height_m > limit + _EPS:
            return CrossingGrade(opening, False, (
                f"a {size.height_m / inch:.2f}\" round is over the {limit / inch:.3g}\" "
                f"{opening.kind} opening it lands in"))
    elif opening.rect_m is None or (
            size.along_m > opening.rect_m[0] + _EPS or size.height_m > opening.rect_m[1] + _EPS):
        want = f"{size.along_m / inch:.2f}\" x {size.height_m / inch:.2f}\""
        has = ("no rectangle" if opening.rect_m is None else
               f"{opening.rect_m[0] / inch:g}\" x {opening.rect_m[1] / inch:g}\"")
        return CrossingGrade(opening, False, (
            f"a {want} rectangle is over the {opening.kind} opening's {has}"))
    if not _inside(opening.ring, run_m, z_m, size):
        return CrossingGrade(opening, False, (
            f"its outline reaches the webs around {opening.kind} opening {opening.key}"))
    return CrossingGrade(opening, True)


def _inside(ring, u: float, z: float, size: RunSize) -> bool:
    """Whether the run's ellipse (round) or box lies in a convex CCW ring."""
    a, b = size.along_m / 2.0, size.height_m / 2.0
    n = len(ring)
    for i in range(n):
        (x0, z0), (x1, z1) = ring[i], ring[(i + 1) % n]
        dx, dz = x1 - x0, z1 - z0
        length = math.hypot(dx, dz)
        if length < _EPS:
            continue
        nx, nz = -dz / length, dx / length
        reach = (math.hypot(nx * a, nz * b) if size.round_ else abs(nx) * a + abs(nz) * b)
        if nx * (u - x0) + nz * (z - z0) - reach < -1e-6:
            return False
    return True


# --- attaching to a floor's members ---------------------------------------------------

#: Member categories that are a whole truss in the deck's own section.
_TRUSS_CATEGORIES = ("joist", "trimmer", "sister_joist")


def _same_member(a: str, b: str) -> bool:
    return " ".join(a.lower().split()) == " ".join(b.lower().split())


def attach_open_web_shapes(members: list, row) -> None:
    """Give every open-web truss in ``members`` its :class:`OpenWebShape`, in place.

    A member whose profile is not the row's product gets none, so a retyped deck reads as
    unlaid (``mep.open_web_panel`` reports UNKNOWN) instead of graded against the wrong row.
    """
    from dataclasses import replace

    from typehaus.resolve.framing.profiles import cross_section

    if row is None:
        return
    cache: dict[float, OpenWebShape] = {}
    for index, member in enumerate(members):
        if member.category not in _TRUSS_CATEGORIES or not _same_member(member.profile, row.member):
            continue
        section = cross_section(member.profile)
        if section.shape != "floor_truss":
            continue
        key = round(member.length_m, 6)
        if key not in cache:
            cache[key] = open_web_shape(row, section, member.length_m)
        members[index] = replace(member, web=cache[key])
