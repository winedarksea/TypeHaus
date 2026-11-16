# haus: editable
# Duct construction, declared once (decision #114): the engine derives every take-off, tee,
# reducer, collar damper, boot, port kit and hanger off the resolved runs
# (resolve/duct_parts.py) and bills them in [duct_parts] / [duct_supports] / [duct_sealing].
# Basis, reads and the seam/hanger arithmetic: notes/air_distribution_products.md
# "DuctStandard" (read 2026-11-05). An unread number is None and grades UNKNOWN.
#   * 1/2 in. w.g. class; round to 14" is 0.013" = 30 ga (IMC 2018 Table 603.4, adopted by
#     Minn. R. 1346.0050; MN deletes the IRC's mechanical chapters, Minn. R. 1309.0010 subp. 3.C).
#     Minn. R. 1346.0603 subps. 1-7 and 9 are repealed; subp. 10 stands: IMC 603.18.3, volume
#     dampers "adjusted ... and locked in place" (revisor.mn.gov, read 2026-11-07).
#   * Elbows: a 90 or 45 turn is a DIE-STAMPED Linx E90/E45 (commercial, 3-12"), C 0.22 at
#     r/D 1.0 (ASHRAE Fitting 3-1; Linx offers 1.0 or 1.5 radius, 1.0 taken): no retail
#     stamped elbow exists, and the retail adjustable's C put R403.5 short (owner, 2026-11-05).
#     Any other turn, or a vertex a run names in `adjustable_elbows` (the stamped laying
#     length does not fit), is a C.L. Ward adjustable 90 set down, dimension A as centre-to-
#     face (4.75/6/7"; read to the far side the 8" radius would be under D/2), C 0.37
#     (Fitting 3-2, 4-piece, r/D 1.0). The stamped elbow's take-off is its 1.0 D centreline
#     radius (radius_diameters); Linx publishes no centre-to-face.
#   * Rectangular turns: a shop-made SMACNA radius elbow at r/W 1.0, no vanes; C 0.25 read at
#     H/W 0.5 (the 8x4 ERV trunk), the same Co the static budget's 59" rectangular bend is.
#   * Supports: SMACNA HVAC DCS 1995 Tables 4-1/4-2; within 2' of each fitting (S4.1). With no
#     framing in reach, a saddle strapped to the deck the duct bears on (house practice; SMACNA
#     draws no bottom support), else a bracket to a wall within 2" (Fig. 4-8) (owner,
#     2026-11-07). Flex per JP Lamborn (IMC 603.10).
#   * Mastic billed by the gallon at the TDS's UL 181B-M 30 mil film: 320 LF at 3" x 20 mil
#     scaled to 30 mil = 213 LF/gal.
#   * In-line damper: C 0.34 fully open, from the smallest round damper with a published AMCA
#     500-D test (Greenheck VCDR-53, 12"); notes/erv_static_budget.md s.10.24.
#   * Broan port kit (manual pp. 10-11): 6 to 8 in. transition, then 12 in. of flex.

from typehaus import (
    DuctElbowRow,
    DuctPartRow,
    DuctStandard,
    DuctSupportRow,
    PortKit,
    Product,
    RectElbowRow,
    RoundGaugeRow,
    ft,
    inch,
)

