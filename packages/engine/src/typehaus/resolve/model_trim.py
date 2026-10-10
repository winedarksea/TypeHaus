"""Resolved interior trim records: base runs and door casings (→ resolve/interior_trim.py).

Records, not ``ResolvedSolid``s: each carries its own plan rings and absolute elevations,
and ``geometry_millwork`` turns those into prisms for every emitter, the stool precedent.
Kept out of ``resolve/model.py`` only for its length; ``ResolvedModel`` holds the lists.
"""

from __future__ import annotations

from dataclasses import dataclass

Ring = tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class TrimPiece:
    """One board: plan ring, absolute z, and the finished size a cut list reads.

    ``name`` is ``base`` for a base run, else ``leg_left`` / ``leg_right`` / ``head`` /
    ``sill`` for a casing. ``length_m`` runs along the grain; ``width_m`` is the face.
    """

    name: str
    outline: Ring
    z0_m: float
    z1_m: float
    length_m: float
    width_m: float


@dataclass(frozen=True)
class ResolvedBaseRun:
    """One straight piece of base along one wall of one room.

    ``kind`` is the floor's ``Material.base_detail``: only ``trim`` is a board (drawn, cut,
    priced as wood); ``tile`` and ``integral_cove`` are LF billed with their own trade and
    carry their floor material as ``material_ref``. ``length_m`` is the cut length, corner
    allowances included. ``start_corner`` / ``end_corner`` are ``inside`` / ``outside`` where
    the run meets its neighbour in a corner and ``None`` where it dies into a break, named
    in ``breaks``. ``offset_m`` is how far it stands off the wall's finish face (a wood
    band it is nailed over).
    """

    uid: str
    tag: str
    storey: str
    room: str
    wall_tag: str
    kind: str
    material_ref: str
    thickness_m: float
    height_m: float
    piece: TrimPiece
    start_corner: str | None
    end_corner: str | None
    breaks: tuple[str, ...] = ()
    offset_m: float = 0.0
    profile: str = "S4S"

    @property
    def length_m(self) -> float:
        return self.piece.length_m


@dataclass(frozen=True)
class CasingClip:
    """One leg the resolver scribed short (``dropped`` False) or left off (True)."""

    piece: str
    obstruction: str
    remaining_m: float
    dropped: bool


@dataclass(frozen=True)
class ResolvedDoorCasing:
    """The picture-frame casing on one face of one door.

    ``side`` is +1 / -1 along the host wall's left normal. ``pieces`` are the legs and head
    actually installed; a dropped leg is absent there and present in ``clips``.
    """

    uid: str
    tag: str
    storey: str
    opening_ref: str
    opening_uid: str
    wall_tag: str
    room: str
    side: int
    material_ref: str
    thickness_m: float
    casing_width_m: float
    pieces: tuple[TrimPiece, ...]
    clips: tuple[CasingClip, ...] = ()
    profile: str = "S4S"
