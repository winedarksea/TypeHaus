"""House mounting choices; hardware is included in existing fixture package quantities."""

from typehaus.model import ShowerAssemblySpec, ShowerComponent, inch


def combo(valve_face, wall_direction, *, thermo=False, standing=2):
    head_ref = "PROD-MOEN-26008" if thermo else "PROD-MOEN-26010SRN"
    controls = ((ShowerComponent(name="volume", kind="volume", product_ref="PROD-DELTA-T17T"),
                 ShowerComponent(name="temperature", kind="temperature", vertical_offset=inch(1.5),
                                 product_ref="PROD-DELTA-T17T")) if thermo else
                (ShowerComponent(name="control", kind="control"),))
    return ShowerAssemblySpec(
        valve_face=tuple(inch(value) for value in valve_face), wall_direction=wall_direction,
        standing_surface_height=inch(standing), finish="chrome" if thermo else "brushed-nickel",
        components=(*controls, ShowerComponent(name="head", kind="head", product_ref=head_ref),
                    ShowerComponent(name="handheld", kind="handheld", lateral_offset=inch(3.5),
                                    vertical_offset=inch(-3), relative_to_connection=True,
                                    product_ref=head_ref, connection="head")))


# RM-B-BATH's shower (2026-11-25; the sauna rinse until then): valve on the pan's south wall,
# W-B-SA-N. Body base is the slab; standing surface is the 2 in. pan, valve 51 7/16 in. over
# the slab, 4 in. east of the pan's centre to sit mid-bay between W-B-SA-N's 134" and 150"
# studs. No valve pocket: the wall is an ordinary 2x6 now, not a sauna liner.
BASEMENT_SHOWER = combo((4, -18, 51.4375), (0, -1))
# The same valve station for the neo-angle pan turned 180 degrees (2026-11-26): its back is
# local +y, so the wall is local +y and the 4 in. east of centre is local -x.
BASEMENT_NEO_SHOWER = combo((-4, 18, 51.4375), (0, 1))
BATH2_SHOWER_ASSEMBLY = combo((0, 18, 48), (0, 1), thermo=True, standing=1.5)
ATTIC_SHOWER = combo((0, 18, 48), (0, 1))
TUB_SHOWER_ASSEMBLY = ShowerAssemblySpec(
    valve_face=(inch(-30), inch(0), inch(30)), wall_direction=(-1, 0),
    # Illustrative base thickness pending the delivered Sterling section.
    standing_surface_height=inch(2),
    components=(ShowerComponent(name="control", kind="control", product_ref="PROD-DELTA-T14459-SS"),
                ShowerComponent(name="diverter", kind="diverter", vertical_offset=inch(12)),
                ShowerComponent(name="head", kind="head", product_ref="PROD-DELTA-52535-SS",
                                connection="diverter"),
                ShowerComponent(name="spout", kind="spout", vertical_offset=inch(-10),
                                product_ref="PROD-DELTA-T14459-SS"),
                ShowerComponent(name="handheld-connection", kind="outlet",
                                lateral_offset=inch(-8), vertical_offset=inch(18),
                                connection="diverter"),
                ShowerComponent(name="handheld", kind="handheld", lateral_offset=inch(-8),
                                vertical_offset=inch(26), connection="handheld-connection")))
