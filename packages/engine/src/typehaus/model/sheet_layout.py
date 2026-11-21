"""How structural sheathing is laid, declared once (decision #146).

The ``DrywallStandard`` pattern: one house element, ``resolve/sheet_layout.py`` lays every
sheathing layer sheet by sheet off its wall's framing, ``structural.sheathing_edge_support``
grades each break and ``takeoff/sheet_goods.py`` counts sheets off the pieces. The sheet's
size stays on the layer (``Layer.sheet_length`` x 48"). Without a declared standard the
layout runs on this class's defaults.
"""

from __future__ import annotations

from typing import Literal

from typehaus.model.base import Element
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, inch


@register_element
class SheetLayoutStandard(Element):
    """One per plan (a second is an ``integrity.sheet_layout_standard`` error).

    ``min_edge_bearing`` is how much framing face each panel edge needs at a joint: a break
    is backed where it lies within ``member_face / 2 - min_edge_bearing`` of a member's
    centre (a doubled stud's face is the pair's). ``source`` says where the house read it.
    ``max_course_shortfall`` lets a band exceed whole courses by that much, left to the
    layer above (a subfloor edge under the next wall's sheathing), not cut as a sliver.
    """

    orientation: Literal["vertical", "horizontal"] = "vertical"
    min_rip_width: Length = inch(12)
    min_edge_bearing: Length = inch(0.4375)
    stagger_min: Length = inch(16)
    kerf: Length = inch(0.125)
    start_at_through_end: bool = True
    max_course_shortfall: Length = inch(0.75)
    source: str = ""


register_constructor("SheetLayoutStandard", SheetLayoutStandard)
