"""``PublishedHole`` — one row of a header/beam maker's ALLOWABLE HOLES chart.

A sibling of ``PublishedSpan`` / ``PublishedCapacity`` (``model/refs.py``) and
``PublishedCladdingLoad`` (``model/published_cladding.py``), kept in its own module only
because ``refs.py`` is at the file-size limit. Re-exported from ``refs.py``.
"""

from __future__ import annotations

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.quantities import Length


class PublishedHole(HausModel):
    """What a maker publishes about drilling the member it sizes, quoted onto the opening.

    **A published chart is a prescriptive read, not engineering** — the ``PublishedSpan``
    argument, one product family along. No IRC section publishes a bore limit for a header
    (``resolve/mep_bores.header_bore`` says so at length), so a header crossing is UNKNOWN
    until somebody quotes the chart the member is actually cut to. Weyerhaeuser's TJ-9000
    ALLOWABLE HOLES page is that chart for a Trus Joist header; the row is authored on
    ``Door.published_hole`` / ``DoorType.published_hole`` / ``RoughOpening.published_hole``
    and ``mep.run_through_header`` grades every hole in that opening's header against it.

    **A chart is a shape as much as a number.** A maximum diameter alone passes a legal-size
    hole drilled three inches off a bearing, which is the one place no chart allows one. So
    the zone is transcribed too: how far off each bearing, what fraction of the span, what
    band of the DEPTH, and how far apart two holes must be.

    **Most fields are drift guards and they are the point.** ``member`` is the retype guard
    — a row read for a 1.55E TimberStrand LSL says nothing about the sawn 2-2x8 somebody
    left in the model — and ``span``/``plies``/``load_basis`` are the conditions the row was
    read at. A drifted row is UNKNOWN naming the mismatch, never a PASS.
    """

    #: The document, edition and page — enough for a reviewer to open it.
    source: str
    #: The row and column actually read, in the chart's own words.
    table: str
    #: The member the row is for, spelled as the model spells the resolved profile
    #: (e.g. ``"2-1.75x11.875 LVL"``). Normalised-compared: the retype guard.
    member: str
    #: The largest round hole the row publishes for this member's depth.
    max_diameter: Length

    # --- the zone: where along the span, and where in the depth -------------------------
    #: Minimum distance from each BEARING to the hole. TJ-9000's 1.55E LSL page draws 8".
    zone_from_bearing: Length | None = None
    #: The centred fraction of the clear SPAN a hole must lie inside — 1/3 is TJ-9000's
    #: "middle 1/3 span" for Microllam LVL and Parallam PSL. ``None`` = no span fraction
    #: stated (the 1.55E LSL page states the 8" offset instead).
    zone_fraction: float | None = None
    #: The centred fraction of the member's DEPTH a hole must lie inside. TJ-9000 draws
    #: "1/3 depth" on both pages, which is why its maximum diameters are each a shade under
    #: a third of their depth.
    depth_fraction: float | None = None
    #: Absolute clear wood required above and below the hole, where the chart states one
    #: rather than a fraction.
    min_edge_clear: Length | None = None
    #: Minimum clear distance between two holes in the one member.
    min_spacing: Length | None = None
    #: Minimum centre-to-centre spacing expressed as a multiple of the LARGEST hole's
    #: diameter — TJ-9000's "2 x diameter of the largest hole (minimum)".
    min_spacing_diameters: float | None = None
    #: The chart permits ROUND HOLES ONLY where this is set, which is TJ-9000's first
    #: general note. A run that only clips the member takes a NOTCH, and a notch is not a
    #: round hole: it is refused rather than graded against ``max_diameter``.
    round_holes_only: bool = True

    # --- what the row assumes ------------------------------------------------------------
    #: The conditions the chart states and this engine does not check — load pattern,
    #: cantilevers, orientation. Printed on every finding, compared against nothing.
    condition: str = ""
    #: The span the row was read at, where the chart is indexed by one.
    span: Length | None = None
    #: The load basis the row assumes ("uniform loads only", "uniform and/or concentrated").
    load_basis: str | None = None
    #: The ply count the row is for. A retype guard the profile string may not carry.
    plies: int | None = None

    @model_validator(mode="after")
    def _row_is_readable(self) -> PublishedHole:
        for name in ("source", "table", "member"):
            if not str(getattr(self, name)).strip():
                raise ValueError(f"PublishedHole.{name} must name what was read")
        if self.max_diameter.meters <= 0.0:
            raise ValueError("PublishedHole.max_diameter must be positive")
        for name in ("zone_fraction", "depth_fraction"):
            value = getattr(self, name)
            if value is not None and not (0.0 < value <= 1.0):
                raise ValueError(f"PublishedHole.{name} is a fraction in (0, 1]")
        if self.min_spacing_diameters is not None and self.min_spacing_diameters <= 0.0:
            raise ValueError("PublishedHole.min_spacing_diameters must be positive")
        if self.plies is not None and self.plies < 1:
            raise ValueError("PublishedHole.plies must be at least 1")
        return self
