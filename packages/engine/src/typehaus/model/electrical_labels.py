"""House-owned inputs to the derived electrical labels (``resolve/electrical_labels.py``).

The labels themselves are derived, never authored: each comes from the model fact that
triggers it (PV, an ESS, a heating-cable circuit, a remote EVSE breaker). This element holds
only what the house alone knows and a plaque must print. One per plan.
"""

from __future__ import annotations

from typehaus.model.base import Element
from typehaus.model.registry import register_constructor, register_element


@register_element
class LabelStandard(Element):
    """What the house's electrical labels print that the model cannot derive."""

    #: NEC 705.10(2): the emergency phone of each off-site entity servicing the power
    #: sources, as printed ("<who>: <number>"). None is unauthored (the plaque's record is
    #: UNKNOWN); an empty tuple says no off-site entity services them.
    source_service_contacts: tuple[str, ...] | None = None


register_constructor("LabelStandard", LabelStandard)
