# W-BW-SCREEN — white MDO east face and the lower centre timber

Current basis 2026-11-14. The shared source is `plan/entry_screen_finish_spec.py`; cuts,
support mass, purchasing and the local checks all read it. Run
`.venv/bin/python scripts/entry_screen_mdo_report.py --output houses/catlin/notes/entry_screen_mdo_calculations.json`
(exits 1 on any failed check). Acceptance reads **ok**, on the two reads named under
"Still to read".

## Sheet notes
### General
- East face: three white 3/4-inch exterior MDO panels, removable stainless screws, 1/8-inch gaps at timber.
- MDO stops at the north chord post; the end pack and both garage ties stay exposed and oiled.
- Lower centre timber: one KDAT 6x6 framed in like a stud, four S10ACN through each plate into its ends.
- Nail the timber on the flat, before the wall stands and before the band goes on.
- Five 2x4 MDO edge nailers; retain west plywood, plates and cap. Keep bottom drainage open.


## Geometry

- West 5/8-inch CDX (the shear, alone), corrugated skin, field studs, plates, cap and the band
  above are unchanged. The timber and nailers add no roof support and no shear chord.
- `TR-BW-MDO-TIMBER`: one KDAT Southern Pine No. 2 6x6, 5.5 x 5.5, cut 44.44 inches,
  x=72.625–78.125, stations 37.875–43.375, +0.56 to +45. Both faces line up with the band's
  centre post and the chord posts. Pigmented penetrating oil, not white paint.
- Five KDAT 2x4 edge nailers, x=72.625–76.125, +0.56 to +45, at stations 7.125, 14.375
  (`-1`, `-2`), 37.000, 44.250 (`-6`, `-7`) and 66.875 (`-4`). `-3` and `-5` are retired.
- White-painted 3/4-inch Roseburg DuraGard Premium exterior MDO, screwed to framing, face
  x=76.875, 1 1/4 inch behind the exposed timber. No east WRB or cavity.

| Panel | Stations from south node, in | Width, in | Height, in |
|---|---|---|---|
| 1 | 0.125–7.875 | 7.750 | 45.5 |
| 2 | 13.625–37.750 | 24.125 | 45.5 |
| 3 | 43.500–67.625 | 24.125 | 45.5 |

Panels run +2 to +47.5. Net MDO area 56.0 x 45.5 = 17.694 sf. **Nothing north of the chord
post** (owner, 2026-11-14): the two HL33 garage ties sit on the end stud pack's east face at
+10 3/4"..+13 1/4" and +34 3/4"..+37 1/4", and a panel cannot lie flat over them. The end
pack, tie block and ties are finished like the timber and stay inspectable.

Removable No. 8 x 2-1/2-inch 304 stainless pan-head white-head screws: maximum 6 inches at
vertical edges, 12 inches at intermediate studs; minimum 3/8-inch panel edge distance. Pilot
drill; seat heads without crushing the overlay. The nailers keep three stainless 8d toenails
per end; they back MDO edges only.

Prime and paint MDO on both faces, cut edges and holes: compatible exterior primer and two
white exterior acrylic topcoats. Fill edge voids and ease edges. No MDF. Field-treat treated
cuts and holes with 2% copper naphthenate per AWPA M4. Do not dam drainage.

## The timber's end connection

Framed like a stud (owner, 2026-11-14). **Four `S10ACN` (0.148 x 3 inch, 304 stainless
ring shank) through each 1 1/2-inch plate into the timber's end grain**, driven on the flat
before the wall stands and before `SB-BW-BAND` goes on. Nothing is proud of the wall, so the
door sweep is unchanged.

What was ruled out:

- **Screws into the ends.** IAPMO UES ER-192 (rev. 09/08/2026, read 2026-11-14): every
  SDWS/SDWH table requires the screw "installed straight into the side grain of the wood main
  member with the screw axis at a 90-degree angle to the wood fibers", and no toe-screw value
  is published.
