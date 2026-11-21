"""``SheathingNailing`` — a sheathing or subfloor layer's nailing schedule (decisions #105, #147).

Its own module because ``model/assembly.py`` is past the file-size limit. The support
spacing is NOT here: it is read from the host's ``FramingSpec``, so a 24" roof and a 16"
wall bill their own row counts from one schedule.
"""

from __future__ import annotations

from pydantic import Field

from typehaus.model.base import HausModel


class SheathingNailing(HausModel):
    """The nail (a catalog model), and its spacing along supported edges and in the field."""

    part: str
    edge_oc_in: float = Field(gt=0)
    field_oc_in: float = Field(gt=0)
    # A shear wall nails every panel edge at ``edge_oc_in``, the ones on plates or blocking
    # included; an unblocked roof deck nails only the edges that land on a support. A roof
    # whose ``DiaphragmSpec`` is blocked and authors its blocks counts as blocked anyway.
    blocked: bool = False
    source: str = ""
    # The prescriptive row this schedule merely restates (``"IRC 2018 Table R602.3(1) item
    # 31"``). Empty means special: S-001 lists it rather than folding it into one note line.
    code_row: str = ""
