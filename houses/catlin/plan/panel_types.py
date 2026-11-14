"""Catlin's feeder panels: two copies of the library's panel rows, and the garage subpanel.

NOT ``# haus: editable``: the editable dialect has no ``model_copy``, and a panel type is
catalog data, not geometry. The backup subpanel stays in plan/mep_electrical.py.
"""

from library.electrical import panel_type

from typehaus import ElectricalDeviceType, Service, ServicePort, ft, inch

PANEL_TYPES = (
    # ``bus_amps=225`` is what `code.NEC_705_12_interconnection` computes the 120% rule
    # against. It is the busbar rating, deliberately not the main:
    # NEC 705.12(B)(2)(a) sizes the allowable backfeed on the bus, and this panel is a 225A
    # bus behind a 200A main precisely so there is 70A of source headroom.
    #
    # ``service_amps=200`` is THIS PANEL'S MAIN, and it has to be stated now that the
    # service is a Class 320 meter-main (plan/electrical.py, ED-T-METER): without it the
    # 705.12 check borrows the service size and would grade a 320A main against a 225A
    # bus, silently loosening the backfeed allowance on a panel that never sees 320A.
    # ``sccr_a``: the QO154M200P sheet (Jul 2023) "Max Short Circuit Current Rating 22 kA"; the
    # HOM2040M200PC sheet (Oct 2020) "Short Circuit Current Rating 22 kA". NEC 408.6.
    panel_type("ED-T-PANEL-225A", tag="ED-T-PANEL",
               name="225A bus, 200A main (feeder 1 of the 320A service)", sccr_a=22000,
               # The QO154M200P sheet's photo: main breaker at the top of the interior.
               main_feed_end="top"),
    # Feeder 2 of the Class 320 service: the wellness and EV loads, which are what made the
    # 120.82 total need a service upgrade in the first place. 20 spaces for the 5 two-pole
    # circuits in use, including the workshop. ``bus_amps=200`` equals the main:
    # nothing backfeeds this bus, and a 225A bus here would buy headroom nobody needs.
    panel_type("ED-T-PANEL-200A", tag="ED-T-PANEL-2",
               name="200A main (feeder 2 of the 320A service)", sccr_a=22000,
               ports=(ServicePort(tag="feed", service=Service.POWER_240,
                                  position=(ft(0), ft(0), ft(0))),)),
    # The garage subpanel (owner, 2026-11-14): one 90 A feeder from ED-B-PANEL-2, so the
    # garage is one supply (225.30) and its main breaker is the 225.31 building disconnect.
    # Square D HOM1224M100PRB product data sheet (se.com): 12 spaces / 24 circuits, 100 A
    # main breaker, "Bus Rated Current 125.0 A", "Max Short Circuit Current Rating 22 kA",
    # main lugs "AWG 6...AWG 1 copper", NEMA 3R, 18.9 x 14.8 x 4.5 in, operating ambient
    # 23-104 F (the garage is unheated: electrician to confirm). No ``bus_amps``: nothing
    # backfeeds it. Ground bar ordered separately (PK-series kit).
    ElectricalDeviceType(tag="ED-T-PANEL-GARAGE",
                         name="Square D Homeline HOM1224M100PRB, 100A main breaker, 12 spaces, "
                              "NEMA 3R (garage subpanel)",
                         footprint=(inch(14.8), inch(4.5)), height=inch(18.9),
                         plan_symbol="panel", spaces=12, service_amps=100, sccr_a=22000,
                         source="Square D HOM1224M100PRB product data sheet (Schneider "
                                "Electric): 12 spaces, 100 A main, 22 kA, 18.9 x 14.8 x 4.5 in",
                         ports=(ServicePort(tag="feed", service=Service.POWER_240,
                                            position=(ft(0), ft(0), ft(0))),)),
)
