# haus: editable
# Refrigerant linesets (decision #139): one PipeRun per set, vapour x liquid copper ACR,
# lagged and taped with the control cable into one bundle. `serves` names the head; the
# outdoor unit is its `outdoor_ref`, the MUL30 port `outdoor_port`. Filed on `main`
# (datum 0'-0"), so every elevation is absolute. Each path runs outdoor unit -> head; the
# outside legs are hand-drawn, and the oracle is notes/heat_pump_ground_pad.md "Line sets".
#   * HP1: west off the valves, up beside the cabinet's west end, east above it into
#     W-M-N1's 304-320 bay (no window; west of ED-M-LIVING-KET1's box), up through both storeys'
#     plates into FS-ATTIC's north bay, up through the deck and over to the AH's ports.
#   * HP2: three sets side by side (x 380-393) through FS-M-EAST's rim east of the
#     cabinet, between W-M-S2's starter girt and the next course, into its south bay, each
#     level or rising inward through the wall so water runs out. GYM west at y 12 (behind
#     BED's corner), back to y 9 and down beside the head; BED west past the
#     x=18' bearing into FS-M-WEST and up W-M-S1's bay east of WIN-M-BED-S2;
#     LIVING up W-M-S2's 352-367 bay, west in FS-S-EAST's south bay and down over D-M-PORCH's
#     header (the door fills the wall under the head).
#   * HP3: back into W-M-N2's 128-144 bay under the head's plate, up the cavity, out at
#     8'-6 1/2" (between the girt and the top plates, clear of the entry stair), west in a
#     wall-held cover above D-M-ENTRY's head (clear of the canopy joint at y 37'-2 5/8"),
#     and down the house's NW corner to the condenser's west-end valves.

from typehaus import (
    LinesetStandard,
    PipeRun,
    PipeSystem,
    Product,
    RoughOpening,
    from_node,
    ft,
    inch,
    pt,
)

LINESET_PRODUCTS = (
    Product(tag="PROD-LINESET-KIT", brand="(retail)", model="Pre-flared mini-split line set",
            name="Pre-flared, pre-insulated mini-split line set with control cable",
            source="Retail kit: soft ACR pair, flared and capped, 1/2 in. closed-cell lagging, sold in 15/25/35/50/65/75 ft. Brand CONFIRM at order."),
    Product(tag="PROD-LINESET-COVER", brand="(retail)", model="Lineset cover, 4 in.",
            name="PVC lineset cover (channel, elbows, wall inlet), 4 in.",
            source="Retail wall-mounted lineset cover sized for one or two bundles. Brand and fittings CONFIRM at order."),
)

LINESET_STANDARD = [
    LinesetStandard(uid="MFTMKP1FTT", tag="LINESET-STANDARD",
                    stock_kit_lengths=(ft(15), ft(25), ft(35), ft(50), ft(65), ft(75)),
                    service_loop=ft(2), insulation='1/2" closed-cell elastomeric',
                    control_cable_diameter=inch(0.5), kit_product_ref="PROD-LINESET-KIT",
                    exterior_cover_ref="PROD-LINESET-COVER", port_tolerance=inch(12),
                    source="Owner plan 2026-11-20: one pre-flared kit per set, 2 ft service loop. Port tolerance 12 in.: a wall head's factory pigtails reach into the wall behind it, so the field flare need not sit on the port station."),
]

