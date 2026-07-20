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


def _layer_rsi(layer, library: Library, unknown: list[str]) -> float:
    """Series RSI of one layer, parallel-pathed across its cavity fill if it has one.

    A batt between studs is *not* in series with the studs — it is the other path through
    the same depth. Summing both (which a sibling batt layer used to do) overstates a 2x6
    wall by roughly the full cavity R. Area-weighted U per ASHRAE parallel-path:
    ``U = ff*U_framing + (1-ff)*U_fill``.
    """
    from typehaus.quantities import r_us

    mat = library.material(layer.material_ref)
    if mat is None or mat.r_per_inch is None:
        unknown.append(f"{layer.name}({layer.material_ref})")
        return 0.0
    framing_rsi = r_us(mat.r_per_inch * layer.thickness.inches).rsi

    fill = getattr(layer, "cavity", None)
    if fill is None:
        return framing_rsi

    fill_mat = library.material(fill.material_ref)
    if fill_mat is None or fill_mat.r_per_inch is None:
        unknown.append(f"{layer.name}-cavity({fill.material_ref})")
        return 0.0
    fill_thickness = fill.thickness if fill.thickness is not None else layer.thickness
    fill_rsi = r_us(fill_mat.r_per_inch * fill_thickness.inches).rsi
    # A shallower fill leaves still air in the rest of the bay; count only the fill so the
    # result stays conservative rather than crediting an unsealed void.
    if framing_rsi <= 0.0 or fill_rsi <= 0.0:
        return max(framing_rsi, 0.0)
    ff = min(max(fill.framing_factor, 0.0), 1.0)
    u_eff = ff / framing_rsi + (1.0 - ff) / fill_rsi
    return 1.0 / u_eff if u_eff > 0.0 else framing_rsi


def assembly_r_value(asm: Assembly, library: Library, include_lining: bool = True,
                     include_films: bool = True) -> RValueResult:
    """Compute core (+ default_lining) R-value from material r_per_inch (#34)."""
    total_rsi = _FILM_RSI if include_films else 0.0
    unknown: list[str] = []
    layers = list(asm.layers)
    if include_lining:
        layers = list(asm.default_lining) + layers
    for layer in layers:
        total_rsi += _layer_rsi(layer, library, unknown)
    if unknown:
        return RValueResult(value=None, unknown_materials=tuple(unknown))
    return RValueResult(value=rsi(total_rsi), unknown_materials=())
