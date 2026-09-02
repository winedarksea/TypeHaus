"""Cladding expression on an elevation — the outermost visible layer's own module.

``ResolvedLayer`` carries ``material_ref`` and ``board_run`` (which way the boards of a board
finish run), but neither reaches an elevation on its own: without this module the facade is a
bare outline that cannot tell a standing-seam wall from a brick one. This module draws the
module lines a reader identifies the material by — the panel joint, the course band, the
board line — clipped to whatever of that element is actually visible.

What it draws and what it deliberately does not
-----------------------------------------------
A texture that competes with the opening linework is worse than none, so this is a *reading
device* and stays on ``A-WALL-FINI`` (the lightest grey in the table) at the coarsest module
that still identifies the material:

* **Metal panel** — the joint you actually see from across the street. On a face-fastened
  panel that is the sheet side-lap, :data:`_PANEL_LAP_M`; on a clipped or folded panel it is
  the seam itself, :data:`_SEAM_PITCH_M`. ``Material.exposed_fastener`` already states which,
  and it is the same flag ``takeoff.fasteners`` uses, so there is no second source of truth.
  A named ``finish`` outranks both flags, because coverage is a property of the profile and
  not of how it is fixed: the garage's corrugated covers 32" and not PBR's 36", and the
  north/south board & batten's line is the batten itself at :data:`_BATTEN_PITCH_M`, which
  on the flags alone would come out at seam pitch.
* **Masonry** — horizontal course bands at :data:`_MASONRY_BAND_M`, **not** the unit's own
  coursing. This house lays 2" Roman at the garage wainscot and 2-2/3" modular in the sunken
  garden's veneer; at a quarter-inch scale either is twenty-five lines to the foot and prints
  as a solid grey block. The band is an indication that this surface is coursed masonry, and
  it is labelled as such rather than counted.
* **Board finishes** — one line per board, in the direction ``ResolvedLayer.board_run``
  derived from the furring behind it.
* **Everything else** — nothing. Stucco, parge, concrete and a protection panel have no module
  to draw, and inventing one for them would say something about the wall that is not true.

Only the facade plane is textured. On a receding plane the lines would be the same weight as
the receding outline they sit inside and the drawing would go to mush; depth reads through
``A-WALL-BEYD`` instead.

**The roof is skin too, and only sometimes.** A roof plane is textured when its ridge runs
*across* the view — ``ridge_direction == view.u_axis`` — because that is the case where the
slope is seen face-on and its seams, which run down-slope, project to vertical lines at
constant ``u``. Seen from the other pair of compass points the same roof is edge-on: its
whole surface projects to the rake line, and drawing seams across the gable triangle would
state a module running the wrong way over a face that is not there. Catlin's ridge runs
north-south, so its roof is textured on east and west and left bare on the gables — which is
correct, and is why the south elevation shows a clean gable while the east shows a seamed
slope. The garage's ridge runs the other way and takes the opposite pair.
"""

from __future__ import annotations

from shapely.geometry import LineString
from shapely.geometry.base import BaseGeometry

from typehaus.emit.draw.elevation_project import ElevationView, VisiblePiece
from typehaus.emit.draw.palette import family_of
from typehaus.emit.draw.scene import Polyline, SceneBuilder
from typehaus.model.materials import Material
from typehaus.quantities import M_PER_IN
from typehaus.resolve import overlay
from typehaus.resolve.model import ResolvedModel

#: Side-lap spacing of a face-fastened profiled panel — PBR/R-panel covers 36" net.
_PANEL_LAP_M = 0.9144  # 36"

#: Side-lap spacing of a 7/8" corrugated panel, which covers 32" net and not PBR's 36".
#: A side lap drawn every 36" on a 32" sheet is not a rounding — it is a line where no
#: joint is, on every elevation the garage appears in.
_CORRUGATED_LAP_M = 0.8128  # 32"

#: Batten spacing of a concealed-fastener board & batten panel, which covers 20" net. Not a
#: side lap: on this panel the line you read from the street is the batten itself.
_BATTEN_PITCH_M = 0.508  # 20"

#: Seam spacing of a clipped or mechanically-seamed panel. 16" is the common architectural
#: pan width and the one the viewer's seam recipe draws.
_SEAM_PITCH_M = 0.4064  # 16"

#: Course-band pitch for masonry. Four Roman courses, three modular — a module a reader sees
#: as brick without the sheet turning grey. See the module docstring.
_MASONRY_BAND_M = 0.2032  # 8"

#: Board exposure for a lap or T&G board finish with no product dimension to read.
_BOARD_EXPOSURE_M = 0.2032  # 8"

#: Weight, mm. Below every outline weight in :mod:`elevation`, on purpose.
_TEXTURE_WEIGHT = 0.13

#: A texture run shorter than this is a stub between two openings and reads as a smudge.
_MIN_RUN_M = 0.0762  # 3"


