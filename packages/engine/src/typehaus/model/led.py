"""LED tape construction, declared once (decision #137): the ``DuctStandard`` pattern for
24 V lighting.

A ``LightRun`` states a path and a type. What is built along it — the tape, the channel it
sits in, the lens, the caps, clips and modules — comes from the type's ``LedStrip`` and the
``LedChannel`` it names (``resolve/led_sections.py``). What feeds it — controller, lead
gauge, feed end and connector — comes from the house's one ``LedStandard``
(``resolve/led_leads.py``). An unread datasheet figure is ``None`` and grades UNKNOWN.
"""

from __future__ import annotations

from typing import Literal

from pydantic import model_validator

from typehaus.model.base import Element, HausModel
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, ft

#: Output channels a ``LuminaireType.color_mode`` needs from its controller.
COLOR_MODE_CHANNELS = {"fixed": 1, "tunable": 2, "rgb": 3, "rgbw": 4, "rgbcct": 5}

Aperture = Literal["down", "out", "up"]


class LedStrip(HausModel):
    """The tape (or rigid bar) a strip type is made of, off its datasheet.

    ``tape_width``/``tape_height`` are the bare tape, or the silicone tube for IP67/68.
    ``modules`` lists the fixed lengths a rigid-bar product ships in (IKEA MITTLED); a run
    of one is filled with the fewest that fit, ``module_gap`` apart. ``channel_ref`` names
    the ``LedChannel`` a surface run sits in; a shadow-gap run takes the drywall bead.
    """

    tape_width: Length
    # Unpublished on many sheets: unset, it is drawn at the generic tape thickness and the
    # fit check grades width alone.
    tape_height: Length | None = None
    cut_pitch: Length | None = None
    # The datasheet's longest run fed from one end; beyond it a run needs a second feed.
    max_feed_length: Length | None = None
    reel_length: Length | None = None
    modules: tuple[Length, ...] = ()
    module_gap: Length | None = None
    channel_ref: str | None = None
    # The product ships its own proprietary cords (IKEA): no derived lead, no cable billed.
    system_cords: bool = False
    source: str | None = None


@register_element
class LedChannel(Element):
    """An aluminium LED extrusion with its lens, as sold.

    ``kind``: ``u`` a U profile, ``flat`` a shallow surface strip, ``corner45`` a 45-degree
    corner profile. ``ring`` overrides the parametric section for an extrusion the box fields
    cannot express: ``(across, depth)`` points, back at depth 0, opening at ``outer_depth``.
    """

    product_ref: str | None = None
    kind: Literal["u", "flat", "corner45"] = "u"
    outer_width: Length
    outer_depth: Length
    # The back's thickness. Few sheets publish it: unset, it is drawn at the side wall
    # derived from the published outer and inner widths.
    wall: Length | None = None
    inner_width: Length | None = None  # None derives outer_width - 2 * wall
    lens: Literal["opal", "frosted", "clear", "none"] = "frosted"
    lens_shape: Literal["flat", "dome"] = "flat"
    lens_inset: Length | None = None  # below the opening; None is flush
    lens_product_ref: str | None = None
    stick_length: Length | None = None
    end_cap_ref: str | None = None
    clip_ref: str | None = None
    clip_spacing: Length | None = None
    ring: tuple[tuple[Length, Length], ...] = ()
    source: str | None = None

    def inner_width_m(self) -> float:
        if self.inner_width is not None:
            return self.inner_width.meters
        return self.outer_width.meters - 2.0 * (self.wall.meters if self.wall else 0.0)

    def back_m(self) -> float:
        return self.wall.meters if self.wall else (self.outer_width.meters
                                                   - self.inner_width_m()) / 2.0

    @model_validator(mode="after")
    def _fits(self):
        if self.inner_width is None and self.wall is None:
            raise ValueError(f"{self.tag}: a channel states inner_width or wall")
        if self.inner_width_m() <= 0 or self.back_m() >= self.outer_depth.meters:
            raise ValueError(f"{self.tag}: channel walls leave no room for tape")
        return self


class LedController(HausModel):
    """A 24 V controller's outputs: what ``electrical.led_wiring`` grades a run against."""

    channels: int
    max_current_a: float | None = None  # all channels together
    max_channel_current_a: float | None = None
    source: str | None = None


class LedCable(HausModel):
    """One stocked low-voltage cable: its gauge, product and NEC 725 rating."""

    awg: int
    product_ref: str
    rating: Literal["CL2", "CL2R", "CL2P", "CL3", "CL3R"] = "CL2"


@register_element
class LedStandard(Element):
    """How the house wires its 24 V tape (decision #137). One per plan.

    ``cables`` are the stocked gauges; a lead takes the smallest keeping its drop within
    ``max_drop_pct``. ``slack`` is the fraction added to a derived lead for loops and
    terminations. ``max_controller_distance`` bounds a controller's lead from its driver.
    """

    cables: tuple[LedCable, ...]
    max_drop_pct: float = 3.0
    slack: float = 0.10
    max_controller_distance: Length = ft(10)
    connector_ref: str | None = None
    source: str | None = None


for _name, _obj in (("LedStrip", LedStrip), ("LedChannel", LedChannel),
                    ("LedController", LedController), ("LedCable", LedCable),
                    ("LedStandard", LedStandard)):
    register_constructor(_name, _obj)
