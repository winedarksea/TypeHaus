# haus: editable
# Catlin materials — the owner-furnished titanium (Waltly Titanium, bought 2026-10) and the
# stainless fittings that mount it. notes/titanium_handrail_backsplash.md.
from typehaus import (
    Material,
)


MATERIALS_TITANIUM = [
    # RL-M-HANDRAIL-E/-W, ST-B2M. Alloy grade not stated on the order (a bike-frame supplier,
    # likely Gr 9 Ti-3Al-2.5V); the R301.5 hand-calc is graded on Gr 2's floor.
    Material(tag="titanium-alloy-tube", name="Titanium alloy tube, 42 OD x 2.5 wall, brushed",
             r_per_inch=0.0, density=4480.0, vapor_permeance_perms=0.0, hatch="metal",
             color="#9a9a96", product_ref="PROD-WALTLY-TI-TUBE-42X2.5",
             source="Waltly Titanium, 5 pieces x ~1200 mm, owner-furnished; request the mill cert for the grade"),
    # WP-M-KIT-BACKSPLASH. Hung uncut: the factory hems are the finished edges.
    Material(tag="titanium-gr2-sheet-brushed",
             name="Grade 2 titanium sheet, 0.8 mm, teardrop hem, brushed",
             r_per_inch=0.0, density=4510.0, vapor_permeance_perms=0.0, hatch="metal",
             color="#9a9a96", product_ref="PROD-WALTLY-TI-SHEET-GR2-0.8",
             source="Waltly Titanium, 5 sheets 500 x 1000 mm, open teardrop hem 12 mm finished depth, 2.0 mm inside bend radius, owner-furnished; noncombustible"),
    # The handrail's brackets, returns and wall end plates: off-the-shelf 42.4 mm fittings.
    Material(tag="stainless-316-brushed", name="Type 316 stainless, brushed (satin)",
             r_per_inch=0.0, density=8000.0, vapor_permeance_perms=0.0, hatch="metal",
             color="#b4b6b6",
             source="42.4 mm handrail brackets, 90-degree wall-return elbows and wall end plates; A4/316 anchors"),
]
