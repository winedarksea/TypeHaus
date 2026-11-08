"""The MN profile's electrical coverage sentences, on the 2026 NEC (split from ``profile.py``).

Cited through ``model/nec.py``; ``mark`` carries a caveat onto a section whose 2026 number
no source confirms.
"""

from __future__ import annotations

from typehaus.model.nec import NEC, mark

ELECTRICAL_COVERAGE = (
    f"Electrical, on the {NEC.EDITION} (Minn. R. 1309.0010 subp. 3.E deletes IRC ch. "
    f"34-43): {NEC.GFCI_DWELLING} GFCI receptacle locations, {NEC.GFCI_APPLIANCES} "
    "ranges, dryers, dishwashers and sump pumps and "
    f"{NEC.GFCI_OUTDOOR_OUTLETS} outdoor outlets where the model can trace the outlet, "
    f"{mark(NEC.AFCI_DWELLING)} AFCI branch-circuit coverage by room (bathroom lighting "
    "outlets, 2026 210.12(B)(14), are not graded), "
    f"and {NEC.BATHROOM_RECEPTACLE} the receptacle required at each lavatory basin — "
    "with the basin taken as the whole vanity carcass, since no basin extent "
    "is modeled, which makes that reach test permissive rather than exact. No "
    "conductor sizing, box fill, or load calculation, none of which is claimed as a "
    "code result. "
)

SOURCE_SIDE_COVERAGE = (
    f"Source-side NEC: {NEC.INTERCONNECTION} "
    f"busbar interconnection and {NEC.RAPID_SHUTDOWN} PV rapid shutdown; and "
    f"{NEC.OCPD_HEIGHT} / {NEC.SWITCH_HEIGHT} "
    "the highest panel handle at 6'-7\" (the body top where no handle offset is "
    f"stated); {NEC.WORKING_SPACE} panel working space (36\" x 30\" x 6'-6\", door "
    f"swings not graded) and {NEC.DEDICATED_SPACE} dedicated space (no pipe or duct "
    "over a panel); no other article of the NEC is claimed. "
)
