"""What a concrete pour is MADE of: cement, SCMs, aggregate reactivity (→ ``ConcreteSpec``).

Every field is authored or absent. A missing value grades UNKNOWN, never a default: a mix
that does not name its cement is a mix whose cement this model does not know.
``checks/structural/concrete_materials.py`` grades each one against the exposure class.
"""

from __future__ import annotations

from typing import Literal

from typehaus.model.base import HausModel
from typehaus.model.registry import register_constructor


class CementSpec(HausModel):
    """The cement, as the ticket names it.

    ``designation`` is the type verbatim in its own standard's spelling: ``"II"`` or
    ``"I/II"`` (C150), ``"IL"``, ``"IP(MS)"``, ``"IS(HS)"`` (C595), ``"GU"``, ``"MS"``,
    ``"HS"`` (C1157). The sulfate grade reads it (ACI 318-19 Table 19.3.2.1, S1-S3).
    """

    standard: Literal["ASTM C150", "ASTM C595", "ASTM C1157"]
    designation: str
    source: str | None = None


class ScmFractions(HausModel):
    """SCM content, percent of TOTAL cementitious by mass (ACI 318-19 Table 26.4.2.2(b)).

    All three fields are required and 0 is a real answer, so a mix with only fly ash says so.
    ``includes_blended_cement`` must be True when the cement is a blended C595/C1157 type
    with its own pozzolan or slag: the F3 caps count what is in the cement too.
    """

    fly_ash_pct: float          # fly ash or other pozzolans, ASTM C618
    slag_pct: float             # slag cement, ASTM C989
    silica_fume_pct: float      # ASTM C1240
    includes_blended_cement: bool = False


class AsrSpec(HausModel):
    """ASTM C1778's prescriptive route: reactivity class, structure class, prevention level.

    ACI 318-19 §26.4.2.2(d) asks W1/W2 concrete for evidence that the aggregate is not
    alkali-silica reactive, or that it is mitigated, and R26.4.2.2(d) points to C1778.
    ``aggregate_class`` is C1778 Table 1 (C1293 or C1260 expansion); ``structure_class`` is
    its S1-S4 consequence class; ``prevention_level`` is what the mix design delivers.
    """

    aggregate_class: Literal["R0", "R1", "R2", "R3"]
    structure_class: Literal["S1", "S2", "S3", "S4"] | None = None
    prevention_level: Literal["V", "W", "X", "Y", "Z", "ZZ"] | None = None
    source: str | None = None


for _name, _obj in (("CementSpec", CementSpec), ("ScmFractions", ScmFractions),
                    ("AsrSpec", AsrSpec)):
    register_constructor(_name, _obj)
