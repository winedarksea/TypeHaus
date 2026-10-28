"""The formed-metal trim record shared by the manufacturer modules in this package."""

from dataclasses import dataclass


@dataclass(frozen=True)
class TrimProfile:
    name: str
    part_numbers: tuple[tuple[int, str, float, str], ...] = ()
    stock_lengths_in: tuple[float, ...] = (122.0,)
    section_in: tuple[tuple[float, float], ...] = ()
    receiver_throat_in: float | None = None
    min_lap_in: float = 2.0
    hem_notch_in: float = 0.0
    closure: str | None = None
    fastener_role: str = "trim_stitch_screw"
    fastener_spacing_in: float = 12.0
    fastener_rows: int = 1
    #: Extra fasteners through each lap (PBR corner laps are riveted 2 in o.c.; BBD75 takes none).
    lap_fasteners: int = 0
    source: str = ""
    custom: bool = False
    maker: str = "Metal Sales"


def pvdf(number: str, length: float = 122.0) -> tuple[tuple[int, str, float, str], ...]:
    return ((24, "PVDF", length, number),)
