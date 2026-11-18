---
title: "Exterior Door Opening Detail Notes"
applied_to:
  - detail: TR-CATLIN-EXT-DOOR-OPENING
tags:
  - openings
  - doors
  - flashing
source:
  - opening_flashing_spec.md
  - exterior_door_structural_mount.md
  - outie_window_truss_detail.md
---

## Sheet notes

### General
- Cut at D-M-ENTRY: DT-EXT-SWING36, R.O. 3'-2 3/8" x 6'-10 7/8". D-M-PORCH and D-S-BALCONY: same sill package.
- R.O. starts on the 3/4" subfloor, not the joist top. The subfloor runs under the sill; the skin below stops at the datum.
- One sill at all three: ZAI5625FN + 6 3/8" XXXXW on a membrane pan on the subfloor. Crest 1.20" over the LVP (1.45" with 1/4"), 2.23" over the ENTRY landing.
- Wall frame as at the windows (posts, head course, 3/8" ply buck), but the sill is a 2x6 KDAT beam outboard of the girts, face at the extender nose, on a 4-ply seat at each end (exterior_door_sill_beam.md).
- Factory jambs anchor to the stud opening. The buck is a flashing substrate, not anchorage or threshold bearing.
- The sill is a digitized catalog outline until the prehanger's installed section is in hand.

### Keyed
- [K1 @ host#layer:outer-girt:out] Jamb post: KDAT 2x4 flat, inner face on the R.O. edge, 3-1/2" past each end.
- [K2] Self-adhered membrane pan on the subfloor and buck: back dam, end dams 6" up the jambs, over the beam top (ripped 1/4"/ft) and 1/2" down its face to a drip, 3/4" past the cladding.
- [K3 @ host#layer:spray-foam:out] Head: site-brake 24 ga steel drip cap, 1" past each casing end, end dams. Upstand stripped in.
- [K4] Panel end above the head on a perforated strip. Keep the pan outlet open: never caulk or shim across it.
- [K5 @ host#layer:cladding:out] Sealant at the cladding-to-frame joint, at the mount plane, under the drip.

### Spec 07 92 00
- Set the frame on sealant at the back dam only, never across the front, so the pan drains.

# Notes

The door half of the board-and-batten opening key (`opening_perimeter:door:EXT_2X6_BOARD_BATTEN`,
REPORT item 14 / O4-103, O5-103, O3-104). The window half keeps
`outie_window_truss_detail.md`, whose K6 is the window head CAP; a door head is the site-brake
drip cap (`DOOR_HEAD_CUSTOM`, `opening_flashing_spec.md` §4), so the two cannot share a key set.

Model values at the cut (2026-11-06):

- D-M-ENTRY: `DT-EXT-SWING36`, RO 38.375" x 82.875", `sill_m` 0.75" (seated on the subfloor since
  ad946621f), `skin_sill_m` 0.0. Owned pieces: `DOOR_HEAD_CUSTOM`, `PANEL_END_STRIP`, two
  `BBD_PANEL_STARTER`, two sill-pan solids, the perimeter membrane.
- Thresholds (2026-11-18): all three doors take the catalog ZAI sill, so no `threshold`
  profile string is drawn; the crests are in `exterior_door_sill_beam.md` §6 (ENTRY 1.20" over
  the LVP, inside R311.3.1's 1 1/2" with the 1/4" allowance).
- Pan front leg: wrapped down the sill beam's face to a 1/2" drip at 7 1/2" off the sheathing,
  3/4" past the cladding. End dams: `FLASHING.end_dam_m` (6"). Drip cap end lap:
  `head_end_lap_m` (1"); end dams `head_end_dam_m` (3/4").
