"""Refrigerant linesets, declared once (decision #139): the ``LedStandard`` pattern for copper.

A lineset is one ``PipeRun`` of system ``refrigerant``: ``diameter`` is the vapour line,
``liquid_diameter`` the liquid, ``serves`` the indoor head (its ``outdoor_ref`` names the
outdoor unit). ``RefrigerantLimits`` is the outdoor type's published piping table (a
prescriptive read); ``LinesetStandard`` is how the house buys and finishes the sets.
``resolve/linesets.py`` derives one ``ResolvedLineset`` per run off both.
"""

from __future__ import annotations

from typehaus.model.base import Element, HausModel
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, ft, inch


class RefrigerantLimits(HausModel):
    """An outdoor unit's published piping limits. An unread figure stays ``None``
    (graded UNKNOWN by ``mep.lineset_limits``), never defaulted."""

    max_total: Length | None = None
    max_per_port: Length | None = None
    min_per_port: Length | None = None
    #: Rise with the outdoor unit above / below the indoor unit.
    max_rise_od_above: Length | None = None
    max_rise_od_below: Length | None = None
    #: Line length the factory charge covers; past it, ``charge_oz_per_ft`` is added.
    precharged_length: Length | None = None
    charge_oz_per_ft: float | None = None
    source: str


@register_element
class LinesetStandard(Element):
    """How the house buys its linesets. One per plan.

    ``stock_kit_lengths`` are the pre-flared kit lengths on offer; a set orders the smallest
    at or above its developed length plus ``service_loop``. ``exterior_cover_ref`` is the
    lineset cover billed by the foot over each set's outdoor leg.
    """

    stock_kit_lengths: tuple[Length, ...] = (ft(15), ft(25), ft(35), ft(50), ft(65), ft(75))
    service_loop: Length = ft(2)
    insulation: str = '1/2" closed-cell elastomeric'
    #: The two-core control cable taped to the pair; its OD is part of the bundle section.
    control_cable_diameter: Length = inch(0.5)
    kit_product_ref: str | None = None
    exterior_cover_ref: str | None = None
    #: An end within this of its port pair is landed (plan and height).
    port_tolerance: Length = inch(6)
    source: str | None = None


for _name, _obj in (("RefrigerantLimits", RefrigerantLimits),
                    ("LinesetStandard", LinesetStandard)):
    register_constructor(_name, _obj)
