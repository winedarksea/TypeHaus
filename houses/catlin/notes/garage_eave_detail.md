---
title: "Garage Eave Detail Notes"
applied_to:
  - detail: garage_eave_detail
tags:
  - roof
  - eave
  - garage
source:
  - plan/storeys/garage.py _GARAGE_EAVE_TRIM
  - plan/assemblies.py GARAGE_ROOF
---

## Sheet notes

### General
- Roof: raised-heel trusses at 24" o.c., 4:12, 16" overhang on the top chord tails.
- Deck: 3/4" Structural 1 plywood. Self-adhered membrane, full field. Nail-strip standing seam.
- Attic: vented. Blown fill level on the ceiling, stopped at the bearing walls.
- Wall: 2x6, sheathing with integral WRB, corrugated metal panel.

### Keyed
- [K1] Raised heel on the plate. Truss tie at every truss.
- [K2] 2x6 fascia nailer on the tails, 1" formed metal fascia over it.
- [K3] Vented soffit, fascia back to the wall. Keep baffles clear at every bay.
- [K4] Formed drip edge: 2" flange on the deck, bend over the deck edge, face over the metal fascia.
- [K5] Membrane laps OVER the drip flange. Seam panels hem over the drip nose.
- [K6] 5" K-gutter, back sheet BEHIND the drip face, rim 1/2" below the deck edge.
- [K7] Drip kick 3/4" out and down, into the trough.
- [K8] Gutter falls 1/16" per foot north to the east and west leaders.

### Spec 07 61 00
- Drip edge and fascia from the same dark PVDF coil as the house trim.
- Build order: fascia, soffit, drip edge, membrane, standing seam, gutter.
- Lap order: roofing over drip over membrane-lapped deck; drip face over gutter back.

# Notes

The garage eave is the conventional overhung eave the house does not have: fascia and
soffit close a 16" truss-tail overhang, and a K-gutter hangs on the fascia. Every piece is
derived from the roof's own `EaveTrim` (plan/storeys/garage.py), so the section cut draws
the real trim and the sheet only names it.

- The formed drip edge is one piece of metal per edge: flange on the deck at 4:12, a nose
  over the deck edge and the fascia's top, a face down the fascia to the gutter rim, and a
  kick that starts outboard of the gutter's back sheet so the back sheet stands behind the
  drip. On the rakes the face drops 1-1/2" over the fascia.
- The canopy (RF-BW-CANOPY) carries the same drip edge and trough; it has no soffit.
