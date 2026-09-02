"""Hidden-line orthographic exterior elevations (M3, → 30 §Elevations).

This is the drawing half; :mod:`typehaus.emit.draw.elevation_project` is the geometry half.
The projector turns the derived-geometry IR into a front-to-back list of visible (u, z)
regions; everything here decides how those regions are *drawn* — which AIA layer, at what
weight, with what texture on the cladding, what glyph inside a window, and where the grade
line, the material callouts and the level datums go without landing on top of each other.

Depth hierarchy
---------------
Three layers carry it. The **dominant plane** — the depth bucket holding the most visible
area, which on every facade of a house is that facade's own cladding — keeps ``A-WALL``.
Anything *behind* it by more than :data:`_FACADE_BAND_M` recedes to ``A-WALL-BEYD``.
Anything below grade goes to ``A-WALL-BELW``, dashed. Note the asymmetry: a thing standing
*in front* of the dominant plane (a porch, a balcony guard, a retaining wall) keeps the full
weight, because it is nearer the eye, not further from it.
"""

from __future__ import annotations

from typehaus.emit.draw.elevation_annotate import (
    ANNO_HEIGHT_IN,
    emit_grade_profile,
    emit_sheet_annotations,
    grade_datum,
)
from typehaus.emit.draw.elevation_finish import emit_cladding_texture
from typehaus.emit.draw.elevation_openings import emit_opening_glyphs
from typehaus.emit.draw.elevation_project import (
    VisiblePiece,
    collect_candidates,
    occlude,
    rings_of,
    split_at_grade,
    view_for,
)
from typehaus.emit.draw.scene import Polyline, Scene, SceneBuilder, Text
from typehaus.quantities import M_PER_IN
from typehaus.resolve import overlay
from typehaus.resolve.model import ResolvedModel

#: How far past the building the sheet's right-hand annotation column starts.
_EXTEND_M = 0.6096  # 24"

#: Two surfaces within this depth of each other read as one plane on a drawing — a wall and
#: its window casing, a roof and its drip edge. 24" is one wall thickness plus its trim and a
#: reveal; a jog smaller than that is detail, not massing.
_FACADE_BAND_M = 0.6096

#: Depth-bucket width for finding the dominant plane. Coarser than :data:`_FACADE_BAND_M` on
#: purpose: the question is which *massing* plane carries the elevation, and a facade whose
#: segments differ by an inch of cladding build-up must land in one bucket.
_PLANE_BUCKET_M = 0.3048  # 12"

#: Two wall segments whose outer faces agree to within this are the same plane of cladding.
#: 1/2" — every exterior wall in this house aligns on ``face("sheathing-ext")``, so coplanar
#: segments agree exactly and the tolerance only has to absorb the overlay grid.
_COPLANAR_M = 0.0127

#: Ring simplification after a merge, metres. Same tolerance the projector uses.
_SIMPLIFY_M = 1e-4

#: Line weights, mm, by drawing family at the facade plane. The receding and below-grade
#: bands scale these down rather than replacing them, so a receding window still reads as a
#: window and not as a wall.
_FAMILY_WEIGHT = {"body": 0.50, "roof": 0.50, "trim": 0.35, "rail": 0.30,
                  "glaz": 0.25, "sash": 0.20, "door": 0.35}
_BAND_WEIGHT_SCALE = {"facade": 1.0, "beyond": 0.55, "below": 0.45}

#: The layer each family draws on at the facade plane. Receding *building* — wall, roof,
#: trim, guard — goes to A-WALL-BEYD outright, which is what the layer exists for. An
#: opening keeps its own layer wherever it stands and carries the depth in its weight
#: instead: a window on the garage is still a window, and greying it out loses that.
_FAMILY_LAYER = {"body": "A-WALL", "roof": "A-ROOF", "trim": "A-ROOF-TRIM",
                 "rail": "A-RAIL", "glaz": "A-GLAZ", "sash": "A-GLAZ-SASH",
                 "door": "A-DOOR"}
_RECEDES_TO_BEYOND = frozenset({"body", "roof", "trim", "rail"})


def build_elevation(model: ResolvedModel, facing: str) -> Scene:
    """Project the building into one cardinal elevation, hidden lines removed.

    ``facing`` is the compass direction the elevation *looks at* — a "south elevation" is the
    view of the south face, seen from the south. The signature is the one
    ``sheets.py``/``render.py`` call; everything else here is free to move.
    """
    view = view_for(facing)
    b = SceneBuilder(name=f"elevation-{view.facing}", units="in")
    pieces = _merge_wall_runs(occlude(collect_candidates(model, view), view))
    grade_z = grade_datum(model)
    facade_depth = _dominant_plane_depth(pieces)
    facade = [piece for piece in pieces if _band_of(piece, facade_depth) == "facade"]

    for piece in pieces:
        _emit_piece(b, piece, facade_depth, grade_z)
    emit_cladding_texture(b, model, facade, view)
    emit_opening_glyphs(b, model, pieces, view)

    lo_u, hi_u = _facade_extent(pieces, facade_depth)
    emit_grade_profile(b, model, view, facade_depth, lo_u, hi_u)
    emit_sheet_annotations(b, model, facade, _margin_u(pieces))
    b.add(Text(anchor=(lo_u / M_PER_IN, _label_z(pieces)),
               content=f"{view.facing.upper()} ELEVATION",
               height=ANNO_HEIGHT_IN * 1.5, align="left"))
    return b.build()


