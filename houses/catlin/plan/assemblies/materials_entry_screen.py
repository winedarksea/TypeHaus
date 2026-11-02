"""Materials for the entry screen's drained metal infill."""
from typehaus import Material

MATERIALS_ENTRY_SCREEN = [
    Material(tag="entry-screen-bone-white-aluminum", product_ref="PROD-BW-ALUMINUM",
             name='UNA-CLAD Bone White PVDF aluminum, 0.050 inch', density=2700,
             color="#e8e3d7", finish="metal", source="Nominal aluminum density; formed returns, "
             "clips, stiffeners and flashings require separate quantity and weight allowances."),
    Material(tag="entry-screen-wrb", product_ref="PROD-BW-WRB", name="DuPont Tyvek HomeWrap",
             areal_density_kg_m2=0.07, hatch="membrane", color="#deded8",
             source="Continuous WRB, shingle-lapped into drained and ventilated cassette flashings."),
]
