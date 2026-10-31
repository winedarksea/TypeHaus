"""Generic drywall beads and the LED shadow-gap bead (→ ``DrywallStandard``, #103).

Placeholders a house replaces with its own products: no product, no price, the
``drywall-corner-bead`` idiom. Billed by the LF in ``takeoff/drywall_trims.py``.
"""

from __future__ import annotations

from typehaus.model import Material

MATERIALS: tuple[Material, ...] = (
    Material(tag="drywall-corner-bead", name="Drywall outside corner bead",
             source="Generic outside-corner accessory; product selection pending."),
    Material(tag="drywall-frame-termination-bead", name="Drywall window-frame termination bead",
             source="Generic window-return frame accessory; product selection pending."),
    Material(tag="drywall-j-bead", name="Drywall J-bead",
             source="Generic termination at a bare edge; product selection pending."),
    Material(tag="drywall-l-bead-tearaway", name="Drywall tear-away L-bead",
             source="Generic frame termination for a trimless door; product selection pending."),
    Material(tag="drywall-reveal-bead", name="Drywall reveal bead (tile stop)",
             source="Generic shadow reveal where tile ends on gypsum; product selection "
             "pending."),
    Material(tag="drywall-shadow-gap-bead", name="Drywall LED shadow-gap bead",
             source="Generic Z shadow bead at the wall-ceiling edge; product selection "
             "pending."),
)
