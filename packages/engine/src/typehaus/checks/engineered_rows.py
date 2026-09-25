"""The engineered-item table: one row per kind, its check and its permit line.

A leaf (jurisdiction + engineering only) so ``mn_residential/profile.py`` can read it
without importing ``checks.structural``, which imports back into ``checks.code``.
A line blocks iff its kind has a registered, non-deferred calculation.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks.jurisdiction import PermitItemSpec
from typehaus.engineering import DEFERRALS
from typehaus.engineering.registry import has_calc


@dataclass(frozen=True)
class ItemRow:
    """One engineering kind's check and its permit line."""

    name: str  # the check id is ``structural.<name>``
    kind: str
    doc: str
    subject: str
    code: str  # the finding's citation
    absent: str  # the earned N/A
    label: str  # the permit line
    code_refs: tuple[str, ...]  # the permit line's citations

    @property
    def check_id(self) -> str:
        return f"structural.{self.name}"


ROWS: tuple[ItemRow, ...] = (
    ItemRow("base_rotation", "base_rotation",
            "Base STIFFNESS of a fixed cast column — the sway its rotating footing adds.",
            "the fixed column base's rotational stiffness and the sway it adds",
            "ACI 318-19 §6.6.4; IBC 2018 §1806.3.4",
            "no cast column in this plan is fixed at its base",
            "Fixed column base rotation (stiffness and sway)",
            ("ACI 318-19 §6.6.4", "ACI 318-19 §6.2.5.3", "IBC 2018 §1806.3.4")),
    ItemRow("deck_tie", "deck_tie",
            "A deck braced by a tie to a concrete wall, and whether the tie carries it.",
            "the tie bracing this deck to a concrete wall — every load on the deck, "
            "torsion included, against the tie part's published allowables",
            "the tie part's evaluation report; ASCE 7-16 §29.3; IRC R301.5",
            "no deck in this plan is tied to a concrete wall",
            "Deck lateral tie to a concrete wall",
            ("IRC R301.5", "ASCE 7-16 §29.3", "the tie part's evaluation report")),
    ItemRow("column_head_joint", "column_head_joint",
            "The joint at a lateral-system column's head: connector, shear, torsion, seat.",
            "the column head joint — connector capacity, column shear and torsion, "
            "and bearing at the beam seat",
            "ACI 318-19 §22.5, §22.7, §22.8",
            "no cast column in this plan is a lateral system",
            "Cast column head joint (connector, shear, torsion)",
            ("ACI 318-19 §22.5", "ACI 318-19 §22.7", "ACI 318-19 §22.8")),
    ItemRow("veneer_beam", "veneer_beam",
            "A cast beam carrying a masonry wythe between two walls.",
            "a cast beam carrying a masonry wythe — flexure, shear, torsion, "
            "deflection and end anchorage",
            "ACI 318-19 §9, §22.7, §24.2, §25.4.3",
            "no footingless wall in this plan carries another wall on its top",
            "Cast beam carrying a masonry veneer",
            ("ACI 318-19 §9.5", "ACI 318-19 §22.7", "ACI 318-19 §24.2.2",
             "ACI 318-19 §25.4.3", "TMS 402-22 §13.1.2.3")),
    ItemRow("veneer_anchor", "veneer_anchor",
            "The anchors tying a beam-borne masonry wythe back across its insulated standoff.",
            "masonry veneer anchors across the insulated standoff — anchor capacity, "
            "buckling and the wythe's bending between rows",
            "TMS 402-16 §12.2; IRC R703.8.4",
            "no masonry wythe in this plan stands on a veneer beam",
            "Masonry veneer anchorage over an insulated standoff",
            ("TMS 402-16 §12.2", "IRC R703.8.4")),
    ItemRow("thermal_break", "thermal_break_transfer",
            "An isolation joint between two separately founded pours — the board and its thrust.",
            "an isolation board between separately founded pours — the board's "
            "strain and the thrust it passes along the house's lateral path",
            "ACI 347R-14; ACI 318-19 §22.3; ASTM C578",
            "no isolation board in this plan separates two pours",
            "Isolation joint between separately founded pours",
            ("ACI 347R-14", "ACI 318-19 §22.3", "ASTM C578")),
    ItemRow("tiered_retaining", "tiered_retaining",
            "A footingless gravity wall retaining fill above a taller cut.",
            "a segmental gravity wall retaining fill — sliding, overturning, "
            "bearing, and its interaction with the wall below",
            "IRC R404.4; IBC 2018 §1807.2",
            "no footingless wall in this plan retains fill",
            "Segmental gravity retaining walls (tiered)",
            ("IRC R404.4", "IBC 2018 §1807.2")),
)


def is_blocking(kind: str) -> bool:
    """A registered calculation gates; a deferred or uncomputed kind is UNKNOWN and cannot."""
    return has_calc(kind) and kind not in DEFERRALS


def permit_items() -> tuple[PermitItemSpec, ...]:
    return tuple(PermitItemSpec(r.label, (r.check_id,), r.code_refs,
                                blocking=is_blocking(r.kind)) for r in ROWS)
