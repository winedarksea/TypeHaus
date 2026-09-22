"""``PublishedCladdingLoad`` — one row of a cladding panel's published allowable-load table.

A sibling of ``PublishedSpan`` / ``PublishedCapacity`` (``model/refs.py``), kept in its own
module only because ``refs.py`` is at the file-size limit.
"""

from __future__ import annotations

from typehaus.model.base import HausModel
from typehaus.quantities import Length


class PublishedCladdingLoad(HausModel):
    """A panel maker's allowable uniform load, quoted onto the panel's ``Material``.

    **A prescriptive read, not engineering** — the ``PublishedSpan`` argument: a reviewer
    opens the install guide, finds the row, and the question is closed.
    ``structural.cladding_wind`` grades the ASCE 7 C&C demand against it in BOTH
    directions (``checks/structural/published.graded_against_published_cladding``).

    It lives on the Material, not on a wall, because the row is the product's: every wall
    that clads in it (through ``layer_materials``) reaches the same row.

    **Most fields are drift guards.** ``member`` and ``gauge`` must appear in the
    Material's own name; ``coverage`` matches ``fastener_coverage_in``; the model's girt
    spacing may not EXCEED ``fastener_spacing``; ``panel_fastener`` must lead
    ``Material.panel_fastener``; the support must be wood at least
    ``min_support_thickness``; ``demand_psf``, ``wind_speed_mph`` are increase-only and
    any ``exposure`` change drifts. A drifted row is UNKNOWN naming it, never a PASS.

    ``excludes`` is compared against nothing: it is the table's own disclaimer (what the
    row does NOT cover), printed on every finding so a PASS cannot read wider than the row.
    """

    #: The document, edition and page — enough for a reviewer to open it.
    source: str
    #: The table and column read, in its own words.
    table: str
    #: The product the row is for, as the Material's name spells it.
    member: str
    #: Allowable (ASD) outward (suction) and inward uniform loads, psf.
    allowable_outward_psf: float
    allowable_inward_psf: float
    #: The fastener spacing the row is indexed by — along the panel, i.e. the girt spacing
    #: for a vertically-run panel.
    fastener_spacing: Length
    #: What the row assumes that the engine does not check, printed on the finding.
    condition: str
    #: Sheet gauge the row is for.
    gauge: int | None = None
    #: Net panel coverage the row is for.
    coverage: Length | None = None
    #: The maker's named fastener, verbatim.
    panel_fastener: str | None = None
    #: The support the maker accepts, verbatim ("Lumber - 1x or thicker").
    support_material: str | None = None
    #: The least support thickness that wording means (0.75" for "1x").
    min_support_thickness: Length | None = None
    #: Printed conditions of the table's basis — not compared.
    deflection_limit: str | None = None
    stress_increase: bool = False
    span_condition: str | None = None
    #: The table's own exclusion, verbatim. Printed on every finding.
    excludes: str | None = None
    #: The demand the reader judged the row against, psf ASD. Increase-only guard.
    demand_psf: float | None = None
    #: The wind basis the demand was read at.
    wind_speed_mph: float | None = None
    exposure: str | None = None
