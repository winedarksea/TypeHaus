"""``JoistFlangeAllowance`` — an I-joist maker's published limit on load hung from the bottom
flange, keyed by member profile like ``JoistHoleChart``.

A prescriptive read (the reviewer opens the bulletin and finds the line), not engineering.
``structural.equipment_hangers`` sums each joist's hung load in every ``window`` against it.
"""

from __future__ import annotations

from pydantic import Field, model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length


class JoistFlangeAllowance(HausModel):
    #: The member, spelled as the model resolves it (``"11.875 TJI 230"``).
    member: str
    #: The document, edition and the line read, in its own words.
    source: str
    #: Total concentrated load allowed in any ``window`` of the joist, lb.
    max_load_lb: float = Field(gt=0)
    #: Of that, the most allowed on ONE side of the web (a bridge bears on one side), lb.
    max_side_load_lb: float | None = Field(default=None, gt=0)
    window: Length
    #: What the line assumes (fastener centred in the flange, no duration increase).
    condition: str = ""

    @model_validator(mode="after")
    def _readable(self) -> JoistFlangeAllowance:
        if not self.member.strip() or not self.source.strip():
            raise ValueError("JoistFlangeAllowance needs the member and the source read")
        if self.window.meters <= 0:
            raise ValueError("JoistFlangeAllowance.window must be positive")
        return self


register_constructor("JoistFlangeAllowance", JoistFlangeAllowance)