def emit_cladding_texture(b: SceneBuilder, model: ResolvedModel,
                          facade_pieces: list[VisiblePiece],
                          view: ElevationView) -> None:
    """Draw each facade-plane body element's outermost material as a light texture.

    ``facade_pieces`` is already banded by the caller — only the dominant plane is textured
    (see the module docstring), and which plane that is is :mod:`elevation`'s decision. The
    roof rides the same list and is admitted only when ``view`` sees its slope face-on.
    """
    board_runs = _board_run_index(model)
    catalog = {material.tag: material for material in model.plan.library.materials}
    face_on = _face_on_roof_uids(model, view)
    for piece in facade_pieces:
        candidate = piece.candidate
        if candidate.family == "roof":
            if candidate.uid.split("-", 1)[0] not in face_on:
                continue
            # Seams run down-slope, and down-slope has no component along ``u`` on the view
            # that sees the slope face-on — so they project to vertical lines whatever the
            # pitch is. The material still decides *whether* there is a module to draw.
            recipe = _recipe_for(catalog.get(candidate.material_ref or ""),
                                 candidate.material_ref, None)
            recipe = None if recipe is None else ("vertical", recipe[1])
        elif candidate.family == "body":
            recipe = _recipe_for(catalog.get(candidate.material_ref or ""),
                                 candidate.material_ref, board_runs.get(candidate.uid))
        else:
            continue
        if recipe is None:
            continue
        direction, pitch = recipe
        for line in _module_lines(piece.geometry, direction, pitch):
            b.add(Polyline(points=line, layer="A-WALL-FINI", lineweight=_TEXTURE_WEIGHT,
                           uid=candidate.uid, tag=candidate.tag))


def _face_on_roof_uids(model: ResolvedModel, view: ElevationView) -> frozenset[str]:
    """Uids of the roofs whose slope this view sees as a surface rather than as a line.

    A gable's ridge and the view's in-plane axis are the whole test. Ridge along ``y`` and a
    view whose ``u`` is ``y`` (east/west): the slope falls in ``x``, which is the view's depth
    axis, so the surface projects to its full rise and is seen face-on. The same roof from
    north or south projects to the rake line and has no surface to texture.
    """
    return frozenset(roof.uid for roof in model.roofs
                     if roof.ridge_direction == view.u_axis)


def _recipe_for(material: Material | None, material_ref: str | None,
                board_run: str | None) -> tuple[str, float] | None:
    """(direction, pitch) for a material's module lines, or ``None`` for an untextured one.

    The catalog record is asked before ``palette.family_of``, because two authored fields say
    what a substring can only guess. ``exposed_fastener`` is what separates a face-fastened
    profiled panel from a clipped or folded one — it is the flag ``takeoff.fasteners`` bills
    from — and ``skin_family`` is a declaration that this material is one of the ribbed metal
    skins a building wears from grade to ridge. ``family_of`` misses both here: this house's
    cladding is tagged ``pbr-panel-26``, which contains none of the needles, so the whole
    facade came out blank while the garage's ``standing-seam-nailstrip-26`` was textured.
    """
    if material is not None:
        # The *finish* is asked before either flag. Board & batten is concealed-fastened
        # (``exposed_fastener`` False) and declares ``skin_family="standing-seam"`` for the
        # roof edge's sake, so on the flags alone it falls to ``_SEAM_PITCH_M`` and draws a
        # 16" seam rhythm on a panel whose battens stand at 20". Same failure the corrugated
        # branch below fixes for the garage, one gate earlier.
        if getattr(material, "finish", None) == "board-and-batten":
            return ("vertical", _BATTEN_PITCH_M)
        if getattr(material, "exposed_fastener", False):
            # The *finish* is asked before the flag, because ``exposed_fastener`` says only
            # "screwed through its face" and every face-fastened profile covers a different
            # width. Falling straight to ``_PANEL_LAP_M`` is PBR's 36" for all of them, which
            # draws the garage's 32" corrugated side laps in the wrong place.
            if getattr(material, "finish", None) == "corrugated":
                return ("vertical", _CORRUGATED_LAP_M)
            return ("vertical", _PANEL_LAP_M)
        if getattr(material, "skin_family", None) is not None:
            return ("vertical", _SEAM_PITCH_M)
    family = family_of(material_ref)
    if family == "metal":
        return ("vertical", _SEAM_PITCH_M)
    if family == "masonry":
        return ("horizontal", _MASONRY_BAND_M)
    if family == "siding" and board_run is not None:
        # Boards land perpendicular to their furring; ``board_run`` already states which way
        # the boards themselves run, and a board line runs *along* the board.
        return (board_run, _BOARD_EXPOSURE_M)
    return None


def _board_run_index(model: ResolvedModel) -> dict[str, str | None]:
    """wall uid -> the ``board_run`` of its outermost body layer, where the layer states one."""
    out: dict[str, str | None] = {}
    for wall in model.walls:
        body = wall.body_layers()
        out[wall.uid] = body[-1].board_run if body else None
    return out


def _module_lines(geometry: BaseGeometry, direction: str,
                  pitch: float) -> list[tuple[tuple[float, float], ...]]:
    """Evenly pitched lines across ``geometry``'s bounds, clipped to it, in drawing inches.

    Phased off zero rather than off the element's own edge: two collinear wall segments are an
    authoring convention, not a break in the cladding, and a texture that restarts at each
    segment draws a false joint at every partition inside the house.
    """
    minimum_u, minimum_z, maximum_u, maximum_z = geometry.bounds
    out: list[tuple[tuple[float, float], ...]] = []
    if direction == "vertical":
        start, stop, fixed_lo, fixed_hi = minimum_u, maximum_u, minimum_z, maximum_z
    else:
        start, stop, fixed_lo, fixed_hi = minimum_z, maximum_z, minimum_u, maximum_u
    station = (start // pitch + 1) * pitch
    while station < stop:
        if direction == "vertical":
            cut = LineString([(station, fixed_lo - pitch), (station, fixed_hi + pitch)])
        else:
            cut = LineString([(fixed_lo - pitch, station), (fixed_hi + pitch, station)])
        clipped = overlay.intersection(cut, geometry)
        for segment in getattr(clipped, "geoms", (clipped,)):
            coords = list(getattr(segment, "coords", ()))
            if len(coords) >= 2 and LineString(coords).length >= _MIN_RUN_M:
                out.append(tuple((u / M_PER_IN, z / M_PER_IN) for u, z in coords))
        station += pitch
    return out
