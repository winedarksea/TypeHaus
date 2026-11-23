"""Site-length bolts and lags an HL angle is fixed with (decision #147).

Commodity HDG parts bought by length; ``takeoff/site_bolts.py`` derives the length from the
grip and picks the next stocked one. The knee-brace bolts (``braces.py``) are the precedent.
"""

from typehaus.hardware.catalog import (
    EXPOSURE_TREATED,
    ROLE_SITE_BOLT,
    ROLE_SITE_LAG,
    StructuralHardware,
)

#: Stocked HDG hex bolt and lag lengths, inches: 1/2" steps to 6", then 7, 8, 10, 12.
_STOCK_IN = (4.0, 4.5, 5.0, 5.5, 6.0, 7.0, 8.0, 10.0, 12.0)


def _lengths(prefix: str) -> dict:
    return {length: f"{prefix}X{length:g}-HDG" for length in _STOCK_IN}


def _bolt(dia_in: float, label: str, code: str) -> StructuralHardware:
    return StructuralHardware(
        tag=f"hex-bolt-{code}-hdg-a307-site",
        name=f"{label} in HDG A307 hex bolt with nut and washer",
        role=ROLE_SITE_BOLT, manufacturer="generic", model=f"BOLT-{code}-HDG",
        part_number_by_length_in=_lengths(f"BOLT-{code}"), exposure=EXPOSURE_TREATED,
        finish="hdg", bolt_diameter_in=dia_in,
        source="Hot-dip galvanized hex bolt, ASTM A307 Gr A (HL fn 8: A307 or better), with a "
               "heavy-hex nut and one USS washer under the nut on the wood face; ASTM F2329 "
               "galvanizing (R317.3.1 in treated wood). Length from the grip (decision #147).")


def _lag(dia_in: float, label: str, code: str) -> StructuralHardware:
    return StructuralHardware(
        tag=f"lag-screw-{code}-hdg-site", name=f"{label} in HDG hex lag screw with washer",
        role=ROLE_SITE_LAG, manufacturer="generic", model=f"LAG-{code}-HDG",
        part_number_by_length_in=_lengths(f"LAG-{code}"), exposure=EXPOSURE_TREATED,
        finish="hdg", bolt_diameter_in=dia_in,
        source="Hot-dip galvanized hex lag screw, ASME B18.2.1, with a USS washer; Simpson "
               "C-C-2024 p. 303 HL fn 7: a lag of the bolt's diameter, >= 5 in long, may "
               "replace the bolt.")


#: A DTT pair's rod (catlin's landing, G5): the catalog's deck-to-house lateral detail names
#: "1/2" diameter HDG threaded rod with nuts and washers" (C-C-2026 p. 326). Cut from stock.
TENSION_ROD_12 = StructuralHardware(
    tag="threaded-rod-12-hdg-site", name="1/2 in HDG threaded rod with two nuts and washers",
    role="site_tension_rod", manufacturer="generic", model="ROD-12-HDG",
    part_number_by_length_in={length: f"ROD-12X{length:g}-HDG"
                              for length in (12.0, 18.0, 24.0, 36.0)},
    exposure=EXPOSURE_TREATED, finish="hdg", bolt_diameter_in=0.5,
    source="Hot-dip galvanized 1/2-13 threaded rod (ASTM A307 / F2329), cut to length, two "
           "heavy-hex nuts and two USS washers over the DTT seats' own washers; the length "
           "runs seat to seat plus a washer, nut and two threads past each (decision #147).")

SITE_BOLTS = (
    _bolt(0.5, "1/2", "12"), _bolt(0.75, "3/4", "34"),
    _lag(0.5, "1/2", "12"), _lag(0.75, "3/4", "34"), TENSION_ROD_12,
)
