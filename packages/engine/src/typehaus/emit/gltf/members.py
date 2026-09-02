"""Framing members as solid boxes, and the split between roof *framing* and roof *skin*."""

from __future__ import annotations

from typehaus.emit.gltf.mesh import _MeshBuilder
from typehaus.emit.gltf.palette import _color, _material_finish_color
from typehaus.resolve.geometry_ir import GSweep
from typehaus.resolve.geometry_members import member_solid
from typehaus.resolve.model import FramedMember

# A roof carries two different kinds of member: sticks (rafters, truss chords and webs, gable
# studs, outlookers, barge rafters, the fascia nailed to the rafter tails — framing, and they
# belong under the framing toggle with every other stick) and skin (the wall→roof closure
# bands, the derived soffit, the roof-edge cladding — envelope, and they belong with the roof
# shell they finish). These are the skin categories: layer functions plus the derived trim.
# Fascia is trim by category but framing by trade (its members carry trade="framing"), so it
# counts as framing here. Mirrored by ``ROOF_SKIN_CATEGORIES`` in ui/src/three/members.ts —
# keep the two in step.
ROOF_SKIN_CATEGORIES = frozenset({
    "sheathing", "membrane", "insulation", "furring", "cladding", "airgap", "air_gap",
    "lining", "finish", "soffit", "gutter", "ridge_cap", "corner_trim",
})


def is_roof_framing_member(member: FramedMember) -> bool:
    """Whether a roof member is structural framing rather than envelope skin or trim."""
    return member.category.lower() not in ROOF_SKIN_CATEGORIES


def _add_member(mb: _MeshBuilder, member: FramedMember) -> None:
    """Emit one member from the shared IR box.

    This used to build its own geometry with ``width_m / 2`` as *every* half-extent, which
    ignored both ``orient`` and ``depth_m``: an upright 2x6 stud exported as a 5.5" square
    post, and its section did not follow the wall it stood in. ``member_box`` is the IFC
    implementation — the one that was right — so the two exports now agree by construction
    rather than by review.
    """
    # A member that names a material is a *skin* band (wall→roof closure, derived trim, roof
    # edge cladding), not lumber: colour it the way the wall and roof layer stacks colour the
    # same material, so a standing-seam closure reads as white metal rather than category grey.
    color = (_material_finish_color(member.material, member.category)
             if member.material else _color(member.category))
    if member.plan_outline is not None:
        mb.add_prism(member.plan_outline, member.z0_m, member.z1_m, color)
        return
    solid = member_solid(member)
    if solid is None:  # degenerate; no importer can tessellate a zero-area shell
        return
    if isinstance(solid, GSweep):
        mb.add_sweep(solid, color)
        return
    mb.add_gbox(solid, color)


def owned_elsewhere(member: FramedMember, container_uid: str) -> bool:
    """Whether a member emitted under ``container_uid`` in fact belongs to another element.

    A wall→roof closure band is resolved by the roof (it needs the roof planes to know how
    high to climb) but it is the *wall's* own weather skin carried past the top plate, and it
    carries the wall's uid in ``parent_uid``. Filing it with the roof is what put a gable
    end's whole layer stack — a full raking triangle of wall, not a 12" strip — behind the
    roof toggle and made it select as the roof. Ownership is the member's own answer, so both
    exporters and the viewer ask it here rather than guessing from the container.
    """
    return bool(member.parent_uid) and member.parent_uid != container_uid
