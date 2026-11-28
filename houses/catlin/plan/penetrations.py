# haus: editable
# Metal-wall penetrations and exterior mounts (decision #142). The 4" ccSPF is the WRB and
# the 2" rainscreen cavity drains: every crossing's real seal is a PVC sleeve set to the
# sheathing BEFORE the spray (a hold point), butyl-taped at its flange, the foam sprayed to
# it, the annulus low-expansion PU after the run is pulled (the one re-sealable seal: cut
# and re-foamed from outside through the closure). The panel closure deflects rain and
# closes the cavity to bugs: an EPDM boot (Dektite class) on a flat, the lineset cover's
# wall inlet, a hydrant's own escutcheon, or the block a device stands on. Urethane bead
# (colour tube) at the panel; neutral-cure silicone only where a boot maker requires it.
# The engine finds every crossing and mount by geometry (resolve/wall_penetrations.py).
# A device 5" wide or less that sits 1" inside one rigid flat, its mid-height line in a girt
# course, mounts direct on the pan (butyl, two 316 screws into the girt): no block (#155).

from typehaus import (
    BondSleeveRow,
    BootRow,
    FlatMountRow,
    LinesetInletRow,
    Material,
    MountBlockRow,
    PenetrationSleeveRow,
    PenetrationStandard,
    Product,
    StrapBlockRow,
    StrutRow,
    inch,
)

_DEKTITE = "ITW Buildex Dektite (Ferguson catalog listings, 2026-11-20): pipe OD range x base diameter x height."
_SCH40 = "Schedule 40 PVC pipe cut as a sleeve: OD per ASTM D1785."

PENETRATION_PRODUCTS = (
    Product(tag="PROD-DEKTITE-1", brand="ITW Buildex", model="Dektite #1 (B4003910)",
            name="EPDM pipe flashing #1, 1/4-2 in. pipe, 4-3/4 in. base", source=_DEKTITE),
    Product(tag="PROD-DEKTITE-3", brand="ITW Buildex", model="Dektite #3 (B4009910)",
            name="EPDM pipe flashing #3, 1/4-4 in. pipe, 7-3/4 in. base", source=_DEKTITE),
    Product(tag="PROD-DEKTITE-4", brand="ITW Buildex", model="Dektite #4 (B4011910)",
            name="EPDM pipe flashing #4, 3-6 in. pipe, 9-1/4 in. base", source=_DEKTITE),
    Product(tag="PROD-PVC-SLEEVE-0-75", brand="(retail)", model="3/4 in. Sch 40 PVC",
            name="3/4 in. Sch 40 PVC sleeve (1.050 in. OD)", source=_SCH40),
    Product(tag="PROD-PVC-SLEEVE-1-5", brand="(retail)", model="1-1/2 in. Sch 40 PVC",
            name="1-1/2 in. Sch 40 PVC sleeve (1.900 in. OD)", source=_SCH40),
    Product(tag="PROD-PVC-SLEEVE-2", brand="(retail)", model="2 in. Sch 40 PVC",
            name="2 in. Sch 40 PVC sleeve (2.375 in. OD)", source=_SCH40),
    Product(tag="PROD-PVC-SLEEVE-2-5", brand="(retail)", model="2-1/2 in. Sch 40 PVC",
            name="2-1/2 in. Sch 40 PVC sleeve (2.875 in. OD)", source=_SCH40),
    Product(tag="PROD-PVC-SLEEVE-3", brand="(retail)", model="3 in. Sch 40 PVC",
            name="3 in. Sch 40 PVC sleeve (3.500 in. OD)", source=_SCH40),
    Product(tag="PROD-PVC-SLEEVE-4", brand="(retail)", model="4 in. Sch 40 PVC",
            name="4 in. Sch 40 PVC sleeve (4.500 in. OD)", source=_SCH40),
    Product(tag="PROD-PVC-SLEEVE-6", brand="(retail)", model="6 in. Sch 40 PVC",
            name="6 in. Sch 40 PVC sleeve (6.625 in. OD)", source=_SCH40),
    Product(tag="PROD-LINESET-WALL-INLET", brand="DiversiTech", model="230-WC4 class",
            name="Lineset cover wall inlet, 4 in., hooded flange",
            source="DiversiTech SpeediChannel 4 in. wall inlet class. Flange size representative: CONFIRM on the cover system ordered."),
    Product(tag="PROD-CELLULAR-PVC-SHEET-3-4", brand="(retail)", model="3/4 in. cellular PVC sheet",
            name="White cellular PVC sheet, 3/4 in. x 4 ft x 8 ft (Azek/Versatex class)",
            source="Mount blocks and strap blocks cut from sheet; strap blocks laminated from it with PVC cement."),
    Product(tag="PROD-UNISTRUT-P1006", brand="Unistrut", model="P1006 EG",
            name="3/8 in.-16 spring nut for 1-5/8 in. strut",
            source="Unistrut catalog: P1006 channel nut with spring, 3/8-16, electro-galvanized."),
    Product(tag="PROD-SS316-WOOD-SCREW-6", brand="(retail)", model="#14 x 6 in. 316 SS",
            name="316 stainless wood screw, #14 x 6 in., EPDM-washered",
            source="plan/mep_vent_clamps.py: 6 in. through block, panel and ~1 in. into the 1 1/2 in. KDAT girt or rake nailer."),
    Product(tag="PROD-SS316-SEALING-SCREW-14X2", brand="Aspen Fasteners", model="#14 x 2 in. Type A 316 SS",
            name="316 stainless sheet-metal screw, #14 x 2 in., hex indented washer head, bonded neoprene sealing washer",
            source="aspenfasteners.com #14 X 2\" Type A hex indented washer head with sealing washer, AISI 316 (50/box, checked 2026-11-27). Flat-mounted devices: ~1.5 in. into the girt. The washer is neoprene, not EPDM: it sits under the device ear, out of the sun."),
    Product(tag="PROD-BUTYL-TAPE-1", brand="(retail)", model="Butyl tape, 1 in.",
            name="Butyl sealant tape, 1 in. x 1/8 in. x 30 ft",
            source="Sleeve flanges to the sheathing, boot bases and block holes to the panel."),
    Product(tag="PROD-URETHANE-SEALANT", brand="Metal Sales", model="Colour-matched urethane tube",
            name="Polyurethane sealant, panel colour, 10.1 oz",
            source="Metal Sales colour tubes: the panel bead at a boot, inlet or block head."),
)

