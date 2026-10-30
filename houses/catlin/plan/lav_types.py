"""Selected vanity assemblies and their separately purchased components."""

from library.placeables import front_zone
from plan.bath_finish import (
    THEME_FAUCET_PART, THEME_MATERIAL_REFS,
    UTILITY_FAUCET_PART, UTILITY_MATERIAL_REFS,
)
from plan.lav_ports import lav_ports
from typehaus.model import (
    FixturePart, FixtureType, Footprint2D, ModelRepresentation, Mount,
    PortCertainty, Service, inch, pt,
)

NEEDS = frozenset({Service.DRAIN, Service.WATER_HOT, Service.WATER_COLD, Service.VENT})
TUBULAR_TRAP = FixturePart(role="trap", product_ref="PROD-DEARBORN-707BN-1")
BONDED_BOWL = FixturePart(role="basin", product_ref="PROD-SS-LAV-16X13")
CORIAN_TOP = FixturePart(role="top", product_ref="PROD-CORIAN-GLACIER-WHITE")

ANGSJON_36 = FixtureType(
    tag="FX-ANGSJON-36", name='ÄNGSJÖN 36 with ORRSJÖN 37 single-bowl top',
    footprint=(inch(37), inch(21.75)), height=inch(27.625 + 8.4375),
    mount=Mount(elevation=inch(8.375)),
    plan_symbol="drawer-vanity", basin=True, needs=NEEDS,
    product_ref="PROD-IKEA-ANGSJON-36",
    parts=(FixturePart(role="basin", product_ref="PROD-IKEA-ORRSJON-37"),
           THEME_FAUCET_PART, FixturePart(role="trap", product_ref="PROD-IKEA-RANNILEN")),
    cabinet_body_footprint=Footprint2D(points=(
        pt(inch(-18), inch(-10.125)), pt(inch(18), inch(-10.125)),
        pt(inch(18), inch(10.875)), pt(inch(-18), inch(10.875)),
    )),
    ports=lav_ports(21.75, base_in=8.375),
    model_representation=ModelRepresentation(symbol="drawer-vanity", material_refs=THEME_MATERIAL_REFS),
    clearances=(front_zone(inch(37), inch(21.75), inch(21), "lavatory front clearance"),),
    source="Owner 2026-10-24; IKEA AA-2400655-5 / AA-2376395-4 / AA-2141893-6, "
           "notes/assets. 36 in. rim AFF; exact house installation stubs at 20/24 in. "
           "Cabinet 36 x 21 x 25 1/8, top 37 x 21 3/4. Ports are installation setout "
           "for adjustable RÄNNILEN, not manufacturer-published fixed outlets.",
)
ANGSJON_36_SS = ANGSJON_36.model_copy(update={
    "tag": "FX-ANGSJON-36-SS", "height": inch(27.625 + 6.25),
    "name": 'ÄNGSJÖN 36 / ORRSJÖN 37, Indy stainless',
    "parts": (ANGSJON_36.parts[0], UTILITY_FAUCET_PART, ANGSJON_36.parts[2]),
    "model_representation": ModelRepresentation(symbol="drawer-vanity-indy", material_refs=UTILITY_MATERIAL_REFS),
})


def sektion_vanity(width_in, product_ref, *, utility=False):
    return FixtureType(
        tag=f"FX-VANITY-{width_in}-SEKTION" + ("-SS" if utility else ""),
        name=f'{width_in} in. floating SEKTION / AXSTAD, bonded Corian bowl',
        footprint=(inch(width_in), inch(18)), height=inch(36 + (6.25 if utility else 8.4375)),
        plan_symbol="vanity", model_representation=ModelRepresentation(
            symbol="sektion-vanity-indy" if utility else "sektion-vanity",
            material_refs=UTILITY_MATERIAL_REFS if utility else THEME_MATERIAL_REFS),
        product_ref=product_ref, basin=True, needs=NEEDS,
        parts=(UTILITY_FAUCET_PART if utility else THEME_FAUCET_PART,
               TUBULAR_TRAP, BONDED_BOWL, CORIAN_TOP,
               FixturePart(role="rail", product_ref="PROD-IKEA-SEKTION-RAIL-84",
                           length=inch(width_in))),
        ports=lav_ports(18),
        countertop_cutout=Footprint2D(points=(
            pt(inch(-8.1875), inch(-7.625)), pt(inch(8.1875), inch(-7.625)),
            pt(inch(8.1875), inch(5.375)), pt(inch(-8.1875), inch(5.375)),
        )),
        clearances=(front_zone(inch(width_in), inch(18), inch(21), "lavatory front clearance"),),
        source="Owner fabrication setout 2026-10-24; IKEA US SEKTION AXSTAD wall cabinet, "
               "30 in. body on 2 1/4 in. rear ledger chase, bottom 5 1/2 in. AFF, "
               "36 in. Corian rim. Corian 810P bowl envelope; exact wall stubs 20/24 in. "
               "Single-hole fabricated top; cabinet/chase follow Bath2 construction.",
    )

