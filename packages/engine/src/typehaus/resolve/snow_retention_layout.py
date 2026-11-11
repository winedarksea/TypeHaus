"""One roof-local component layout shared by rendering and purchasing."""

from __future__ import annotations

import math
from dataclasses import dataclass

from typehaus.findings import Finding, element_error
from typehaus.hardware.snow_retention import (
    GEOMETRY_TOLERANCE_M,
    INCH_M,
    MAX_END_CANTILEVER_IN,
    MAX_SUPPORT_SPACING_IN,
    SNOCLIP_WIDTH_IN,
    SPLICE_GAP_IN,
    STOCK_LENGTH_IN,
)
from typehaus.model.enums import ConnectorKind
from typehaus.model.structure import Connector
from typehaus.resolve.model import ResolvedModel
from typehaus.resolve.roof_geometry import roof_plane_z, roof_slope_coordinate


@dataclass(frozen=True)
class SnowRetentionLayout:
    roof_ref: str
    origin: tuple[float, float, float]
    along: tuple[float, float, float]
    downhill: tuple[float, float, float]
    normal: tuple[float, float, float]
    start: float
    end: float
    supports: tuple[float, ...]
    snow_clips: tuple[float, ...]
    segments: tuple[tuple[float, float], ...]
    roof_material: str
    sheet_thickness: float
    seam_height: float

    def world(self, along: float, downhill: float, normal: float):
        return tuple(self.origin[i] + self.along[i] * along
                     + self.downhill[i] * downhill + self.normal[i] * normal
                     for i in range(3))


def rail_segments(start: float, end: float) -> tuple[tuple[float, float], ...]:
    """Balance cuts so a run just over stock length has no tiny unsupported tail."""
    count = max(1, math.ceil((end - start - GEOMETRY_TOLERANCE_M)
                             / (STOCK_LENGTH_IN * INCH_M)))
    step = (end - start) / count
    return tuple((start + index * step, start + (index + 1) * step)
                 for index in range(count))


def _snow_clip_stations(supports, profile, segments, enabled):
    if not enabled:
        return ()
    # Image II's central striation is directly under the nominal midpoint. Use the
    # nearest flat pan interval wide enough for the whole rubber foot instead.
    flat_centres = tuple(
        (a[0] + b[0]) / 2 for a, b in zip(
            profile.section_points_m, profile.section_points_m[1:], strict=False)
        if abs(a[1] - profile.sheet_thickness_m) < GEOMETRY_TOLERANCE_M
        and abs(b[1] - a[1]) < GEOMETRY_TOLERANCE_M
        and b[0] - a[0] >= SNOCLIP_WIDTH_IN * INCH_M)
    if not flat_centres:
        return None
    clips = []
    clearance = (SNOCLIP_WIDTH_IN + SPLICE_GAP_IN) * INCH_M / 2
    for start, end in zip(supports, supports[1:], strict=False):
        candidates = [start + offset for offset in flat_centres
                      if start + offset < end
                      and all(abs(start + offset - joint) >= clearance
                              for _, joint in segments[:-1])]
        if not candidates:
            return None
        clips.append(min(candidates, key=lambda value: (
            round(abs(value - (start + end) / 2) / GEOMETRY_TOLERANCE_M), value)))
    return tuple(clips)


