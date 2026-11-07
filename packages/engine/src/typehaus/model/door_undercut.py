"""The house's door undercut: what a leaf is hung at, and the range it must stay in.

An undercut is the gap from the leaf's bottom to the finished floor under it. A stock
prehung's slab is cut on site to ``hung`` over the higher finished floor at its doorway
(``resolve/door_sizing``); ``advisory.door_undercut`` grades the realized gap against
``minimum``..``maximum``, and ``mep.door_transfer_air`` reads the same gap as relief area.
"""

from __future__ import annotations

from pydantic import model_validator

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor
from typehaus.quantities import Length


class DoorUndercut(HausModel):
    hung: Length
    minimum: Length
    maximum: Length
    source: str | None = None

    @model_validator(mode="after")
    def _hung_within_range(self) -> DoorUndercut:
        if not 0 <= self.minimum.meters <= self.hung.meters <= self.maximum.meters:
            raise ValueError("DoorUndercut needs 0 <= minimum <= hung <= maximum")
        return self


register_constructor("DoorUndercut", DoorUndercut)
