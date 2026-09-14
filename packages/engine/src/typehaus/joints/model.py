"""The :class:`Joint` record — one derived structural connection, located.

A joint is deliberately *not* a BOM row and *not* a ``Finding``. A row says how many to
buy and a finding says whether the path is covered; both are opinions about the same
underlying fact, which is that a connection of some role belongs at some point. Keeping
the fact in its own shape is what lets the order, the report and the drawing be checked
against each other instead of against three independent derivations.
"""

from __future__ import annotations

from dataclasses import dataclass
from hashlib import blake2s


@dataclass(frozen=True)
class Joint:
    """One derived structural connection, with enough geometry to draw a marker."""

    #: The ``hardware/catalog.py`` ``ROLE_*`` constant this joint calls for.
    role: str
    #: The resolved designation — "H2.5A", "MASA", "LSSR". What a click should name.
    part: str
    storey: str
    #: Plan location in project-frame metres.
    point: tuple[float, float]
    #: Plate top / carrier soffit / pour top — whichever face this part lands on.
    z_m: float
    #: ``"x"`` or ``"y"``: the support or carrier line, snapped to the dominant component.
    #: Orientation is what makes five hundred identical little boxes legible, and it is
    #: derivable at every joint, so it is never guessed.
    axis: str
    #: Is this part cast into, or anchored into, a pour? Decides the solid category, and
    #: through it who is quoted the part — the concrete sub, not the framer. Answered from
    #: what is actually under the joint, so a post base that moves from a pier to a deck
    #: re-files itself honestly.
    embedded: bool
    #: The element tags this joint connects, for the inspector and the row basis.
    members: tuple[str, ...]
    #: Stable identity. Two resolves of an unedited model must produce the same string, and
    #: an edit elsewhere in the house must not renumber this one — which is why it is a
    #: hash of *where and what* rather than an ordinal.
    key: str


def joint_key(role: str, anchor_tag: str, point: tuple[float, float], z_m: float,
              grid_m: float) -> str:
    """The stable identity of a joint: its role, its anchor, and its snapped location.

    Snapped to ``grid_m`` — the same ``coincident_bearing_tolerance_in`` that decides two
    member ends over one bearing wall are one joint — so a coordinate that moves by a float
    hair does not mint a new part. **Never an ordinal:** ``shell_json`` sorts solids by uid,
    so an enumerated scheme would renumber every marker downstream of an unrelated edit and
    turn a one-line change into a whole-file diff.
    """
    grid = max(grid_m, 1e-9)
    return (f"{role}|{anchor_tag}|{point[0] / grid:.0f}|{point[1] / grid:.0f}"
            f"|{z_m / grid:.0f}")


def marker_uid(key: str) -> str:
    """The ``ResolvedSolid`` uid for a joint's marker: ``CM-`` plus a digest of its key."""
    return "CM-" + blake2s(key.encode("utf-8"), digest_size=6).hexdigest()


def axis_of(p0: tuple[float, float], p1: tuple[float, float]) -> str:
    """``"x"`` or ``"y"`` for a line, by dominant component.

    The same snap ``resolve/accessories._resolve_connector`` applies to an authored
    ``Connector.axis``, so a derived marker and an authored one beside it read the same way.
    """
    return "x" if abs(p1[0] - p0[0]) >= abs(p1[1] - p0[1]) else "y"