- **Bent A35Z.** The 1/8-inch gaps beside the timber cannot take a 1 7/16-inch leg.

Hand pass (the report reproduces it):

```
demand    guard 200 lb at midspan -> 100 lb per end (C_D 1.0)
          wind 16.661 psf x 32/12 ft x 44.44/12 ft / 2 = 82.3 lb per end (C_D 1.6)
nail      NDS 12.3.1, D 0.148, plate 1.5" side, 1.5" in the timber (10.1 D), G 0.55 both
          F_e = 16,600 x 0.55^1.84 = 5,526 psi; mode IV governs
          Z = D²/K_D x sqrt(2 F_em F_yb / (3 (1 + R_e)))
            = 0.148²/2.2 x sqrt(2 x 5,526 x 60,000 / 6) = 0.009956 x 10,512 = 104.7 lb
adjust    x C_eg 0.67 (end grain) x C_M 0.70 (wet) = 49.1 lb per nail
guard     100 / (4 x 49.1) = 100 / 196.4 = 0.51
wind      82.3 / (4 x 49.1 x 1.6) = 82.3 / 314.2 = 0.26
```

F_yb 60,000 psi is an assumed floor, not a published value. Z goes as its square root: the
guard row still passes at 16,000 psi, and at the 100,000 psi the engine carries for a common
steel nail it reads 135.1 lb (0.39).

The timber as a member, NDS Supplement Table 4D SP No. 2 timbers, wet row (Fb 850, Fv 165,
E 1.2e6): 200 lb x 44.44 / 4 / 27.729 in³ = 80.1 psi, **0.094**; shear 0.060; wind bending
0.039. The 1/4-inch deflection limit is a project criterion, not a statutory one.

**Plates and sill.** A guard load on the timber reaches the plates as it does from any stud;
the wall's own guard row (`deck_tie/FS-BW-FLOOR`, 0.653) already takes 200 lb anywhere on
it. `BM-BW-SCSILL` was sized at the thin-brick wall's 77 plf (197 lb-ft); today's 55.62 plf
line with the timber's point load is under that.

**Door.** `D-G-SERVICE` clears every screen solid by 0.641 inch at the 87-degree stop
(1/4 inch required), measured at a 1/2-inch pivot inset: measure the delivered frame's pivot
before setting the stop (`garage_service_door_outswing.md`).

## Weight

Support wood 54.43 lb (timber 29.1, five nailers 25.3); hardware and paint reserve 2.16 lb
(2 lb paint and fastening, eight end nails). Both are charged once through the MDO's areal
density. The wall is **37.53 plf**, the line with the band **55.62 plf**, **163.65 lb** to
each west chord: `north_entry_piers.md` §2a.

## Purchasing

One 48 x 96-inch MDO sheet, **three 8-foot KDAT 2x4s** for five nailers and **one 8-foot
KDAT 6x6**. Two 24.125 x 45.5-inch panels fit end to end in one strip; the narrow panel fits
alongside. Verify actual thickness, framing and finish sample before cutting. Prices are
budget allowances.

## Still to read

- The `S10ACN`'s bending yield strength, from Simpson (graded at an assumed 60 ksi floor).
- C_eg against NDS 2018 §12.5.2 in print. It was read from AWC's summary of the 2015 changes:
  "For fasteners with D<1/4 inch, Ceg = 0.67 is applicable where the fastener is installed
  in end grain."

Sources: [IAPMO ER-192](https://forms.iapmo.org/ues_reports/reports/er_0192.pdf),
[AWC, changes to the 2015 NDS](https://awc.org/publications/changes-to-the-2015-national-design-specification-nds-for-wood-construction),
[SFPA dimensional lumber design values](https://www.anthonyforest.com/assets/pdf/dv-2013-visual-grades.pdf),
[Roseburg DuraGard](https://www.roseburg.com/resources/duragard-mdo-premium-flyer/),
[APA MDO/HDO](https://www.apawood.org/engineered-wood-products/plywood-osb/mdohdo-panels/).
