"""Roof blocking connections, selected for their actual wood-to-wood joint."""

from typehaus.hardware.catalog import (
    EXPOSURE_DRY,
    EXPOSURE_TREATED,
    ROLE_DIAPHRAGM_BLOCKING_END_TIE,
    ROLE_MODELED_CONNECTOR,
    AllowableLoads,
    StructuralHardware,
)
from typehaus.library.hardware._common import _SIMPSON
from typehaus.library.hardware.roof_ties import _LTP4_ALLOWABLE

_ZMAX = ("the Z suffix is the ZMAX (G185) coating of the same part; the coating changes "
         "neither the steel nor the nailing")

#: ZMAX at an untreated, roofed joint is the owner's choice for an open canopy (2026-10-06);
#: by wood contact alone this joint is dry, hence the exposure.
LS30Z_DIAPHRAGM_BLOCKING_END_TIE = StructuralHardware(
    tag="simpson-ls30z-diaphragm-blocking-end-tie",
    name="LS30Z skewable angle, diaphragm blocking end",
    role=ROLE_DIAPHRAGM_BLOCKING_END_TIE,
    manufacturer=_SIMPSON,
    model="LS30Z",
    exposure=EXPOSURE_DRY,
    source="Simpson C-C-2026 p.313, LS30: one angle at each solid blocking or nailer end, "
           "direct to side-grain wood, with HDG nails to match the ZMAX coating. The fully "
           "nailed diaphragm deck must restrain rotation before loading a single-angle "
           "connection.",
    allowable=AllowableLoads(
        lateral_f1_lb=275.0,
        load_duration_factor=1.6,
        species="SPF / HF; conservative where the block is LSL and the truss is SPF",
        fasteners="6 - 0.148 in x 1-1/2 in HDG nails per angle, three per leg",
        citation="Simpson Strong-Tie C-C-2026 p.313, LS30, SPF/HF Wind/Seismic (160), "
                 "1-1/2 in nail row. DF/SP reads 320 lbf. A single LS requires the "
                 "carried member to be restrained against rotation. " + _ZMAX,
    ),
)

#: The canopy's collector plates nail into treated glulam: ZMAX with HDG nails (IRC
#: R317.3.1). Simpson publishes no stainless LTP4, so the house's stainless rule yields here.
LTP4Z_LATERAL_TIE_PLATE = StructuralHardware(
    tag="simpson-ltp4z-lateral-tie-plate",
    name="LTP4Z lateral tie plate (ZMAX)",
    role=ROLE_MODELED_CONNECTOR,
    manufacturer=_SIMPSON,
    model="LTP4Z",
    exposure=EXPOSURE_TREATED,
    source="Simpson Strong-Tie LTP4 in ZMAX (strongtie.com/ltp), 12 0.131 in x 1-1/2 in "
           "HDG nails, six per member, where one member is preservative-treated",
    allowable=AllowableLoads(
        lateral_f1_lb=_LTP4_ALLOWABLE.lateral_f1_lb,
        lateral_f2_lb=_LTP4_ALLOWABLE.lateral_f2_lb,
        load_duration_factor=_LTP4_ALLOWABLE.load_duration_factor,
        species=_LTP4_ALLOWABLE.species,
        fasteners=_LTP4_ALLOWABLE.fasteners.replace("(12) 0.131 in x 1 1/2 in",
                                                    "(12) 0.131 in x 1 1/2 in HDG"),
        citation=_LTP4_ALLOWABLE.citation + "; " + _ZMAX,
    ),
)
