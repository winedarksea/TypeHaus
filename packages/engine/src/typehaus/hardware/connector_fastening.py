"""The fastener schedule a connector is installed with (decision #105).

The type lives here and the schedules live in ``library/hardware/connector_schedules.py``,
the ``StructuralHardware`` split. A schedule exists only for connectors whose coating or
wood contact makes the wrong nail a failure: stainless, ZMAX/HDG, or landing in treated wood.
"""

from __future__ import annotations

from dataclasses import dataclass

#: Connector and fastener finishes; a joint never mixes the two families.
STAINLESS_FINISHES = frozenset({"ss304", "ss316"})
ZINC_FINISHES = frozenset({"zmax", "hdg", "g90", "mech_galv"})


@dataclass(frozen=True)
class SiteBolt:
    """A site-length bolt or lag through one leg (decision #147); ``leg`` indexes
    ``Connector.connects``. A bolt's length is derived from the grip; a lag takes
    ``min_length_in`` (HL fn 7: >= 5")."""

    diameter_in: float
    per_leg: int
    leg: int
    kind: str  # "bolt" | "lag"
    min_length_in: float = 0.0


@dataclass(frozen=True)
class ConnectorFastening:
    """One connector's fasteners: ``(count, fastener model, into)`` per term.

    ``fasteners`` is empty where the screws ship in the connector's own box (CBSTQ-SDS2,
    DTT2Z); a joint bolted at the site names its ``site_bolts`` instead.
    """

    finish: str
    fasteners: tuple[tuple[int, str, str], ...]
    citation: str
    site_bolts: tuple[SiteBolt, ...] = ()

    @property
    def per_connector(self) -> int:
        return sum(count for count, _model, _into in self.fasteners)


def connector_fastening(model: str) -> ConnectorFastening | None:
    """The schedule for an EXACT part designation, or ``None``.

    Exact on purpose: ``hardware_by_model`` prefix-matches, and ABU66SS must never read the
    ABU66's schedule. Imported lazily, like ``structural_hardware_catalog``.
    """
    from typehaus.library.hardware.connector_schedules import CONNECTOR_FASTENERS

    return CONNECTOR_FASTENERS.get(model)