# ASHRAE Fitting 3-1/3-2 angle factors (Locklin 1950): C at 30/45/90 deg = C90 x 0.45/0.60/1.00,
# linear between; an adjustable elbow set down to any turn up to 90 reads them.
_K = ((30.0, 0.45), (45.0, 0.60), (90.0, 1.0))
_READ = "notes/air_distribution_products.md, DuctStandard (read 2026-11-05)"
_IMPERIAL = "Imperial Mfg. catalog Dec 2017 (SKU and gauge only; no dimensions published)"
_IMP26 = "Imperial PP1142 Galvanized Duct, Pipe & Fittings, Aug 2026 (imperialgroup.s3.amazonaws.com/site/PP1142-Galvanized-Catalogue-En-2026-August-2026-08-18-03.45-PM.pdf), read 2026-11-07; SKU and gauge only, no dimensions"
_SPIN = "Imperial PP1142 Aug 2026 p.17 'Spin Collar - (With Damper)', 28 ga (read 2026-11-07); the catalog does not say the damper locks: the submittal or a sample must show a locking handle (Minn. R. 1346.0603 subp. 10 -> IMC 603.18.3 'locked in place'), otherwise M&M 504MSD4 (28 ga, 5.50 in., 'locking handle', mmmfg.com 504MSD submittal)"
_MM400 = "M&M Mfg. 400 round reducer submittal (mmmfg.com/wp-content/themes/speedwagon/pdf/400_Model_(1).pdf, read 2026-11-07): 1.75 collar + 2.50-3.50 taper + 1.75 collar; a stand-in for the Imperial GV0821 + GV0811 set, whose length is unpublished"
_INC68 = "Imperial GV0772 (28 ga, PP1142 Aug 2026 SKU and gauge only; no length in Imperial's catalog or the retailer listings reached; Zoro and Home Depot refused automated reads; searched 2026-11-12). Stand-in: M&M Mfg. 400 round reducer submittal (mmmfg.com/wp-content/themes/speedwagon/pdf/400_Model_(1).pdf, read 2026-11-12): 'Hemmed Collars' 1.75 + '2.50 to 3.50' + 1.75 = 6.0-7.0 in. overall, no per-size table; the 7.0 in. maximum is drawn, no collar engagement credited"
_STAMPED = "li-hvac.com/product/sw-elbows (read 2026-11-05): die stamped, 3-12 in., 1.0 or 1.5 radius"
_STRAP = "DiversiTech TDS DOC134521 (cdn.shopify.com/s/files/1/0253/0852/8730/files/Specifications__710-004.pdf, a reseller-hosted copy of the maker's sheet), read 2026-11-07: 710-005 (DS-221) 1 in. x 100 ft, 22 ga; 710-001 is 26 ga, not this"
_SADDLE = "House practice (owner, 2026-11-07): 1 in. x 22 ga strap band over the duct, screwed to the deck it bears on each side. SMACNA HVAC DCS 1995 has no figure for a duct supported from below; S4.1: supports 'installed as required to maintain alignment', attachments 'not limited to the specific methods shown'"
_BRACKET = "SMACNA HVAC DCS 1995 Fig. 4-8 supports from wall: 'locate ducts against wall or maximum of 2 in. away'; 1 in. x 22 ga band to a wall anchor (owner, 2026-11-07)"
_ROUND = "SMACNA HVAC DCS 1995 Table 4-2, round to 10 in."
_RECT = "SMACNA HVAC DCS 1995 Table 4-1, half-perimeter to 30 in."
_FLEX = "JP Lamborn Installation Guidelines Rev. 11-16 (sylvane.com/cdn/shop/files/installation-guide-jpl-mhp25-25-ft-insulated-flex-duct.pdf, read 2026-11-07): 'supported at 4 ft maximum intervals by means of min 1.5 in. wide straps'; IMC 603.10 sends flex to the manufacturer"
_RECT_ELBOW = "SMACNA HVAC DCS 1995 rectangular radius elbow, shop-fabricated, r/W 1.0, no vanes; Co 0.25 at r/W 1.0, H/W 0.5 (ASHRAE 'Fitting Loss Coefficients', online supplement to Principles of HVAC 9th ed., 2021, Fitting 3-5 p. 12, after Idelchik Diagram 6-1; read 2026-11-08, notes/erv_static_budget.md)"
_DAMPER = "In-line single-blade volume damper fully open: no 4 in. maker publishes a loss, so C is read off Greenheck VCDR-53 (Aug 2023) AMCA 500-D Fig. 5.3 fully ducted, 12 in.: 0.19 in. wg at 3000 fpm = 0.34 x VP (0.32-0.36 over the table), above the 0.30 ASHRAE butterfly term notes/erv_static_budget.md s.4 uses; body length unpublished (drawn at its diameter)"
_KIT = "Broan B210E75RT manual pp. 10-11; transition C 0.22 is the sudden 6/8 in. bound"

