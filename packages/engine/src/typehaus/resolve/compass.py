"""The one path from the plan frame to the compass (decision #153, extending #11).

Plan coordinates are a PROJECT-north frame: +x project east, +y project north. Authoring,
the canvas and plan sheets never tilt. ``Site.true_north`` (θ) relates that frame to the
compass: θ is measured CLOCKWISE on the plan from project north (+y) to true north, so

    true bearing = plan bearing − θ

and true north on the plan is the vector ``(sin θ, cos θ)``. Bearings here are radians,
clockwise from north, in [0, 2π). This module is the only reader of ``site.true_north``
outside model, IFC and the server payload (a lint enforces it).

Grid (``Site.crs``) north differs from true north by the meridian convergence; the
``grid_*`` functions carry that, and both the IFC map conversion and the survey import use
them so the two directions share one transform. ``Site.lat/lon`` is the plan origin (0, 0).
"""

from __future__ import annotations

import math
from functools import lru_cache

_TAU = 2.0 * math.pi
_CARDINALS_4 = ("N", "E", "S", "W")
_CARDINALS_8 = ("N", "NE", "E", "SE", "S", "SW", "W", "NW")


def true_north_rad(site) -> float:  # noqa: ANN001 — Site; avoids a model import here
    """θ: clockwise angle on the plan from project north (+y) to true north, radians."""
    if site is None:
        return 0.0
    return site.true_north.radians  # a non-Site raises rather than reading as θ = 0


def plan_bearing(dx: float, dy: float) -> float:
    """Bearing of a plan vector, clockwise from project north (+y), in [0, 2π)."""
    return math.atan2(dx, dy) % _TAU


def true_bearing(dx: float, dy: float, site) -> float:  # noqa: ANN001
    """True (compass) bearing of a plan vector, in [0, 2π)."""
    return (plan_bearing(dx, dy) - true_north_rad(site)) % _TAU


def plan_vector_for_true_bearing(bearing: float, site) -> tuple[float, float]:  # noqa: ANN001
    """Unit plan vector pointing at a true bearing (0 = true north)."""
    b = bearing + true_north_rad(site)
    return math.sin(b), math.cos(b)


def cardinal(bearing: float, points: int = 4) -> str:
    """Nearest cardinal (4) or intercardinal (8) name; an exact tie goes clockwise."""
    names = {4: _CARDINALS_4, 8: _CARDINALS_8}[points]
    sector = 360.0 / points
    deg = math.degrees(bearing) % 360.0
    return names[int(math.floor((deg + sector / 2.0 + 1e-9) / sector)) % points]


def quadrant_bearing_text(bearing: float, *, minutes: bool = True) -> str:
    """Surveyor's quadrant bearing, ``N 45°00' E`` (or ``N 45° E`` without minutes)."""
    azimuth = math.degrees(bearing) % 360.0
    ns = "N" if azimuth <= 90.0 or azimuth >= 270.0 else "S"
    angle = azimuth if azimuth <= 90.0 else (
        180.0 - azimuth if azimuth < 180.0 else (
            azimuth - 180.0 if azimuth < 270.0 else 360.0 - azimuth))
    ew = "E" if azimuth < 180.0 else "W"
    if not minutes:
        return f"{ns} {round(angle)}° {ew}"
    degrees = int(angle)
    mins = int(round((angle - degrees) * 60.0))
    if mins == 60:
        degrees, mins = degrees + 1, 0
    return f"{ns} {degrees}°{mins:02d}' {ew}"


def wall_outward_normal(wall, model=None) -> tuple[float, float]:  # noqa: ANN001
    """Unit plan normal of a resolved wall's exterior face.

    Read off the resolved layers (``sill_alignment.outward_sign``: the last layer's side).
    With fewer than two thick layers that side is undefined, so the envelope's exterior
    face probe decides when ``model`` is given. A degenerate axis returns ``(0, 0)``.
    """
    from typehaus.resolve.geometry import wall_frame
    from typehaus.resolve.sill_alignment import outward_sign

    origin, _tangent, left, axis_length = wall_frame(wall)
    if axis_length <= 1e-9:
        return 0.0, 0.0
    sign = outward_sign(wall)
    thick = [layer for layer in wall.layers if layer.polygon and layer.thickness_m > 0]
    if len(thick) < 2 and model is not None:
        from typehaus.resolve.envelope_geometry import envelope_geometry

        probe = envelope_geometry(model).exterior_face_probe(wall)
        if probe is not None:
            (x0, y0), (x1, y1) = probe.coords[0], probe.coords[-1]
            mid = ((x0 + x1) / 2 - origin[0], (y0 + y1) / 2 - origin[1])
            off = mid[0] * left[0] + mid[1] * left[1]
            if abs(off) > 1e-9:
                sign = 1.0 if off > 0 else -1.0
    return sign * left[0], sign * left[1]


