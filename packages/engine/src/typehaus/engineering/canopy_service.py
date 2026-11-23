"""ONE service rule for the north-entry canopy zone's connectors (review M2, 2026-11-23).

By exposure, stated per part:

* **exposed to weather** — everything under the open-sided canopy roof or on the landing:
  the post caps, angles and bases, the band's slat connectors and plate screws, the landing
  ties. WET. Where the catalog publishes an in-service MC > 19% column it is read
  (KBS1Z, C-C-2026 p. 324); otherwise NDS 2018 Table 11.3.3's C_M 0.70 is applied to the dry
  row — which, for a part whose evaluation report is scoped to MC <= 19% (ESR-2604 ACE6Z,
  ESR-3096 A35Z, ESR-3050 CBSTQ, ESR-2330 DTT2), is a grading OUTSIDE the report, said so.
* **under roofing** — the LTP4Z eave clips and LSTA24 joint straps sit on nailers under the
  roof sheathing and roofing: DRY, stated.

Decision 17 (landing tie wet throughout) is this rule's landing half.
"""

from __future__ import annotations

#: NDS 2018 Table 11.3.3, dowel-type fasteners, in-service MC > 19%.
WET_CM = 0.70

WET_RULE = ("graded WET by the canopy's one exposure rule (exposed to weather under the "
            "open canopy): NDS 2018 Table 11.3.3 C_M 0.70 on the dry catalog row")
OUTSIDE_REPORT = ("its evaluation report covers in-service MC <= 19% only, so the wet value "
                  "is a reading outside the report")
DRY_UNDER_ROOFING = ("DRY by the canopy's exposure rule: it sits on its nailer under the "
                     "roof sheathing and roofing, not in the weather")
