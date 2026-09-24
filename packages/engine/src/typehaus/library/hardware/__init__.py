"""Shared structural connection hardware — the parts the hardware take-off bills.

Each item is the *published product family*, keyed by the condition (role) the resolved
model derives, so a house never names a part number in its plan source. Sources cite the
manufacturer system the record describes; no rating here is estimated.

**Allowable loads.** Some items carry an ``AllowableLoads`` record
transcribed from a named evaluation report. Three rules govern every one of them, and they
are the reason the field exists at all rather than a "capacity" column somebody fills in:

1. **A number is copied, never derived.** Nothing here is interpolated, converted, scaled
   from a similar part, or reasoned to. If a report does not print it, the field is ``None``.
2. **``None`` is a finding, not a blank.** Four parts below carry an ``AllowableLoads`` whose
   every value is ``None``. Each one names the document that was read and says why it came
   back empty — an unevaluated part number, a scope exclusion, a value that depends on an
   input this model does not carry. That is a materially different statement from "nobody has
   looked", which is what ``allowable=None`` (the default) means.
3. **The species column is load-bearing.** Simpson tabulate against specific gravity. Catlin
   frames in SPF (SG 0.42) and several of these reports publish only DF/SP (SG 0.50) values.
   Where a report gives both, the SPF/HF figure is what is recorded; where it gives only the
   0.50 value, that is recorded *and said so*, because using it for SPF is an unconservative
   error that no amount of care downstream can detect.

Every one of these was pulled from the report itself, not from a retailer listing. That
distinction turned out to matter: several retailers cite ESR-1622 for the ABU66SS, and
ESR-1622 does not cover it. **What covers it is a Simpson engineering letter rather than a
code report** — see ``_L_F_SSNAILS`` below. A stainless connector is rated at its carbon
twin's published loads; the only thing stainless costs is NAIL withdrawal, and a ring-shank
substitution buys that back. Two records in this file said "unrated" for two years on the
strength of having read the code report and stopped there.
"""

from __future__ import annotations

from typehaus.library.hardware.braces import (
    APVB_BRACE_BOLT,
    APVKB_KNEE_BRACE,
    LAPPED_BRACE_BOLT,
)
from typehaus.library.hardware.fasteners import (
    FASTENMASTER_TIMBERLOK,
    SDPW19_DEFLECTOR_SCREW,
    SDPW_DEFLECTOR_SCREW,
    SDWH_TIMBER_HEX_SCREW,
    SDWS_TIMBER_SCREW,
)
from typehaus.library.hardware.roof_ties import (
    H10ASS_HURRICANE_TIE,
    H25A_HURRICANE_TIE,
    H25ASS_HURRICANE_TIE,
    H25AZ_HURRICANE_TIE,
    HETA20Z_EMBEDDED_BEAM_ANCHOR,
    HGAM10_MASONRY_GUSSET,
    LS30_GABLE_END_TIE,
    LTP4_GABLE_TRUSS_ANCHOR,
    LTP4_LATERAL_TIE_PLATE,
    SILL_ANCHOR_BOLT,
)
from typehaus.library.hardware.s5 import (
    S5_CANDUIT_PIPE_CLAMP,
    S5_COLORGARD_SNOW_RETENTION,
    S5_N_NAIL_STRIP_CLAMP,
    S5_S_SNAP_LOCK_CLAMP,
    S5_SEAM_CLAMP,
)
from typehaus.library.hardware.simpson_hangers import (
    HHUS410_SCL_FACE_MOUNT_HANGER,
    HU28_2Z_FACE_MOUNT_HANGER,
    HU212_3_FACE_MOUNT_HANGER,
    HUC212_3_CONCRETE_HANGER,
    HUC_CONCRETE_HANGER,
    HUCQ_CONCRETE_HANGER,
    IUS_FACE_MOUNT_HANGER,
    LSCZ_STRINGER_CONNECTOR,
    LSSR_SLOPED_HANGER,
    LSTA24_RIDGE_STRAP,
    LUS210Z_FACE_MOUNT_HANGER,
    LUS_FACE_MOUNT_HANGER,
    LUSZ_FACE_MOUNT_HANGER,
    THA_FLOOR_TRUSS_HANGER,
)
from typehaus.library.hardware.simpson_post_bases import (
    ABU44_POST_BASE,
    ABU66SS_POST_BASE,
    ABU_POST_BASE,
    CCQ46SDS_POST_CAP,
    L50Z_POST_TENSION_ANGLE,
    LUS210SS_FACE_MOUNT_HANGER,
    MSTA12Z_POST_TENSION_STRAP,
    PC6Z_POST_CAP,
    POST_BASE_ANCHOR_BOLT,
)
from typehaus.library.hardware.simpson_ties import (
    CS16_COIL_STRAP,
    DTT2Z_FLOOR_TIE,
    MASA_MUDSILL_ANCHOR,
    SP4_STUD_PLATE_TIE,
    SP6_STUD_PLATE_TIE,
    STHD14_STRAP_HOLDOWN,
    STHD14RJ_STRAP_HOLDOWN,
    STHD_STRAP_HOLDOWN,
)
from typehaus.library.hardware.specialty import (
    BEARING_STANDOFF_SHIM,
    DECK_EQUIPMENT_ANCHOR,
    EQUIPMENT_PAD_ANCHOR,
    EXPOSED_FASTENER_PANEL_SCREW,
    KBS1Z_KNEE_BRACE,
    KBS_BEAM_HOLD_DOWN,
    POCKET_FRAME_KIT_1500PF,
    POCKET_FRAME_KIT_HEAVY,
    POLY_PANEL_FASTENER,
    S5_PV_KIT,
    THDSS_LEDGER_ANCHOR,
    THROUGH_PANEL_PIPE_STRAP,
)
from typehaus.library.hardware.ties import TIE_HARDWARE

