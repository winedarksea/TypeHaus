"""Pan-end return hems; rib ends remain open under the house's hot-roof decision.

Image II Pocket Installation Guide pp. 20–23: notch ribs and hem the pan onto an
inserted offset cleat. The pan returns under the drip nose, independent of rib height.
"""

import math
from dataclasses import replace

from typehaus.quantities import inch
from typehaus.resolve.framing.profiles import panel_profile
from typehaus.resolve.geometry_ir import GMesh
from typehaus.resolve.geometry_members import member_solid
from typehaus.resolve.geometry_slice import sweep_mesh
from typehaus.resolve.model import FramedMember
from typehaus.resolve.roof_geometry import roof_plane_z, roof_slope_factor
from typehaus.resolve.surface_clipping import face_normal

HEM_RETURN_M = inch(0.5).meters
CLEAT_SHEET_M = inch(0.032).meters


def _flat_shaded(mesh: GMesh) -> GMesh:
    """Unshare each facet's corners so it carries its own normal, as the viewer requires."""
    positions, triangles, normals = [], [], []
    for triangle in mesh.triangles:
        corners = [mesh.positions[index] for index in triangle]
        normal = face_normal(corners)
        if normal is None:
            continue
        start = len(positions)
        positions.extend(corners)
        normals.extend([normal] * 3)
        triangles.append((start, start + 1, start + 2))
    return GMesh(tuple(positions), tuple(triangles), tuple(normals))


def roof_pan_hems(roof, rect, base, profile, material):
    """Thin return under each pan, cut short of the seam legs at each module edge."""
    along_x = roof.ridge_direction == "x"
    low, high = rect[:2] if along_x else rect[2:]
    across_low, across_high = rect[2:] if along_x else rect[:2]
    factor = roof_slope_factor(roof)
    slope = math.sqrt(factor * factor - 1)
    sheet = profile.sheet_thickness_m
    anchor = (low + high) / 2
    members = []
    for sign, edge in ((-1, across_low), (1, across_high)):
        if roof.form == "shed" and sign > 0:
            continue
        # The inset rectangle precedes the layer-base normal translation.
        edge += sign * base * slope / factor
        support = roof_plane_z(roof, edge) + base * factor
        drop = CLEAT_SHEET_M + 2 * sheet
        # Left-normal coordinates are +cross for a y ridge, -cross for an x ridge.
        out_sign = sign * (-1 if along_x else 1)
        return_rise = HEM_RETURN_M * slope
        ring = (
            (0.0, sheet),
            (0.0, -drop),
            (-out_sign * HEM_RETURN_M, -drop + return_rise),
            (-out_sign * HEM_RETURN_M, -drop + return_rise + sheet),
            (-out_sign * sheet, -drop + sheet),
            (-out_sign * sheet, sheet),
        )
        margin = profile.crown_width_m or sheet
        for k in range(
            math.floor((low - anchor) / profile.pitch_m),
            math.ceil((high - anchor) / profile.pitch_m),
        ):
            center = anchor + k * profile.pitch_m
            a, b = max(low, center + margin), min(high, center + profile.pitch_m - margin)
            if b <= a:
                continue
            p0, p1 = ((a, edge), (b, edge)) if along_x else ((edge, a), (edge, b))
            member = FramedMember(
                parent_uid=roof.uid,
                child_key=f"pan-hem-{sign}-{k}",
                category="roof_panel_hem",
                profile=panel_profile(HEM_RETURN_M / inch(1).meters, drop / inch(1).meters),
                p0=p0,
                p1=p1,
                z0_m=support,
                z1_m=support + sheet,
                length_m=b - a,
                material=material,
                connection="roof:pan-hem",
                section_ring=ring,
            )
            mesh = _flat_shaded(sweep_mesh(member_solid(member)))
            members.append(replace(member, surface_mesh=mesh))
    return tuple(members)
