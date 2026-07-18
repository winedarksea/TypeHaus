"""Model-level analysis helpers shared by the card and the checks (R-value, etc.).

Tri-state honest (#32): a computation missing an input reports UNKNOWN with the material
named, never a silent zero or a fabricated pass.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.assembly import Assembly
from typehaus.model.plan import Library
from typehaus.quantities import RValue, rsi


@dataclass(frozen=True)
class RValueResult:
    value: RValue | None  # None => UNKNOWN
    unknown_materials: tuple[str, ...]  # layer/material names lacking r_per_inch

    @property
    def known(self) -> bool:
        return self.value is not None

    def fmt(self) -> str:
        if self.value is None:
            missing = ", ".join(self.unknown_materials)
            return f"UNKNOWN (missing r_per_inch: {missing})"
        return self.value.fmt()


# Still-air surface film resistances (RSI), interior + exterior, ASHRAE nominal.
_FILM_RSI = 0.12 + 0.03


def assembly_r_value(asm: Assembly, library: Library, include_lining: bool = True,
                     include_films: bool = True) -> RValueResult:
    """Compute core (+ default_lining) R-value from material r_per_inch (#34)."""
    total_rsi = _FILM_RSI if include_films else 0.0
    unknown: list[str] = []
    layers = list(asm.layers)
    if include_lining:
        layers = list(asm.default_lining) + layers
    for layer in layers:
        mat = library.material(layer.material_ref)
        if mat is None or mat.r_per_inch is None:
            unknown.append(f"{layer.name}({layer.material_ref})")
            continue
        from typehaus.quantities import r_us

        r = r_us(mat.r_per_inch * layer.thickness.inches)
        total_rsi += r.rsi
    if unknown:
        return RValueResult(value=None, unknown_materials=tuple(unknown))
    return RValueResult(value=rsi(total_rsi), unknown_materials=())
