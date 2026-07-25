"""Framing members as solid boxes, and the split between roof *framing* and roof *skin*."""

from __future__ import annotations

from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _color, _material_finish_color
from typehaus.resolve.framing.profiles import cross_section
from typehaus.resolve.model import FramedMember


# A roof carries two different kinds of member: sticks (rafters, truss chords and webs, gable
# studs, outlookers, barge rafters — framing, and they belong under the framing toggle with
# every other stick) and skin (the wall→roof closure bands, the derived fascia/soffit, the
# roof-edge cladding — envelope, and they belong with the roof shell they finish). These are
# the skin categories: layer functions plus the derived trim. Mirrored by
# ``ROOF_SKIN_CATEGORIES`` in ui/src/three/members.ts — keep the two in step.
ROOF_SKIN_CATEGORIES = frozenset({
    "sheathing", "membrane", "insulation", "furring", "cladding", "airgap", "air_gap",
    "lining", "finish", "fascia", "soffit",
})


def is_roof_framing_member(member: FramedMember) -> bool:
    """Whether a roof member is structural framing rather than envelope skin or trim."""
    return member.category.lower() not in ROOF_SKIN_CATEGORIES


def _member_half_width(profile: str) -> float:
    # Half the parsed cross-section width, so glTF box widths agree with the UI (which
    # consumes model_json's cross_section-derived width_m) for every profile — including
    # "hanger", "tapered tread", "deck WxT", and multi-ply LVLs.
    return cross_section(profile).width_m / 2.0


def _add_member(mb: _MeshBuilder, member: FramedMember) -> None:
    half = _member_half_width(member.profile)
    # A member that names a material is a *skin* band (wall→roof closure, derived trim, roof
    # edge cladding), not lumber: colour it the way the wall and roof layer stacks colour the
    # same material, so a standing-seam closure reads as white metal rather than category grey.
    color = (_material_finish_color(member.material, member.category)
             if member.material else _color(member.category))
    mb.add_member_box(
        (member.p0[0], member.p0[1], member.z0_m),
        (member.p1[0], member.p1[1], member.z1_m), half, color,
        z0_end=member.z0_end_m, z1_end=member.z1_end_m,
    )
