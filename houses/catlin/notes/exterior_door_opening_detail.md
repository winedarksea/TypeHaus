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
- Cut at D-M-ENTRY: DT-EXT-SWING36, R.O. 3'-2 3/8" x 6'-10 7/8". D-M-PORCH and D-S-BALCONY: same wall, own sills.
- R.O. starts on the 3/4" subfloor, not the joist top. The subfloor runs under the sill; the skin below stops at the datum.
- Thresholds at the cut: ENTRY 1 5/8" over the LVP, 2 5/8" over the landing; PORCH 1 1/2" / 1 9/16". BALCONY: catalog sill.
- Wall frame as at the windows: girt jamb posts on the R.O. edge, head and sill courses, 3/8" ply buck.
- Factory jambs anchor to the stud opening. The buck is a flashing substrate, not anchorage or threshold bearing.
- Sill and threshold sections are schematic until the supplier's installed section is in hand.

### Keyed
- [K1 @ host#layer:outer-girt:out] Jamb post: KDAT 2x4 flat, inner face on the R.O. edge, 3-1/2" past each end.
- [K2] Pan on the buck at the seat: sloped, back dam, end dams 6" up the jambs. Front leg runs 1/2" past the cladding to a drip.
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
- Thresholds are the drawn `thr. above` strings off each door's own cut (`opening_unit
  ._threshold_strings`, 1/16" rounding): ENTRY 1 5/8" / 2 5/8", PORCH 1 1/2" / 1 9/16".
  D-S-BALCONY's catalog ZAI sill carries no `threshold` profile, so no figure is drawn
  (`french_door_catalog_installation.md` has its crest).
- Pan front leg: `FLASHING.head_projection_m` (1/2") past the cladding face, as
  `opening_flashing_spec.md` §6 says. End dams: `FLASHING.end_dam_m` (6"). Drip cap end lap:
  `head_end_lap_m` (1"); end dams `head_end_dam_m` (3/4").

ENTRY's 1 5/8" over the LVP is over R311.3.1's 1 1/2"; that is the deferred interior grading in
ad946621f (`plans/TODO.md`), not a drawing question.
