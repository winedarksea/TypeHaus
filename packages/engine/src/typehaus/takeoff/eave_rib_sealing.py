"""Eave sealing quantities: plug and hem-bead volume per run, whole cartridges overall.

A filled rib is a volume, so nothing here is a nominal foot per rib. Rounding happens once,
on the pooled volume of one product, so a small run never buys a whole tube of its own.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import ceil, pi

from typehaus.library.trim.image_ii_eave_sealing import EAVE_RIB_SEALING_BY_KIT
from typehaus.quantities import M_PER_IN

CUBIC_IN_PER_FL_OZ = 1.8046875


@dataclass(frozen=True)
class EaveRunSealing:
    roof_tag: str
    run_key: str
    sealant_part: str
    tape_part: str
    terminations: int
    plug_volume_in3: float
    hem_length_m: float
    hem_volume_in3: float
    tape_length_m: float

    @property
    def tag(self) -> str:
        return f"{self.roof_tag}:{self.run_key}"


@dataclass(frozen=True)
class CartridgeOrder:
    sealant_part: str
    net_volume_in3: float
    gross_volume_in3: float
    cartridges: int
    tags: tuple[str, ...]


def eave_run_sealing(model) -> tuple[EaveRunSealing, ...]:
    """One row per run that has a sealing specification; unresolved ends bill nothing."""
    rows = []
    for run in getattr(model, "eave_sealing_runs", ()):
        spec = EAVE_RIB_SEALING_BY_KIT.get(run.kit)
        if spec is None:
            continue
        treated = sum(1 for end in run.rib_ends if end.treatment is not None)
        area_in2 = run.rib_cavity_area_m2 / M_PER_IN ** 2
        bead_in2 = pi * spec.hem_bead_diameter_in.value ** 2 / 4
        rows.append(EaveRunSealing(
            run.roof_tag, run.run_key, spec.sealant.part, spec.tape_part, treated,
            treated * area_in2 * spec.plug_fill_depth_in.value, run.hem_length_m,
            run.hem_length_m / M_PER_IN * bead_in2, run.tape_length_m))
    return tuple(rows)


def cartridge_orders(model) -> tuple[CartridgeOrder, ...]:
    """Whole cartridges per sealant product, after waste, pooled across runs."""
    specs = {spec.sealant.part: spec for spec in EAVE_RIB_SEALING_BY_KIT.values()}
    runs = eave_run_sealing(model)
    orders = []
    for part in sorted({run.sealant_part for run in runs}):
        pooled = [run for run in runs if run.sealant_part == part]
        spec = specs[part]
        net = sum(run.plug_volume_in3 + run.hem_volume_in3 for run in pooled)
        gross = net * (1 + spec.waste_fraction.value)
        capacity = spec.sealant.cartridge_fl_oz.value * CUBIC_IN_PER_FL_OZ
        orders.append(CartridgeOrder(part, net, gross, ceil(gross / capacity),
                                     tuple(run.tag for run in pooled)))
    return tuple(orders)
