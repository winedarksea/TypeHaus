"""Site model: parcel, setbacks, spot elevations, utilities (→ Permit-ready plan set Phase 4).

These are plain value objects nested inside ``Site`` (like ``JoistSpec`` inside
``FloorSystem``) — not independently identified elements, since nothing else references
them by tag.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from typehaus.model.base import Element, HausModel
from typehaus.model.enums import UtilityKind
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D, ft, m, pt


class MonthlyNormal(HausModel):
    """One month's climate normals — mean outdoor dry-bulb + mean RH.

    Twelve of these (January..December) on ``Site.monthly_normals`` feed the seasonal-mean
    (ISO 13788-style) condensation gate; the 99% design-hour walk keeps using
    ``Site.design_temp_heating`` as a cold-snap screen. Plain unit-suffixed floats, like
    ``Site.ground_snow_load_psf`` — these are published normals, not authored quantities.
    """

    temp_f: float  # monthly mean outdoor dry-bulb, °F
    rh: float  # monthly mean outdoor relative humidity, percent (0-100)


class SetbackSpec(HausModel):
    """A required setback from one parcel edge (``parcel[edge] -> parcel[(edge+1) % n]``)."""

    edge: int
    distance: Length
    label: str = ""  # "FRONT" | "SIDE" | "REAR"


class SpotElevation(HausModel):
    """An authored elevation at a point, relative to the main-floor 0 datum.

    ``kind`` says what the reading *is*. ``"grade"`` is the soil plane and is what an
    elevation's or a section's ground line is drawn through. ``"structure"`` is the top of
    something built — a sunken-court floor, a retaining wall's cap — which is a real
    elevation the model needs (``engineering/balcony_wind`` takes the lowest spot on the
    site, R401.3 reads every station) but is **not** ground: drawn into a ground line it
    ramps the profile down into a courtyard 20 feet away from the facade.
    """

    position: Point2D
    elevation: Length
    kind: Literal["grade", "structure"] = "grade"


class ImperviousSurface(HausModel):
    """A hardscape abutting the building (walk, patio, driveway, slab) — R401.3 requires it to
    slope away from the foundation at a minimum of 2% within the first 10 feet.

    Declarative and vibe-code-friendly: author the hardscape ``outline`` in the plan frame plus
    the grade ``near_elevation`` at the edge meeting the foundation and the ``far_elevation`` at
    the outer edge (both datum-relative, like :class:`SpotElevation`). ``code.R401_3_impervious``
    derives the run away from the foundation from the outline and computes the fall/run slope.
    """

    label: str  # "front walk" | "patio" | "driveway" | ...
    outline: tuple[Point2D, ...]  # hardscape polygon ring, plan frame
    near_elevation: Length  # grade where the surface meets the foundation
    far_elevation: Length  # grade at the outer edge, away from the foundation
    # What the hardscape IS, as opposed to what it is called. The zoning coverage table
    # groups on this: St Paul bounds driveway-and-parking paving separately from total
    # impervious area, so a driveway has to be distinguishable from a patio by something
    # better than reading ``label``. A driveway needs no element type of its own.
    kind: Literal["walk", "patio", "driveway", "pad", "stair", "other"] = "other"


class UtilityLine(HausModel):
    """A utility run from the street/main to a building penetration point."""

    kind: UtilityKind
    path: tuple[Point2D, ...]  # street/main -> entry
    entry: Point2D  # building penetration point
    depth: Length | None = None


class Contour(HausModel):
    """A survey contour line at a constant grade elevation (site-plan basemap topo).

    Elevation is relative to the main-floor 0 datum, like ``SpotElevation`` — a GeoJSON
    basemap in feet above the datum is normalized to that convention on load.
    """

    elevation: Length
    points: tuple[Point2D, ...]


class Easement(HausModel):
    """A recorded burden on the parcel — the one thing on a site plan a reviewer will not
    let you build over.

    ``outline`` is the easement area itself, in the plan frame, rather than a centreline
    plus a width, because that is what gets hatched on C-101 and what a footprint has to be
    checked against. ``width`` is carried anyway when the instrument states one (a 6' side
    utility easement), since the recorded document is the authority and the drawn ring is a
    depiction of it.
    """

    kind: str  # "utility" | "drainage" | "access" | "sewer" | ...
    outline: tuple[Point2D, ...]
    width: Length | None = None
    description: str = ""  # recording reference / instrument wording


class ErosionControl(HausModel):
    """One erosion and sediment control measure, as the site plan shows it.

    A permit set carries these as lines and a symbol, not as a computed quantity: silt
    fence runs along the downhill parcel lines, a rock construction entrance sits where
    vehicles leave the site, inlet protection sits on the storm structure that receives the
    runoff. ``path`` is a polyline for a fence and may be a single point for an entrance or
    an inlet — the drawing decides how to render it, and the model does not pretend the
    three measures share a geometry.
    """

    kind: Literal["silt_fence", "construction_entrance", "inlet_protection"]
    path: tuple[Point2D, ...]
    description: str = ""


class StreetFrontage(HausModel):
    """A public street abutting one parcel edge, and its right-of-way width.

    The ROW matters because the front setback is measured from the property line and the
    street centreline is a different line entirely; naming the frontage is also what makes
    "FRONT" mean something on a corner lot with two of them.
    """

    name: str  # street name, or "TBD" before the lot is chosen
    edge: int  # index into ``Site.parcel``, same convention as SetbackSpec
    right_of_way_ft: float | None = None


class Benchmark(HausModel):
    """The surveyed point every other elevation on the set is referenced to.

    ``elevation`` is datum-relative like :class:`SpotElevation` — the benchmark's job here
    is to say *which* physical object on the ground carries the datum ("top nut of hydrant
    at the NE corner"), so a field crew can recover it. Its assumed value in a public datum,
    where one exists, belongs in ``description``.
    """

    position: Point2D
    elevation: Length
    description: str = ""


@dataclass(frozen=True)
class Basemap:
    """Parsed GeoJSON site basemap: the parcel ring plus survey contour lines.

    Held as a plain value object (not a plan element) — the loader hands it to the
    manifest, which attaches the contours to :class:`Site` and may adopt the parcel.
    """

    parcel: tuple[Point2D, ...] = ()
    contours: tuple[Contour, ...] = ()


def load_basemap_geojson(path: str | Path, *, unit: str = "ft") -> Basemap:
    """Load a parcel boundary + contour lines from a GeoJSON ``FeatureCollection``.

    Coordinates are read in the project plan frame (default feet, not lon/lat) so a
    freshly surveyed basemap drops straight onto the authored geometry.  A feature is a
    *parcel* when its ``role`` property is ``"parcel"`` or its geometry is a ``Polygon``;
    a *contour* when ``role`` is ``"contour"`` or the geometry is a ``LineString``.
    Contour grade comes from the ``elevation`` (or ``elev``/``z``) property.
    """
    if unit not in ("ft", "m"):
        raise ValueError(f"unsupported basemap unit {unit!r}; use 'ft' or 'm'")
    to_length = ft if unit == "ft" else m
    data = json.loads(Path(path).read_text())
    features = data.get("features", []) if data.get("type") == "FeatureCollection" else [data]

    parcel: tuple[Point2D, ...] = ()
    contours: list[Contour] = []
    for feature in features:
        geometry = feature.get("geometry") or {}
        properties = feature.get("properties") or {}
        role = properties.get("role")
        gtype = geometry.get("type")
        coords = geometry.get("coordinates") or []
        if role == "parcel" or (role is None and gtype == "Polygon"):
            ring = coords[0] if gtype == "Polygon" and coords else coords
            parcel = _ring_to_points(ring, to_length)
        elif role == "contour" or (role is None and gtype in ("LineString", "MultiLineString")):
            elevation = properties.get("elevation",
                                       properties.get("elev", properties.get("z", 0.0)))
            lines = coords if gtype == "MultiLineString" else [coords]
            for line in lines:
                pts = tuple(pt(to_length(c[0]), to_length(c[1])) for c in line)
                if len(pts) >= 2:
                    contours.append(Contour(elevation=to_length(elevation), points=pts))
    return Basemap(parcel=parcel, contours=tuple(contours))


@register_element
class WindowWell(Element):
    """An areaway serving a below-grade emergency escape opening (R310.2.3).

    A first-class element rather than a nested value object, unlike its neighbours here,
    because it *references* one: ``serves_opening`` names the Window or RoughOpening it
    belongs to, and only elements carry tags other elements can point at.

    Deliberately non-geometric — no resolve pass, no glTF or IFC emission, not draggable in
    the UI. The check reads the authored element directly, the way the stair-well guard rule
    reads ``FloorOpening`` and ``Railing``. Adding it as a geometric kind would mean touching
    the resolver, both emitters and the viewer for a rectangle in the dirt that nobody looks
    at in 3D; adding it as data costs three lines and answers the code question.
    """

    serves_opening: str  # Window / RoughOpening tag this well lets you climb out of
    outline: tuple[Point2D, ...]  # well plan ring, project frame
    floor_elevation: Length  # well bottom, datum-relative like SpotElevation
    # R310.2.3.1: a well deeper than 44" needs a permanently affixed ladder or steps.
    ladder: bool = False
    ladder_width: Length | None = None
    drained: bool = False  # R310.2.3.2 connection to the foundation drainage system
    cover: str | None = None  # grate/cover product, where one is fitted


def _ring_to_points(ring: list, to_length) -> tuple[Point2D, ...]:
    pts = [pt(to_length(c[0]), to_length(c[1])) for c in ring]
    # GeoJSON polygons repeat the first vertex to close the ring; the plan frame does not.
    if len(pts) >= 2 and pts[0].xy_m == pts[-1].xy_m:
        pts = pts[:-1]
    return tuple(pts)


for _name, _obj in (
    ("MonthlyNormal", MonthlyNormal),
    ("SetbackSpec", SetbackSpec),
    ("SpotElevation", SpotElevation),
    ("ImperviousSurface", ImperviousSurface),
    ("UtilityLine", UtilityLine),
    ("Contour", Contour),
    ("Easement", Easement),
    ("ErosionControl", ErosionControl),
    ("StreetFrontage", StreetFrontage),
    ("Benchmark", Benchmark),
    ("WindowWell", WindowWell),
):
    register_constructor(_name, _obj)
