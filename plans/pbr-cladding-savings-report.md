# House-wall cladding: snap-lock seam → exposed-fastener PBR panel

**Taken 2026-08-26.** The catlin house's wall cladding moved from `standing-seam-snaplock`
(24 ga, concealed floating clips) to `pbr-panel-26` (26 ga, exposed-fastener PBR, 36" net
coverage, 1-1/4" major ribs at 12" o.c.), face-fastened with Simpson **T09150HWAM** #9 x
1-1/2" 316 stainless panel screws with bonded EPDM washers.

Two assemblies moved: `CATLIN_EXT_2X6` and `PLANT_EXT_2X6_HUMID`. `CATLIN_EXT_2X6_SWINBURNE`
keeps the snap-lock layer as the one-line revert.

**The garage was excluded.** `GARAGE_WALL_2X6` has no furring — cladding sits straight on
Zip-R — so PBR there needs a whole new girt layer plus through-insulation structural screws,
and that cost cancels the saving over 631 SF. It keeps `standing-seam-nailstrip-26` and its
28 `S-5-N` wind clamps. Both roofs (`CATLIN_ROOF`, `GARAGE_ROOF`) are untouched.

---

## The saving

Figures are the takeoff's own, before and after, from `haus takeoff houses/catlin --csv`.

| line | before | after | delta |
|---|---|---|---|
| `envelope_layers` house-wall cladding, 3,670.7 → 3,672.2 SF | $32,119 – $58,731 | $16,525 – $26,623 | **−$15,594 / −$32,108** |
| 48 `S-5-S` wall wind clamps | $300 – $492 | — | −$300 / −$492 |
| 11 `S-5! CanDuit` rings (#11 ×3, #13 ×8) | $110 – $242 | — | −$110 / −$242 |
| 13 `S-5!` seam clamps: 11 carried under those rings, plus the 2 wall-mounted enclosure clamps | $117 – $195 | — | −$117 / −$195 |
| 11 `SS316-STANDOFF-STRAP` through-panel straps | — | $32 – $58 | +$32 / +$58 |
| 3,098 `T09150HWAM` panel screws (2,473 field + 625 sidelap) | — | $1,794 – $2,246 | **+$1,794 / +$2,246** |
| roof layers (metal, polyiso, ZIP, OSB, deck barrier), from the grown cladding lap | $31,021 – $54,939 | $31,231 – $55,307 | +$210 / +$368 |
| **net, before waste / contingency / tax** | **$850,207 – $1,778,149** | **$836,164 – $1,747,870** | **−$14,043 / −$30,279** |

**Marked up**, the saving grows, because every stage of the ladder scales with it:

| stage | before | after | delta |
|---|---|---|---|
| `subtotal_net` | $850,207 – $1,778,149 | $836,164 – $1,747,870 | −$14,043 / −$30,279 |
| waste | $13,752 – $25,153 | $13,068 – $23,654 | −$684 / −$1,499 |
| `subtotal_ordered` | $863,959 – $1,803,301 | $849,232 – $1,771,524 | −$14,727 / −$31,777 |
| contingency (10%) | $86,396 – $180,330 | $84,923 – $177,152 | −$1,473 / −$3,178 |
| tax (8.53%) | $25,825 – $49,801 | $25,247 – $48,438 | −$579 / −$1,363 |
| **total** | **$976,181 – $2,033,432** | **$959,402 – $1,997,114** | **−$16,778 / −$36,318** |

The material/labour split of the net delta is **−$5,929 / −$14,022 material** and
**−$8,114 / −$16,257 labour**. That split is not decoration: per `takeoff/cost_model.py`
waste applies to material and to merged lines but **never** to declared labour, so the waste
line above moves on the material half only — which is why waste falls by roughly 12% of the
material saving rather than by 10% of all of it.

**Sanity check.** `plans/cost-options.md` independently pre-estimated −$15,600 / −$29,000
for this exact move. (That file was rewritten on 2026-08-31 and no longer has numbered
sections; the swap is now the "House-wall cladding → PBR" entry under **Do not reopen**,
where it sits because it is TAKEN and is in the baseline.) The realised low end lands just under that and the high end runs past
it, for a reason that is arithmetic rather than a modelling surprise: the pre-flight was
written against 3,512 SF and the resolved area is 3,672 SF.

## Where the money actually went

- **The panel is cheaper on both halves, for separate reasons.** Material $1.75–2.75/SF
  against $3.75–7.00: 26 ga PBR is the commodity metal-panel product and carries no clips at
  all, which on a snap-lock wall is real material and not only labour. Labour $2.75–4.50/SF
  against $5.00–9.00: no clips to set, no clip line to lay out, no seamer pass, no seamer
  rental. Both rows still carry this wall's 20–35% trim load — 45 openings, and a ribbed
  panel is if anything worse for trim than a flat pan, since every opening wants a closure
  strip shaped to the rib as well as a jamb return.
- **The clamps went because they cannot work, not to save money.** An `S-5-S` closes on a
  snap-lock leg and there is no leg left; `S5_CANDUIT_PIPE_CLAMP` declares
  `requires_role=ROLE_STANDING_SEAM_CLAMP`, so each ring would have arrived with a bracket
  that has nothing to grip. The 11 pipe fixings moved to a 316 stainless two-hole strap on a
  standoff block, screwed through the panel into the girt with two of the same panel screws.
  The ~$180–350 that saves is a consequence, not the argument.
- **The screws are the counterpart, and they are billed on purpose.** 3,098 of them, as a
  *counted part* rather than inside the $/SF rate — the first cladding fixings in this house
  billed that way. `Material.exposed_fastener` is what enables it and is the double-billing
  guard: the four seam profiles' fixings stay inside their own rates, and `[basis_notes]`
  records that the five rows must never be re-merged.
- **A small counter-effect, honestly reported.** The roof laps the cladding, so a face 3/4"
  further out grows the roof footprint slightly: +$210 / +$368 across every roof layer —
  the metal, both polyiso courses, the ZIP, the OSB top deck and the deck vapour barrier.
  It is inside the noise of the saving but it is not zero.

## What it cost that is not money

- **Service life.** The gaskets set the clock, not the steel. Expect a re-screw at 25–30
  years — a maintenance event a clipped, seamed wall does not have at all.
- **Appearance.** Oil-canning on a screwed 26 ga panel at eye level is more visible than on
  a floating clipped one. The renderers model this: `RIBBED_PANEL_PROFILE` carries a *lower*
  oil-canning term than the seam profile (a screwed panel is pulled tight to its girts every
  24"), but 26 ga is a thinner sheet than the 24 ga it replaced, and that runs the other way.
- **No corner-zone densification.** The 48 corner wind clamps are gone, and the screw
  schedule that replaced them is a uniform field grid. If a wind analysis is ever run, the
  lever is tightening the screw pitch in the corner zone — not re-authoring clamps onto a
  panel that cannot take them. `plan/wind_clamps.py` says so in its header.

## Geometry that moved with it

The cladding face went **6.5" → 7.25"** (`params/roof_trim.py::_WALL_OUTBOARD_IN`). Windows
and doors did **not** move: they mount on the outer girt plane, which is unchanged — only
the cladding return depth at a jamb changed. What did move:

- the breezeway's house face (`params/breezeway.py`), and the garage with it;
- the birdsmouth notch, deeper by 0.75 × 4/12 = 0.25" (1.667" → 1.917"), because the
  zero-overhang roof laps the cladding;
- the roof's `top-deck` edge setback, which clips at the cladding face (0.5" → 1.25").

**The garage moved only 3/8" of the house's 3/4", and half of that difference is a bug fix.**
`params/breezeway.py` was carrying a 3/8" rainscreen furring on the *garage* face that
`GARAGE_WALL_2X6` dropped on 2026-08-20 — the modelled garage face had stood 3/8" south of
where it actually is for six days, and the breezeway clear gap was 3/8" optimistic the whole
time. Correcting that rather than recomputing off it gave back exactly half the move. The
breezeway slot holds at **4'-0 1/2"**, still one uncut 4'-0" polycarbonate panel with its
1/2" reveal — unchanged, which was the constraint.

The flush zero-overhang roof edge survives because both the wall panel and the roofing
declare `skin_family="standing-seam"`, which is what
`resolve/roof_edge_geometry.continuous_skin_cladding` actually reads. Drop it on either and
the edge silently reverts to a fascia-and-drip-edge detail nobody has drawn.

## Exports

**IFC (`out/model.ifc`, `haus build`) is the Revit / SketchUp path**, and the panel arrives
in it the same way every other cladding does: `IFCMATERIAL('pbr-panel-26')` inside each
exterior wall's `IfcMaterialLayerSet`, as a 0.03175 m (1-1/4") layer named "cladding". Revit
reads that layer set natively on IFC link/import; SketchUp reads it through its IFC importer.
The 11 pipe fixings that replaced the CanDuit rings come through as `IfcDiscreteAccessory`
with a `category` of `panel_strap` — *not* `pipe_strap`, because `emit/trades.py` reads any
`pipe_*` category as a routed pipe run and would have filed a wall strap under plumbing.

**The `.glb` (`/model.glb`) needed a fix to match the viewer.** All five metal skins author
`color="#6b7076"` — that is the *drawing* hatch tone `material_color` pairs with
`hatch="metal"`, not the coil paint — and `_material_finish_color` read it before it reached
its standing-seam test, so the export painted the whole house's cladding blue-grey while the
live viewer painted it 0xE8E8E2 white. The seam test now runs first for a cladding layer, and
it dispatches on the DECLARED finish before falling back to guessing from the tag, which is
the only way it can see `pbr-panel-26` (no "seam" in the tag, on purpose). 45 wall meshes now
carry the coil white in the `.glb`; the two CMU specs, which author two different greys
deliberately, still keep their own. This was a pre-existing parity break that the new panel
inherited rather than caused — `standing-seam-snaplock` exported grey too.
