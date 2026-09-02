"""Orthographic projection + painter's-order occlusion for exterior elevations (→ 30 §Elevations).

``plans/30-m3-permit.md`` committed to this shape and it was never built: *"orthographic
projection of geometry-iterator output (triangles → coplanar merge → outlines, painter's-order
occlusion)"*. This module is that sentence.

Why the geometry IR and not the resolved records
------------------------------------------------
:class:`~typehaus.resolve.geometry_ir.GeometryModel` already carries, per element, every solid
the building is made of — the wall body already jamb-split into piers/sills/headers, already
banded (``Layer.extent``), already raked under a gable, the roof already a real sloped surface
with its edge setbacks applied, the window already a frame + glass + exterior casing. Rebuilding
any of that from ``ResolvedWall.axis`` loses it — no way to know that a brick wainscot stops at
4'-0" or that an attic wall is raked. So the projector reads the IR, and the only things it
asks the resolved model for are
names (tag, storey, material) that the IR deliberately does not carry.

The projection
--------------
A cardinal elevation is a parallel projection along one horizontal axis. For a viewer looking
along ``d`` with ``up = +z``, the drawing's rightward axis is ``d x up``:

===========  ================  ==============  =====================
elevation    viewer looks      u (rightward)   depth (away from eye)
===========  ================  ==============  =====================
south        +y                +x              +y
north        -y                -x              -y
east         -x                +y              -x
west         +x                -y              +x
===========  ================  ==============  =====================

The two mirrored views are the point: a north elevation drawn with ``u = +x`` puts west on the
left, which is what you see from *inside* the building. The old elevation did exactly that.

The shadow of a solid is the union of the projections of its boundary faces — every point of
the shadow is hit by a ray that meets the boundary, so no interior sampling is needed. A
``GPrism``'s full-height ``voids`` therefore contribute their own side faces and never punch a
hole: a vertical shaft is not see-through from a horizontal eye. Openings are not voids in this
IR (the wall body is jamb-split instead), which is what leaves the real hole a window sits in.

Occlusion
---------
Front to back, maintaining one ``covered`` region: a candidate's visible part is
``silhouette - covered``, and its whole silhouette then joins ``covered``. Candidates whose
cheap (u, z) bounding box is already inside ``covered`` skip the exact projection entirely,
which is what keeps ~7,500 framing solids and every interior partition off the clock.

**Every shapely boolean here goes through** :mod:`typehaus.resolve.overlay`. A bare
``unary_union`` is fatal on the published web app's GEOS 3.12.1 and silently fine on this
venv's 3.13, so the bug cannot be seen locally — read that module's docstring before touching
a boolean in this file.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field

from shapely.geometry import Polygon, box
from shapely.geometry.base import BaseGeometry
from shapely.prepared import prep

from typehaus.resolve import overlay
from typehaus.resolve.geometry_ir import (
    ElementGeometry,
    GBox,
    GMesh,
    GPrism,
    GSolid,
    GSweep,
)
from typehaus.resolve.model import ResolvedModel

Vec3 = tuple[float, float, float]
UZ = tuple[float, float]

#: A projected face thinner than this in either direction carries no area worth unioning —
#: the two *end* faces of a wall standing parallel to the elevation plane are exactly this,
#: and there are two of them per prism per layer per wall. Dropping them before shapely sees
#: them is the single largest saving in the projector. 10 microns.
_DEGENERATE_M = 1e-5

#: A visible fragment smaller than this is a noding sliver, not a piece of building: two
#: coplanar layers whose faces agree to a micron leave one, and drawing it puts a 1/64" tick
#: on the sheet that reads as a defect. 3e-4 m2 is under half a square inch.
_MIN_VISIBLE_AREA_M2 = 3e-4

#: Ring simplification tolerance. Collinear vertices survive every union (the noder inserts
#: one wherever two coplanar faces meet) and each one is a DXF vertex nobody asked for. 0.1 mm
#: is two orders of magnitude below the thinnest thing this drawing shows.
_SIMPLIFY_M = 1e-4


@dataclass(frozen=True)
class ElevationView:
    """One cardinal viewing direction, as the two scalar maps the projector needs."""

    facing: str
    #: Multiplies the in-plane world axis to give ``u``. -1 for north and west: those two
    #: views are mirrored, and a drawing that is not mirrored is a view from inside.
    u_sign: float
    #: Which world axis is in-plane — ``"x"`` for north/south, ``"y"`` for east/west.
    u_axis: str
    #: Multiplies the out-of-plane world axis to give depth (larger = further from the eye).
    depth_sign: float

    def u_of(self, x: float, y: float) -> float:
        return self.u_sign * (x if self.u_axis == "x" else y)

    def depth_of(self, x: float, y: float) -> float:
        return self.depth_sign * (y if self.u_axis == "x" else x)


_VIEWS = {
    "south": ElevationView("south", +1.0, "x", +1.0),
    "north": ElevationView("north", -1.0, "x", -1.0),
    "east": ElevationView("east", +1.0, "y", -1.0),
    "west": ElevationView("west", -1.0, "y", +1.0),
}


def view_for(facing: str) -> ElevationView:
    """The :class:`ElevationView` for a cardinal facing, or ``ValueError``."""
    try:
        return _VIEWS[facing.lower()]
    except KeyError:
        raise ValueError(f"unknown elevation facing {facing!r}") from None


# --- projecting one solid ----------------------------------------------------------------
def _prism_faces(solid: GPrism) -> Iterator[tuple[Vec3, ...]]:
    ring = solid.ring
    tops = solid.top if solid.top is not None else (solid.z1_m,) * len(ring)
    for index, (x0, y0) in enumerate(ring):
        x1, y1 = ring[(index + 1) % len(ring)]
        t0, t1 = tops[index], tops[(index + 1) % len(ring)]
        yield ((x0, y0, solid.z0_m), (x1, y1, solid.z0_m), (x1, y1, t1), (x0, y0, t0))
    if solid.top is not None:
        # A raked top is a real sloped surface; its projection is not covered by the side
        # faces of a re-entrant ring. A flat top projects to a line and is skipped.
        yield tuple((x, y, t) for (x, y), t in zip(ring, tops, strict=True))
    for void in solid.voids:
        for index, (x0, y0) in enumerate(void):
            x1, y1 = void[(index + 1) % len(void)]
            yield ((x0, y0, solid.z0_m), (x1, y1, solid.z0_m),
                   (x1, y1, solid.z1_m), (x0, y0, solid.z1_m))


def _box_faces(solid: GBox) -> Iterator[tuple[Vec3, ...]]:
    bottom, top = solid.corners_bottom, solid.corners_top
    for index in range(len(bottom)):
        following = (index + 1) % len(bottom)
        yield (bottom[index], bottom[following], top[following], top[index])
    yield bottom
    yield top


def _sweep_faces(solid: GSweep) -> Iterator[tuple[Vec3, ...]]:
    dx, dy, dz = solid.extrude
    far = tuple((x + dx, y + dy, z + dz) for x, y, z in solid.profile)
    yield solid.profile
    yield far
    for index in range(len(solid.profile)):
        following = (index + 1) % len(solid.profile)
        yield (solid.profile[index], solid.profile[following], far[following], far[index])


def solid_faces(solid: GSolid) -> Iterator[tuple[Vec3, ...]]:
    """Every boundary face of one IR solid, as 3D rings. The shadow is their union."""
    if isinstance(solid, GPrism):
        yield from _prism_faces(solid)
    elif isinstance(solid, GBox):
        yield from _box_faces(solid)
    elif isinstance(solid, GMesh):
        for a, b, c in solid.triangles:
            yield (solid.positions[a], solid.positions[b], solid.positions[c])
    elif isinstance(solid, GSweep):
        yield from _sweep_faces(solid)


def solid_vertices(solid: GSolid) -> tuple[Vec3, ...]:
    """Every vertex of one IR solid — enough for a bounding box and a depth range."""
    if isinstance(solid, GPrism):
        tops = solid.top if solid.top is not None else (solid.z1_m,) * len(solid.ring)
        return tuple((x, y, z) for (x, y), top in zip(solid.ring, tops, strict=True)
                     for z in (solid.z0_m, top))
    if isinstance(solid, GBox):
        return tuple(solid.corners_bottom) + tuple(solid.corners_top)
    if isinstance(solid, GMesh):
        return tuple(solid.positions)
    if isinstance(solid, GSweep):
        dx, dy, dz = solid.extrude
        return tuple(solid.profile) + tuple(
            (x + dx, y + dy, z + dz) for x, y, z in solid.profile)
    return ()


def project_solids(solids: tuple[GSolid, ...], view: ElevationView) -> BaseGeometry:
    """The (u, z) shadow of a group of solids, on the fixed-precision overlay grid."""
    faces: list[Polygon] = []
    for solid in solids:
        for face in solid_faces(solid):
            points = [(view.u_of(x, y), z) for x, y, z in face]
            us = [u for u, _ in points]
            zs = [z for _, z in points]
            if max(us) - min(us) < _DEGENERATE_M or max(zs) - min(zs) < _DEGENERATE_M:
                continue  # projects to a line — an end face, or a flat top/bottom
            polygon = Polygon(points)
            if not polygon.is_valid:
                polygon = polygon.buffer(0)  # a self-touching triangle fan, not a sliver drop
            if not polygon.is_empty:
                faces.append(polygon)
    return overlay.union_all(faces)


# --- candidates and occlusion ------------------------------------------------------------
@dataclass
class Candidate:
    """One thing that may appear on the elevation, with its silhouette computed lazily.

    ``key`` groups IR parts into a single drawn object — every layer of a wall is one wall
    outline, every baluster of a railing is one railing — so the sheet carries the building's
    edges rather than its assembly's. ``near_depth`` is what the painter's order sorts on and
    is read straight off the vertices, so a candidate that turns out to be hidden is culled
    before its silhouette is ever unioned.
    """

    key: tuple[str, str, int]
    uid: str
    tag: str
    kind: str
    family: str
    material_ref: str | None
    solids: list[GSolid] = field(default_factory=list)
    near_depth: float = float("inf")
    far_depth: float = float("-inf")
    u0: float = float("inf")
    z0: float = float("inf")
    u1: float = float("-inf")
    z1: float = float("-inf")

    def absorb(self, solid: GSolid, view: ElevationView) -> None:
        self.solids.append(solid)
        for x, y, z in solid_vertices(solid):
            u, depth = view.u_of(x, y), view.depth_of(x, y)
            self.near_depth = min(self.near_depth, depth)
            self.far_depth = max(self.far_depth, depth)
            self.u0, self.u1 = min(self.u0, u), max(self.u1, u)
            self.z0, self.z1 = min(self.z0, z), max(self.z1, z)

    @property
    def bbox(self) -> Polygon:
        return box(self.u0, self.z0, self.u1, self.z1)

    def silhouette(self, view: ElevationView) -> BaseGeometry:
        return project_solids(tuple(self.solids), view)


@dataclass(frozen=True)
class VisiblePiece:
    """What one candidate actually shows, after everything nearer has been subtracted."""

    candidate: Candidate
    geometry: BaseGeometry


def occlude(candidates: list[Candidate], view: ElevationView) -> list[VisiblePiece]:
    """Painter's-order hidden-line removal, front to back.

    Ties on ``near_depth`` are broken by tag so the same model always draws the same sheet —
    two coplanar surfaces (a flashing lying on the cladding it laps) is a real configuration
    and one of them has to win, but it must win the same way every run.
    """
    ordered = sorted(candidates, key=lambda item: (item.near_depth, item.tag, item.family))
    covered: BaseGeometry | None = None
    prepared = None
    out: list[VisiblePiece] = []
    for candidate in ordered:
        if covered is not None:
            if prepared is None:
                prepared = prep(covered)
            if prepared.contains(candidate.bbox):
                continue  # wholly behind something opaque — never projected at all
        silhouette = candidate.silhouette(view)
        if silhouette.is_empty:
            continue
        visible = silhouette if covered is None else overlay.difference(silhouette, covered)
        visible = _drop_slivers(visible)
        if not visible.is_empty:
            out.append(VisiblePiece(candidate=candidate, geometry=visible))
        covered = silhouette if covered is None else overlay.union_all([covered, silhouette])
        prepared = None
    return out


def _drop_slivers(geometry: BaseGeometry) -> BaseGeometry:
    """Discard fragments under :data:`_MIN_VISIBLE_AREA_M2` and collinear-only vertices."""
    if geometry.is_empty:
        return geometry
    parts = getattr(geometry, "geoms", (geometry,))
    kept = [part for part in parts
            if getattr(part, "area", 0.0) >= _MIN_VISIBLE_AREA_M2]
    if not kept:
        return Polygon()
    merged = overlay.union_all(kept)
    return merged.simplify(_SIMPLIFY_M, preserve_topology=True)


def split_at_grade(geometry: BaseGeometry,
                   grade_z: float) -> tuple[BaseGeometry, BaseGeometry]:
    """(above, below) halves of a visible region, cut on the flat grade datum.

    The datum rather than the interpolated spot-elevation profile: a below-grade line is a
    convention saying "this is buried", and cutting it on a sloping profile would put a
    stepped kink in every foundation outline for a distinction nobody reads at this scale.
    """
    minimum_u, minimum_z, maximum_u, maximum_z = geometry.bounds
    if minimum_z >= grade_z:
        return geometry, Polygon()
    if maximum_z <= grade_z:
        return Polygon(), geometry
    span = box(minimum_u - 1.0, grade_z, maximum_u + 1.0, maximum_z + 1.0)
    return overlay.intersection(geometry, span), overlay.difference(geometry, span)


def rings_of(geometry: BaseGeometry) -> list[tuple[UZ, ...]]:
    """Every closed ring of a (multi)polygon, exterior and interior alike, in metres."""
    out: list[tuple[UZ, ...]] = []
    for part in getattr(geometry, "geoms", (geometry,)):
        exterior = getattr(part, "exterior", None)
        if exterior is None:
            continue
        out.append(tuple(exterior.coords)[:-1])
        out.extend(tuple(ring.coords)[:-1] for ring in part.interiors)
    return [ring for ring in out if len(ring) >= 3]


# --- what an exterior elevation can see --------------------------------------------------
#: IR element kind -> drawing family. A kind absent from this table is not drawn, and every
#: absence is a decision: framing (7,469 solids in the reference house) is behind cladding,
#: decking or a ceiling everywhere it exists; plumbing, HVAC, conduit, drain tile and pipe
#: sleeves are buried or interior; ``ceiling`` and ``earth`` are the insides of surfaces this
#: view looks at from outside. Seam clamps and panel straps are excluded for a different
#: reason — they are real and they are visible, but at 1/4"=1'-0" a 3" clip is a dot, and
#: eighty-two dots along an eave read as dirt on the sheet rather than as hardware.
_KIND_FAMILY = {
    "wall": "body", "slab": "body", "footing": "body", "pad": "body", "floor": "body",
    "column": "body", "beam": "body", "soffit": "body",
    "roof": "roof", "solar_panel": "roof",
    "fascia": "trim", "gutter": "trim", "downspout": "trim", "flashing": "trim",
    "snow_guard": "trim", "vent": "trim",
    "railing": "rail", "railing_infill": "rail",
    "glazing": "glaz", "glazing_trim": "sash",
}

#: An opening's own parts split three ways: the glass reads as glass, and everything else —
#: frame, mullion, stile, track, leaf, exterior casing — reads as the product's linework,
#: which is a door's line for a door and a sash's for a window.
_GLASS_PART_KEYS = frozenset({"glass"})


#: Depth bucket a drawing group is keyed on, in addition to its owner and family. A *run* —
#: a radon vent, a drain, a raceway — reaches the IR as dozens of small elements sharing one
#: parent uid, and grouping the whole run by uid alone sorts every piece of it at the depth of
#: whichever piece is nearest the eye. The radon riser's roof terminal stands proud of the
#: north wall, so the whole run, three storeys of it inside the house, was drawn in front of
#: the facade. Bucketing by depth splits the run back into the planes it actually occupies;
#: 12" is coarse enough that a railing's posts and infill panels stay one railing.
_DEPTH_BUCKET_M = 0.3048


def _base_uid(uid: str) -> str:
    """The owning element's uid. Accessory geometry suffixes its parent (``…-00-back``)."""
    return uid.split("-", 1)[0]


