"""What a joint's marker looks like, per role — including whether it is drawn at all.

A ``ResolvedSolid`` is a plan polygon extruded vertically. Any shape is available *in plan*
and nothing but a prism in elevation, so an L-shaped tie is not drawable and should not be.
**These are markers, not models of the parts**: "a tie of this family is at this joint",
legible among five hundred siblings. What makes them read is not silhouette but
orientation, and orientation is derivable at every joint — the support line for a tie, the
run for a mudsill anchor, the carrier for a hanger, the ridge for a strap — so it is never
guessed.

``draw`` starts narrow on purpose. Every role below is located and billed whether or not it
is drawn; widening is a ``False`` becoming a ``True`` here, not a new derivation.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.hardware.catalog import (
    ROLE_BEAM_HOLD_DOWN,
    ROLE_EMBEDDED_STRAP_HOLDOWN,
    ROLE_FACE_MOUNT_JOIST_HANGER,
    ROLE_FLOOR_TRUSS_HANGER,
    ROLE_GABLE_END_TIE,
    ROLE_GABLE_TRUSS_ANCHOR,
    ROLE_HURRICANE_TIE,
    ROLE_IJOIST_FACE_MOUNT_HANGER,
    ROLE_LATERAL_TIE_PLATE,
    ROLE_MUDSILL_ANCHOR,
    ROLE_POST_BASE,
    ROLE_POST_BASE_ANCHOR,
    ROLE_RIDGE_TIE_STRAP,
    ROLE_SLOPED_JOIST_HANGER,
)

#: The solid category a non-embedded, non-hanger connector marker is filed under. Matches
#: the authored connector family in ``resolve/accessories.py``, so a derived marker and an
#: authored one read the same in the viewer and under one visibility toggle.
CATEGORY_CONNECTOR = "connector"
#: Cast into or anchored into a pour — the concrete sub's scope, not the framer's.
CATEGORY_CONNECTOR_EMBEDDED = "connector_embedded"
#: A saddle a member sits in, which reads differently from a strap or a tie.
CATEGORY_CONNECTOR_HANGER = "connector_hanger"


@dataclass(frozen=True)
class MarkerRule:
    """One role's marker: drawn or not, and how big in each of its own axes.

    Half-extents are in inches, in the joint's own frame: ``along`` runs with
    ``Joint.axis``, ``across`` crosses it. ``half_h`` is half the prism's height where it is
    a number; ``None`` means the height comes from the joint (a hanger is as deep as the
    member it carries) and :mod:`typehaus.resolve.connector_markers` supplies it.
    """

    draw: bool
    along_in: float = 1.0
    across_in: float = 0.25
    half_h_in: float | None = 2.25
    category: str = CATEGORY_CONNECTOR


#: Start narrow: the roof ties, the mudsill anchors, the ridge straps, the sloped hangers
#: and the embedded holdowns — the families a person asked to be able to see. The rest are
#: located and billed exactly as before and simply not drawn yet.
MARKER_RULES: dict[str, MarkerRule] = {
    # Straddling the plate top. Long in the support's direction, thin across it.
    ROLE_HURRICANE_TIE: MarkerRule(draw=True, along_in=1.00, across_in=0.25, half_h_in=2.25),
    # Across the sill, coming up out of the pour.
    ROLE_MUDSILL_ANCHOR: MarkerRule(draw=True, along_in=0.75, across_in=0.25, half_h_in=3.00,
                                    category=CATEGORY_CONNECTOR_EMBEDDED),
    # A saddle: as deep as the member it carries, so ``half_h_in`` is deferred.
    ROLE_SLOPED_JOIST_HANGER: MarkerRule(draw=True, along_in=1.50, across_in=0.75,
                                         half_h_in=None,
                                         category=CATEGORY_CONNECTOR_HANGER),
    # An LSTA24 is two feet of strap over the peak: long, and almost nothing thick.
    ROLE_RIDGE_TIE_STRAP: MarkerRule(draw=True, along_in=12.00, across_in=0.63,
                                     half_h_in=0.25),
    # Deep, because most of an STHD is inside the pour and that is the point of seeing it.
    ROLE_EMBEDDED_STRAP_HOLDOWN: MarkerRule(draw=True, along_in=0.75, across_in=0.25,
                                            half_h_in=10.00,
                                            category=CATEGORY_CONNECTOR_EMBEDDED),
    # Drawn: it is roof-level, visible, and the whole point of adding the leg was that
    # nobody could see it was missing. An LS30: 3-3/8" across the wall, 2-1/4" legs.
    ROLE_GABLE_END_TIE: MarkerRule(draw=True, along_in=1.13, across_in=1.69, half_h_in=1.13),
    # An HGA10 on the plate beside the gable truss's chord.
    ROLE_GABLE_TRUSS_ANCHOR: MarkerRule(draw=True, along_in=1.75, across_in=1.25,
                                        half_h_in=1.25),
    ROLE_FACE_MOUNT_JOIST_HANGER: MarkerRule(draw=False, along_in=1.50, across_in=0.75,
                                             half_h_in=None,
                                             category=CATEGORY_CONNECTOR_HANGER),
    ROLE_IJOIST_FACE_MOUNT_HANGER: MarkerRule(draw=False, along_in=1.50, across_in=0.75,
                                              half_h_in=None,
                                              category=CATEGORY_CONNECTOR_HANGER),
    ROLE_FLOOR_TRUSS_HANGER: MarkerRule(draw=False, along_in=1.50, across_in=0.75,
                                        half_h_in=None,
                                        category=CATEGORY_CONNECTOR_HANGER),
    ROLE_LATERAL_TIE_PLATE: MarkerRule(draw=False, along_in=1.50, across_in=0.25,
                                       half_h_in=1.50),
    ROLE_POST_BASE: MarkerRule(draw=False, along_in=2.75, across_in=2.75, half_h_in=1.50),
    # Drawn: a cast-in bolt is set wet, so the concrete sub has to see it before the pour.
    ROLE_POST_BASE_ANCHOR: MarkerRule(draw=True, along_in=0.31, across_in=0.31,
                                      half_h_in=4.00,
                                      category=CATEGORY_CONNECTOR_EMBEDDED),
    ROLE_BEAM_HOLD_DOWN: MarkerRule(draw=False, along_in=0.63, across_in=0.25, half_h_in=6.00),
}
