"""Joint nailers behind a sheet-laid cladding panel's vertical joints (decision #146).

A panel siding hung on HORIZONTAL furring (a girt band) meets the furring only at the
courses, so its vertical edges are bare between them; the panel maker wants every edge on
2x framing. A furring band with ``FramingSpec.panel_joint_nailers`` takes a nailer of its
own stock, laid flat in its plane and cut between the courses, at each vertical joint: one
piece per bare span the courses, jamb posts and ladders leave (``unbacked_spans``), never
below the band's own start (the panel's foot over a screened base stays bare). The run's
two end edges take one too, flush with the panel's end (``end_stations``). A joint
whose nailer would clash with an opening or another member is not placeable, and the
column walk moves the joint instead (``sheet_layout.lay_run``).
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.furring import STRAPPING_CATEGORY
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember
from typehaus.resolve.sheet_layout_backing import Rect, unbacked_spans
from typehaus.resolve.sheet_stock import wall_layer

_MIN_PIECE_M = 0.125 * M_PER_IN  # a bare span under a panel gap's width needs no piece
_EPS = 1e-6
NAILER_PREFIX = "nailer-"


@dataclass(frozen=True)
class NailerSpec:
    """The stock a band's joint nailers are cut from: ``face`` on the wall, ``depth`` through."""

    band: str
    profile: str
    material: str
    face_m: float
    depth_m: float


def cladding_backing(wall, layer):
    """The framed layer a cladding layer is hung on: the nearest furring or structure inboard."""
    index = next(i for i, ly in enumerate(wall.layers) if ly is layer)
    return next((ly for ly in reversed(wall.layers[:index])
                 if ly.function in ("furring", "structure") and not ly.is_cavity), None)


def nailer_spec(plan, wall, backing) -> NailerSpec | None:
    """The band's nailer stock where it is horizontal furring that asks for joint nailers."""
    if backing is None or backing.function != "furring":
        return None
    authored = wall_layer(plan, wall, backing.source_layer_name or backing.name)
    spec = authored.framing if authored is not None else None
    if spec is None or not spec.panel_joint_nailers or spec.direction != "horizontal":
        return None
    section = cross_section(spec.member)
    face, depth = max(section.width_m, section.depth_m), min(section.width_m, section.depth_m)
    if spec.laid == "edge":
        face, depth = depth, face
    return NailerSpec(backing.name, spec.member, authored.material_ref, face, depth)


def band_floor(wall) -> float:
    """Where the furring band starts: over a screened rainscreen base the starter course is
    lifted clear of the base metal (``apply_girt_starter_rise``), and so is every nailer."""
    return wall.z0_m + getattr(wall, "girt_starter_rise_m", 0.0)


def _overlaps(a: tuple[float, float, float, float], b: tuple[float, float, float, float]
              ) -> bool:
    return (min(a[1], b[1]) - max(a[0], b[0]) > _EPS
            and min(a[3], b[3]) - max(a[2], b[2]) > _EPS)


def nailer_spans(ctx, spec: NailerSpec, x: float) -> list[tuple[float, float]] | None:
    """The bare spans along the joint at ``x`` a nailer fills, or None where one would clash
    with an opening or a member already in the band."""
    holes = [(h[1], h[2], h[3], h[4]) for h in ctx.holes]
    floor = band_floor(ctx.run.face_at(x).wall)
    spans = [(max(a, floor), b) for a, b in unbacked_spans(
        ctx.rects, True, x, ctx.z0, ctx.top(x), ctx.params.bearing, holes)
        if b - max(a, floor) > _MIN_PIECE_M]
    half = spec.face_m / 2.0
    for a, b in spans:
        piece = (x - half, x + half, a, b)
        if any(_overlaps(piece, h) for h in holes) or any(
                _overlaps(piece, (r.s0, r.s1, r.z0, r.z1)) for r in ctx.rects):
            return None
    return spans


def nailers_at(run, frame_of, spec: NailerSpec, ctx, breaks: list[float], label: str = ""):
    """``(wall tag, member, rect)`` per nailer piece at every placeable joint in ``breaks``.

    ``frame_of(face)`` is the face's ``Frame``; a piece is keyed on its wall, ``label`` and
    the joint's index along the run, so a re-resolve mints the same keys."""
    out = []
    for index, x in enumerate(breaks):
        spans = nailer_spans(ctx, spec, x)
        face = run.face_at(x)
        frame = frame_of(face)
        if not spans or frame is None:
            continue
        offset = frame.inner + frame.side * spec.depth_m / 2.0
        point = (frame.origin[0] + frame.d[0] * x + frame.n[0] * offset,
                 frame.origin[1] + frame.d[1] * x + frame.n[1] * offset)
        for piece, (a, b) in enumerate(spans):
            key = f"{NAILER_PREFIX}{spec.band}-{label}{index:03d}-{piece}"
            member = FramedMember(face.wall.uid, key, STRAPPING_CATEGORY, spec.profile, point,
                                  point, a, b, b - a, orient=frame.n, material=spec.material)
            out.append((face.wall.tag, member,
                        Rect(x - spec.face_m / 2.0, x + spec.face_m / 2.0, a, b, key)))
    return out


def end_stations(run, spec: NailerSpec) -> list[float]:
    """Where an end nailer centres: flush with each end of the run, under the panel's edge."""
    half = spec.face_m / 2.0
    return [run.lo + half, run.hi - half] if run.hi - run.lo > 2.0 * spec.face_m else []


def with_nailers(model, by_wall: dict[str, list]) -> None:
    """Append each wall's derived nailers to its members."""
    from dataclasses import replace

    if not by_wall:
        return
    model.walls = [replace(w, members=(*w.members, *by_wall[w.tag])) if w.tag in by_wall
                   else w for w in model.walls]
