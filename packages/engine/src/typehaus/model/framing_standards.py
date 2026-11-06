"""Framing standards, declared once per house: the ``TrimStandard`` / ``BoxStandard`` idiom.

``resolve`` never reads ``preferences.toml``, so a house's framing upgrades beyond code are
authored here and the solver reads them (decision #116).
"""

from __future__ import annotations

import re

from pydantic import field_validator

from typehaus.model.base import Element
from typehaus.model.registry import register_constructor, register_element

_RE_BUILT_UP = re.compile(r"^\s*(?P<plies>[1-4])\s*-\s*2x(?P<depth>4|6|8|10|12)\s*$")


def built_up_size(spec: str | None) -> str | None:
    """``"2-2x8"`` (plies-and-nominal, the spelling the ladder emits) normalised, or None."""
    match = _RE_BUILT_UP.match(spec or "")
    return f"{match['plies']}-2x{match['depth']}" if match else None


@register_element
class HeaderStandard(Element):
    """How the house sizes wall headers past the code minimum.

    ``min_bearing_header`` (``"2-2x8"``) drops every R602.7 candidate smaller than itself in a
    BEARING wall. ``None`` is code minimum. ``structural.header_span`` still grades whatever
    is framed against R602.7, so the minimum never hides a shortfall.
    """

    min_bearing_header: str | None = None

    @field_validator("min_bearing_header")
    @classmethod
    def _built_up(cls, value: str | None) -> str | None:
        if value is None:
            return None
        size = built_up_size(value)
        if size is None:
            raise ValueError(f"min_bearing_header {value!r} is not a built-up size, e.g. "
                             "'2-2x8'")
        return size


register_constructor("HeaderStandard", HeaderStandard)
