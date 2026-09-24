"""Structural screws through exterior insulation and deflection screws.

Split out of the former ``library/hardware.py``; see the package docstring.
"""

from __future__ import annotations

from typehaus.hardware.catalog import (
    EXPOSURE_DRY,
    ROLE_EXTERIOR_INSULATION_SCREW,
    ROLE_GIRT_STANDOFF_SCREW,
    ROLE_PARTITION_DEFLECTION_SCREW,
    AllowableLoads,
    StructuralHardware,
)
from typehaus.library.hardware._common import _SIMPSON

# Structural wood screws through continuous exterior insulation. Two families cover the
# range: the 0.220" SDWS Timber Screw up to 8" (a wall's foam sandwich), and the 0.190"
# SDWH Timber-Hex beyond it (a roof's, which carries far more foam). Only one family may
# serve the role at a given length, so the two ladders must not overlap.
SDWS_TIMBER_SCREW = StructuralHardware(
    tag="simpson-sdws-timber-screw",
    name="SDWS Timber Screw (0.220 in shank)",
    role=ROLE_EXTERIOR_INSULATION_SCREW,
    manufacturer=_SIMPSON,
    model="SDWS22___DB",
    part_number_by_length_in={
        3.0: "SDWS22300DB", 4.0: "SDWS22400DB", 5.0: "SDWS22500DB",
        6.0: "SDWS22600DB", 8.0: "SDWS22800DB",
    },
    # IAPMO UES ER-192 Table 7: every SDWS22 threads 3 in, whatever its overall length. That
    # is why this family cannot serve a girt crossing — at 8 in over a 6 in clamped stack,
    # 1 in of that thread stands inside the members it is supposed to be pulling together.
    thread_length_in_by_length_in={
        3.0: 3.0, 4.0: 3.0, 5.0: 3.0, 6.0: 3.0, 8.0: 3.0,
    },
    source="Simpson Strong-Tie SDWS Timber Screw product family (strongtie.com/sdws) — "
           "0.220 in shank structural wood screw, Double-Barrier coated (DB); thread "
           "lengths per IAPMO UES ER-192 Table 7",
)

# The girt crossing screw, and the only member of its role. Chosen on THREAD, not length:
# 2 in of thread on an 8 in screw leaves 6 in of plain shank to span the 6 in clamped stack
# (girt 1-1/2 in + three-ply block 4-1/2 in), so every turn of the thread is pulling the
# stack together rather than standing in it. See ``engineering/girt_screw.py``.
FASTENMASTER_TIMBERLOK = StructuralHardware(
    tag="fastenmaster-timberlok",
    name="TimberLOK heavy-duty wood screw (0.189 in shank)",
    role=ROLE_GIRT_STANDOFF_SCREW,
    manufacturer="FastenMaster",
    model="TLOK",
    part_number_by_length_in={6.0: "TLOK06", 8.0: "TLOK08", 10.0: "TLOK10"},
    thread_length_in_by_length_in={6.0: 2.0, 8.0: 2.0, 10.0: 2.0},
    source="FastenMaster TimberLOK, ICC-ES ESR-1078 (reissued 2026-01) Table 1A — 2 in "
           "thread at every length; coating rated for ACQ-D <= 0.40 pcf per §4.1.7 / "
           "Table 6",
)