SEKTION_30 = sektion_vanity(30, "PROD-IKEA-SEKTION-WALL-30-AXSTAD")
SEKTION_24_SS = sektion_vanity(24, "PROD-IKEA-SEKTION-WALL-24-AXSTAD", utility=True)
CHULTON_30 = FixtureType(
    tag="FX-CHULTON-30", name='Kohler Chulton 30, white quartz and undermount basin',
    footprint=(inch(30.9375), inch(22.4375)), height=inch(36 + 8.4375),
    plan_symbol="drawer-vanity", basin=True, needs=NEEDS,
    product_ref="PROD-KOHLER-REC39579",
    model_representation=ModelRepresentation(symbol="door-drawer-vanity", material_refs=THEME_MATERIAL_REFS),
    parts=(THEME_FAUCET_PART, TUBULAR_TRAP),
    cabinet_body_footprint=Footprint2D(points=(
        pt(inch(-15), inch(-10.78125)), pt(inch(15), inch(-10.78125)),
        pt(inch(15), inch(11.21875)), pt(inch(-15), inch(11.21875)),
    )),
    ports=lav_ports(22.4375, certainty=PortCertainty.APPROXIMATE),
    clearances=(front_zone(inch(30.9375), inch(22.4375), inch(21), "lavatory front clearance"),),
    source="Kohler ASB-0 dimensioned image, read 2026-10-24, notes/assets: "
           "30 15/16 x 22 7/16 in.; 39 5/16 in. including backsplash, one faucet hole. "
           "6702 fits. Rim and rough-ins remain approximate until installation drawing.",
)
SUNNERSTA_BAR_SINK = FixtureType(
    tag="FX-SUNNERSTA-BAR-SINK", name="SUNNERSTA integral bar sink, Indy stainless",
    footprint=(inch(18), inch(14)), height=inch(20 + 6.25), basin=True,
    mount=Mount(elevation=inch(16)), plan_symbol="lavatory-wall-hung", needs=NEEDS,
    product_ref="PROD-IKEA-SUNNERSTA-SINK",
    parts=(UTILITY_FAUCET_PART, TUBULAR_TRAP),
    model_representation=ModelRepresentation(symbol="sunnersta-sink", material_refs=UTILITY_MATERIAL_REFS),
    ports=lav_ports(14, base_in=16, certainty=PortCertainty.APPROXIMATE),
    source="Existing SUNNERSTA sink, owner 2026-10-24; exact bowl station unpublished. "
           "Plumbing stations approximate; included sink bills with the kitchenette.",
)
# Same tag as the library's LAUNDRY_SINK, which the manifest drops. Not a lavatory: basin=False,
# so 210.52(D) stays off it and 210.52(F) governs. Footprint and declared height are the
# library's; the 34 in. rim is the cabinet top the listing sells it as.
LAUNDRY_TUB = FixtureType(
    tag="FX-LAUNDRY-SINK-24", name="Glacier Bay QL033Y utility tub, white cabinet, bundled faucet",
    footprint=(inch(24), inch(21)), height=inch(43), plan_symbol="laundry-sink",
    basin=False, needs=NEEDS,
    product_ref="PROD-GLACIER-BAY-QL033Y",
    parts=(FixturePart(role="faucet", product_ref="PROD-GLACIER-BAY-QL033Y-FAUCET"),),
    source="Owner selection 2026-10-24: Glacier Bay QL033Y, Home Depot #206057007 (spec sheet "
           "not retrieved). Bundled flex-neck faucet; its hose adapter is not used, so no "
           "hose-bibb tee is carried on the cold. Ports are the library's allowance.",
)
LAV_TYPES = (ANGSJON_36, ANGSJON_36_SS, SEKTION_30, SEKTION_24_SS, CHULTON_30,
             SUNNERSTA_BAR_SINK, LAUNDRY_TUB)
