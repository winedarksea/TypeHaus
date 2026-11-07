"""Shared primitives for the structural permit sheets S-100/S-101 (→ 30 §Sheets).

Notation (feet-and-inches, bearing elevations) and the handful of plan-geometry helpers
both structural sheet builders need. Keeping them here rather than in ``_shared`` keeps the
architectural plan family and the structural sheet family independent.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from typehaus.emit.draw.typography import feet_inches_8th
from typehaus.model.assembly import FramingSpec
from typehaus.quantities import M_PER_IN
from typehaus.resolve.envelope_geometry import envelope_geometry
from typehaus.resolve.model import ResolvedModel, ResolvedRoof

if TYPE_CHECKING:
    from typehaus.engineering.snow_drift import DriftReach

M_TO_FT = 3.280839895013123
IN_PER_FT = 12.0


def feet_inches(meters: float) -> str:
    """Architectural length notation to 1/8", e.g. ``12'-6 1/4"`` (``feet_inches_8th``)."""
    return feet_inches_8th(meters / M_PER_IN)


def inches(meters: float) -> str:
    """Thickness notation to the nearest eighth, e.g. ``8"`` / ``3-1/2"``.

    A 3-1/2" slab must not print as 4" on a schedule the concrete crew reads, so this keeps
    the eighth-inch fraction carpenters and the authored ``Length`` both work in.
    """
    return inches_text(meters / M_PER_IN)


EIGHTHS_PER_INCH = 8


def inches_text(total_inches: float) -> str:
    eighths = round(total_inches * EIGHTHS_PER_INCH)
    whole, remainder = divmod(abs(eighths), EIGHTHS_PER_INCH)
    sign = "-" if eighths < 0 else ""
    if remainder == 0:
        return f"{sign}{whole}\""
    numerator, denominator = remainder, EIGHTHS_PER_INCH
    while numerator % 2 == 0:
        numerator //= 2
        denominator //= 2
    return f"{sign}{whole}-{numerator}/{denominator}\"" if whole else \
        f"{sign}{numerator}/{denominator}\""


def elevation_feet(meters: float) -> str:
    """Bearing/top-of-wall elevation in decimal feet off the project grade datum.

    Decimal feet (not feet-and-inches) is the surveying convention a footing schedule and a
    site plan share, and the project datum is grade, so the sign reads as depth directly.
    """
    return f"{meters * M_TO_FT:+.2f}'"


def outline_center(outline) -> tuple[float, float]:
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def outline_bbox(outline) -> tuple[float, float, float, float]:
    xs = [p[0] for p in outline]
    ys = [p[1] for p in outline]
    return min(xs), min(ys), max(xs), max(ys)


def bboxes_overlap(a: tuple[float, float, float, float],
                   b: tuple[float, float, float, float], tolerance: float = 0.0) -> bool:
    return (a[0] <= b[2] + tolerance and b[0] <= a[2] + tolerance
            and a[1] <= b[3] + tolerance and b[1] <= a[3] + tolerance)


def point_in_bbox(point: tuple[float, float],
                  box: tuple[float, float, float, float]) -> bool:
    return box[0] <= point[0] <= box[2] and box[1] <= point[1] <= box[3]


def outline_area_m2(outline) -> float:
    """Shoelace area of a plan ring (rings are simple, → resolve.model.Ring)."""
    if len(outline) < 3:
        return 0.0
    total = 0.0
    for index, (x0, y0) in enumerate(outline):
        x1, y1 = outline[(index + 1) % len(outline)]
        total += x0 * y1 - x1 * y0
    return abs(total) / 2.0


def wall_center(wall) -> tuple[float, float]:
    (x0, y0), (x1, y1) = wall.axis
    return (x0 + x1) / 2.0, (y0 + y1) / 2.0


def wall_length_m(wall) -> float:
    (x0, y0), (x1, y1) = wall.axis
    return ((x1 - x0) ** 2 + (y1 - y0) ** 2) ** 0.5


def truss_heel_note(spec: FramingSpec) -> str | None:
    """``STANDARD HEEL`` for an unauthored truss heel; else the height and where it is taken.

    The heel is measured at the outside face of bearing (decision #108), and that is printed
    with the number because a plant reading it at the wall line builds a different truss.
    """
    if spec.roof_frame != "truss":
        return None
    if spec.heel_height is None:
        return "STANDARD HEEL"
    return f"HEEL {inches(spec.heel_height.meters)} AT OUTSIDE FACE OF BEARING"


#: ASCE 7-16 Table 7.3-2 thermal factor: a roof over heated space, and an unheated or
#: open-air one (a garage, a canopy).
SNOW_CT_HEATED = 1.0
SNOW_CT_UNHEATED = 1.2


def roof_snow_thermal_factor(model: ResolvedModel, roof: ResolvedRoof) -> float:
    """C_t off the derived thermal boundary, never an authored flag.

    A cold vented attic over heated space (Table 7.3-2's 1.1) is not distinguished.
    """
    heated, _ = envelope_geometry(model).is_envelope_roof(roof)
    return SNOW_CT_HEATED if heated else SNOW_CT_UNHEATED


def flat_roof_snow_psf(ground_psf: float, c_t: float) -> float:
    """p_f = 0.7 C_e C_t I_s p_g (ASCE 7 eq. 7.3-1) at C_e = I_s = 1.0."""
    return 0.7 * c_t * ground_psf


def roof_snow_drift(model: ResolvedModel, roof: ResolvedRoof,
                    preferences: object) -> DriftReach | None:
    """The authored drift on ``roof`` as ``structural.truss_reactions`` grades it, or ``None``."""
    from typehaus.engineering.registry import EngineeringContext
    from typehaus.engineering.roof_beam import compute
    from typehaus.engineering.snow_drift import drift_reach

    if not drifted_design_snow_psf(preferences):
        return None
    ctx = EngineeringContext(plan=model.plan, model=model, preferences=preferences)
    records = {record.item_id: record for record in compute(ctx)}
    return drift_reach(model, preferences, records, roof)


def drifted_design_snow_psf(preferences: object) -> float | None:
    """The house's authored design snow for a roof-carrying beam (``roof_beam_snow_psf``)."""
    psf = getattr(getattr(preferences, "structural", None), "roof_beam_snow_psf", None)
    return float(psf) if psf else None


def drift_width_ft(preferences: object) -> float | None:
    """How far the authored drift runs from the drifted roof's far edge, ft."""
    width = getattr(getattr(preferences, "structural", None), "roof_beam_drift_width_ft", None)
    return float(width) if width else None


def snow_drift_text(roof: ResolvedRoof, drift: DriftReach | None,
                    preferences: object) -> str | None:
    """One sentence for S-001 and S-102: ``roof_snow_drift`` and the trusses it reaches.

    Claims only what is authored: the design snow is the house's number, not a derivation.
    """
    if drift is None:
        return None
    psf = drifted_design_snow_psf(preferences)
    snow = f"AUTHORED DESIGN SNOW {psf:.1f} PSF (PREFERENCES [STRUCTURAL] ROOF_BEAM_SNOW_PSF)"
    total = sum(1 for m in roof.members if m.category == "roof_truss")
    if drift.whole:
        trusses = f"; ALL {total} TRUSSES ARE DRIFT TRUSSES" if total else ""
        return f"{snow} ON {roof.tag}{trusses}."
    keys = ", ".join(key.upper() for key in sorted(drift.trusses))
    lead = (f"{roof.tag} {keys} ({len(drift.trusses)} OF {total}) ARE DRIFT TRUSSES"
            if drift.trusses else f"{roof.tag} CARRIES IT")
    width = drift_width_ft(preferences)
    reach = (f"RUNS {width:g} FT FROM ITS FAR EDGE INTO {roof.tag} (ROOF_BEAM_DRIFT_WIDTH_FT)"
             if width is not None else f"IS HELD OVER ALL OF {roof.tag} (NO DRIFT WIDTH STATED)")
    return (f"{lead}: THE DRIFT ON {drift.source} (AUTHORED DESIGN SNOW {psf:.1f} PSF, "
            f"PREFERENCES [STRUCTURAL] ROOF_BEAM_SNOW_PSF) {reach}. QUOTE THEM WITH THE "
            f"SURCHARGE NAMED, NOT ON GROUND SNOW ALONE.")
