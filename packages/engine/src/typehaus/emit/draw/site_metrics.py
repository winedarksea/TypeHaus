"""Zoning arithmetic for C-101 and the cover sheet — pure, no drawing IR.

One module, two consumers: the site plan's coverage table and the cover's PROJECT DATA
block. That is deliberate. Lot area, building coverage and paving percentage are the three
numbers a zoning reviewer checks first, and a set where the cover and C-101 disagree about
any of them is a set that gets returned — so both read the same functions over the same
parcel ring, and no lot area is stored anywhere to drift from it.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.model.project import Site
from typehaus.quantities import Point2D
from typehaus.resolve.model import ResolvedModel

SF_PER_M2 = 10.763910416709722
FT_PER_M = 3.280839895013123

# St Paul Ord. 23-43 (2023-11-26) repealed R1-R4 / RT1 / RT2; the residential districts are
# RL, H1 and H2. Only the maximum lot coverage is tabulated here — the setbacks are authored
# per parcel as ``SetbackSpec`` because front-setback averaging off the adjoining houses
# makes them a survey result, not a district constant. Height is the district's own limit.
#
# Minnesota profile only: another jurisdiction's district names would collide with these,
# so a caller outside the MN profile passes ``None`` and gets a table with no limit column
# rather than St Paul's numbers silently applied elsewhere.
@dataclass(frozen=True)
class ZoningLimits:
    max_lot_coverage_pct: float
    max_height_ft: float


ZONING_LIMITS: dict[str, ZoningLimits] = {
    "RL": ZoningLimits(max_lot_coverage_pct=40.0, max_height_ft=35.0),
    "H1": ZoningLimits(max_lot_coverage_pct=45.0, max_height_ft=35.0),
    "H2": ZoningLimits(max_lot_coverage_pct=50.0, max_height_ft=39.0),
}

# Ord. 23-43: driveway and parking paving in a residential district is capped at the LESSER
# of 15% of the lot or 1,000 sf, and a front-yard driveway at 12 feet wide.
MAX_PAVING_FRACTION = 0.15
MAX_PAVING_FT2 = 1000.0
MAX_FRONT_DRIVEWAY_WIDTH_FT = 12.0

# Paving that counts against the driveway/parking cap, as opposed to total impervious area.
_PAVING_KINDS = ("driveway", "pad")


def _ring_area_ft2(points: tuple[Point2D, ...]) -> float:
    """Shoelace area of a plan ring, in square feet. Sign-free — a ring is a ring."""
    verts = [p.xy_m for p in points]
    if len(verts) < 3:
        return 0.0
    twice = 0.0
    for i, (x0, y0) in enumerate(verts):
        x1, y1 = verts[(i + 1) % len(verts)]
        twice += x0 * y1 - x1 * y0
    return abs(twice) / 2.0 * SF_PER_M2


def lot_area_ft2(site: Site) -> float | None:
    """Area of the parcel ring, or ``None`` when fewer than three vertices are authored."""
    if len(site.parcel) < 3:
        return None
    return _ring_area_ft2(site.parcel)


def building_coverage_ft2(model: ResolvedModel) -> float | None:
    """Footprint area of the primary building, in square feet.

    Reuses the site plan's own ``_primary_footprint`` (largest foundation-wall enclosure)
    so the number in the coverage table is the area of the polygon the sheet draws. A house
    with no foundation walls resolved reports ``None`` rather than zero: "no coverage" and
    "coverage not derivable" are different answers and only one of them is a compliance
    statement.
    """
    from typehaus.emit.draw.siteplan import _primary_footprint

    footprint = _primary_footprint(model)
    if footprint is None:
        return None
    return float(footprint.area) * SF_PER_M2


def impervious_ft2(site: Site) -> dict[str, float]:
    """Impervious hardscape area by ``ImperviousSurface.kind``, square feet."""
    out: dict[str, float] = {}
    for surface in site.impervious_surfaces:
        area = _ring_area_ft2(surface.outline)
        if area <= 0.0:
            continue
        out[surface.kind] = out.get(surface.kind, 0.0) + area
    return out


def paving_ft2(site: Site) -> float:
    """Driveway and parking paving only — what Ord. 23-43's 15% / 1,000 sf cap bounds."""
    by_kind = impervious_ft2(site)
    return sum(by_kind.get(kind, 0.0) for kind in _PAVING_KINDS)