# The two SDPW records are ONE role on two shank diameters — the same non-overlapping ladder
# SDWS/SDWH make above. What picks between them here is NOT length, though: it is the
# TOP-PLATE condition each is published for, which is why both carry ``fits_nominal`` and why
# ``takeoff/partition_fasteners.py`` selects with ``hardware_for_role_and_nominal``.
#
# ** THIS IS THE ONE SCREW HERE THAT MUST NOT CLAMP. ** A polymer sleeve on the shank holds a
# non-bearing partition's top plate a set distance below the joist or rafter over it, so the
# deck deflects onto nothing while the wall stays braced against out-of-plane load. The gap is
# "the space between the top surface of the top plate and the lower surface of the supporting
# members", and Simpson warn that a 0" gap "may result in unintended loading of the partition
# wall". The offset driver bit in the carton is what sets it.
#
# Installation facts that are constraints, not trivia (C-F-2025TECHSUP p. 100): the top plate
# is PREDRILLED 3/8"; the supporting member is NOT predrilled; "the polymer sleeve shall not
# penetrate the supporting member"; and the supporting member must be at least as thick as the
# minimum penetration. A wall running parallel to and BETWEEN the framing above must be
# fastened to code-prescribed blocking — which is the third case the take-off counts.
#
# ``thread_length_in_by_length_in`` is populated because ER-192 publishes it, but the
# clamped-stack rule it feeds is inapplicable to this part by design.
_SDPW_ALLOWABLE_NOTE = (
    "Allowable lateral load, ASD, C_D = 1.6 (safety factor 5.0), at the 3/4 in gap this "
    "house builds — IAPMO UES ER-192 Table 37 / C-F-2025TECHSUP pp. 100-101. The table is "
    "indexed by GAP and by OFFSET (head clear of the plate), not by direction, and F1 "
    "(parallel to the top plate) and F2 (perpendicular) read the same cell, which is why "
    "both fields below carry it. Uplift is deliberately absent and must stay absent: this "
    "joint releases vertically, which is the entire point of the sleeve."
)

SDPW_DEFLECTOR_SCREW = StructuralHardware(
    tag="simpson-sdpw-deflector-screw",
    name="Strong-Drive SDPW DEFLECTOR screw (0.140 in shank)",
    role=ROLE_PARTITION_DEFLECTION_SCREW,
    manufacturer=_SIMPSON,
    model="SDPW14___",
    exposure=EXPOSURE_DRY,
    part_number_by_length_in={3.5: "SDPW14312", 5.0: "SDPW14500"},
    thread_length_in_by_length_in={3.5: 2.0, 5.0: 2.0},
    fits_nominal=("single 2x top plate", "built-up top plate to 2-1/4 in"),
    source="Simpson Strong-Tie Strong-Drive SDPW DEFLECTOR screw, IAPMO UES ER-192 "
           "(rev. 2026-09-08) and Fastening Systems Technical Guide C-F-2025TECHSUP "
           "pp. 100-101 — washer-head 6-lobe T-25 screw with a polypropylene sleeve "
           "(1.38 in on the 3-1/2 in, blue; 2.88 in on the 5 in, orange) setting a "
           "deflection gap at a non-bearing partition's top plate. Type 17 point, e-coat, "
           "INTERIOR DRY SERVICE ONLY (dry-service treatment chemicals and FRT wood are "
           "permitted). Cartons of 50 (-R50) include the offset driver bit; PWKIT25T is "
           "the replacement bit kit. Minimum penetration into the supporting member 1/2 in, "
           "point included. Published gap capacity up to 3/4 in on the 3-1/2 in and 1-1/2 "
           "in on the 5 in. **This record's allowables and spacings are published for a "
           "single 2x or a built-up top plate to 2-1/4 in — NOT for a double 2x**, which "
           "is the SDPW19600's row below",
    allowable=AllowableLoads(
        lateral_f1_lb=140.0,
        lateral_f2_lb=140.0,
        load_duration_factor=1.6,
        species="SPF (minimum specific gravity 0.42); ER-192 Table 37 covers SPF/HF/DFL/SP "
                "and the value recorded is the one that applies to what is built here. An "
                "I-joist flange must be at least 1-1/8 in thick",
        fasteners="The screw IS the fastener: one SDPW14500 through a predrilled 3/8 in "
                  "hole in the top plate, the supporting member undrilled, the sleeve "
                  "stopping short of it. 140 lbf is the 2x + 3/4 in WSP top-plate row at "
                  "0 in offset and a 1/2 in, 3/4 in or 1-1/2 in gap; at a 3/4 in offset "
                  "the same row falls to 105 / 80 / 45 lbf",
        citation=_SDPW_ALLOWABLE_NOTE,
    ),
)

