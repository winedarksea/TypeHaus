"""The court's escape ladder: one purchased fixed ladder, graded by R310.3.2.1.

NOT editable (a type is never written back by a UI drag). The instance is `court_ladder.py`.
"""
from typehaus import Product
from typehaus.model import FurnitureType, LadderSpec, Mount, MountKind, PlacementStrategy, inch

COURT_LADDER_PRODUCTS = (
    Product(tag="PROD-TRIARC-WLA6SS", brand="Tri-Arc", model="WLA6SS",
            name="Aluminum fixed ladder, 10 steps, side-step exit",
            url="https://www.partssource.com/parts/tri-arc/WLA6SS",
            source=("Read 2026-11-27 (PartsSource listing; Zoro/manufacturer pages 403): "
                    "10 ft 2 in overall, 10 steps at 12 in, 18 in step width, 3/4 in rungs, "
                    "21-1/16 in overall, top step 9 ft, 300 lb. Stand-off from the wall is "
                    "NOT published there: 7 in assumed (OSHA 1910.23 toe clearance), confirm "
                    "on the data sheet before ordering. 'Top step 9 ft' + 12 in spacing from "
                    "a 12 in first rung gives 9 rungs (12..108 in); the listing's '10 steps' "
                    "is read as counting the platform step. The 12-step WLA8SS the owner "
                    "cited has an 11 ft top step, too tall for this 9.2 ft rise.")),
)

# Overall envelope: 21-1/16" wide, 7" clear stand-off + 1 1/2" rail deep, 122" to the rail top.
COURT_LADDER_TYPE = FurnitureType(
    tag="FT-COURT-LADDER-WLA6SS", name="Court escape ladder (Tri-Arc WLA6SS)",
    footprint=(inch(21.0625), inch(8.5)), height=inch(122),
    placement=PlacementStrategy.WALL_ATTACHED, plan_symbol="fixed-ladder",
    product_ref="PROD-TRIARC-WLA6SS",
    mount=Mount(kind=MountKind.WALL, elevation=inch(0)),
    ladder=LadderSpec(rung_inside_width=inch(18), rung_projection=inch(7),
                      rung_spacing=inch(12), rung_count=9, first_rung_height=inch(12),
                      exit="side_step", rail_extension=inch(14), rated_load_lb=300),
    source="IRC 2018 R310.3.2.1 rung rules; Tri-Arc WLA6SS (PROD-TRIARC-WLA6SS)")

COURT_LADDER_TYPES = (COURT_LADDER_TYPE,)