def coverage_table(model: ResolvedModel, site: Site, *,
                   zoning_district: str | None = None) -> list[tuple[str, ...]]:
    """The C-101 coverage table as rows of ``(ITEM, VALUE, ALLOWED)``.

    ``ALLOWED`` is empty wherever the district is unstated or unknown to ``ZONING_LIMITS``:
    a coverage percentage with no limit beside it is still the number the reviewer wants,
    and inventing a limit would be worse than printing none. Rows the model cannot derive
    are omitted, not printed as zero.
    """
    district = zoning_district if zoning_district is not None else site.zoning_district
    limits = ZONING_LIMITS.get(district or "")
    lot = lot_area_ft2(site)
    rows: list[tuple[str, ...]] = [("ZONING DISTRICT", district or "NOT STATED", "")]
    if lot is None:
        rows.append(("LOT AREA", "NOT SURVEYED", ""))
        return rows
    rows.append(("LOT AREA", f"{lot:,.0f} SF", ""))

    building = building_coverage_ft2(model)
    if building is not None:
        pct = building / lot * 100.0
        allowed = f"{limits.max_lot_coverage_pct:.0f}% MAX" if limits else ""
        rows.append(("BUILDING COVERAGE", f"{building:,.0f} SF ({pct:.1f}%)", allowed))

    by_kind = impervious_ft2(site)
    for kind in sorted(by_kind):
        rows.append((f"{kind.upper()} AREA", f"{by_kind[kind]:,.0f} SF", ""))

    paving = paving_ft2(site)
    if paving > 0.0:
        cap = min(lot * MAX_PAVING_FRACTION, MAX_PAVING_FT2)
        rows.append(("DRIVEWAY / PARKING PAVING", f"{paving:,.0f} SF "
                     f"({paving / lot * 100.0:.1f}%)",
                     f"{cap:,.0f} SF MAX (LESSER OF 15% / 1,000 SF)"))

    total_impervious = (building or 0.0) + sum(by_kind.values())
    if by_kind or building is not None:
        rows.append(("TOTAL IMPERVIOUS", f"{total_impervious:,.0f} SF "
                     f"({total_impervious / lot * 100.0:.1f}%)", ""))
    if limits:
        rows.append(("BUILDING HEIGHT", "SEE ELEVATIONS", f"{limits.max_height_ft:.0f}' MAX"))
    return rows


def _bearing(dx_m: float, dy_m: float, true_north_deg: float) -> str:
    """Surveyor's quadrant bearing of a lot line, e.g. ``N 45°00' E``.

    Measured from TRUE north: the plan frame's +y is project north and ``Site.true_north``
    is project north's deviation from true, so the deviation is added here rather than
    quietly labelling a project bearing as a compass one.
    """
    azimuth = (math.degrees(math.atan2(dx_m, dy_m)) + true_north_deg) % 360.0
    ns = "N" if azimuth <= 90.0 or azimuth >= 270.0 else "S"
    angle = azimuth if azimuth <= 90.0 else (
        180.0 - azimuth if azimuth < 180.0 else (
            azimuth - 180.0 if azimuth < 270.0 else 360.0 - azimuth))
    ew = "E" if azimuth < 180.0 else "W"
    degrees = int(angle)
    minutes = int(round((angle - degrees) * 60.0))
    if minutes == 60:
        degrees, minutes = degrees + 1, 0
    return f"{ns} {degrees}°{minutes:02d}' {ew}"


def lot_line_dimensions(site: Site) -> list[tuple[int, float, str]]:
    """One ``(edge index, length in feet, bearing)`` per parcel edge, in ring order.

    The edge index is the same convention ``SetbackSpec.edge`` and ``StreetFrontage.edge``
    use — ``parcel[i] -> parcel[(i + 1) % n]`` — so a dimension and the setback measured
    against it name the same line.
    """
    verts = [p.xy_m for p in site.parcel]
    if len(verts) < 3:
        return []
    true_north_deg = site.true_north.degrees if site.true_north is not None else 0.0
    out: list[tuple[int, float, str]] = []
    for i, (x0, y0) in enumerate(verts):
        x1, y1 = verts[(i + 1) % len(verts)]
        dx, dy = x1 - x0, y1 - y0
        out.append((i, math.hypot(dx, dy) * FT_PER_M, _bearing(dx, dy, true_north_deg)))
    return out
