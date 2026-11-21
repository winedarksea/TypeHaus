"""Where landing framing hangs on an authored column's face.

``resolve/stairs/post_cuts.py`` stops a landing rim or joist at a column it meets, so the
cut end sits ON a face, its depth inside the column's height. That end is hung: a face-mount
hanger on the column (``authored.hanger_part`` picks the concealed-flange LUC, the part
Simpson publishes for post conditions). Geometric like ``hung.py``, never by name.
"""

from __future__ import annotations

import math

from typehaus.hardware.config import HangerDetectionRules
from typehaus.joints.bearing import is_treated
from typehaus.quantities import M_PER_IN
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import ResolvedModel

# A cut end this close to a column face is on it.
_ON_FACE_M = M_PER_IN / 16.0


def column_hung_connections(model: ResolvedModel, rules: HangerDetectionRules) -> list:
    """One ``HungConnection`` per landing-framing end standing on a column face."""
    from typehaus.joints.hung import HungConnection

    columns = [solid for solid in model.solids
               if solid.category in rules.carrier_column_categories and solid.outline]
    if not columns:
        return []
    found = []
    for member in model.all_members():
        if member.category not in rules.column_hung_categories or member.p0 == member.p1:
            continue
        width = member.plan_width_m or cross_section(member.profile).width_m
        for point, other in ((member.p0, member.p1), (member.p1, member.p0)):
            run = math.dist(point, other)
            into = ((other[0] - point[0]) / run, (other[1] - point[1]) / run)
            column = _column_face_under(columns, point, into, width, member)
            if column is None:
                continue
            xs = [p[0] for p in column.outline]
            ys = [p[1] for p in column.outline]
            along_x = abs(into[0]) > 0.5
            centre = (((min(xs) + max(xs)) / 2.0, point[1]) if along_x
                      else (point[0], (min(ys) + max(ys)) / 2.0))
            found.append(HungConnection(
                member_key=f"{member.parent_uid}:{member.child_key}",
                member_profile=member.profile, carrier_tag=column.tag, sloped=False,
                carrier_category="column",
                carrier_treated=is_treated(model, column.assembly,
                                           material_ref=column.material),
                station_m=0.0, point_m=centre, carrier_soffit_m=member.z0_m,
                member_depth_m=member.z1_m - member.z0_m,
                axis="y" if along_x else "x", member_category=member.category,
                outward_xy=into, member_width_m=width, seat_z_m=member.z0_m))
    return found


def _column_face_under(columns, point, into, width: float, member):
    """The column whose face ``point`` stands on, the member leaving it along ``into``."""
    if abs(into[0]) < 0.99 and abs(into[1]) < 0.99:
        return None  # only axis-aligned framing meets a square face
    axis = 0 if abs(into[0]) > 0.5 else 1
    for column in columns:
        if not (column.z0_m <= member.z0_m + 1e-6 and member.z1_m <= column.z1_m + 1e-6):
            continue
        lo = min(p[axis] for p in column.outline)
        hi = max(p[axis] for p in column.outline)
        face = hi if into[axis] > 0 else lo
        if abs(point[axis] - face) > _ON_FACE_M:
            continue
        side_lo = min(p[1 - axis] for p in column.outline)
        side_hi = max(p[1 - axis] for p in column.outline)
        if (point[1 - axis] - width / 2.0 >= side_lo - 1e-6
                and point[1 - axis] + width / 2.0 <= side_hi + 1e-6):
            return column
    return None
