"""How an Image II eave is sealed, per the April 2026 Installation Guide.

Selected by ``Material.roof_edge_trim_kit``. Every number says whether the manufacturer
publishes it: the guide says "fill" and gives no depth, bead size or coverage, so those are
labelled allowances and stay visible through ``open_items`` until someone closes them.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

_GUIDE = "Image II Installation Guide 4/2026"


class ValueBasis(Enum):
    MANUFACTURER = "manufacturer"
    ESTIMATING_ALLOWANCE = "estimating allowance"


@dataclass(frozen=True)
class SourcedValue:
    value: float
    basis: ValueBasis
    source: str

    @property
    def is_allowance(self) -> bool:
        return self.basis is ValueBasis.ESTIMATING_ALLOWANCE


@dataclass(frozen=True)
class TubeSealant:
    part: str
    name: str
    color: str
    #: ``None`` until a current manufacturer data sheet states it.
    chemistry: str | None
    technical_data_source: str | None
    cartridge_fl_oz: SourcedValue


@dataclass(frozen=True)
class EaveRibSealingSpec:
    kit: str
    treatment: str
    source: str
    sealant: TubeSealant
    tape_part: str
    plug_fill_depth_in: SourcedValue
    hem_bead_diameter_in: SourcedValue
    waste_fraction: SourcedValue

    def open_items(self) -> tuple[str, ...]:
        """What still rests on an allowance or on data nobody has published."""
        items = []
        if self.sealant.chemistry is None or self.sealant.technical_data_source is None:
            items.append(f"{self.sealant.part} chemistry and technical data are unconfirmed")
        for label, sourced in (
            (f"{self.sealant.part} cartridge size", self.sealant.cartridge_fl_oz),
            ("rib plug fill depth", self.plug_fill_depth_in),
            ("hem bead size", self.hem_bead_diameter_in),
            ("sealant waste", self.waste_fraction),
        ):
            if sourced.is_allowance:
                items.append(f"{label} is an estimating allowance: {sourced.source}")
        return tuple(items)


IMAGE_II_EAVE_SEALING = EaveRibSealingSpec(
    kit="IMAGE_II",
    treatment="tube-sealant-plug",
    source=f"{_GUIDE} pp. 26-29 (fill exposed rib ends), p. 31 (bead in the open hem)",
    sealant=TubeSealant(
        part="64032XX",
        name="Image II tube sealant, color match",
        color="color match to the roof panel",
        chemistry=None,
        technical_data_source=None,
        cartridge_fl_oz=SourcedValue(
            10.3, ValueBasis.ESTIMATING_ALLOWANCE,
            "2021 PIM-5 lists a 10.3 oz urethane cartridge; the 2026 catalog lists 3.31 lb "
            "and no package size"),
    ),
    tape_part="6403899",
    plug_fill_depth_in=SourcedValue(
        1.5, ValueBasis.ESTIMATING_ALLOWANCE,
        f"{_GUIDE} gives no depth; set to its 1-1/2 in rib notch (p. 31)"),
    hem_bead_diameter_in=SourcedValue(
        0.25, ValueBasis.ESTIMATING_ALLOWANCE,
        f"{_GUIDE} p. 31 says a continuous bead and gives no size"),
    waste_fraction=SourcedValue(
        0.20, ValueBasis.ESTIMATING_ALLOWANCE, "cartridge tails and tooling loss"),
)

EAVE_RIB_SEALING_BY_KIT = {IMAGE_II_EAVE_SEALING.kit: IMAGE_II_EAVE_SEALING}