def snow_retention_layout(model: ResolvedModel, connector: Connector
                          ) -> tuple[SnowRetentionLayout | None, list[Finding]]:
    """Resolve explicit run intent; invalid hosts never fall back to marker geometry."""
    from typehaus.resolve.roof_panel_skin import profiled_roof_layers, seam_stations

    def invalid(message):
        return None, [element_error("integrity.snow_retention_layout",
                                    f"{connector.tag}: {message}", connector.tag)]

    spec = connector.snow_retention
    if spec is None:
        return invalid("a snow-retention run specification is required")
    if (connector.kind is not ConnectorKind.SNOW_GUARD or connector.elevation is not None
            or connector.roof_mount is not None):
        return invalid("use SNOW_GUARD with roof-derived elevation, without roof_mount")
    roofs = [roof for roof in model.roofs if roof.tag in connector.connects]
    if len(roofs) != 1:
        return invalid("connects must name exactly one resolved host roof")
    roof = roofs[0]
    if roof.form not in ("gable", "shed"):
        return invalid("snow-retention geometry supports gable and shed roofs")
    if connector.axis not in (roof.ridge_direction, "-" + roof.ridge_direction):
        return invalid("rail axis must be parallel to the host roof ridge")
    layers = list(profiled_roof_layers(roof, model))
    if len(layers) != 1 or layers[0][3].key != "standing-seam":
        return invalid("S-5-N requires the supported Image II standing-seam roof profile")
    layer, base, rect, profile = layers[0]
    along_index = 0 if roof.ridge_direction == "x" else 1
    cross_index = 1 - along_index
    position = connector.position.xy_m
    centre = position[along_index]
    start, end = centre - spec.length.meters / 2, centre + spec.length.meters / 2
    along_low, along_high = rect[:2] if along_index == 0 else rect[2:]
    cross_low, cross_high = rect[2:] if along_index == 0 else rect[:2]
    cross = position[cross_index]
    if (start < along_low - GEOMETRY_TOLERANCE_M
            or end > along_high + GEOMETRY_TOLERANCE_M
            or not cross_low < cross < cross_high):
        return invalid("rail extent and clamp line must lie inside the roof panel footprint")
    across = [point[cross_index] for point in roof.footprint]
    low, high = min(across), max(across)
    ridge = (low + high) / 2
    if roof.form != "shed" and abs(cross - ridge) < GEOMETRY_TOLERANCE_M:
        return invalid("clamp line must be on a roof slope, clear of the ridge")
    direction = 1.0 if roof.form == "shed" or cross > ridge else -1.0
    run = high - low if roof.form == "shed" else (high - low) / 2
    if run <= GEOMETRY_TOLERANCE_M:
        return invalid("host roof must have a nonzero slope span")
    slope = (roof.ridge_z_m - roof.eave_z_m) / run
    if roof.form == "shed":
        direction = -1.0
    factor = math.hypot(1, slope)
    along = tuple(float(i == along_index) for i in range(3))
    downhill = tuple(direction / factor if i == cross_index else
                     (-slope / factor if i == 2 else 0.0) for i in range(3))
    normal = tuple(direction * slope / factor if i == cross_index else
                   (1 / factor if i == 2 else 0.0) for i in range(3))
    # The offset roof pan remains at the authored x/y. Layer depth is normal to
    # the roof; its vertical intercept is base * factor, not base / factor.
    z = roof_plane_z(roof, roof_slope_coordinate(roof, position)) + base * factor
    supports = tuple(value for value in seam_stations(roof, model)
                     if start <= value <= end)
    if len(supports) < 2:
        return invalid("rail needs at least two seam-clamp supports")
    segments = rail_segments(start, end)
    clips = _snow_clip_stations(supports, profile, segments, spec.snow_clip is not None)
    if clips is None:
        return invalid("no flat pan interval accommodates the SnoClip foot clear of splices")
    layout = SnowRetentionLayout(
        roof.tag, (position[0], position[1], z), along, downhill, normal,
        start - centre, end - centre, tuple(s - centre for s in supports),
        tuple(s - centre for s in clips),
        tuple((a - centre, b - centre) for a, b in segments), layer.material_ref,
        profile.sheet_thickness_m, profile.depth_m)
    findings = []
    if (max(supports[0] - start, end - supports[-1])
            > MAX_END_CANTILEVER_IN * INCH_M + GEOMETRY_TOLERANCE_M):
        findings.extend(invalid("rail end cantilever exceeds S-5!'s 8-inch limit")[1])
    if any(b - a > MAX_SUPPORT_SPACING_IN * INCH_M + GEOMETRY_TOLERANCE_M
           for a, b in zip(supports, supports[1:], strict=False)):
        findings.extend(invalid("support spacing exceeds ColorGard 2.0's 42-inch limit")[1])
    for segment_start, segment_end in layout.segments:
        if sum(segment_start - GEOMETRY_TOLERANCE_M <= s
               <= segment_end + GEOMETRY_TOLERANCE_M for s in layout.supports) < 2:
            findings.extend(invalid("each cut crossmember needs at least two clamps")[1])
            break
    return layout, findings
