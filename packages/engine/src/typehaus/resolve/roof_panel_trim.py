"""Image II rake turn-ups and non-vented ridge Z-closures.

Metal Sales Image II Pocket Installation Guide (2014 PDF, effective 6/2011):
pp. 20–23 eave hem/offset cleat; p. 26 rake with minimum 1 inch field turn-up;
pp. 32–33 non-vented ridge with sealed 1 inch Z-closures.
https://www.metalsales.us.com/wp-content/uploads/2020/03/Image-II-Pocket-Installation-Guide-2014.pdf
"""

import math

from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import panel_profile
from typehaus.resolve.metal_skin_profiles import PANEL_PROFILES
from typehaus.resolve.model import FramedMember
from typehaus.resolve.roof_edge_geometry import mitred_span, roof_edge_runs
from typehaus.resolve.roof_geometry import roof_plane_z, roof_slope_factor
from typehaus.resolve.trim_bands import formed_edge_bands

RAKE_LAP_M = inch(1.25).meters
RAKE_LEG_M = inch(4).meters
RIDGE_HALF_WIDTH_M = inch(6).meters
CLOSURE_FLANGE_M = inch(0.5).meters


def panel_profile_for_layer(model, cladding):
    if cladding is None:
        return None
    material = model.plan.library.material(cladding.material_ref)
    return PANEL_PROFILES.get(material.finish) if material else None


def rake_panel_trim(roof, profile, base, material):
    """The drip stays underneath; a separate crown-height rake covers the turned-up pan."""
    members = []
    factor = roof_slope_factor(roof)
    top = (base + profile.depth_m) * factor
    sheet = profile.sheet_thickness_m
    entry = next((e for e in roof.layer_edge_setbacks if e["layer"] == "roofing"), {})
    for run in roof_edge_runs(roof):
        if run.is_eave:
            continue
        outer = -float(entry.get(run.edge_name, 0.0))
        span = mitred_span(run, -outer - RAKE_LAP_M, -outer + RAKE_LAP_M)
        if span is None:
            continue
        bands = formed_edge_bands(2 * RAKE_LAP_M, RAKE_LEG_M, sheet)
        # A field-turned panel edge, under the cap's inboard lap (guide p. 26).
        bands = (*bands, ("turnup", RAKE_LAP_M - sheet, sheet, profile.depth_m * factor, 0.0))
        for key, offset, width, bottom_drop, top_drop in bands:
            center = outer - RAKE_LAP_M + offset + width / 2
            p0 = tuple(span.p0[i] + run.normal[i] * center for i in range(2))
            p1 = tuple(span.p1[i] + run.normal[i] * center for i in range(2))
            members.append(
                FramedMember(
                    parent_uid=roof.uid,
                    child_key=f"{run.key}-panel-rake-{key}",
                    category="corner_trim",
                    profile=panel_profile(
                        width / inch(1).meters, (bottom_drop - top_drop) / inch(1).meters
                    ),
                    p0=p0,
                    p1=p1,
                    z0_m=span.z0_m + top - bottom_drop,
                    z1_m=span.z0_m + top - top_drop,
                    z0_end_m=span.z1_m + top - bottom_drop,
                    z1_end_m=span.z1_m + top - top_drop,
                    length_m=math.dist(p0, p1),
                    material=material,
                    connection="roof:panel-rake",
                )
            )
    return tuple(members)


def ridge_panel_closures(roof, profile, base, material):
    """Profile-cut Z web in every pan; the crown flange seats the closed cap."""
    from typehaus.resolve.geometry_roofs import layer_inset_rect

    if roof.form != "gable":
        return ()
    along_x = roof.ridge_direction == "x"
    entry = next((e for e in roof.layer_edge_setbacks if e["layer"] == "roofing"), {})
    rect = layer_inset_rect(roof, entry, base)
    low, high = rect[:2] if along_x else rect[2:]
    across = [p[1 if along_x else 0] for p in roof.footprint]
    ridge = (min(across) + max(across)) / 2
    factor = roof_slope_factor(roof)
    sheet = profile.sheet_thickness_m
    members = []
    anchor = (low + high) / 2
    for sign in (-1, 1):
        cross = ridge + sign * RIDGE_HALF_WIDTH_M
        crown = roof_plane_z(roof, cross) + (base + profile.depth_m) * factor
        for k in range(
            math.floor((low - anchor) / profile.pitch_m),
            math.ceil((high - anchor) / profile.pitch_m),
        ):
            center = anchor + k * profile.pitch_m
            a, b = max(low, center), min(high, center + profile.pitch_m)
            if b <= a:
                continue

            def height(u, center=center, cross=cross):
                local = min(profile.pitch_m, max(0., u - center))
                points = profile.section_points_m
                for (x0, h0), (x1, h1) in zip(points, points[1:], strict=False):
                    if x0 <= local <= x1:
                        return (
                            roof_plane_z(roof, cross)
                            + (base + h0 + (h1 - h0) * (local - x0) / (x1 - x0)) * factor
                        )
                raise ValueError("Closure station outside panel module")

            stations = [
                a,
                *(center + x for x, _ in profile.section_points_m if a < center + x < b),
                b,
            ]
            bottom = [(u - a, height(u)) for u in stations]
            p0, p1 = ((a, cross), (b, cross)) if along_x else ((cross, a), (cross, b))
            # Crown segments have no opening. A tiny lap keeps the profile polygon simple.
            web_top = crown + sheet
            outline = (*bottom, (b - a, web_top), (0.0, web_top))
            key = f"ridge-closure-{sign}-{k}"
            common = dict(
                parent_uid=roof.uid,
                category="ridge_closure",
                p0=p0,
                p1=p1,
                length_m=b - a,
                material=material,
                connection="ridge:profile-closure",
            )
            members.append(
                FramedMember(
                    **common,
                    child_key=f"{key}-face",
                    profile=panel_profile(sheet / inch(1).meters, profile.depth_m / inch(1).meters),
                    plan_width_m=sheet,
                    z0_m=min(h for _, h in bottom),
                    z1_m=web_top,
                    elevation_profile=outline,
                )
            )
            members.append(
                FramedMember(
                    **common,
                    child_key=f"{key}-top",
                    profile=panel_profile(
                        CLOSURE_FLANGE_M / inch(1).meters, sheet / inch(1).meters
                    ),
                    plan_width_m=CLOSURE_FLANGE_M,
                    z0_m=crown,
                    z1_m=web_top,
                )
            )
            lower = (*bottom, *((u, z + sheet) for u, z in reversed(bottom)))
            members.append(
                FramedMember(
                    **common,
                    child_key=f"{key}-bottom",
                    profile=panel_profile(
                        CLOSURE_FLANGE_M / inch(1).meters, sheet / inch(1).meters
                    ),
                    plan_width_m=CLOSURE_FLANGE_M,
                    z0_m=min(h for _, h in bottom),
                    z1_m=crown + sheet,
                    elevation_profile=lower,
                )
            )
    return tuple(members)
