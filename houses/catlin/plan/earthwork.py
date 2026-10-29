# haus: editable
# The over-dig for the house and the court, dug as one hole (→ notes/foundation_aggregate_and_backfill.md).
# Native spoil in <=8" lifts beyond the drain column, light plates only within ~3' of the XPS,
# a 12" clayey cap sloped >=6" in 10' (R401.3). Backfill only once the deck braces the wall
# tops (R404.1.7). Slope, swell and shrink are PRESUMED till values until the soils report (BLD-12).
# Type A, not B: a 1:1 lip ran ~4' past both side lot lines. Every house side is <=8' deep, so it
# stands 3 1/2' plumb and lays back 3/4:1, its lip ~5" inside the lot; the court (to 11.6' deep) lays back
# 3/4:1 from its floor. A report reading B or C means shoring or an easement, not a flatter slope.
# The garage trench and the north-entry pier holes stay in the residual earthwork allowance.
from typehaus import Excavation, SideSlope, SoilFactor
from typehaus.model import ft, inch

EXCAVATION = [
    Excavation(uid="51B78YHGNF", tag="EX-HOUSE",
        hosts=("FB-B-S1", "FB-B-S2", "FB-B-S3", "FB-B-S4", "FB-B-E1", "FB-B-E2", "FB-B-N1",
               "FB-B-N2", "FB-B-N3", "FB-B-N4", "FB-B-W1", "FB-B-W2", "FB-B-CS", "FB-B-CS2",
               "FB-B-CN", "FB-B-CN2", "FB-B-STR", "FB-B-STR3", "FB-B-STR3B", "FB-SG-W1",
               "FB-SG-E1", "FB-SG-W2", "FB-SG-E2", "FB-SG-S", "FB-SG-ARCH"),
        working_space=inch(24),
        side_slope=SideSlope(h_per_v=0.75, basis="OSHA 29 CFR 1926 Subpart P App. B, Type A soil (stiff clay till, qu >= 1.5 tsf): 3/4:1, an unsupported vertical lower 3 1/2' max where the dig is 8' or less; soil presumed, confirm with soils report", vertical_toe=inch(42), vertical_toe_max_depth=ft(8)),
        swell=SoilFactor(fraction=0.30, source="Caterpillar Performance Handbook, swell factors: clay, natural bed, ~30%; presumed till"),
        shrink=SoilFactor(fraction=0.15, source="Peurifoy, Construction Planning, Equipment and Methods, bank-to-compacted shrinkage for clay 10-20%; midpoint, presumed till"),
        cap_thickness=inch(12),
        cap_material="native clay, low-permeability cap",
        lift=inch(8)),
]