LINESETS_MAIN = [
    PipeRun(uid="KXX7EXWCF9", tag="PR-A-RFG-HP1", system=PipeSystem.REFRIGERANT, serves=("EQ-S-HP1-AH",),
            material="copper_acr", diameter=inch(0.75), liquid_diameter=inch(0.375),
            path=(pt(inch(298.625), inch(454.03125)), pt(inch(294.5), inch(454.03125)),
                  pt(inch(294.5), inch(441.5)), pt(inch(294.5), inch(441.5)),
                  pt(inch(307.875), inch(441.5)), pt(inch(307.875), inch(429.1)),
                  pt(inch(307.875), inch(429.1)), pt(inch(307.875), inch(427.6)),
                  pt(inch(307.875), inch(427.6)), pt(inch(307.875), inch(421.5)),
                  pt(inch(303.875), inch(421.5)), pt(inch(279.75), inch(421.5)),
                  pt(inch(279.75), inch(421.5)), pt(inch(279.75), inch(322)),
                  pt(inch(279.75), inch(322)), pt(inch(279.75), inch(328.5))),
            elevations=(inch(-5), inch(-5), inch(-5), inch(30), inch(30), inch(30),
                        inch(104.5), inch(109.5), inch(233), inch(236), inch(242.5),
                        inch(242.5), inch(272), inch(272), inch(251), inch(251))),
    PipeRun(uid="F5MDC6F8QB", tag="PR-B-RFG-HP2-GYM", system=PipeSystem.REFRIGERANT, serves=("EQ-B-HP2-GYM",),
            outdoor_port="A", material="copper_acr", diameter=inch(0.375),
            liquid_diameter=inch(0.25),
            path=(pt(inch(376.16), inch(-25.86)), pt(inch(393), inch(-25.86)),
                  pt(inch(393), inch(-10)), pt(inch(393), inch(12)),
                  pt(inch(234.75), inch(12)), pt(inch(231.75), inch(9)),
                  pt(inch(221.25), inch(9)), pt(inch(221.25), inch(9))),
            elevations=(inch(-10), inch(-10), inch(-6.1), inch(-5.5), inch(-7), inch(-7),
                        inch(-7), inch(-21.5))),
    PipeRun(uid="660NG5X4HJ", tag="PR-M-RFG-HP2-BED", system=PipeSystem.REFRIGERANT, serves=("EQ-M-HP2-BED",),
            outdoor_port="B", material="copper_acr", diameter=inch(0.375),
            liquid_diameter=inch(0.25),
            path=(pt(inch(376.16), inch(-25.86)), pt(inch(385.25), inch(-25.86)),
                  pt(inch(385.25), inch(9)), pt(inch(206.35), inch(9)),
                  pt(inch(200.6), inch(3.25)), pt(inch(200.6), inch(3.25))),
            elevations=(inch(-7), inch(-7), inch(-3.25), inch(-3.25), inch(-3.25),
                        inch(89.5))),
    PipeRun(uid="RZ435RNK9F", tag="PR-M-RFG-HP2-LIVING", system=PipeSystem.REFRIGERANT,
            serves=("EQ-M-HP2-LIVING",), outdoor_port="C", material="copper_acr",
            diameter=inch(0.375), liquid_diameter=inch(0.25),
            path=(pt(inch(376.16), inch(-25.86)), pt(inch(380.25), inch(-25.86)),
                  pt(inch(380.25), inch(3.1)), pt(inch(359.4), inch(3.1)),
                  pt(inch(359.4), inch(3.1)), pt(inch(355.4), inch(5)),
                  pt(inch(256.7), inch(5)), pt(inch(252.7), inch(3.1)),
                  pt(inch(252.7), inch(3.1))),
            elevations=(inch(-4), inch(-4), inch(-4), inch(-4), inch(109.5), inch(115),
                        inch(115), inch(109.5), inch(100))),
    PipeRun(uid="VZK9M5DP8Y", tag="PR-M-RFG-HP3-STAIR", system=PipeSystem.REFRIGERANT,
            serves=("EQ-M-HP3-STAIR",), material="copper_acr", diameter=inch(0.5),
            liquid_diameter=inch(0.25),
            path=(pt(inch(0), inch(461.85)), pt(inch(-4), inch(461.85)),
                  pt(inch(-4), inch(441.5)), pt(inch(-4), inch(441.5)),
                  pt(inch(136), inch(441.5)), pt(inch(136), inch(429.1)),
                  pt(inch(136), inch(429.1)), pt(inch(136), inch(426.9))),
            elevations=(inch(-10), inch(-10), inch(-10), inch(102.5), inch(102.5),
                        inch(102.5), inch(36), inch(34))),
    # The framed-wall holes (sleeved, sloped out, sealed to the air barrier). HP2's three sets
    # cross FS-M-EAST's LSL rim below the wall, each in its own TJ-8000 rim hole: a floor
    # penetration, not a wall RoughOpening (one there frames a header into the plates).
    RoughOpening(uid="5XPG5EHW9R", tag="AO-M-RFG-HP1", host="W-M-N1", position=from_node("N-M-NE", inch(122.125)),
                 width=inch(4), height=inch(4), sill_height=inch(28),
                 penetration_for=("PR-A-RFG-HP1",)),
    RoughOpening(uid="JRPGX9HKB5", tag="AO-M-RFG-HP3", host="W-M-N2", position=from_node("N-M-N1", inch(78)),
                 width=inch(4), height=inch(4), sill_height=inch(100.5),
                 penetration_for=("PR-M-RFG-HP3-STAIR",)),
]
