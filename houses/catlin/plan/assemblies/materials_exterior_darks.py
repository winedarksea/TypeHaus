"""The exterior darks, every one coloured and named from ``plan/exterior_palette.py``.

Swap the facade there, not here. Tags name the PRODUCT, never the colour, so a swap moves no
join key (prices.toml, tests, goldens). Not ``# haus: editable``: it computes from the palette.
"""

from plan.exterior_palette import ANDERSEN, AZEK, CLOPAY, METAL, UNA_CLAD_MATTE_BLACK, WINDOW
from typehaus import Material

_M = METAL.label

MATERIALS_EXTERIOR_DARKS = [
    # The house's one exterior dark: rake/eave/ridge trim coil, opening casings, guards, the
    # garage fascia and the roof edge chain. Not named "*seam*": renderers key the ribbed
    # standing-seam finish off that substring and this is flat brake-formed stock.
    Material(tag="metal-dark-exterior", name=f"{_M}, formed",
             r_per_inch=0.0, density=7850.0, perm_rating=0.0, hatch="metal",
             color=METAL.hex, product_ref="PROD-STOCK-DARK-TRIM-COIL",
             source=f"RF-HOUSE rake/eave/ridge trim coil, opening casings, exterior guards; {_M}, {METAL.solar}"),
    # The same colour on seamless K-style stock: a different PRODUCT, and prices.toml
    # qualifies [drainage] on the tag (roll-formed on site, not shop-brake-formed).
    Material(tag="metal-dark-kstyle", name=f"Prefinished K-style gutter coil, matched to {_M}",
             r_per_inch=0.0, density=2700.0, perm_rating=0.0, hatch="metal",
             color=METAL.hex, product_ref="PROD-STOCK-DARK-KSTYLE-COIL",
             source=f"garage south eave + balcony gutter/leaders; Metal Sales publishes no K-style gutter line, so seamless aluminium coil colour-matched to {_M}"),
    # The rainscreen base Z and the balcony base flashings. Metal Sales PVDF Galvalume flat
    # (owner: one maker), 24 ga stocked.
    # Galvalume's oxide does not re-form in chloride the way aluminium's does: hem every
    # edge, keep it off concrete and wet mortar.
    Material(tag="metal-flat-sheet",
             name=f"Metal Sales PVDF flat sheet, Galvalume (AZ50), {METAL.colour}",
             r_per_inch=0.0, density=7850.0, vapor_permeance_perms=0.0, hatch="metal",
             color=METAL.hex,
             source=f"rainscreen base Z-flashing, balcony base flashings; Metal Sales PVDF flat sheet in {METAL.colour} ({METAL.solar}), Galvalume AZ50; 24 ga stocked (Metal Sales PVDF flat-stock data sheet); every exposed edge hemmed; never in contact with concrete or fresh mortar"),
    # The garage stem band (24" on all four walls, 0.050") and its stem-top Z (0.040"), back
    # to aluminium 2026-10-30 for the plowed, salted apron: aluminium's oxide re-forms in
    # chloride. Una-Clad 3105-H14, made in Anoka, MN; Matte Black is stocked in both gauges
    # (Una-Clad colour chart 03/2026). 48" x 120" sheet rips into two 24" bands. Minimum bend
    # radius 2T at 0.040", 3T at 0.050", so hems are open (teardrop), never flattened. The
    # Galvalume corrugated panel oversails the Z: sealant or EPDM between, and never let the
    # aluminium touch concrete or mortar. Tag kept from the 2026-09 band.
    Material(tag="aluminum-flat-pvdf",
             name=f"Una-Clad PVDF aluminium flat sheet, {UNA_CLAD_MATTE_BLACK.colour}",
             r_per_inch=0.0, density=2700.0, vapor_permeance_perms=0.0, hatch="metal",
             color=UNA_CLAD_MATTE_BLACK.hex,
             source=f"garage ICF stem exterior band (all four walls, 0.050\") + stem-top Z-flashing (0.040\"); Una-Clad Kynar 500/Hylar 5000 pre-finished aluminium sheet, ASTM B209 3105-H14, 48\" x 120\", {UNA_CLAD_MATTE_BLACK.colour} (stocked at 0.040\" and 0.050\"), {UNA_CLAD_MATTE_BLACK.solar}; manufactured Anoka MN (Elevate TIS 2016, 2026-08-11); 2T/3T minimum bend radius, open hems; #9 316 stainless gasketed screws; sealant/EPDM where the Galvalume corrugated panel oversails the Z; never in contact with concrete or fresh mortar"),
    # BBD75 Transition Trim at the panel's horizontal joints (Layer.joint_trim_material_ref).
    Material(tag="bbd-transition-trim",
             name=f"Metal Sales BBD75 Transition Trim 55536XX, {METAL.line}, {METAL.colour}",
             r_per_inch=0.0, density=7800.0, vapor_permeance_perms=0.0, hatch="metal",
             color=METAL.hex,
             source=f"Metal Sales BBD75 Install Guide 10/2025 p.14, 40 (Transition Trim 55536XX); {_M}, {METAL.solar}"),
    # The canopy's steel east posts when EAST_POST_SYSTEM = "steel": ASTM A500 Gr C HSS,
    # galvanized after fabrication (A123) then powder-coated, a "duplex" system.
    Material(tag="steel-hss-duplex", name="HSS, hot-dip galvanized + powder-coated (duplex)",
             r_per_inch=0.0, density=7850.0, perm_rating=0.0, hatch="metal",
             color=METAL.hex,
             source=f"PT-BW-RE/-RNE steel variant — ASTM A500 Gr C, ASTM A123 then powder coat matched to {_M} (notes/canopy_garage_diaphragm.md §5)"),
    # The basement's exposed-XPS band (`_PROTECTION_PANEL`). The library's
    # `foundation-coating-acrylic` is the same product in stock grey; Tuff II has no stock
    # dark (Concrete Grey, White, Tanner, Linens, Cairn, Taupe, Sand), so this is a custom
    # tint to the metal above it. A dark skin over XPS runs hot (XPS softens near 165 F):
    # confirm the maker's minimum LRV over foam before ordering.
    Material(tag="foundation-coating-acrylic-tinted",
             name=f"Trowel-applied acrylic foundation coating over mesh (1/8\"), tinted to {METAL.colour}",
             r_per_inch=0.0, density=1400.0, vapor_permeance_perms=5.0, coating=True,
             hatch="concrete", color=METAL.hex,
             source=f"basement exposed-XPS band, 6\" below grade to wall top; acrylic foundation coating over mesh (Tuff II class), custom-tinted to {_M} (the trim above it); confirm the custom match and the maker's minimum LRV over foam before ordering"),
    # Site paint on the exterior door faces and frames: no product named, so matched to METAL.
    Material(tag="door-paint-exterior", name=f"Exterior door field paint, matched to {_M}",
             coating=True, color=METAL.hex, finish="paint",
             source="Site-applied coating approved for fiberglass/composite frame; factory colour quote alternate."),
    # Window frames, by product (`WindowType.frame_material_ref`).
    Material(tag="drutex-alucover-cap", name=f"Drutex Alucover aluminium cap, RAL {WINDOW.colour} matt",
             hatch="metal", color=WINDOW.hex,
             source=f"Drutex IGLO Energy Alucover exterior cap, RAL {WINDOW.colour} matt powder coat (plan/opening_products.py). Colour is RAL's own sRGB (ral-farben.de colour list, read 2026-10-30)."),
    Material(tag="andersen-400-exterior", name=f"{ANDERSEN.label} exterior (Perma-Shield vinyl)",
             color=ANDERSEN.hex,
             source=f"Andersen 400 casement, {ANDERSEN.colour} exterior. Colour sampled from Andersen's swatch (andersenwindows.com, read 2026-10-30). The 400 Series offers no grey."),
    # The overhead door's leaf (`DT-EXT-OVERHEAD192.leaf_material_ref`).
    Material(tag="clopay-classic-steel", name=f"{CLOPAY.label} factory paint",
             hatch="metal", color=CLOPAY.hex,
             source="Clopay Classic Steel GDU293, Charcoal. Colour sampled from Clopay's paint-color-charcoal chip (clopaydoor.com, read 2026-10-30). Black is R-6.5 only (GDU266)."),
    # The French doors' returns and casing.
    Material(tag="captivate-sheet", name=f"{AZEK.label} 3/4 inch sheet trim",
             color=AZEK.hex, product_ref="PROD-AZEK-CAPTIVATE-SHEET",
             source=f"AZEK 2026 product guide AS03448096, 3/4 x 48 x 96 smooth sheet; Captivate {AZEK.colour} factory finish. Field-rip returns/casing; two sheets for both doors. Colour sampled from AZEK's 2025 Captivate swatch (read 2026-10-30); a physical sample governs."),
]