DUCT_PRODUCTS = (
    Product(tag="PROD-DUCT-ELBOW-4", brand="C.L. Ward", model="90 Adjustable Elbow 4in",
            name="4 in. adjustable 90 degree galvanized elbow", source=_READ,
            equals=("PROD-DUCT-ELBOW-4-30",)),
    Product(tag="PROD-DUCT-ELBOW-6", brand="C.L. Ward", model="90 Adjustable Elbow 6in",
            name="6 in. adjustable 90 degree galvanized elbow", source=_READ,
            equals=("PROD-DUCT-ELBOW-6-30",)),
    Product(tag="PROD-DUCT-ELBOW-8", brand="C.L. Ward", model="90 Adjustable Elbow 8in",
            name="8 in. adjustable 90 degree galvanized elbow", source=_READ,
            equals=("PROD-DUCT-ELBOW-8-30",)),
    Product(tag="PROD-DUCT-ELBOW-S-4", brand="Linx (Li-HVAC)", model="E90/E45 4in",
            name="4 in. die-stamped 90/45 degree galvanized elbow", source=_STAMPED),
    Product(tag="PROD-DUCT-ELBOW-S-6", brand="Linx (Li-HVAC)", model="E90/E45 6in",
            name="6 in. die-stamped 90/45 degree galvanized elbow", source=_STAMPED),
    Product(tag="PROD-DUCT-ELBOW-S-8", brand="Linx (Li-HVAC)", model="E90/E45 8in",
            name="8 in. die-stamped 90/45 degree galvanized elbow", source=_STAMPED),
    Product(tag="PROD-DUCT-ELBOW-4-30", brand="Imperial", model="GV0286",
            name="4 in. adjustable 90 degree elbow, 30 ga", source=_IMPERIAL),
    Product(tag="PROD-DUCT-ELBOW-6-30", brand="Imperial", model="GV0296",
            name="6 in. adjustable 90 degree elbow, 30 ga", source=_IMPERIAL),
    Product(tag="PROD-DUCT-ELBOW-8-30", brand="Imperial", model="GV1330",
            name="8 in. adjustable 90 degree elbow, 30 ga", source=_IMPERIAL),
    Product(tag="PROD-DUCT-SPIN-4", brand="Imperial", model="GV0851",
            name="4 in. spin collar with damper, 28 ga", source=_SPIN),
    Product(tag="PROD-DUCT-SPIN-6", brand="Imperial", model="GV0853",
            name="6 in. spin collar with damper, 28 ga", source=_SPIN),
    Product(tag="PROD-DUCT-SADDLE-4", brand="Imperial", model="GV0979",
            name="4 in. wye saddle tap, 28 ga", source=_IMPERIAL),
    Product(tag="PROD-DUCT-TEE-6-4", brand="Imperial", model="GV0890",
            name="6 x 6 x 4 in. full-flow tee, 30 ga", source=_IMPERIAL),
    Product(tag="PROD-DUCT-TEE-6-6", brand="Imperial", model="GV0893",
            name="6 x 6 x 6 in. full-flow tee, 30 ga", source=_IMP26),
    Product(tag="PROD-DUCT-TEE-4-4", brand="Master Flow", model="T4X4X4",
            name="4 x 4 x 4 in. round tee, galvanized",
            url="https://www.homedepot.com/p/4-in-Round-Tee-T4X4X4/100131692",
            source="Master Flow (GAF) T4X4X4, Home Depot listing, about $16 (owner, 2026-11-10); gauge and dimensions not published: the tee's laying length stays estimated"),
    # DU-ERV-EA's drain tee at the riser foot (M1-114, 2026-11-12): a tap in the invert, no
    # branch stub, so nothing hangs below the wrap. Capped until a line reaches a receptor.
    Product(tag="PROD-DUCT-DRAIN-TAP-8", brand="Any", model="3/4 in. PVC bulkhead tap",
            name="8 in. duct drain tee: 3/4 in. PVC bulkhead fitting (male adapter and locknut) through the duct's invert, mastic-sealed, with a 3/4 in. cap",
            source="house practice (2026-11-12); no SKU read: a commodity bulkhead fitting field-set in the duct"),
    Product(tag="PROD-DUCT-REDUCER-8-4", brand="Imperial", model="GV0821 + GV0811",
            name="8 to 4 in. reducer set: GV0821 8 to 6 in. (28 ga) + GV0811 6 to 4 in. (30 ga), stacked",
            source=_IMP26),
    Product(tag="PROD-DUCT-REDUCER-6-4", brand="Imperial", model="GV0811",
            name="6 to 4 in. reducer, 30 ga", source=_IMPERIAL),
    Product(tag="PROD-DUCT-REDUCER-8-6", brand="Imperial", model="GV0821",
            name="8 to 6 in. reducer, 28 ga", source=_IMPERIAL),
    Product(tag="PROD-DUCT-INCREASER-6-8", brand="Imperial", model="GV0772",
            name="6 to 8 in. increaser, 28 ga", source=_INC68),
    Product(tag="PROD-DUCT-INCREASER-4-5", brand="Imperial", model="GV0766",
            name="4 to 5 in. increaser, 30 ga", source=_IMPERIAL),
    Product(tag="PROD-DUCT-BOOT-2X10X4", brand="Snappy", model="P13-204",
            name="2-1/4 x 10 x 4 in. 90 degree floor boot", source=_READ,
            equals=("PROD-DUCT-BOOT-2X10X4-IMP",)),
    Product(tag="PROD-DUCT-BOOT-2X10X4-IMP", brand="Imperial", model="GV0602",
            name="2-1/4 x 10 x 4 in. 90 degree floor boot", source=_IMPERIAL),
    Product(tag="PROD-DUCT-BOOT-12X6X6", brand="Imperial", model="GV0671",
            name="6 x 12 x 6 in. end boot", source=_IMPERIAL),
    Product(tag="PROD-DUCT-FLEX-R8", brand="JP Lamborn", model="MHP-45R8",
            name="R-8 insulated flexible duct, UL 181 Class 1", source=_READ),
    Product(tag="PROD-DUCT-CONNECTOR", brand="Duro Dyne", model="MFN",
            name="metal-fabric-metal flexible duct connector", source=_READ),
    Product(tag="PROD-DUCT-MASTIC", brand="Hardcast", model="Versa-Grip 181 (304138)",
            name="UL 181A-M/B-M duct sealant, 1 gal pail (white)", pack_quantity=4,
            url="https://dam.carlisle.com/asset/697a8b90-f75b-4788-85be-11bd95838c09/Versa-Grip-181-TDS.pdf",
            source="Carlisle Versa-Grip 181 TDS 0124 (read 2026-11-07): 304138 = case of (4) 1-gal pails, white; UL 181B-M pail rate '20- to 30-mil wet film thickness at 3 in. wide', coverage 'up to 320 lin. ft. at 3 in. width, 20-mil'; billed at 30 mil, 320 x 20/30 = 213 LF/gal"),
    Product(tag="PROD-DUCT-TAPE", brand="Nashua", model="324A",
            name="UL 181A-P/B-FX foil tape, 2.5 in. x 60 yd", source=_READ),
    Product(tag="PROD-DUCT-STRAP", brand="DiversiTech", model="710-005 (DS-221)",
            name="1 in. x 100 ft galvanized duct strapping, 22 ga (SMACNA Table 4-2)",
            source=_STRAP),
    Product(tag="PROD-DUCT-STRAP-FLEX", brand="Any", model="1-1/2 in. flex duct strap",
            name="1-1/2 in. wide flex duct hanger strap (JP Lamborn); no retail roll read",
            source=_FLEX),
)

