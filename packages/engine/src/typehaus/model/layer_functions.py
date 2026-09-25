"""One row per :class:`LayerFunction`: every subsystem's answer about a layer's role.

The trade map, the envelope takeoff's billable set, the weather-skin test, the AIA layer and
hatch fallback, the glTF colour, the skin sets and the fastened set each kept their own
table keyed by the enum's value, so a new member needed four edits that failed in three
test files. They now read this one; ``test_layer_function_table`` demands a row per member.
Consumers keep only their NON-function keys (``air_gap``, ``lining``, member categories).
"""

from __future__ import annotations

from dataclasses import dataclass

from typehaus.model.enums import LayerFunction

RGBA = tuple[float, float, float, float]


@dataclass(frozen=True)
class LayerFunctionInfo:
    #: ``emit/trade_rules`` fallback trade (material and scope may still override it).
    trade: str
    #: ``takeoff/envelope`` bills it by area. False is a waiver or a bill elsewhere.
    billable: bool
    #: Closes the building from outboard: laps the rim on a lifted wall (``layer_bands``).
    weather: bool
    #: AIA layer a cut band files under (``emit/draw/palette.aia_layer``).
    aia: str
    #: Hatch family when neither the tag table nor the material names one.
    hatch: str | None
    #: glTF colour; ``None`` falls back to the palette's neutral grey.
    rgba: RGBA | None
    #: Envelope skin on a roof, not roof framing (``emit/gltf/members``).
    roof_skin: bool
    #: Envelope skin whose contacts ``structural.member_interference`` does not grade.
    interference_skin: bool
    #: May carry the structural screw through exterior foam (``hardware/config``).
    fastened: bool
    #: ``emit/finishes`` layer-palette key (else the function falls to FALLBACK_KEY).
    finish_key: bool
    #: ``emit/finishes`` visibility bucket.
    visibility_group: str
    #: Takeoff wording for a member of this category (``takeoff/labels.ROLE_GLOSSARY``).
    role_label: str | None = None


F = LayerFunction
LAYER_FUNCTIONS: dict[LayerFunction, LayerFunctionInfo] = {
    F.STRUCTURE: LayerFunctionInfo(
        trade="framing", billable=False, weather=False, aia="A-WALL", hatch="lumber",
        rgba=(0.62, 0.45, 0.28, 1.0), roof_skin=False, interference_skin=False,
        fastened=False, finish_key=True, visibility_group="structure"),
    F.SHEATHING: LayerFunctionInfo(
        trade="framing", billable=True, weather=True, aia="A-WALL", hatch="osb",
        rgba=(0.72, 0.72, 0.70, 1.0), roof_skin=True, interference_skin=True,
        fastened=True, finish_key=True, visibility_group="sheathing"),
    F.MEMBRANE: LayerFunctionInfo(
        trade="siding", billable=True, weather=True, aia="A-WALL-PATT", hatch="membrane",
        rgba=(0.30, 0.45, 0.55, 1.0), roof_skin=True, interference_skin=True,
        fastened=False, finish_key=True, visibility_group="membrane"),
    # The DRAINAGE trade's: hung by the crew already in the hole, inspected at backfill.
    # Bills like the membrane it protects (a roll of dimpled HDPE, not nothing).
    F.DRAINAGE: LayerFunctionInfo(
        trade="drainage", billable=True, weather=True, aia="A-WALL", hatch=None,
        rgba=None, roof_skin=False, interference_skin=False,
        fastened=False, finish_key=False, visibility_group="other"),
    F.INSULATION: LayerFunctionInfo(
        trade="insulation", billable=True, weather=False, aia="A-WALL-INSU", hatch="batt",
        rgba=(0.93, 0.74, 0.36, 1.0), roof_skin=True, interference_skin=True,
        fastened=False, finish_key=True, visibility_group="insulation"),
    # Air: waived from the area bill. Translucent in glTF — it is the void behind the girts.
    F.AIRGAP: LayerFunctionInfo(
        trade="siding", billable=False, weather=True, aia="A-WALL-PATT", hatch=None,
        rgba=(0.80, 0.85, 0.90, 0.35), roof_skin=True, interference_skin=True,
        fastened=True, finish_key=True, visibility_group="airgap",
        role_label="vent-gap strip"),
    # Bills as lumber in the framing cut list, not by area.
    F.FURRING: LayerFunctionInfo(
        trade="siding", billable=False, weather=False, aia="A-WALL", hatch=None,
        rgba=(0.68, 0.52, 0.34, 1.0), roof_skin=True, interference_skin=True,
        fastened=True, finish_key=True, visibility_group="furring", role_label="furring"),
    F.CLADDING: LayerFunctionInfo(
        trade="siding", billable=True, weather=True, aia="A-WALL", hatch=None,
        rgba=(0.55, 0.58, 0.60, 1.0), roof_skin=True, interference_skin=True,
        fastened=False, finish_key=True, visibility_group="cladding"),
    F.FINISH: LayerFunctionInfo(
        trade="drywall", billable=True, weather=False, aia="A-WALL-FINI", hatch=None,
        rgba=(0.90, 0.89, 0.86, 1.0), roof_skin=True, interference_skin=False,
        fastened=False, finish_key=True, visibility_group="finish"),
}
del F


def info(function: LayerFunction) -> LayerFunctionInfo:
    return LAYER_FUNCTIONS[function]


def values_where(**flags: bool) -> frozenset[str]:
    """Enum values whose row matches every ``flag=value`` given."""
    return frozenset(f.value for f, row in LAYER_FUNCTIONS.items()
                     if all(getattr(row, k) == v for k, v in flags.items()))


def by_value(field: str) -> dict[str, object]:
    """``{enum value: row.<field>}`` for every row whose field is not ``None``."""
    return {f.value: getattr(row, field) for f, row in LAYER_FUNCTIONS.items()
            if getattr(row, field) is not None}
