"""Snow-retention clamp capacity against the drift-loaded tributary wedge.

``structural.sliding_snow`` asks whether retention is authored; this asks whether its
clamps hold the snow behind them. Demand is the 45-degree wedge upslope of the rail
(MCA cold-climate guide, Fig. 12, as a screening boundary), widening into every coplanar
roof the run continues onto, loaded with the house's authored balanced snow plus the
roof-step drift triangle, and resolved downslope by sin(theta). Oracle:
``houses/catlin/notes/s5_snow_retention_review.md`` "Final clamp check".

Graded: the clamps' aggregate allowable, at ideal equal sharing. Named and NOT graded:
the rail's bending and end reactions, and the panel's attachment to the deck.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass

from typehaus.checks._authoring import structural_advisory as _advisory
from typehaus.checks._authoring import unknown as _unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.engineering.registry import records_of
from typehaus.engineering.snow_drift import DriftAxis, abutting, drift_axis
from typehaus.findings import Finding, Result, not_applicable
from typehaus.library.hardware.s5 import S5_N_IMAGE_II_24GA_DRAG
from typehaus.model.enums import ConnectorKind
from typehaus.model.structure import Connector
from typehaus.resolve.snow_retention_layout import snow_retention_layout

CHECK_ID = "structural.snow_retention_capacity"
_FT = 0.3048
_SAME_PLANE_FT = 0.01
_UNGRADED = ("ColorGard rail bending and end reactions (unequal clamp sharing) and the "
             "panel attachment to the deck are not graded: missing inputs (S-5! rail "
             "allowables, the panel maker's clip/fastener drag values)")


@dataclass(frozen=True)
class SnowWedge:
    """One rail's tributary wedge, in plan feet along the ridge axis."""

    rail_low: float
    rail_high: float
    run_low: float    # coplanar run's extent along the ridge
    run_high: float
    upslope_ft: float
    slope: float      # rise / run


@dataclass(frozen=True)
class DriftTriangle:
    balanced_psf: float
    surcharge_psf: float
    width_ft: float
    sign: float
    origin_ft: float  # distance downwind is ``sign * y - origin_ft``


def wedge_drag_lbf(wedge: SnowWedge, drift: DriftTriangle) -> tuple[float, float]:
    """(downslope drag lbf, vertical snow lb) on the wedge, integrated exactly.

    The inner integral over y has a closed form, so the integrand in t is piecewise
    quadratic; Simpson's rule on each piece between breakpoints is exact.
    """
    k = math.hypot(1.0, wedge.slope)
    south = wedge.rail_low - wedge.run_low
    north = wedge.run_high - wedge.rail_high

    def antiderivative(y: float) -> float:
        z = drift.sign * y - drift.origin_ft
        w = drift.width_ft
        drift_part = z if z < 0 else (z - z * z / (2 * w) if z <= w else w / 2)
        return drift.balanced_psf * y + drift.surcharge_psf * drift.sign * drift_part

    def bounds(t: float) -> tuple[float, float]:
        return wedge.rail_low - min(k * t, south), wedge.rail_high + min(k * t, north)

    def strip(t: float) -> float:
        low, high = bounds(t)
        return antiderivative(high) - antiderivative(low)

    breaks = {0.0, wedge.upslope_ft, south / k, north / k}
    for peak in (drift.origin_ft, drift.origin_ft + drift.width_ft):
        y = drift.sign * peak
        breaks.update(((wedge.rail_low - y) / k, (y - wedge.rail_high) / k))
    stations = sorted(t for t in breaks if 0.0 <= t <= wedge.upslope_ft)
    vertical = sum((b - a) / 6 * (strip(a) + 4 * strip((a + b) / 2) + strip(b))
                   for a, b in zip(stations, stations[1:], strict=False))
    return vertical * wedge.slope / k, vertical


def _coplanar_run(model, roof, along: int) -> tuple[float, float, list[str]]:
    """The extent along the ridge of ``roof`` plus every coplanar roof abutting it there."""
    def same_plane(other) -> bool:
        cross = 1 - along
        return (other.form == roof.form and other.ridge_direction == roof.ridge_direction
                and all(abs(a - b) <= _SAME_PLANE_FT * _FT for a, b in (
                    (other.eave_z_m, roof.eave_z_m), (other.ridge_z_m, roof.ridge_z_m),
                    (min(p[cross] for p in other.footprint),
                     min(p[cross] for p in roof.footprint)),
                    (max(p[cross] for p in other.footprint),
                     max(p[cross] for p in roof.footprint)))))

    run, tags, grew = [roof], [], True
    while grew:
        grew = False
        for other in model.roofs:
            if any(other is r for r in run) or not same_plane(other):
                continue
            if any((hit := abutting(r.footprint, other.footprint)) and hit[0] == along
                   for r in run):
                run.append(other)
                tags.append(other.tag)
                grew = True
    values = [p[along] for r in run for p in r.footprint]
    return min(values) / _FT, max(values) / _FT, tags


