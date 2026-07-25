"""Site model: parcel, setbacks, spot elevations, utilities (→ Permit-ready plan set Phase 4).

These are plain value objects nested inside ``Site`` (like ``JoistSpec`` inside
``FloorSystem``) — not independently identified elements, since nothing else references
them by tag.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from typehaus.model.base import HausModel
from typehaus.model.enums import UtilityKind
from typehaus.model.registry import register_constructor
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
    """An authored grade elevation at a point, relative to the main-floor 0 datum."""

    position: Point2D
    elevation: Length


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
):
    register_constructor(_name, _obj)