def _element_near_depth(element: ElementGeometry, view: ElevationView) -> float:
    """The depth of the point of one IR element closest to the eye."""
    depths = [view.depth_of(x, y)
              for part in element.parts for solid in part.solids
              for x, y, _z in solid_vertices(solid)]
    return min(depths) if depths else float("inf")


def collect_candidates(model: ResolvedModel, view: ElevationView) -> list[Candidate]:
    """Group the geometry IR into the objects one elevation draws, with their depths.

    Grouping is per *element*, not per part: a wall's fourteen layers are one wall outline
    and a railing's two hundred balusters are one railing. That is both what a drawing wants
    and what makes the occlusion pass affordable — 600-odd candidates instead of 11,709
    solids, each culled or projected exactly once.
    """
    geometry = model.geometry
    if geometry is None or not geometry.elements:
        raise ValueError(
            "build_elevation needs the resolved geometry IR; this model was resolved "
            "without it (resolve_preview skips the geometry stage)")
    tags = _tag_index(model)
    doors = {opening.uid for opening in model.openings if opening.is_door}
    candidates: dict[tuple[str, str, int], Candidate] = {}
    # (candidate key) -> the depth of the nearest *part* seen so far. A candidate's
    # ``material_ref`` is the material of whichever part stands closest to the eye, which is
    # exactly the definition of "the outermost visible layer" the cladding texture wants.
    outermost: dict[tuple[str, str, int], float] = {}
    for element in geometry.elements:
        if element.kind not in _KIND_FAMILY and element.kind != "opening":
            continue
        near = _element_near_depth(element, view)
        if near == float("inf"):
            continue  # an element with parts but no solids (a preview stub)
        base = _base_uid(element.uid)
        bucket = round(near / _DEPTH_BUCKET_M)
        for part in element.parts:
            family = _family_of(element.kind, part.key, base in doors)
            if family is None:
                continue
            key = (base, family, bucket)
            candidate = candidates.get(key)
            if candidate is None:
                candidate = Candidate(key=key, uid=base, tag=tags.get(base, base),
                                      kind=element.kind, family=family, material_ref=None)
                candidates[key] = candidate
            part_depth = float("inf")
            for solid in part.solids:
                candidate.absorb(solid, view)
                part_depth = min(part_depth, min(view.depth_of(x, y)
                                                 for x, y, _z in solid_vertices(solid)))
            if part_depth < outermost.get(key, float("inf")):
                outermost[key] = part_depth
                candidate.material_ref = (part.catalog.material_ref
                                          if part.catalog is not None else None)
    return [candidate for candidate in candidates.values() if candidate.solids]


def _family_of(kind: str, part_key: str, is_door: bool) -> str | None:
    if kind == "opening":
        if part_key in _GLASS_PART_KEYS:
            return "glaz"
        return "door" if is_door else "sash"
    return _KIND_FAMILY.get(kind)


def _tag_index(model: ResolvedModel) -> dict[str, str]:
    """uid -> authored tag, over every resolved record that owns IR geometry."""
    index: dict[str, str] = {}
    for group in (model.walls, model.openings, model.solids, model.roofs, model.floors,
                  model.soffits):
        for record in group:
            index[record.uid] = record.tag
    return index
