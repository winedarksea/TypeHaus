"""The graded result of one cut in a framing member (``mep_bores``)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BoreVerdict:
    """One cut, graded. ``ok is None`` means **no published rule reaches this member**.

    ``limit_in`` is the number the rule allows and ``actual_in`` what was asked for, so a
    consumer can print the margin rather than the verdict alone — "0.44" over" is actionable
    and "FAIL" is not.
    """

    ok: bool | None
    kind: str  # "bore" | "notch" | "plate_cut"
    actual_in: float
    limit_in: float | None
    basis: str
    #: What a person has to do for an otherwise-illegal cut to become legal. Stated, never
    #: applied: introducing a strap to make a route legal is a structural redesign.
    remedy: str | None = None

    @property
    def unknown(self) -> bool:
        return self.ok is None
