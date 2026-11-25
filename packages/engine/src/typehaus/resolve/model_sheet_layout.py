"""Records of the sheathing and panel-cladding sheet layout (``resolve/sheet_layout.py``).

Stations ``s`` are metres along the wall from its axis start; ``z`` is absolute.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SheetPiece:
    """One piece of sheathing as hung: ``kind`` is ``full`` (a whole sheet), ``rip`` (full
    length, narrower), ``short`` (a course remainder) or ``cut`` (an opening or a rake
    trims it). ``z1_far`` is the top at ``s1`` where a rake slopes it; ``apex_z`` the top of a
    gable peak falling inside the piece (None where its top is the straight ``z1``-``z1_far``)."""

    s0: float
    s1: float
    z0: float
    z1: float
    z1_far: float
    kind: str
    opening_cuts: tuple[str, ...] = ()
    apex_z: float | None = None

    @property
    def width_m(self) -> float:
        return self.s1 - self.s0

    @property
    def height_m(self) -> float:
        return max(self.z1, self.z1_far, self.apex_z or self.z0) - self.z0

    @property
    def area_m2(self) -> float:
        if self.apex_z is None:
            return self.width_m * ((self.z1 + self.z1_far) / 2.0 - self.z0)
        # Two trapezoids meeting at the apex; its station is read off the rake's symmetry.
        rise = (self.apex_z - self.z1) + (self.apex_z - self.z1_far)
        s_apex = self.width_m * (self.apex_z - self.z1) / rise if rise > 0 else 0.0
        return (s_apex * ((self.z1 + self.apex_z) / 2.0 - self.z0)
                + (self.width_m - s_apex) * ((self.apex_z + self.z1_far) / 2.0 - self.z0))


@dataclass(frozen=True)
class SheetBreak:
    """A joint between two pieces. ``orient`` ``vertical``: at station ``at`` from ``lo`` to
    ``hi`` in z; ``horizontal``: at elevation ``at`` from ``lo`` to ``hi`` in s.

    ``backed`` holds where framing lies under both edges along the whole joint (less the
    openings it crosses); ``backing`` names the member nearest the joint (``child_key``, or
    ``<floor>:<child_key>``) and ``offset_m`` the joint's distance from its centre line.
    ``unbacked_m`` is the joint length with no framing under it. ``opening_corner_m`` is the
    distance to the nearest opening edge, recorded and not graded."""

    at: float
    lo: float
    hi: float
    orient: str
    backing: str | None
    offset_m: float | None
    backed: bool
    unbacked_m: float = 0.0
    opening_corner_m: float | None = None
    unbacked_spans: tuple[tuple[float, float], ...] = ()  # along the joint, where bare


@dataclass(frozen=True)
class ResolvedSheetLayout:
    """One run of sheathing laid sheet by sheet: a wall's layer (or ``-tee-i`` piece) and
    any collinear faces it joins across a tee (``resolve/sheet_layout_runs.py``). Stations
    run from ``wall_tag``'s axis start along it.

    ``framed`` is False where no framing stands behind the layer (masonry, a hung board):
    pieces are laid on the bare module and no break is graded. ``start_end`` is the end the
    walk began at (``start`` | ``end``); ``shortfall_m`` the band height left to the layer
    above (``SheetLayoutStandard.max_course_shortfall``)."""

    wall_tag: str
    layer_name: str
    material_ref: str
    thickness_m: float
    lo: float
    hi: float
    z0: float
    z1: float
    sheet_w_m: float
    sheet_l_m: float
    start_end: str
    pieces: tuple[SheetPiece, ...]
    vertical_breaks: tuple[SheetBreak, ...]
    horizontal_breaks: tuple[SheetBreak, ...]
    framed: bool
    shortfall_m: float = 0.0
    vertical: bool = True  # sheets stand with their length up (the standard's orientation)
    # Every wall face the run crosses: ``(wall tag, layer name, lo, hi)`` in run stations.
    faces: tuple[tuple[str, str, float, float], ...] = ()
    function: str = "sheathing"  # or "cladding": a panel siding laid on its furring
    # The joint nailers derived behind a cladding run's vertical joints (also on the walls).
    nailers: tuple = ()

    @property
    def wall_tags(self) -> tuple[str, ...]:
        return tuple(dict.fromkeys(tag for tag, _n, _a, _b in self.faces)) or (self.wall_tag,)

    def wall_at(self, s: float) -> str:
        """The wall whose face holds run station ``s`` (the nearest, past either end)."""
        if not self.faces:
            return self.wall_tag
        return min(self.faces, key=lambda f: 0.0 if f[2] <= s <= f[3]
                   else min(abs(s - f[2]), abs(s - f[3])))[0]

    @property
    def breaks(self) -> tuple[SheetBreak, ...]:
        return self.vertical_breaks + self.horizontal_breaks
