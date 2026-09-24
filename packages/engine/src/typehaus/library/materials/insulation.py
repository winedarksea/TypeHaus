"""Insulation: batts, boards, sprayed and blown."""

from __future__ import annotations

from typehaus.library.materials._common import _UAF
from typehaus.model import Material

MATERIALS: tuple[Material, ...] = (
    Material(
        tag="polyiso",
        name="Polyisocyanurate CI",
        r_per_inch=5.6,
        perm_rating=1.0,
        hatch="rigid",
        color="#e8d64f",
        foam_plastic=True,
        air_impermeable=True,
        source=f"{_UAF}: 'Expanded polyurethane, R-11, board stock' 0.4-1.6 perm-in; "
        "midpoint of the published range",
    ),
    Material(
        tag="fiberglass",
        name="Fiberglass batt",
        r_per_inch=3.7,
        perm_rating=116.0,
        hatch="batt",
        color="#f3c6d0",
        source="AHFC Alaska Building Manual Appendix 2: 100 mm (4 in.) glass fibre "
        "wool 28.97 perm = 116 perm-in",
    ),
    Material(
        tag="mineral-wool",
        name="Mineral wool batt",
        r_per_inch=4.2,
        perm_rating=116.0,
        hatch="batt",
        color="#c7c2bd",
        source=f"{_UAF}: 'Mineral wool, unprotected' 116 perm-in; AHFC Appendix 2 "
        "gives 28.97 perm at 100 mm (4 in.), the same 116 perm-in",
    ),
    # Closed-cell (2 lb) spray polyurethane foam — what fills a rim cavity that no sheet
    # membrane can reach. It is the insulation, the air barrier AND the vapour retarder in
    # one bonded, seamless application, which is exactly why it is specified where a floor
    # band interrupts a wall's control layers: 3" runs about 0.53 perm, a Class II retarder,
    # with no seam to fail. `resolve/construction_rim.py` bills it by the lineal foot of rim.
    Material(
        tag="closed-cell-spray-foam",
        name="Closed-cell spray polyurethane foam (2 lb)",
        r_per_inch=6.5,
        density=32.0,
        perm_rating=1.6,
        hatch="batt",
        color="#e8d9b5",
        foam_plastic=True,
        air_impermeable=True,
        source="published ccSPF range R-5.9 to R-7.0 per inch and ASTM E96 permeance "
        "1.2-2.0 perm at 1 in.; midpoints of the published ranges, per this "
        "file's convention",
    ),
    Material(
        tag="icf-eps",
        name="ICF EPS form",
        r_per_inch=4.0,
        perm_rating=3.9,
        hatch="rigid",
        color="#f0f0e6",
        foam_plastic=True,
        source=f"{_UAF}: 'Expanded polystyrene, bead' 2.0-5.8 perm-in; midpoint of "
        "the published range",
    ),
    Material(
        tag="eps",
        name="EPS rigid insulation",
        r_per_inch=4.0,
        perm_rating=3.9,
        hatch="rigid",
        color="#eef0f2",
        foam_plastic=True,
        source=f"{_UAF}: 'Expanded polystyrene, bead' 2.0-5.8 perm-in (midpoint); "
        'Type II datasheets publish 5.0 perm at 1", inside that band',
    ),
    Material(
        tag="xps",
        name="XPS rigid insulation",
        r_per_inch=5.0,
        perm_rating=1.2,
        hatch="rigid",
        color="#f2b8c6",
        foam_plastic=True,
        source=f"{_UAF}: 'Expanded polystyrene, extruded' 1.2 perm-in; Owens Corning "
        'FOAMULAR publishes 1.1 perm max at 1" by ASTM E96',
    ),
    # Intrinsic catalog facts are shared; each assembly carries its own thickness and use.
    Material(
        tag="eps-deck-form",
        name="BuildDeck EPS deck form",
        r_per_inch=2.9,
        perm_rating=3.9,
        hatch="rigid",
        color="#f0f0e6",
        foam_plastic=True,
        source=(
            "BuildDeck installed-section R-values; EPS permeance from ASHRAE/UAF bead-EPS range."
        ),
    ),
    Material(
        tag="pet-felt-panel",
        name='PET acoustic felt panel, 1/2" (9mm+ compressed)',
        r_per_inch=3.5,
        density=200.0,
        perm_rating=10.0,
        hatch="insulation",
        color="#6f7a72",
        finish="felted",
        source="Recycled-PET architectural acoustic panel technical data.",
    ),
    _POLYISO_FOIL := Material(
        tag="polyiso-foil",
        name="Foil-faced polyisocyanurate",
        r_per_inch=6.0,
        perm_rating=0.03,
        hatch="rigid",
        color="#d9d2a8",
        foam_plastic=True,
        source="Foil-faced polyisocyanurate product data.",
    ),
    Material(
        tag="blown-fiberglass",
        name="Blown (loose-fill) fiberglass",
        r_per_inch=2.5,
        perm_rating=116.0,
        hatch="batt",
        color="#f6d9e1",
        source="NAIMA/manufacturer loose-fill fiberglass settled-density data.",
    ),
    Material(
        tag="fiberglass-r19",
        name='Fiberglass batt, R-19 (6-1/4")',
        r_per_inch=3.04,
        perm_rating=116.0,
        hatch="batt",
        color="#f3c6d0",
        source="R-19 fiberglass batt published loft and R-value.",
    ),
    Material(
        tag="fiberglass-r30c",
        name='Fiberglass cathedral batt, R-30C compressed to 6-7/8"',
        r_per_inch=3.78,
        perm_rating=116.0,
        hatch="batt",
        color="#f3c6d0",
        source="Manufacturer compressed-batt R-value charts for R-30 cathedral batts.",
    ),
    # Polyiso foil-faced on BOTH faces with its own interior-exposure listing: the one board
    # here that may stand in a room without a thermal barrier (IRC R316.6 specific approval),
    # which is why it is a separate row and not the generic ``polyiso-foil`` above. The
    # thermal numbers are ``polyiso-foil``'s; the published R-6.5/in is not claimed.
    _POLYISO_FOIL.model_copy(update={
        "tag": "polyiso-foil-thermax",
        "name": "DuPont Thermax Sheathing, foil-faced polyiso",
        "thermal_barrier_listing": (
            "Intertek CCRR-0435 (rev. 2026-06-19) §5.5: Thermax boards may be installed "
            "without the IRC R316.4 / IBC 2603.4 thermal barrier; §5.1: max 4 in., any wall "
            "or floor/ceiling assembly, any type of structure, interior fasteners max 24 in. "
            "o.c. across / 48 in. along the board (NFPA 286, UL 1715)"),
        "source": (
            "DuPont Thermax Sheathing PIS 43-D100094 (2025-07-25): R-13 at 2 in., 0.03 perm, "
            "1 mil aluminum both faces; max use temperature 250 F per Thermax Heavy Duty PIS "
            "43-D100093"),
    }),
)
