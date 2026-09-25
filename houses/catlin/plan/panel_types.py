"""Catlin's two service panels, as copies of the library's panel rows under the house's own tags.

NOT ``# haus: editable``: the editable dialect has no ``model_copy``, and a panel type is
catalog data, not geometry. The backup subpanel stays in plan/mep_electrical.py.
"""

from library.electrical import panel_type

from typehaus import Service, ServicePort, ft

PANEL_TYPES = (
    # ``bus_amps=225`` is what `code.NEC_705_12_interconnection` computes the 120% rule
    # against. It is the busbar rating, deliberately not the main:
    # NEC 705.12(B)(3)(2) sizes the allowable backfeed on the bus, and this panel is a 225A
    # bus behind a 200A main precisely so there is 70A of source headroom.
    #
    # ``service_amps=200`` is THIS PANEL'S MAIN, and it has to be stated now that the
    # service is a Class 320 meter-main (plan/electrical.py, ED-T-METER): without it the
    # 705.12 check borrows the service size and would grade a 320A main against a 225A
    # bus, silently loosening the backfeed allowance on a panel that never sees 320A.
    panel_type("ED-T-PANEL-225A", tag="ED-T-PANEL",
               name="225A bus, 200A main (feeder 1 of the 320A service)"),
    # Feeder 2 of the Class 320 service: the wellness and EV loads, which are what made the
    # 220.82 total need a service upgrade in the first place. 20 spaces for the 4 two-pole
    # circuits in use — room to add, not room to fill. ``bus_amps=200`` equals the main:
    # nothing backfeeds this bus, and a 225A bus here would buy headroom nobody needs.
    panel_type("ED-T-PANEL-200A", tag="ED-T-PANEL-2",
               name="200A main (feeder 2 of the 320A service)",
               ports=(ServicePort(tag="feed", service=Service.POWER_240,
                                  position=(ft(0), ft(0), ft(0))),)),
)