STRUCTURAL_HARDWARE: tuple = (
    SDWS_TIMBER_SCREW,
    SDWH_TIMBER_HEX_SCREW,
    SDPW_DEFLECTOR_SCREW,
    SDPW19_DEFLECTOR_SCREW,
    FASTENMASTER_TIMBERLOK,
    LSSR_SLOPED_HANGER,
    LSCZ_STRINGER_CONNECTOR,
    LSTA24_RIDGE_STRAP,
    LUS_FACE_MOUNT_HANGER,
    LUSZ_FACE_MOUNT_HANGER,
    IUS_FACE_MOUNT_HANGER,
    HHUS410_SCL_FACE_MOUNT_HANGER,
    THA_FLOOR_TRUSS_HANGER,
    HUC_CONCRETE_HANGER,
    APVB_BRACE_BOLT,
    MASA_MUDSILL_ANCHOR,
    STHD_STRAP_HOLDOWN,
    DTT2Z_FLOOR_TIE,
    SP4_STUD_PLATE_TIE,
    SP6_STUD_PLATE_TIE,
    CS16_COIL_STRAP,
    ABU_POST_BASE,
    ABU44_POST_BASE,
    MSTA12Z_POST_TENSION_STRAP,
    L50Z_POST_TENSION_ANGLE,
    POST_BASE_ANCHOR_BOLT,
    PC6Z_POST_CAP,
    CCQ46SDS_POST_CAP,
    LTP4_LATERAL_TIE_PLATE,
    SILL_ANCHOR_BOLT,
    H25A_HURRICANE_TIE,
    H25AZ_HURRICANE_TIE,
    LS30_GABLE_END_TIE,
    LTP4_GABLE_TRUSS_ANCHOR,
    HGAM10_MASONRY_GUSSET,
    HETA20Z_EMBEDDED_BEAM_ANCHOR,
    S5_SEAM_CLAMP,
    S5_S_SNAP_LOCK_CLAMP,
    S5_N_NAIL_STRIP_CLAMP,
    S5_CANDUIT_PIPE_CLAMP,
    S5_PV_KIT,
    S5_COLORGARD_SNOW_RETENTION,
    KBS_BEAM_HOLD_DOWN,
    KBS1Z_KNEE_BRACE,
    LAPPED_BRACE_BOLT,
    POLY_PANEL_FASTENER,
    DECK_EQUIPMENT_ANCHOR,
    BEARING_STANDOFF_SHIM,
    EQUIPMENT_PAD_ANCHOR,
    EXPOSED_FASTENER_PANEL_SCREW,
    THROUGH_PANEL_PIPE_STRAP,
    POCKET_FRAME_KIT_1500PF,
    POCKET_FRAME_KIT_HEAVY,
    *TIE_HARDWARE,
)


#: Parts this catalog holds a **capacity record** for without billing them.
#:
#: ``STRUCTURAL_HARDWARE`` above is the BOM's catalog: every item in it is something the
#: take-off can select and order, and adding to it changes what a house buys. This tuple is
#: for the other case — a part number that appears in a house's plan source or in a
#: published table and whose allowable load somebody needs to be able to look up, without it
#: becoming a purchasable role. ``allowable_for_model`` searches both; nothing else does.
#:
#: The ABU66SS is here because ``hardware_by_model("ABU66SS")`` prefix-matches the galvanised
#: ABU66, and a reader asking "what is this base rated for" must not be handed the wrong
#: report's numbers. Keeping it out of ``STRUCTURAL_HARDWARE`` keeps every BOM line, role
#: lookup and price row exactly where it was.
CAPACITY_ONLY_RECORDS: tuple = (
    ABU66SS_POST_BASE,
    STHD14RJ_STRAP_HOLDOWN,
    STHD14_STRAP_HOLDOWN,
    H25ASS_HURRICANE_TIE,
    H10ASS_HURRICANE_TIE,
    THDSS_LEDGER_ANCHOR,
    APVKB_KNEE_BRACE,
    HUCQ_CONCRETE_HANGER,
    HUC212_3_CONCRETE_HANGER,
    HU212_3_FACE_MOUNT_HANGER,
    HU28_2Z_FACE_MOUNT_HANGER,
    LUS210Z_FACE_MOUNT_HANGER,
    LUS210SS_FACE_MOUNT_HANGER,
)
