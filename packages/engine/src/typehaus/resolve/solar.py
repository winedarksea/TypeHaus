"""Authored SolarPanel -> tilted corner geometry on its roof plane.

The one place the tilt math lives: a module's four plan corners come from its origin,
its along-ridge width, and its down-slope length foreshortened by the pitch; the corner
elevations ride the roof plane (``roof_height_at``) offset along the plane normal by the
standoff and thickness. IFC, glTF, and the viewer all read the resolved corners.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.model.structure import SolarPanel
from typehaus.resolve.model import ResolvedModel, ResolvedSolarPanel
from typehaus.resolve.roof_geometry import roof_height_at


def resolve_solar(model: ResolvedModel) -> list[Finding]:
    findings: list[Finding] = []
    for storey in model.plan.storeys:
        for element in model.plan.storey_elements(storey.tag):
            if isinstance(element, SolarPanel):
                findings.extend(_resolve_panel(model, element, storey.tag))
    return findings


def _resolve_panel(model: ResolvedModel, panel: SolarPanel, storey_tag: str) -> list[Finding]:
    roof = next((r for r in model.roofs if r.tag == panel.roof_ref), None)
    if roof is None:
        return [Finding(
            severity=Severity.ERROR, check_id="integrity.solar_roof_ref",
            message=f"solar panel {panel.tag} references missing roof {panel.roof_ref}",
            element_tags=(panel.tag,), result=Result.FAIL,
        )]

    xs = [p[0] for p in roof.footprint]
    ys = [p[1] for p in roof.footprint]
    if roof.ridge_direction == "y":
        low, high = min(xs), max(xs)
    else:
        low, high = min(ys), max(ys)
    half_span = (high - low) / 2.0
    rise = roof.ridge_z_m - roof.eave_z_m
    slope = rise / half_span if half_span > 1e-9 else 0.0  # dz per plan metre down-slope
    plane_factor = (1.0 + slope * slope) ** 0.5  # panel-plane length per plan length
    ridge = (low + high) / 2.0

    ox, oy = panel.origin.xy_m
    width = panel.width.meters
    plan_length = panel.length.meters / plane_factor  # foreshortened down-slope run
    cross = ox if roof.ridge_direction == "y" else oy
    downhill = -1.0 if cross <= ridge else 1.0  # away from the ridge

    if roof.ridge_direction == "y":
        plan = [(ox, oy), (ox, oy + width),
                (ox + downhill * plan_length, oy + width), (ox + downhill * plan_length, oy)]
        # Surface z = f(cross-axis): gradient is along x; the outward normal leans back
        # over the ridge by the same slope.
        normal = (downhill * -slope / plane_factor, 0.0, 1.0 / plane_factor)
    else:
        plan = [(ox, oy), (ox + width, oy),
                (ox + width, oy + downhill * plan_length), (ox, oy + downhill * plan_length)]
        normal = (0.0, downhill * -slope / plane_factor, 1.0 / plane_factor)

    # Emitters (the IFC closed shell in particular) require counter-clockwise plan
    # winding; the down-slope direction flips it on one side of the ridge.
    area2 = sum(plan[i][0] * plan[(i + 1) % 4][1] - plan[(i + 1) % 4][0] * plan[i][1]
                for i in range(4))
    if area2 < 0:
        plan.reverse()

    def offset(points, distance):
        return tuple(
            (x + normal[0] * distance, y + normal[1] * distance,
             roof_height_at(roof, (x, y)) + normal[2] * distance)
            for x, y in points)

    standoff = panel.standoff.meters
    model.solar_panels.append(ResolvedSolarPanel(
        uid=panel.uid, tag=panel.tag, storey=storey_tag, roof_ref=panel.roof_ref,
        corners_bottom=offset(plan, standoff),
        corners_top=offset(plan, standoff + panel.thickness.meters),
        watts=panel.watts, product=panel.product,
    ))
    return []