def facade_name(normal: tuple[float, float], site) -> str:  # noqa: ANN001
    """The one facade name: nearest true cardinal of an outward plan normal."""
    return cardinal(true_bearing(normal[0], normal[1], site))


def facade_bearing_text(normal: tuple[float, float], site) -> str | None:  # noqa: ANN001
    """``"faces N 37° W"`` when the face is off its cardinal, else ``None``."""
    bearing = true_bearing(normal[0], normal[1], site)
    off = (math.degrees(bearing) + 45.0) % 90.0 - 45.0
    if abs(off) < 0.5:
        return None
    return f"faces {quadrant_bearing_text(bearing, minutes=False)}"


# --- grid (Site.crs) <-> plan ------------------------------------------------------------

@lru_cache(maxsize=32)
def _grid_origin_and_true_north(crs: str, lon: float, lat: float) -> tuple[float, float, float]:
    import pyproj

    transformer = pyproj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)
    e0, n0 = transformer.transform(lon, lat)
    e1, n1 = transformer.transform(lon, lat + 1e-4)
    if not all(math.isfinite(v) for v in (e0, n0, e1, n1)):
        raise ValueError("non-finite georeference transform")
    # Grid bearing of true north: the negative of the meridian convergence.
    return e0, n0, math.atan2(e1 - e0, n1 - n0)


def grid_origin(site) -> tuple[float, float, float] | None:  # noqa: ANN001
    """``(easting, northing, grid bearing of true north)`` at ``Site.lat/lon``, or None.

    Best-effort: a lat/lon outside the CRS's domain (a test fixture's (0, 0)) is None.
    """
    try:
        return _grid_origin_and_true_north(site.crs, float(site.lon), float(site.lat))
    except Exception:  # noqa: BLE001 — georef is best-effort
        return None


def grid_rotation_rad(site) -> float:  # noqa: ANN001
    """φ: clockwise angle on the plan from project north to GRID north.

    θ less the grid bearing of true north; falls back to θ when the CRS is unreachable.
    """
    origin = grid_origin(site)
    return true_north_rad(site) - (origin[2] if origin is not None else 0.0)


def grid_to_plan(easting: float, northing: float, site) -> tuple[float, float]:  # noqa: ANN001
    """A ``Site.crs`` grid point to plan metres (origin at ``Site.lat/lon``)."""
    origin = grid_origin(site)
    if origin is None:
        raise ValueError(f"cannot georeference site in {site.crs!r}")
    de, dn = easting - origin[0], northing - origin[1]
    phi = grid_rotation_rad(site)
    c, s = math.cos(phi), math.sin(phi)
    return de * c + dn * s, -de * s + dn * c


def plan_to_grid(x_m: float, y_m: float, site) -> tuple[float, float]:  # noqa: ANN001
    """Plan metres to a ``Site.crs`` grid point: the inverse of :func:`grid_to_plan`."""
    origin = grid_origin(site)
    if origin is None:
        raise ValueError(f"cannot georeference site in {site.crs!r}")
    phi = grid_rotation_rad(site)
    c, s = math.cos(phi), math.sin(phi)
    return origin[0] + x_m * c - y_m * s, origin[1] + x_m * s + y_m * c


@lru_cache(maxsize=8)
def _from_wgs84(crs: str):  # noqa: ANN202
    import pyproj

    return pyproj.Transformer.from_crs("EPSG:4326", crs, always_xy=True)


def lonlat_to_plan(lon: float, lat: float, site) -> tuple[float, float]:  # noqa: ANN001
    """WGS84 lon/lat to plan metres, through ``Site.crs`` (a metre-unit grid)."""
    return grid_to_plan(*_from_wgs84(site.crs).transform(lon, lat), site)


def project_east_grid_axis(site) -> tuple[float, float]:  # noqa: ANN001
    """Plan +x as a unit (easting, northing) vector: IfcMapConversion's X axis."""
    phi = grid_rotation_rad(site)
    return math.cos(phi), math.sin(phi)


__all__ = [
    "cardinal", "facade_bearing_text", "facade_name", "grid_origin", "grid_rotation_rad",
    "grid_to_plan", "lonlat_to_plan", "plan_bearing", "plan_to_grid",
    "plan_vector_for_true_bearing", "project_east_grid_axis", "quadrant_bearing_text",
    "true_bearing", "true_north_rad", "wall_outward_normal",
]