DUCT_STANDARD = [
    DuctStandard(
        uid="J1VHFGGW6S", tag="DUCT-STANDARD",
        pressure_class_in_wg=0.5,
        seal_class="UL 181B-M mastic or UL 181B-FX tape, every joint and seam (IMC 603.9)",
        sealant_product_ref="PROD-DUCT-MASTIC",
        tape_product_ref="PROD-DUCT-TAPE",
        sealant_coverage_lf=213.0,
        sealant_unit="gal",
        tape_roll_length=ft(180),
        insulation_product_ref="PROD-AIR-ELASTOMERIC-1IN",
        citations=("IMC 2018 603 (Minn. R. 1346)", "IMC 2018 Table 603.4 (Minn. R. 1346.0050)",
                   "SMACNA HVAC DCS 1995"),
        round_gauges=(
            RoundGaugeRow(max_diameter=inch(14), gauge=30, thickness=inch(0.013),
                          source="IMC 2018 Table 603.4 (Minn. R. 1346.0050), round < 12 and 12-14 in., 1/2 in. w.g. galv: 0.013 in.; proofread against UpCodes, Minnesota Mechanical Code 2020 (IMC 2018 with amendments), 2026-11-12 (codes.iccsafe.org refused automated access)"),
        ),
        elbows=(
            DuctElbowRow(diameter=inch(4), product_ref="PROD-DUCT-ELBOW-S-4", kind="stamped",
                         radius_diameters=1.0, loss_c=0.22, angle_k=_K, source=_STAMPED),
            DuctElbowRow(diameter=inch(6), product_ref="PROD-DUCT-ELBOW-S-6", kind="stamped",
                         radius_diameters=1.0, loss_c=0.22, angle_k=_K, source=_STAMPED),
            DuctElbowRow(diameter=inch(8), product_ref="PROD-DUCT-ELBOW-S-8", kind="stamped",
                         radius_diameters=1.0, loss_c=0.22, angle_k=_K, source=_STAMPED),
            DuctElbowRow(diameter=inch(4), product_ref="PROD-DUCT-ELBOW-4", angles=(90.0,),
                         center_to_face=inch(4.75), loss_c=0.37, angle_k=_K, source=_READ),
            DuctElbowRow(diameter=inch(6), product_ref="PROD-DUCT-ELBOW-6", angles=(90.0,),
                         center_to_face=inch(6), loss_c=0.37, angle_k=_K, source=_READ),
            DuctElbowRow(diameter=inch(8), product_ref="PROD-DUCT-ELBOW-8", angles=(90.0,),
                         center_to_face=inch(7), loss_c=0.37, angle_k=_K, source=_READ),
        ),
        rect_elbow=RectElbowRow(radius_ratio=1.0, loss_c=0.25, aspect_ratio=0.5,
                                source=_RECT_ELBOW),
        parts=(
            DuctPartRow(kind="collar_damper", size="4in", product_ref="PROD-DUCT-SPIN-4",
                        source=_IMPERIAL),
            DuctPartRow(kind="damper", size="4in", product_ref="PROD-AIR-DAMPER-4-MANUAL",
                        loss_c=0.34, source=_DAMPER),
            DuctPartRow(kind="collar_damper", size="8in", integral=True,
                        source="the plenum's own trunk spigot; a trunk is not balanced"),
            DuctPartRow(kind="collar_damper", size="6in", integral=True,
                        source="the level-2 extract plenum's own riser spigot; a riser is not balanced"),
            # The flat level-2 extract (2026-11-08): a 4" spin collar does not fit a 4"-tall
            # side, so each branch leaves on a 4x4 tap with a square-to-round, made with the trunk.
            DuctPartRow(kind="takeoff", size="8x4", branch="4in", fabricated=True,
                        source="4 x 4 in. side tap and square-to-round, shop-fabricated with the trunk"),
            DuctPartRow(kind="takeoff", size="6x4", branch="4in", fabricated=True,
                        source="4 x 4 in. side tap and square-to-round, shop-fabricated with the neck"),
            DuctPartRow(kind="reducer", size="8x4", branch="6x4", fabricated=True,
                        source="rectangular transition, shop-fabricated"),
            DuctPartRow(kind="reducer", size="8x4", branch="4in", fabricated=True,
                        source="end transition to the last branch, shop-fabricated"),
            DuctPartRow(kind="takeoff", size="8in", branch="4in",
                        product_ref="PROD-DUCT-SADDLE-4", source=_IMPERIAL),
            DuctPartRow(kind="takeoff", size="10x8", branch="6in",
                        product_ref="PROD-DUCT-SPIN-6", source=_IMPERIAL),
            DuctPartRow(kind="takeoff", size="18x8", branch="6in",
                        product_ref="PROD-DUCT-SPIN-6", source=_IMPERIAL),
            DuctPartRow(kind="takeoff", size="18x8", branch="4in",
                        product_ref="PROD-DUCT-SPIN-4", source=_IMPERIAL),
            DuctPartRow(kind="takeoff", size="10x6", branch="6in",
                        product_ref="PROD-DUCT-SPIN-6", source=_IMPERIAL),
            DuctPartRow(kind="takeoff", size="18x8", branch="10x8", fabricated=True,
                        source="rectangular branch, shop-fabricated with the trunk"),
            DuctPartRow(kind="takeoff", size="18x8", branch="12x12", fabricated=True,
                        source="DU-S-HP-SUP-DROP's top take-off at the trunk's north cap, shop-fabricated"),
            DuctPartRow(kind="tee", size="6in", branch="6in", product_ref="PROD-DUCT-TEE-6-6",
                        source=_IMP26),
            # REG-M-RET3's branch off LAUNDRY's crown (2026-11-10).
            DuctPartRow(kind="tee", size="4in", branch="4in", product_ref="PROD-DUCT-TEE-4-4",
                        source="Master Flow T4X4X4 (owner, 2026-11-10); gauge and dimensions unpublished"),
            # Imperial makes no 8 to 4; the set's laying length is unpublished. Stand-in: two
            # M&M 400s at their 7.0" maximum, one 1.75" collar engaged: 7.0 + 7.0 - 1.75.
            DuctPartRow(kind="reducer", size="8in", branch="4in",
                        product_ref="PROD-DUCT-REDUCER-8-4", length=inch(12.25),
                        source=_MM400),
            DuctPartRow(kind="reducer", size="18x8", branch="10x6", fabricated=True,
                        length=inch(18),
                        source="flat-bottomed offset transition, 18in, shop-fabricated"),
            DuctPartRow(kind="cap", fabricated=True,
                        source="end cap past a run's last branch, shop-made and sealed"),
            DuctPartRow(kind="boot", size="4in", branch="4x4", integral=True,
                        source="the disc valve's own collar (Vents-US AM 100 VRF)"),
            DuctPartRow(kind="boot", size="4in", branch="4in", integral=True,
                        source="the register box's own collar (PROD-AIR-STAIR-REGISTER-BOX)"),
            DuctPartRow(kind="boot", size="4in", branch="4x8", integral=True,
                        source="the valve box's own collar (PROD-AIR-SUITEBATH-BOOT)"),
            DuctPartRow(kind="boot", size="4in", branch="none", integral=True,
                        source="a vent or hood with no neck takes the duct on its spigot"),
            DuctPartRow(kind="boot", size="4in", branch="5x5",
                        product_ref="PROD-DUCT-INCREASER-4-5", source=_IMPERIAL),
            DuctPartRow(kind="boot", size="4in", branch="10x2.25",
                        product_ref="PROD-DUCT-BOOT-2X10X4", source=_READ),
            DuctPartRow(kind="boot", size="8in", branch="8in", fabricated=True,
                        source="REG-T-HPWH-STAIR-1210's shop-fabricated boot includes its rear 8in collar"),
            DuctPartRow(kind="boot", size="6in", branch="12x6",
                        product_ref="PROD-DUCT-BOOT-12X6X6", source=_IMPERIAL),
            DuctPartRow(kind="boot", size="6in", branch="8x6", fabricated=True,
                        source="no 8 x 6 x 6 boot stocked by Imperial; shop-fabricated"),
            DuctPartRow(kind="boot", size="10x6", branch="12x6", fabricated=True,
                        source="top take-off register boot on the trunk, shop-fabricated"),
            DuctPartRow(kind="boot", size="10x8", branch="12x6", fabricated=True,
                        length=inch(6),
                        source="register box on the rectangular branch, shop-fabricated, 6in deep"),
            DuctPartRow(kind="boot", size="18x8", branch="12x6", fabricated=True,
                        source="top take-off register boot on the trunk, shop-fabricated"),
            DuctPartRow(kind="boot", size="12x10", branch="24x12", fabricated=True,
                        source="REG-S-HP-RET filter box up into the bay, shop-fabricated"),
            DuctPartRow(kind="boot", size="6x4", branch="12x12", fabricated=True,
                        source="RM-S-SUITE return filter box, locking balancing damper, shop-fabricated"),
            DuctPartRow(kind="boot", size="12x6", branch="12x12", fabricated=True,
                        source="RM-S-BED3 return filter box, locking balancing damper, shop-fabricated"),
            DuctPartRow(kind="boot", size="12x12", branch="none", fabricated=True,
                        source="REG-A-HP-EAST-RET's stub: damper box on EQ-S-ERV-MIX's face, locked at 35 cfm, shop-fabricated"),
        ),
        supports=(
            DuctSupportRow(section="round", max_size=inch(10), spacing=ft(12),
                           product_ref="PROD-DUCT-STRAP", width=inch(1),
                           thickness=inch(0.0336), source=_ROUND),
            DuctSupportRow(section="rectangular", max_size=inch(30), spacing=ft(10),
                           product_ref="PROD-DUCT-STRAP", width=inch(1),
                           thickness=inch(0.0336),
                           source=_RECT),
            DuctSupportRow(section="round", max_size=inch(10), spacing=ft(12), hanger="saddle",
                           product_ref="PROD-DUCT-STRAP", width=inch(1),
                           thickness=inch(0.0336), source=_SADDLE),
            DuctSupportRow(section="rectangular", max_size=inch(30), spacing=ft(10),
                           hanger="saddle", product_ref="PROD-DUCT-STRAP", width=inch(1),
                           thickness=inch(0.0336), source=_SADDLE),
            DuctSupportRow(section="round", max_size=inch(10), spacing=ft(12), hanger="bracket",
                           product_ref="PROD-DUCT-STRAP", width=inch(1),
                           thickness=inch(0.0336), source=_BRACKET),
            DuctSupportRow(section="flex", max_size=inch(12), spacing=ft(4),
                           product_ref="PROD-DUCT-STRAP-FLEX", width=inch(1.5),
                           source=_FLEX),
        ),
        # flex_bend_loss_c: LBNL (Abushakra, Walker, Sherman 2002) Table 4, non-metallic flex 90 degree
        # bend, 6" 1.18 / 8" 2.85 (notes/flex_lead_bend_basis.md section 3); charged only where a
        # lead bends.
        port_kits=(
            PortKit(type_ref="EQ-T-BROAN-B210E75RT", ports=("outdoor", "exhaust"),
                    transition_product_ref="PROD-DUCT-INCREASER-6-8",
                    transition_length=inch(7), transition_loss_c=0.22,
                    flex_product_ref="PROD-DUCT-FLEX-R8", flex_length=inch(12), flex_bend_loss_c=2.85,
                    source=_KIT),
            PortKit(type_ref="EQ-T-BROAN-B210E75RT", ports=("supply", "return"),
                    flex_product_ref="PROD-DUCT-FLEX-R8", flex_length=inch(12),
                    flex_bend_loss_c=1.18,
                    source="Broan B210E75RT manual pp. 10-11"),
            PortKit(type_ref="EQ-T-GREE-FLEXX-ULTRA-24-AH",
                    flex_product_ref="PROD-DUCT-CONNECTOR", flex_length=inch(3),
                    connector=True, source="notes/air_distribution_products.md section 7"),
        ),
    ),
]
