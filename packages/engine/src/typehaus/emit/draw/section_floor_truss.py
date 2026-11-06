"""An open-web floor truss in section: chords, TrimEnds, chase posts and Warren webs.

The twin of ``section_truss`` for a floor truss, drawn from the same derived
``OpenWebShape`` (``resolve/open_web.py``) the viewer and the checks read: nothing here
decides where a web goes. Polygons are in the truss plane: ``s`` from the p0 end, ``z``
absolute.
"""

from __future__ import annotations

from typehaus.emit.draw.section_truss import _bar, emit_truss_cut


def floor_truss_sticks(member, section) -> list[list[tuple[float, float]]]:
    """Each stick of ``member``'s truss as a polygon, or none where it carries no shape."""
    shape = member.web
    if shape is None:
        return []
    z0, depth, chord = member.z0_m, section.depth_m, section.flange_thickness_m
    length = member.length_m
    sticks = [[(0.0, z0), (length, z0), (length, z0 + chord), (0.0, z0 + chord)],
              [(0.0, z0 + depth - chord), (length, z0 + depth - chord),
               (length, z0 + depth), (0.0, z0 + depth)]]
    for stick in shape.sticks:
        if stick.kind == "diagonal":
            sticks.append(_bar((stick.run0_m, z0 + stick.z0_m), (stick.run1_m, z0 + stick.z1_m),
                               shape.web_thickness_m, shape.web_thickness_m / 2.0))
        else:
            a, b = stick.run0_m, stick.run1_m
            low, high = z0 + stick.z0_m, z0 + stick.z1_m
            sticks.append([(a, low), (b, low), (b, high), (a, high)])
    return sticks


def emit_floor_truss_cut(b, member, section, plane, crop, uid, tag, pattern, material,
                         is_cut: bool) -> bool:
    """Draw ``member`` as its sticks, along or across the cut (see ``emit_truss_cut``)."""
    return emit_truss_cut(b, member, section, plane, crop, uid, tag, pattern, material,
                          is_cut, sticks=floor_truss_sticks(member, section))
