"""Grounding and bonding, declared once (decision #123): the ``BoxStandard`` idiom for earth.

``GroundingStandard`` names the parts (one per plan; a second is an
``integrity.grounding_standard`` error). ``GroundingElectrode`` is a rod, a concrete-encased
electrode (the "Ufer", whose qualifying bar is read off ``model.rebar``) or a ring.
``BondingConductor`` is a solid bond between two tagged things: there is no resistive,
diode or capacitive variant, because NEC 250.106 and NFPA 780 require a solid bond and
the checks grade it by graph connectivity (``resolve/grounding.py``).
"""

from __future__ import annotations

from typing import Literal

from typehaus.model.base import Element
from typehaus.model.registry import register_constructor, register_element
from typehaus.quantities import Length, Point2D

ElectrodeKind = Literal["rod", "concrete_encased", "ring"]
ElectrodeUse = Literal["ges", "lps_terminal"]
ConductorMaterial = Literal["copper", "aluminum"]
BondRole = Literal["gec", "bonding_jumper", "ibt", "water_bond", "counterpoise", "down_lead"]


@register_element
class GroundingStandard(Element):
    """The house's grounding parts: rod, clamps, IBT and the lightning-hook conductors."""

    rod_product_ref: str
    rod_diameter: Length
    rod_length: Length
    #: One acorn clamp per rod (UL 467, direct burial).
    rod_clamp_product_ref: str
    #: The listed clamp onto the concrete-encased electrode's stub.
    encased_clamp_product_ref: str | None = None
    #: The intersystem bonding termination's product (NEC 250.94).
    ibt_product_ref: str | None = None
    #: Bimetallic Al-Cu transition connector on the down-lead.
    transition_product_ref: str | None = None
    #: Fastener holding an exposed conductor to the cladding, and its spacing.
    conductor_fastener_product_ref: str | None = None
    conductor_fastener_spacing: Length | None = None
    #: Counterpoise / down-lead conductor (NFPA 780 Table 4.1.1.1.1 Class I; advisory only).
    counterpoise_size: str = "2"
    counterpoise_material: ConductorMaterial = "copper"
    counterpoise_depth: Length | None = None
    down_lead_size: str = "1/0"
    down_lead_material: ConductorMaterial = "aluminum"
    #: Minimum above-grade height of an Al-to-Cu transition (NFPA 780 4.2.2.3.1: 18 in).
    transition_min_height: Length | None = None
    #: NEC 250.53(A)(3): rods at least this far apart.
    min_rod_spacing: Length

    def product_refs(self) -> tuple[str, ...]:
        refs = (self.rod_product_ref, self.rod_clamp_product_ref,
                self.encased_clamp_product_ref, self.ibt_product_ref,
                self.transition_product_ref, self.conductor_fastener_product_ref)
        return tuple(dict.fromkeys(ref for ref in refs if ref))


@register_element
class GroundingElectrode(Element):
    """One electrode. ``top_elevation`` is project-frame absolute; the building is the storey's.

    A rod's ``length`` defaults to the standard's. A ``concrete_encased`` electrode names
    its footing in ``host_ref``; its qualifying length is DERIVED from that footing's bars,
    never authored. ``position`` is where the stub or the rod head is.
    """

    kind: ElectrodeKind
    use: ElectrodeUse = "ges"
    position: Point2D
    top_elevation: Length
    length: Length | None = None
    host_ref: str | None = None
    description: str = ""


@register_element
class BondingConductor(Element):
    """A solid bond from one tagged element to another (electrode, device, pipe run, panel).

    ``path``/``elevations`` follow ``ConduitRun``: plan polyline plus one absolute height per
    vertex. With no path the length is the straight 3D distance between the two ends.
    """

    from_ref: str
    to_ref: str
    role: BondRole
    size: str  # AWG, e.g. "6", "4", "1/0"
    material: ConductorMaterial = "copper"
    bare: bool = True
    path: tuple[Point2D, ...] = ()
    elevations: tuple[Length, ...] | None = None
    description: str = ""


for _name, _obj in (("GroundingStandard", GroundingStandard),
                    ("GroundingElectrode", GroundingElectrode),
                    ("BondingConductor", BondingConductor)):
    register_constructor(_name, _obj)
