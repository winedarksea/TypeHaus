"""TJ-8000 (March 2025) p.4: the clear distance between adjacent rim holes.

Quoted: "The horizontal distance between the edges of adjacent round holes must be at least
twice the diameter of the largest adjacent round hole, and three times the length of the
largest adjacent rectangular hole." Closely grouped round holes are permitted if the group's
perimeter meets the single-hole requirements. The guide measures along the rim, so a vertical
offset buys nothing. A round/rectangular pair is not addressed: the larger requirement governs.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.checks._authoring import failed as _fail
from typehaus.checks.mep._format import feet_inches
from typehaus.findings import Finding
from typehaus.quantities import M_PER_IN


@dataclass(frozen=True)
class RimHole:
    """One run's hole through a rim: ``length_m`` is its extent ALONG the rim."""

    kind: str
    tag: str
    station_m: float
    length_m: float
    round_: bool
    z0_m: float
    z1_m: float

    @property
    def required_m(self) -> float:
        return (2.0 if self.round_ else 3.0) * self.length_m


def rim_spacing_findings(cid: str, floor, rim_key: str, holes: list[RimHole],
                         window, done: set, ends: tuple[float, float]) -> list[Finding]:
    """A FAIL per neighbouring pair (once, whichever run is asked first) too close.

    A short pair is a "closely grouped" set, and allowed, when the group's envelope is itself
    a legal hole: no longer than the rim window (2/3 the depth), inside it vertically, and
    2x (round) / 3x (rectangular) its length from both rim ends (``ends``, along-rim m).
    """
    ordered = sorted(holes, key=lambda h: h.station_m)
    out: list[Finding] = []
    for a, b in zip(ordered, ordered[1:], strict=False):
        key = (rim_key, a.tag, b.tag, round(a.station_m, 6), round(b.station_m, 6))
        if key in done:
            continue
        done.add(key)
        clear = (b.station_m - b.length_m / 2.0) - (a.station_m + a.length_m / 2.0)
        need = max(a.required_m, b.required_m)
        if clear >= need - 1e-9:
            continue
        span = (b.station_m + b.length_m / 2.0) - (a.station_m - a.length_m / 2.0)
        lo, hi = a.station_m - a.length_m / 2.0, b.station_m + b.length_m / 2.0
        end_need = (2.0 if a.round_ and b.round_ else 3.0) * span
        if (span <= window.height_m + 1e-9 and min(a.z0_m, b.z0_m) >= window.z0_m - 1e-9
                and max(a.z1_m, b.z1_m) <= window.z1_m + 1e-9
                and lo - ends[0] >= end_need - 1e-9 and ends[1] - hi >= end_need - 1e-9):
            continue
        rule = ("2x the diameter" if a.round_ and b.round_ else
                "3x the length" if not (a.round_ or b.round_) else "2x D / 3x L, the larger")
        out.append(_fail(
            cid,
            f"{a.kind} {a.tag} and {b.kind} {b.tag} bore {floor.tag}'s edge rim {rim_key} "
            f"{feet_inches(a.station_m)} and {feet_inches(b.station_m)} along it, their "
            f"holes' edges {clear / M_PER_IN:.2f}\" apart against {need / M_PER_IN:.2f}\" "
            f"(TJ-8000 p.4: {rule} of the larger adjacent hole)",
            (a.tag, b.tag, floor.tag),
            fix="move one crossing along the rim, or take both through one hole whose "
                "outline is within 2/3 the rim's depth"))
    return out
