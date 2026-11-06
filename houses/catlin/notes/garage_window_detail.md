---
title: "Garage Window Detail Notes"
applied_to:
  - detail: TR-CATLIN-GARAGE-WINDOW
tags:
  - garage
  - openings
  - flashing
source:
  - opening_flashing_spec.md
  - garage_wall_detail_side.md
---

## Sheet notes

### General
- Cut at WIN-G-N1; WIN-G-S1 is the same unit. WT-1424-FIX, R.O. 1'-2" x 2'-0", sill 3'-6" above the stem top.
- Wood wall: 2x6 at 24" o.c., 5/8" CDX, 2" of 2 lb closed-cell foam per bay. No WRB.
- Innie: the unit sits in the stud plane, outer face on the CDX. No buck projection, no vent gap.
- Bucks before foam. The bay foam is the air and water plane; the CDX is the membrane substrate.
- Jamb, sill and head trim are site brakes from 24 ga flat stock.

### Keyed
- [K1 @ host#layer:cdx:out] Fluid-applied membrane round the R.O., lapped 2" onto the CDX.
- [K2 @ host#layer:cladding:out] Sill pan: 1/4"/ft on a tapered KDAT shim, back dam on a strip at the studs' inner face. Out past the panel to a drip.
- [K3] Head: 24 ga steel over the casing, end dams, 3" upstand stripped in to the CDX. Sealant under the drip.
- [K4] Steel head and trim never touch aluminium: EPDM or sealant between.

# Notes

The window half of the garage opening key (`opening_perimeter:window:GARAGE_WALL_2X6`, REPORT
item 14 / O4-103): the doors keep `garage_wall_detail_side.md`, whose keyed notes are the stem
band, curb cap, sill and overhead header, none of which a window cut shows.

Model values (2026-11-06): WIN-G-N1 and WIN-G-S1 are `WT-1424-FIX`, RO 14" x 24", `sill_m` 42"
over `W-G-W`'s `base_ref_z_m` (-12", the ICF stem top), so the sill is 30" above the datum.
`W-G-W` layers: gwb-int 5/8", stud 5 1/2" (stud-cavity foam 2"), cdx 5/8", cladding 7/8".
`window_seat.outer_m` is 0: the frame's outer face is on the CDX. Owned trim: two
`WINDOW_JAMB_CUSTOM`, one `WINDOW_SILL_CUSTOM`, one `OPENING_HEAD`.

Flashing per `opening_flashing_spec.md` §7 (windows and `D-G-SERVICE`: §3's sequence on CDX)
and §4 (the steel head). The head rise is `FLASHING.head_rise_m` (3").