def _merge_wall_runs(pieces: list[VisiblePiece]) -> list[VisiblePiece]:
    """Dissolve the seams between coplanar wall segments of the same material.

    A facade is authored as six or seven wall segments because that is where the partitions
    inside land, and this house says so about its own framing in as many words: *"a course is
    one stick on the job, and the seam is an artifact of where the partitions land inside"*.
    Drawn segment by segment the facade came out as a grid of panels — a vertical rule at
    every tee and a horizontal one at every storey — none of which is a joint in the cladding.
    Unioning the visible regions removes exactly the shared edges and keeps every real one: a
    material change, a plane change and an opening all survive because they break the group.

    Provenance goes to the largest contributor. That is a real loss — the merged run carries
    one wall's uid into XDATA rather than six — and it is the price of drawing the building
    instead of the model. Only walls merge; a window, a guard and a gutter are products with
    their own identity and keep it.
    """
    grouped: dict[tuple[str, str | None, int], list[VisiblePiece]] = {}
    passthrough: list[VisiblePiece] = []
    for piece in pieces:
        candidate = piece.candidate
        if candidate.kind != "wall":
            passthrough.append(piece)
            continue
        key = (candidate.family, candidate.material_ref,
               round(candidate.near_depth / _COPLANAR_M))
        grouped.setdefault(key, []).append(piece)
    out = list(passthrough)
    for members in grouped.values():
        principal = max(members, key=lambda item: item.geometry.area)
        if len(members) == 1:
            out.append(principal)
            continue
        merged = overlay.union_all([item.geometry for item in members])
        out.append(VisiblePiece(candidate=principal.candidate,
                                geometry=merged.simplify(_SIMPLIFY_M, preserve_topology=True)))
    return out


def _margin_u(pieces: list[VisiblePiece]) -> float:
    """The u past *everything* drawn — where the annotation column starts.

    Measured off the whole projection rather than off the facade plane: the freestanding
    garage is 28 feet in front of this house's north wall, so on the east elevation it reaches
    well past the facade — measuring off the facade plane would draw the dimension string
    straight through it.
    """
    if not pieces:
        return _EXTEND_M
    return float(max(piece.geometry.bounds[2] for piece in pieces)) + _EXTEND_M


# --- depth banding -----------------------------------------------------------------------
def _dominant_plane_depth(pieces: list[VisiblePiece]) -> float:
    """The depth of the plane carrying the most visible area — the facade's own cladding.

    Taking the *frontmost* plane instead is the obvious rule and it is wrong here: on this
    house's south elevation the freestanding sunken-garden structure stands 30 feet in front
    of the building, and making that the reference greys out the entire house on its own
    principal elevation.
    """
    if not pieces:
        return 0.0
    area_by_bucket: dict[int, float] = {}
    for piece in pieces:
        bucket = round(piece.candidate.near_depth / _PLANE_BUCKET_M)
        area_by_bucket[bucket] = area_by_bucket.get(bucket, 0.0) + piece.geometry.area
    dominant: int = max(area_by_bucket.items(), key=lambda item: (item[1], -item[0]))[0]
    return float(dominant) * _PLANE_BUCKET_M


def _band_of(piece: VisiblePiece, facade_depth: float) -> str:
    return "beyond" if piece.candidate.near_depth > facade_depth + _FACADE_BAND_M else "facade"


def _emit_piece(b: SceneBuilder, piece: VisiblePiece, facade_depth: float,
                grade_z: float) -> None:
    """One visible region's outline, split at the grade line so the buried part reads buried."""
    family = piece.candidate.family
    band = _band_of(piece, facade_depth)
    above, below = split_at_grade(piece.geometry, grade_z)
    for geometry, geometry_band in ((above, band), (below, "below")):
        if geometry.is_empty:
            continue
        layer = ("A-WALL-BELW" if geometry_band == "below"
                 else "A-WALL-BEYD" if geometry_band == "beyond" and family in _RECEDES_TO_BEYOND
                 else _FAMILY_LAYER[family])
        weight = _FAMILY_WEIGHT[family] * _BAND_WEIGHT_SCALE[geometry_band]
        linetype = "DASHED" if geometry_band == "below" else "CONTINUOUS"
        for ring in rings_of(geometry):
            b.add(Polyline(points=tuple((u / M_PER_IN, z / M_PER_IN) for u, z in ring),
                           layer=layer, closed=True, lineweight=round(weight, 3),
                           linetype=linetype, uid=piece.candidate.uid,
                           tag=piece.candidate.tag))


def _facade_extent(pieces: list[VisiblePiece], facade_depth: float) -> tuple[float, float]:
    """The u-range of the facade plane itself — what the sheet margins are measured off."""
    facade = [piece for piece in pieces if _band_of(piece, facade_depth) == "facade"]
    chosen = facade or pieces
    if not chosen:
        return (0.0, 0.0)
    bounds = [piece.geometry.bounds for piece in chosen]
    return (min(bound[0] for bound in bounds), max(bound[2] for bound in bounds))


def _label_z(pieces: list[VisiblePiece]) -> float:
    tops = [piece.geometry.bounds[3] for piece in pieces]
    return ((max(tops) if tops else 0.0) + 0.6) / M_PER_IN
