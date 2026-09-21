"""The north-entry landing's TIE to the garage stem (owner, 2026-09-21).

The two carriers `BM-BW-FC`/`-FE` cross the ICF stem (`W-GF-S1`, `W-GF-S-DR`) with 3 3/4"
to spare. An `HGAM10` pair per carrier ties each to the stem's core, and that authored
hardware is the whole claim: `engineering/deck_tie_basis.wall_ties` reads it and DERIVES that
`FS-BW-FLOOR` is braced by the garage, so the four landing piers lean and stop grading base
moment, sway and head lateral. What the tie then carries is `deck_tie/FS-BW-FLOOR`
(notes/north_entry_piers.md §10).

**The gusset cannot reach the carrier on its own.** An HGAM10 is a 3" x 3" angle, 3 1/2"
long (FL11473 Figure 1): its wood leg stands 3" off the stem top and the carrier soffit is
3 3/4" up. So each carrier takes a KDAT 4x tie block, 3 1/2" deep, screwed up into its
soffit and stopping 1/4" off the concrete — the gap is kept, so nothing bears on the garage.
The pair screws to the block's two faces (FL11473 fn 4: a member >= 2 1/2" wide when
installed each side; the 4x is 3 1/2"). The block's own screws are named in the note, not
graded.

**Where on the stem.** Over the 6" CORE, 5 1/2" inboard of the node line (2 1/2" of foam,
then half the core): the Titen 2 screws want concrete and FL11473 fn 6's 1 1/2" edge.
"""

from typehaus import Connector, ConnectorKind, ft, inch, pt

from params.north_entry_frame import BEAM_X_FT, DECK_JOIST_TOP_FT, JOIST_DEPTH_IN
from plan.storeys.garage import GARAGE_Y_SOUTH

#: The stem top, -1'-0" (W-GF-* `_STEM_TOP`), and the tie line over its core.
STEM_TOP_FT = -1.0
STEM_CORE_Y_FT = GARAGE_Y_SOUTH.feet + 5.5 / 12
#: Half the 3 1/2" tie block: each gusset's wood leg is on a block face.
_BLOCK_HALF_IN = 1.75
#: The gusset's centre, half its 3" leg above the stem top.
_TIE_ELEVATION_FT = STEM_TOP_FT + 1.5 / 12

assert DECK_JOIST_TOP_FT - JOIST_DEPTH_IN / 12 - STEM_TOP_FT > 3.5 / 12, \
    "the carrier soffit no longer clears a 3 1/2in tie block over the stem"

LANDING_TIES = [
    Connector(uid="ARD33PDHYR", tag="CN-BW-STEMTIE-FC-A", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(BEAM_X_FT[0]) - inch(_BLOCK_HALF_IN), ft(STEM_CORE_Y_FT)),
              elevation=ft(_TIE_ELEVATION_FT), size="HGAM10",
              connects=("BM-BW-FC", "W-GF-S1")),
    Connector(uid="AJ70HT0M2D", tag="CN-BW-STEMTIE-FC-B", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(BEAM_X_FT[0]) + inch(_BLOCK_HALF_IN), ft(STEM_CORE_Y_FT)),
              elevation=ft(_TIE_ELEVATION_FT), size="HGAM10",
              connects=("BM-BW-FC", "W-GF-S1")),
    Connector(uid="0TW5SE2NX5", tag="CN-BW-STEMTIE-FE-A", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(BEAM_X_FT[1]) - inch(_BLOCK_HALF_IN), ft(STEM_CORE_Y_FT)),
              elevation=ft(_TIE_ELEVATION_FT), size="HGAM10",
              connects=("BM-BW-FE", "W-GF-S-DR")),
    Connector(uid="VNT251FTF3", tag="CN-BW-STEMTIE-FE-B", kind=ConnectorKind.HURRICANE_TIE,
              position=pt(ft(BEAM_X_FT[1]) + inch(_BLOCK_HALF_IN), ft(STEM_CORE_Y_FT)),
              elevation=ft(_TIE_ELEVATION_FT), size="HGAM10",
              connects=("BM-BW-FE", "W-GF-S-DR")),
]
