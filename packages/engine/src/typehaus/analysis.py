"""Model-level analysis helpers shared by the card and the checks (R-value, etc.).

Tri-state honest (#32): a computation missing an input reports UNKNOWN with the material
named, never a silent zero or a fabricated pass.
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.assembly import Assembly
from typehaus.model.enums import LayerFunction
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

    fills = getattr(layer, "cavity_fills", ())
    if not fills:
        return framing_rsi

    # Several fills in one bay (flash-and-batt) are in SERIES with each other and in
    # PARALLEL with the framing, which runs past all of them: 5" of ccSPF plus 6-7/8" of
    # batt is one 11-7/8" bay path, not two bays. Summing their R and then parallel-pathing
    # once against the full-depth framing is the only reading that keeps the joist a single
    # thermal bridge instead of counting it twice.
    fill_rsi = 0.0
    for fill in fills:
        fill_mat = library.material(fill.material_ref)
        if fill_mat is None or fill_mat.r_per_inch is None:
            unknown.append(f"{layer.name}-cavity({fill.material_ref})")
            return 0.0
        fill_thickness = layer.cavity_thickness(fill)
        fill_rsi += r_us(fill_mat.r_per_inch * fill_thickness.inches).rsi
    # A shallower fill leaves still air in the rest of the bay; count only the fill so the
    # result stays conservative rather than crediting an unsealed void.
    if framing_rsi <= 0.0 or fill_rsi <= 0.0:
        return max(framing_rsi, 0.0)
    ff = layer.cavity_framing_factor
    u_eff = ff / framing_rsi + (1.0 - ff) / fill_rsi
    return 1.0 / u_eff if u_eff > 0.0 else framing_rsi


def assembly_r_value(asm: Assembly, library: Library, include_lining: bool = True,
                     include_films: bool = True) -> RValueResult:
    """Compute core (+ default_lining) R-value from material r_per_inch (#34).

    Walks ``Assembly.depth_layers()``, not every authored layer: the regions of a split row
    (``Layer.slot``) are side by side up the wall, not in series through it, so adding all of
    them would report a four-colour brick wythe at four wythes' worth of R. What this reports
    for such a row is the FIRST region's — a split row's R genuinely varies with elevation,
    and a single number for the assembly can only be one of them. Same simplification a
    banded layer has always had here.
    """
    total_rsi = _FILM_RSI if include_films else 0.0
    unknown: list[str] = []
    layers = list(asm.depth_layers())
    if include_lining:
        layers = list(asm.default_lining) + layers
    for layer in layers:
        total_rsi += _layer_rsi(layer, library, unknown)
    if unknown:
        return RValueResult(value=None, unknown_materials=tuple(unknown))
    return RValueResult(value=rsi(total_rsi), unknown_materials=())


# The framing solver's o.c. default when a STRUCTURE layer's FramingSpec leaves it open;
# reported so the delta compare never shows a blank spacing for an authored-by-omission wall.
DEFAULT_FRAMING_SPACING_IN = 16.0


@dataclass(frozen=True)
class AssemblyMetrics:
    """The comparable facts of one assembly — the delta-compare row's data (#53, → 21b).

    Model-free like the section card itself: everything here reads off the authored
    ``Assembly``, so two candidate assemblies can be weighed against each other before
    either is placed on a wall. ``stc`` stays None unless the assembly carries a lab test
    (#50) — an acoustic number is never computed.
    """

    tag: str
    r_value: RValueResult
    thickness_in: float
    layer_count: int
    structure_member: str | None       # nominal lumber size of the STRUCTURE layer, e.g. "2x6"
    framing_spacing_in: float | None   # o.c. of that layer's framing
    stc: int | None
    variant_of: str | None

    def as_dict(self) -> dict:
        return {
            "tag": self.tag,
            "r_value": (round(self.r_value.value.r_us, 3)
                        if self.r_value.value is not None else None),
            "r_value_unknown_materials": list(self.r_value.unknown_materials),
            "thickness_in": round(self.thickness_in, 4),
            "layer_count": self.layer_count,
            "structure_member": self.structure_member,
            "framing_spacing_in": self.framing_spacing_in,
            "stc": self.stc,
            "variant_of": self.variant_of,
        }


def assembly_metrics(asm: Assembly, library: Library) -> AssemblyMetrics:
    """Roll one assembly up to the numbers a designer compares alternatives on.

    Thickness sums the whole built stack (default lining + core) because that is what the
    hallway loses; cavity fill is deliberately excluded — it lives *inside* its host layer's
    depth (→ :class:`CavityFill`) and adding it would double-count the wall.
    """
    # depth_layers(), so a split row (`Layer.slot`) counts once — see assembly_r_value.
    stack = list(asm.default_lining) + list(asm.depth_layers())
    structure = next((ly for ly in stack if ly.function is LayerFunction.STRUCTURE), None)
    spec = structure.framing if structure is not None else None
    spacing_in = None
    if spec is not None:
        spacing_in = (spec.spacing.inches if spec.spacing is not None
                      else DEFAULT_FRAMING_SPACING_IN)
    return AssemblyMetrics(
        tag=asm.tag,
        r_value=assembly_r_value(asm, library),
        thickness_in=sum(layer.thickness.inches for layer in stack),
        layer_count=len(stack),
        structure_member=spec.member if spec is not None else None,
        framing_spacing_in=spacing_in,
        stc=asm.stc,
        variant_of=asm.variant_of,
    )
