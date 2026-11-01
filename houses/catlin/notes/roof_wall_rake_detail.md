---
title: "Roof-to-Gable Rake Detail Notes"
applied_to:
  - transition: TR-CATLIN-RAKE
tags:
  - roof
  - wall
  - rake
  - air-barrier
  - insulation
source:
  - plan/assemblies.py ROOF
  - resolve/roof_image_ii.py
  - notes/metal_trim_kit.md
---

## Sheet notes

### General
- Roof: 11-7/8" TJI 230 at 24" o.c., parallel to the gable. 6:12, zero overhang.
- Bay: 5" ccSPF on deck, R-30C batt. Foam is the air and vapour barrier.
- Deck: 19/32" CDX, 40/20, oversailing the gable to the girt face.
- Butyl membrane 240 F, full field to the deck edge. 24 ga Image II, nail flange.
- Wall: 2x6, 1/2" ply, 4" ccSPF, 1/2" gap, KDAT girts, 3/4" BBD75. No WRB.

### Keyed
- [K1] Rake: stock Residential Rake 52126XX over the membrane at the deck edge.
- [K2] Rake leg stops 1" under the wall head and covers the closure.
- [K3] BBD75 slope-cut at the rake; Universal Closure 6411499 taped to it.
- [K4] Rake foot sits on the Extended Eave leg; the rake sheds onto the eave.
- [K5] Rake nailer on the raked top plate closes the cladding's raked edge.
- [K6] Wall foam tight to the deck underside: closed-cell fill. No high-expansion foam.

### Spec 07 61 00
- No gutter and no strip-in at a rake: the field membrane runs to the deck edge.
- Build order: deck, membrane, eave, rake, pan. The rake laps the eave, never under it.

# Notes

The house's N/S walls are gables (`RF-HOUSE` ridge runs north-south), so the
`wall_roof:EXT_2X6_BOARD_BATTEN|ROOF` cut is a rake. It used to bind `TR-CATLIN-EAVE`
and printed the eave's gutter-flange continuity, which does not exist here (C7-E7).

- Rake piece: Metal Sales Residential Rake 52126XX, 24 ga PVDF, the stock section
  (`library/trim/_image_ii.py`, resolved by `resolve/roof_image_ii.py`). Its bottom sits
  1.0" below the BBD75 wall head to hide the 3/4" Universal Closure. The 1.0" lap is a
  Catlin rule; no manual publishes one (DESIGN-LOG, "House rake is the stock 52126XX").
- BBD75 under the rake: Universal Closure 6411499 taped to the slope-cut panel, covered by
  the rake face, PBR p. 61 method (`metal_trim_kit.md`, Wall edges).
- Corner: the rake foot stands on the Extended Eave's leg and lip, and the eave runs
  through to the rake's outer face, so the rake sheds onto the eave
  (`roof_wall_eave_detail.md`).
- The cavity is closed by the deck oversail, as at the eaves (`metal_trim_kit.md`).
- Rake nailer and its blocks: `catlin_truss_engineering.md` (gable framing).
- Roof stack, membrane and foam: as `roof_wall_eave_detail.md`, which carries the
  arithmetic and the R806.5 path.
