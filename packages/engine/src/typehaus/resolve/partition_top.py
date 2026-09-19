"""An interior partition's framing stops 3/4" clear of the structure above it.

**One rule, one writer.** Before this, a partition's top was written by whichever pass
happened to reach it: ``roof_geometry.apply_to_roof_wall_tops`` raked an attic ``ToRoof``
wall to the roof *deck* plane — through the full depth of the rafter — and
``platform.extend_walls_to_platform`` lifted a storey-line partition to the datum above,
which is the *top* of the joists. Both put a double top plate inside a member, and nothing
caught it (``checks/structural/interference.py`` clears a plate-against-rafter contact
unconditionally as a birdsmouth seat).

A partition is not tight to the structure either. The deck above it deflects, and a
partition that props it is a partition carrying load it was never designed for — so the
plate stops short and a **Simpson Strong-Drive SDPW DEFLECTOR** screw spans the gap,
holding the wall laterally while releasing the joint vertically. See
``houses/catlin/notes/partition_top_deflection.md``.

**Only the framing top moves.** A ``ResolvedWall`` carries two tops and they answer to
different owners: ``plate_top_z_m``/``top_z0_m``/``top_z1_m`` are the framing and are this
module's, while ``z1_m`` is the body — the layer prisms, the gypsum bill, the stair
enclosure's extent, the wet wall a riser climbs — and stays with ``platform.py``. Cutting
the body at the joist soffit too opens a 12-5/8" slot in ``ST-S2A``'s stair enclosure
(``code.R312_1_1_stair_open_side``) and leaves three basement risers standing outside their
own wet wall (``mep.wet_wall_occupancy``). ``platform.py``'s own docstring already states
that asymmetry. In the attic the two coincide, because gypsum cannot pass through a rafter
either.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any

from shapely.geometry import LineString

from typehaus.model.refs import ToRoof
from typehaus.resolve.ceiling_over import (
    ceiling_decks_over,
    deck_structure_underside_m,
)
from typehaus.resolve.layer_bands import reband, reband_for_platform
from typehaus.resolve.layout_lines import lines_by_wall
from typehaus.resolve.model import ResolvedModel, ResolvedRoof, ResolvedWall
from typehaus.resolve.partition import (
    DEFLECTION_GAP_M,
    bearing_ref_tags,
    takes_a_deflection_gap,
)
from typehaus.resolve.roof_geometry import roof_underside_at
from typehaus.resolve.topology import site_grade_elevation_m_from_plan


def _wall_face(wall: ResolvedWall) -> Any:
    """The wall's plan footprint as a polygon — its axis given its own thickness."""
    return LineString(wall.axis).buffer(max(wall.thickness_m, 1e-3) / 2.0, cap_style=2)


def deck_underside_over(model: ResolvedModel, wall: ResolvedWall) -> float | None:
    """The naked structure soffit over ``wall``, or ``None`` where there is none.

    The **minimum** across every deck that roofs the wall. A ``ResolvedWall`` carries one
    flat framing top; a stepped plate is not expressible, and the low reading is the one
    that never runs into structure. Catlin needs both halves of that: the main floor is
    split between an I-joist soffit at -11 7/8" and ``SL-M-DECK``'s SIP soffit at
    -13 7/16", and ``W-B-CW``/``W-B-CW3`` also see ``SL-M-TUBDK`` **20" up**, where a
    ``max`` would put a basement plate 19-1/4" above the ceiling.

    ``ceiling_decks_over`` reads authored outlines, storey elevations and member profiles
    and never touches framing, so this pass is safe in the envelope stage — ``resolve_floors``
    has not run yet and does not have to.

    No structure above ⇒ ``None``, and the caller leaves the wall alone. Never a guess.
    """
    face = _wall_face(wall)
    undersides = [z for storey, deck in ceiling_decks_over(model.plan, wall.storey, face)
                  if (z := deck_structure_underside_m(storey, deck)) is not None]
    return min(undersides) if undersides else None


def roof_underside_rake(model: ResolvedModel, wall: ResolvedWall,
                        roof: ResolvedRoof) -> tuple[float, float]:
    """The raked plate elevations at ``wall``'s two axis ends.

    Subtracting one constant from the rafter soffit at each end keeps the plate parallel to
    the rafters, which is what a raked top plate is.
    """
    return (roof_underside_at(model, roof, wall.axis[0]) - DEFLECTION_GAP_M,
            roof_underside_at(model, roof, wall.axis[1]) - DEFLECTION_GAP_M)


def apply_partition_tops(model: ResolvedModel) -> None:
    """Stop every full-height interior partition's framing under the structure above it.

    Runs in the ``envelope`` stage, straight after ``apply_to_roof_wall_tops`` — which now
    hands the raked partitions over rather than raking them to the deck plane.

    ``replace`` rather than a fresh ``ResolvedWall``, for the reason
    ``apply_to_roof_wall_tops`` spells out: a constructor silently reverts every field it
    does not list, and ``plate_base_z_m`` is written before this by
    ``extend_walls_to_foundation``.
    """
    bearing_refs = bearing_ref_tags(model.plan)
    roofs = {roof.tag: roof for roof in model.roofs}
    grade_m = site_grade_elevation_m_from_plan(model.plan)
    lines = lines_by_wall(model.layout_lines)
    for index, wall in enumerate(model.walls):
        if not takes_a_deflection_gap(model, wall, bearing_refs):
            continue
        top = getattr(model.plan.by_tag(wall.tag), "top", None)
        if isinstance(top, ToRoof) and top.roof_ref in roofs:
            start_z, end_z = roof_underside_rake(model, wall, roofs[top.roof_ref])
            z1 = max(start_z, end_z)
            model.walls[index] = replace(
                wall, z1_m=z1, top_z0_m=start_z, top_z1_m=end_z, plate_top_z_m=None,
                # The body moved with the framing here — the two coincide under a rafter —
                # so every band resolved against the old top is stale (→ ``reband``).
                layers=reband(wall, wall.z0_m, z1, grade_m, lines.get(wall.tag)),
            )
            continue
        underside = deck_underside_over(model, wall)
        if underside is None:
            continue
        plate_top = underside - DEFLECTION_GAP_M
        # ``max``, and the asymmetry is the whole of the two-tops rule. The body NEVER
        # falls below the framing — drywall runs to the top plate — so where the plate
        # drops (a main-storey partition, 108" to 107 3/8") the body follows it down
        # through ``clamp_to_plates``, and where the plate RISES (a basement partition
        # authored at 8'-0" in a 8'-0 1/16" storey, up 13/16" to meet the joist soffit)
        # the body grows with it. What it may never do is move a storey line's body DOWN:
        # that is the shape that opens a 12-5/8" slot in ``ST-S2A``'s stair enclosure and
        # leaves three basement risers outside their own wet wall.
        z1 = max(wall.z1_m, plate_top)
        model.walls[index] = replace(
            wall, z1_m=z1, plate_top_z_m=plate_top,
            layers=reband_for_platform(wall, wall.z0_m, z1, grade_m, lines.get(wall.tag),
                                       plate_top=plate_top,
                                       plate_base=wall.plate_base_z_m),
        )