def _triangle(ctx: CheckContext, axis: DriftAxis | None, along: int) -> DriftTriangle | str:
    structural = getattr(ctx.preferences, "structural", None)
    keys = ("roof_beam_balanced_snow_psf", "roof_beam_drift_surcharge_psf",
            "roof_beam_drift_width_ft")
    values = [getattr(structural, key, None) for key in keys]
    missing = [key for key, value in zip(keys, values, strict=True) if value is None]
    if missing:
        return f"preferences.toml [structural] {', '.join(missing)} not authored"
    if axis is None:
        return "no authored roof-step drift reaches this roof (engineering/snow_drift)"
    if axis.axis != along:
        return "the drift decays across the slope, which this wedge does not integrate"
    balanced, surcharge, width = (float(v) for v in values)
    return DriftTriangle(balanced, surcharge, width, axis.sign, axis.origin_ft)


def _grade(ctx: CheckContext, connector: Connector) -> Finding | None:
    layout, _ = snow_retention_layout(ctx.model, connector)
    if layout is None:
        return None  # integrity.snow_retention_layout reports why
    roof = next(r for r in ctx.model.roofs if r.tag == layout.roof_ref)
    along = 0 if layout.along[0] else 1
    cross = 1 - along
    tags = (connector.tag, roof.tag)
    drift = _triangle(ctx, drift_axis(ctx.model, records_of(ctx), roof), along)
    if isinstance(drift, str):
        return _unknown(CHECK_ID, f"{connector.tag}: {drift}", tags)
    across = [p[cross] for p in roof.footprint]
    low, high = min(across), max(across)
    clamp_line = layout.origin[cross]
    high_line = high if roof.form == "shed" else (low + high) / 2
    run_m = high - low if roof.form == "shed" else (high - low) / 2
    run_low, run_high, onto = _coplanar_run(ctx.model, roof, along)
    wedge = SnowWedge(
        (layout.origin[along] + layout.start) / _FT, (layout.origin[along] + layout.end) / _FT,
        run_low, run_high, abs(high_line - clamp_line) / _FT,
        (roof.ridge_z_m - roof.eave_z_m) / run_m)
    demand, vertical = wedge_drag_lbf(wedge, drift)
    datum = S5_N_IMAGE_II_24GA_DRAG
    gauge = _panel_gauge(ctx, roof)
    if gauge != datum.gauge:
        said = f"is {gauge} ga" if gauge else "states no gauge in its cladding Material's name"
        return _unknown(CHECK_ID, f"{connector.tag}: {roof.tag} {said}; the only drag datum "
                                  f"is {datum.panel}", tags)
    count = len(layout.supports)
    capacity = count * datum.allowable_lbf
    ratio = demand / capacity
    reach = f", running onto {', '.join(onto)}" if onto else ""
    return _advisory(
        CHECK_ID,
        f"{connector.tag}: drift-loaded 45-degree wedge{reach} carries {vertical:,.0f} lb "
        f"({drift.balanced_psf:g} psf balanced + {drift.surcharge_psf:g} psf drift over "
        f"{drift.width_ft:g} ft); downslope drag {demand:,.0f} lbf against {count} "
        f"{datum.clamp_model} x {datum.allowable_lbf:g} lbf = {capacity:,.0f} lbf "
        f"({datum.panel}), d/c {ratio:.3f} at ideal sharing. {_UNGRADED}",
        tags, Result.PASS if ratio <= 1.0 else Result.FAIL,
        fix_hint=None if ratio <= 1.0 else
        "lengthen the rail onto more seams or add a second row upslope",
        code=datum.citation)


def _panel_gauge(ctx: CheckContext, roof) -> int | None:
    """The roof cladding's sheet gauge, as its Material's name spells it ("24 ga")."""
    assembly = ctx.plan.library.resolve_assembly(roof.assembly)
    cladding = [layer for layer in (assembly.layers if assembly else ())
                if layer.function.value == "cladding"]
    material = cladding and ctx.plan.library.material(cladding[-1].material_ref)
    found = re.search(r"\b(\d{2})\s*ga\b", material.name) if material else None
    return int(found.group(1)) if found else None


@check(Tier.STRUCTURAL, CHECK_ID)
def snow_retention_capacity(ctx: CheckContext) -> list[Finding]:
    """Do a snow-retention run's clamps hold the drift-loaded wedge behind them?"""
    runs = [element for element in ctx.plan.all_elements()
            if isinstance(element, Connector) and element.kind is ConnectorKind.SNOW_GUARD
            and element.snow_retention is not None]
    if not runs:
        return [not_applicable(CHECK_ID, "no dimensioned snow-retention run is authored")]
    graded = [finding for finding in (_grade(ctx, run) for run in runs) if finding]
    return graded or [_unknown(CHECK_ID, "no snow-retention run resolves a layout",
                               tuple(run.tag for run in runs))]
