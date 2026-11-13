"""EQ-B-ERV's strut trapeze: rod, strut and the lag under each bridge seat (→ model/product.py).

``rated_load_lb`` is a published allowable per piece, graded by
``structural.equipment_hangers`` against the case weight over the rod count.
"""

from typehaus.model import Product
from typehaus.quantities import ft

ATR_ROD_3_8 = Product(
    tag="PROD-BLINE-ATR-3-8", brand="B-Line (Eaton)", model="ATR 3/8\" x 120\" ZN",
    name="3/8\"-16 all-threaded rod, zinc, 10 ft",
    stock_length=ft(10), rated_load_lb=730,
    source="Eaton B-Line Pipe Hangers & Supports catalog p.236 (rev. 4/28/2014), "
           "\"ATR - All Threaded Rod\" table, row ATR 3/8\" x 120: 16 threads per inch, "
           "Recommended Load 730 lbs (3.24 kN), approx. 29 lbs/100 ft; max temperature 750 F.",
)

P1000_STRUT = Product(
    tag="PROD-UNISTRUT-P1000-PG", brand="Unistrut", model="P1000 10PG",
    name="1-5/8\" x 1-5/8\" 12 ga solid strut channel, pre-galvanized, 10 ft",
    stock_length=ft(10),
    source="Unistrut P1000 submittal sheet: Pregalvanized (PG) ASTM A653 GR 33 G90, "
           "1.89 lbs/ft; beam loading at 24\" span, max allowable uniform load 1,690 lbs "
           "(deflection 0.06\"). Not graded: the trapeze spans 25\" and 47 lb.",
)

LAG_1_4_X_1_1_2 = Product(
    tag="PROD-LAG-1-4X1-1-2-ZN", brand="Generic", model="1/4\" x 1-1/2\" hex lag screw, zinc",
    name="1/4\" x 1-1/2\" hex lag screw with washer, through the bridge strut into a TJI "
         "230 bottom flange (1/8\" lead hole)",
    rated_load_lb=245,
    source="Weyerhaeuser TB-808, Bottom Flange TJI Joist Attachment Connections (July 2025, "
           "expires 7/2027), Design Example: TJI 230, 1/4\" x 1-1/2\" lag through a 1/4\" metal "
           "plate, withdrawal = (T - E) x W = 225 lb/in x 1 3/32\" = 245 lb (Table 2, G = 0.50). "
           "The 12 ga strut is thinner than the example's plate; the thread engaged in the "
           "1.25\" flange is the same T - E.",
)

EQUIPMENT_HANGER_PRODUCTS = (ATR_ROD_3_8, P1000_STRUT, LAG_1_4_X_1_1_2)