#: The 0.195 in rung — a different shank, point, pilot and DRIVER (T-40, bit kit PWKIT40T).
#: **It is this house's screw, and not because of its length.** Simpson publish the
#: SDPW19600's allowables and spacing for the DOUBLE 2x top plate; the 5 in screw's stop at a
#: 2-1/4 in built-up plate. Catlin frames a double 2x on all eleven interior assemblies.
SDPW19_DEFLECTOR_SCREW = StructuralHardware(
    tag="simpson-sdpw19-deflector-screw",
    name="Strong-Drive SDPW DEFLECTOR screw (0.195 in shank)",
    role=ROLE_PARTITION_DEFLECTION_SCREW,
    manufacturer=_SIMPSON,
    model="SDPW19___",
    exposure=EXPOSURE_DRY,
    part_number_by_length_in={6.0: "SDPW19600"},
    thread_length_in_by_length_in={6.0: 3.0},
    fits_nominal=("double 2x top plate",),
    source="Simpson Strong-Tie Strong-Drive SDPW DEFLECTOR screw, IAPMO UES ER-192 "
           "(rev. 2026-09-08) and C-F-2025TECHSUP pp. 100-101 — the 6 in length on the "
           "0.195 in shank, sawtooth point, 6-lobe T-40, 3.10 in gray sleeve, e-coat, "
           "interior dry service, cartons of 50 (-R50) with the offset bit. Minimum "
           "penetration into the supporting member 3/4 in, point included; gap capacity to "
           "1-1/2 in. **The row published for a DOUBLE 2x top plate and thinner**, which "
           "is why this and not the 5 in is the part at a 3 in plate stack",
    allowable=AllowableLoads(
        lateral_f1_lb=165.0,
        lateral_f2_lb=165.0,
        load_duration_factor=1.6,
        species="SPF (minimum specific gravity 0.42); ER-192 Table 37 covers SPF/HF/DFL/SP. "
                "The supporting members here are engineered — 11-7/8 in TJI 230 rafters, "
                "I-joists and open-web floor trusses — which ER-192 permits (dimension "
                "lumber, truss, I-joist, glulam, SCL or CLT) at a flange thickness of at "
                "least 1-1/8 in. **The joist maker's own fastener rules have NOT been read**",
        fasteners="One SDPW19600 through a predrilled 3/8 in hole in the double top plate, "
                  "the supporting member undrilled. 165 lbf is the (2) 2x row at a 3/4 in "
                  "gap, IDENTICAL at 0 in and 3/4 in offset; the same row reads 295 lbf at "
                  "a 0 in gap, 205 at 1/2 in and 75 at 1-1/2 in. The companion MAXIMUM "
                  "SPACING table (8 ft / 10 ft walls at 5 psf, C_D = 1.6) bottoms out at "
                  "42 in / 36 in for this part, which every count this house bills sits "
                  "inside",
        citation=_SDPW_ALLOWABLE_NOTE,
    ),
)

SDWH_TIMBER_HEX_SCREW = StructuralHardware(
    tag="simpson-sdwh-timber-hex-screw",
    name="SDWH Timber-Hex Screw (0.190 in shank)",
    role=ROLE_EXTERIOR_INSULATION_SCREW,
    manufacturer=_SIMPSON,
    model="SDWH19____DB",
    part_number_by_length_in={10.0: "SDWH191000DB", 12.0: "SDWH191200DB"},
    source="Simpson Strong-Tie SDWH Timber-Hex Screw product family "
           "(strongtie.com/sdwh) — long-length structural wood screw for thick "
           "exterior-insulation assemblies",
)

# **Sloped-only and skewed are two different rows, and the house reads the sloped-only
# one.** Every published table splits them (C-C-2026 pp. 178 vs 179; ER-280 Table 11; TJ-4000
# p. 15), because skewing costs fasteners — the header schedule drops 14 -> 13 and the joist
# 12 -> 9, and CSG-TJUS25 p. 10 says why: "All holes must be filled except for the LSSR
# hanger when skewed". catlin's ridge is straight and its rafters land square on it, so the
# skewed row is not this joint's row. The 1,060 lb that circulated in the notes until
# 2026-09-14 was the skewed one.
