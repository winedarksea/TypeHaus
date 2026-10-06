"""Roof blocking connections, selected for their actual wood-to-wood joint."""

from typehaus.hardware.catalog import (
    EXPOSURE_DRY,
    ROLE_DIAPHRAGM_BLOCKING_END_TIE,
    AllowableLoads,
    StructuralHardware,
)

LS30_DIAPHRAGM_BLOCKING_END_TIE = StructuralHardware(
    tag="simpson-ls30-diaphragm-blocking-end-tie",
    name="LS30 skewable angle, diaphragm blocking end",
    role=ROLE_DIAPHRAGM_BLOCKING_END_TIE,
    manufacturer="Simpson Strong-Tie",
    model="LS30",
    exposure=EXPOSURE_DRY,
    source="Simpson C-C-2026 p.313, LS30: one angle at each solid blocking or nailer end, "
           "direct to side-grain wood. The fully nailed diaphragm deck must restrain "
           "rotation before loading a single-angle connection.",
    allowable=AllowableLoads(
        lateral_f1_lb=275.0,
        load_duration_factor=1.6,
        species="SPF / HF; conservative where the block is DF-L and the truss is SPF",
        fasteners="6 - 0.148 in x 1-1/2 in nails per angle, three per leg",
        citation="Simpson Strong-Tie C-C-2026 p.313, LS30, SPF/HF Wind/Seismic (160), "
                 "1-1/2 in nail row. DF/SP reads 320 lbf. A single LS requires the "
                 "carried member to be restrained against rotation.",
    ),
)
