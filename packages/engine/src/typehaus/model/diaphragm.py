"""A deck acting as a diaphragm, and where it DELIVERS its shear when it does not resist it.

``DiaphragmSpec`` moved here from ``refs.py`` (2026-09-29, which was at 497 lines) together
with the type it now carries, ``DiaphragmDelivery``; ``refs.py`` re-exports both, so every
reader still imports them from the one place the sibling published-read types are.
"""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.model.diaphragm_attachment import (
    CollectorBlocking,
    JointNailing,
    PanelEdgeBlocking,
)
from typehaus.quantities import Length


class ReceivingLine(HausModel):
    """One wall of the RECEIVING structure a delivered shear is graded on.

    The wall keeps its own prescriptive grade for its own building; what is graded against
    this row is the delivered load over the wall's SURPLUS braced length (provided less
    required), which is IRC R301.1.3's "engineered element in a prescriptive building".
    """

    #: The receiving ``Wall``, by tag. Must resolve, and must lie on the delivering deck's
    #: boundary or under the receiving roof's bearing.
    wall: str
    #: The SDPWS Table 4.3A row the wall's sheathing is read at, ASD plf (nominal / 2.0).
    unit_shear_asd_plf: float
    #: ``G_a`` of the same row, kips/inch. Read where cast columns remain on the delivering
    #: deck and the wall is stationed as one of its lines (a §1604.4 rigidity split).
    apparent_stiffness_kips_per_in: float
    #: The document, edition, table and row, in its own words.
    source: str


class DiaphragmDelivery(HausModel):
    """What a deck with no lateral system of its own hands to the structure it is tied to.

    ** A CLAIM WITH PARTS IN IT, THE SAME AS THE DIAPHRAGM THAT MAKES IT. ** Declaring a
    delivery says the neighbouring roof takes this deck's shear, that its walls take it to
    the ground, and that a counted set of connectors carries it across the joint. Every one
    of those is named here by tag so each can be refused when it does not resolve: an
    unresolved reference makes the record INCOMPLETE and names it, and a delivery whose
    geometry does not agree (a wall that is neither on the boundary nor under the receiving
    roof) is refused the same way.
    """

    #: The receiving ``Roof``, by tag. It carries a ``DiaphragmSpec`` of its own.
    roof: str
    #: The receiving walls. The axis each resists is its own direction, derived.
    lines: tuple[ReceivingLine, ...] = ()
    #: Axial straps across the joint. Along-joint shear uses continuous deck boundary nailing.
    joint_refs: tuple[str, ...] = ()
    joint_nailing: JointNailing | None = None
    #: An unresolved attachment detail keeps the delivery INCOMPLETE even if nominal
    #: product capacities pass. Clear only after its nailing members and fastening exist.
    joint_attachment_missing: str | None = None
    #: The connectors taking the joint's shear from the receiving roof's frame into the wall
    #: under it (gable frame to top plate), by tag.
    plate_clip_refs: tuple[str, ...] = ()
    #: Whether the delivering deck is supported along ONE edge only — SDPWS 4.2.5.2's
    #: open-front structure, graded on ``L'`` and ``L'/W'``.
    open_front: bool = True
    #: The receiving structure's pad or footing plane and the tolerance a differential
    #: between it and the delivering deck's other bearing plane is detailed for, in words.
    differential_movement: str = ""


class DiaphragmSpec(HausModel):
    """The same read for a ROOF or FLOOR deck asked to act as a diaphragm.

    ** A DIAPHRAGM IS NOT SHEATHING; IT IS SHEATHING PLUS TWO CHORDS AND A COLLECTOR. **
    Declaring one is a design decision with parts in it, which is exactly why the north
    entry canopy's 2026-09-10 revision demoted its strap line to "a tie, not the lateral
    system": no chord and no collector had ever been drawn, so there was nothing to call a
    diaphragm. This type is what it takes to say so, and every field on it is a part
    somebody has to build.

    ** WHAT IT UNLOCKS, AND WHAT THAT COSTS. ** With a diaphragm the shear at the roof plane
    reaches every resisting line, and ``engineering/roof_moment.py`` may share it out. Two
    obligations come with that and both are graded: the diaphragm's own unit shear and
    aspect ratio (SDPWS 4.2.4 — 4:1 blocked, 3:1 unblocked, and the ratio is derived from
    the model's own footprint), and the chord force at midspan.

    ** ``delivers_to`` IS THE THIRD OBLIGATION (2026-09-29). ** A deck whose own supports are
    pinned has no lateral line of its own in some direction; naming the structure it is tied
    to hands that direction's shear across the joint, and ``engineering/diaphragm_delivery``
    grades the joint, the receiving deck and every receiving wall at 100% of it.
    """

    #: The deck layer carrying the shear, by name — the same drift guard as above.
    sheathing_layer: str
    #: Nail size, boundary/edge spacing, field spacing, and blocking.
    fastening: str
    source: str
    #: ASD unit shear, plf, from SDPWS Table 4.2A at the row named in ``fastening``.
    unit_shear_asd_plf: float
    #: ``G_a`` for the same row, kips/inch.
    apparent_stiffness_kips_per_in: float
    #: Whether the panel edges are blocked. It sets the aspect-ratio limit and it is the
    #: difference between a 4:1 deck and a 3:1 one.
    blocked: bool = True
    #: The member acting as the diaphragm CHORD, in words — what it is, where it runs, and
    #: how it is made continuous across its splices. Prose because on a trussed deck the
    #: chord is a derived member with no authored tag, and a reference that cannot resolve
    #: is worse than a sentence that can be read.
    chords: str = ""
    #: The chord's nominal section and ply count, for the bending term of SDPWS 4.2.2 and
    #: for the chord-force limit state.
    chord_member: str = "2x6"
    chord_plies: int = 1
    #: The members that drag the deck's shear into each resisting line, by TAG. These must
    #: resolve: a collector is a real member with a real connection at each end, and naming
    #: one that is not in the model is the failure this whole type exists to prevent.
    collector_refs: tuple[str, ...] = ()
    collector_blocking: tuple[CollectorBlocking, ...] = ()
    panel_edge_blocking: PanelEdgeBlocking | None = None
    #: Σ(Δ_c x) / (2W) — the chord-splice slip term of SDPWS 4.2.2, inches. Zero where the
    #: chord is continuous over the span and has no splice to slip.
    chord_splice_slip: Length | None = None
    #: The neighbouring structure this deck hands its shear to, or ``None``.
    delivers_to: DiaphragmDelivery | None = None

