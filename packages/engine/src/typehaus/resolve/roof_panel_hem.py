"""Pan-end return hems: ribs notched, the pan hemmed onto an inserted offset cleat.

Image II Pocket Installation Guide pp. 20–23. The pan returns under the drip nose,
independent of rib height. Sealing the rib ends is ``roof_eave_rib_ends``.
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
_EDGE_NAMES = {(True, -1): "south", (True, 1): "north", (False, -1): "west", (False, 1): "east"}
CLEAT_SHEET_M = inch(0.032).meters


def flat_shaded(mesh: GMesh) -> GMesh:
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


def cleat_eave_seat(roof, edge: float, sign: float, base: float) -> tuple[float, float]:
    """``(across, z)`` of a cleat eave's pan seat, from the roofing rectangle's edge."""
    factor = roof_slope_factor(roof)
    # The inset rectangle precedes the layer-base normal translation.
    edge += sign * base * math.sqrt(factor * factor - 1) / factor
    return edge, roof_plane_z(roof, edge) + base * factor


def roof_pan_hems(roof, rect, base, profile, material, skip=frozenset(), anchor=None):
    """Thin return under each pan, cut short of the seam legs at each module edge.

    ``skip`` names the eave edges whose pans wrap an Image II Extended Eave instead
    (``roof_image_ii_pan_end``).
    """
    along_x = roof.ridge_direction == "x"
    low, high = rect[:2] if along_x else rect[2:]
    across_low, across_high = rect[2:] if along_x else rect[:2]
    factor = roof_slope_factor(roof)
    slope = math.sqrt(factor * factor - 1)
    sheet = profile.sheet_thickness_m
    anchor = (low + high) / 2 if anchor is None else anchor
    members = []
    for sign, edge in ((-1, across_low), (1, across_high)):
        if roof.form == "shed" and sign > 0:
            continue
        if _EDGE_NAMES[(along_x, sign)] in skip:
            continue
        edge, support = cleat_eave_seat(roof, edge, sign, base)
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
            mesh = flat_shaded(sweep_mesh(member_solid(member)))
            members.append(replace(member, surface_mesh=mesh))
    return tuple(members)