PENETRATION_MATERIALS = (
    Material(tag="strut-pregalvanized", name="Pre-galvanized strut channel (G90)",
             color="#a9adb0",
             source="Unistrut P1000 PG: pre-galvanized ASTM A653 G90."),
)

PENETRATION_STANDARD = [
    PenetrationStandard(
        uid="7G939Y59W4", tag="PENETRATION-STANDARD",
        sleeves=(
            PenetrationSleeveRow(max_outside=inch(1.35), sleeve_diameter=inch(1.9), product_ref="PROD-PVC-SLEEVE-1-5"),
            PenetrationSleeveRow(max_outside=inch(1.8), sleeve_diameter=inch(2.375), product_ref="PROD-PVC-SLEEVE-2"),
            PenetrationSleeveRow(max_outside=inch(2.2), sleeve_diameter=inch(2.875), product_ref="PROD-PVC-SLEEVE-2-5"),
            PenetrationSleeveRow(max_outside=inch(2.8), sleeve_diameter=inch(3.5), product_ref="PROD-PVC-SLEEVE-3"),
            PenetrationSleeveRow(max_outside=inch(3.75), sleeve_diameter=inch(4.5), product_ref="PROD-PVC-SLEEVE-4"),
            PenetrationSleeveRow(max_outside=inch(5.8), sleeve_diameter=inch(6.625), product_ref="PROD-PVC-SLEEVE-6"),
        ),
        bond_sleeves=(
            BondSleeveRow(awg="6", sleeve_diameter=inch(1.05), product_ref="PROD-PVC-SLEEVE-0-75"),
            BondSleeveRow(awg="4", sleeve_diameter=inch(1.05), product_ref="PROD-PVC-SLEEVE-0-75"),
            BondSleeveRow(awg="2", sleeve_diameter=inch(1.05), product_ref="PROD-PVC-SLEEVE-0-75"),
            BondSleeveRow(awg="1/0", sleeve_diameter=inch(1.05), product_ref="PROD-PVC-SLEEVE-0-75"),
        ),
        boots=(
            BootRow(size="#1", min_outside=inch(0.25), max_outside=inch(2), base_width=inch(4.75), base_height=inch(4.75), cone_height=inch(3), product_ref="PROD-DEKTITE-1"),
            BootRow(size="#3", min_outside=inch(0.25), max_outside=inch(4), base_width=inch(7.75), base_height=inch(7.75), cone_height=inch(4), product_ref="PROD-DEKTITE-3", min_trimmed_seal=inch(1.75)),
            BootRow(size="#4", min_outside=inch(3), max_outside=inch(6), base_width=inch(9.25), base_height=inch(9.25), cone_height=inch(5), product_ref="PROD-DEKTITE-4", min_trimmed_seal=inch(1.75)),
        ),
        strap_block=StrapBlockRow(depth=inch(5), max_width=inch(5), height=inch(7), batten_clearance=inch(1), rake_hem_drop=inch(0.83), rake_clearance=inch(0.25), material_ref="pvc-trim", product_ref="PROD-CELLULAR-PVC-SHEET-3-4", screw_ref="PROD-SS316-WOOD-SCREW-6", screws_per_block=2),
        lineset_inlet=LinesetInletRow(product_ref="PROD-LINESET-WALL-INLET", cover_size=inch(4), flange_width=inch(5.5), flange_height=inch(5.5), projection=inch(3), material_ref="pvc-opening-flashing"),
        mount_block=MountBlockRow(thickness=inch(0.75), margin=inch(1), material_ref="pvc-trim", product_ref="PROD-CELLULAR-PVC-SHEET-3-4"),
        flat_mount=FlatMountRow(max_width=inch(5), edge_clearance=inch(1), screw_edge=inch(0.75), screws=2, screw_ref="PROD-SS316-SEALING-SCREW-14X2"),
        strut=StrutRow(product_ref="PROD-UNISTRUT-P1000-PG", spring_nut_ref="PROD-UNISTRUT-P1006", end_margin=inch(2), side_inset=inch(2), material_ref="strut-pregalvanized"),
        sleeve_lip=inch(0.25),
        sleeve_material_ref="pvc-opening-flashing",
        boot_material_ref="epdm",
        cover_material_ref="pvc-opening-flashing",
        butyl_ref="PROD-BUTYL-TAPE-1",
        annulus_foam_ref="PROD-AIR-WALL-SEAL-FOAM",
        panel_sealant_ref="PROD-URETHANE-SEALANT",
        bridgeable_rib_height=inch(0.3125),
        boot_screw_spacing=inch(2),
        source="Owner plan 2026-11-20 (decision #142): sleeve at the foam plane, closure at the panel. Sleeves one size over the run (or lagged bundle), the sleeve ID at least 1/4 in. over its OD.",
    ),
]
