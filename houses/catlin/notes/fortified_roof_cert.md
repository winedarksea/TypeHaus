# FORTIFIED Home™ — High Wind & Hail, Roof level (2026-08-30)

Minnesota is not a hurricane state, so the applicable IBHS program track is **FORTIFIED
Home™ — High Wind**, not Hurricane. Minn. Stat. 65A.298 requires insurers to file a
mandated wind/hail premium discount for FORTIFIED-designated homes, and the state's
Commerce bulletin sets its discount thresholds against **"FORTIFIED Roof + Hail"**
(35%+), not bare Roof alone — which is why the Hail Supplement is folded in below even
though Silver/Gold are out of scope. Silver and Gold are declined on purpose: both add
impact-resistant window/door/garage-door requirements this house does not need. For a
standing-seam **metal** roof the hail requirement is a UL 2218 Class 4 product/SKU check
(many 24ga steel panels already qualify), not a design change — so folding it in costs
nothing but a manufacturer letter.

Target: **FORTIFIED Home™ — High Wind & Hail, Roof level, New Roof (2025 standard)**.
Foundation/dwelling-type eligibility (§2.2–2.4) is trivially met (stem-wall/slab,
single-family) and needs no tracking here.

This note is the single source of truth for the gap analysis; `checks/structural/
fortified_roof.py`'s three sub-checks point back to it for anything they cannot grade
(nailing schedule, gauge, fastener spacing, ASTM/ICC compliance — all documentation facts,
not modeled ones), and every other edit made for this certification cites it.

## What the house already gets right, no action

- Rafters are 11⅞" I-joists at 16" o.c. — under §2.5's 24" o.c. cap, above its 2" nominal
  minimum.
- Roof deck is 5/8" OSB — above §4.1's 7/16" performance-category minimum.
- Roof is unvented/hot-roof cathedral construction, so §4.9 (ridge/gable vent TAS 100(A))
  is moot — there is no attic to ventilate.
- PV is S-5! clamped to standing seam with zero penetrations (not ballasted, which would
  be disqualifying) — meets the *form* of §4.10; the paperwork gap is tracked below.
- The heat-pump condensers sit on `FS-SG-DECK`, the sunken garden's freestanding balcony —
  a separate unconditioned structure with a 5" gap from the house, not a roof over living
  space, so §2.6/§2.7's scope does not reach it.
- `checks/structural/uplift_path.py` already grades the roof-to-wall, wall-to-foundation,
  and beam-to-post uplift chain tri-state (PASS/FAIL/UNKNOWN) with the "advisory, not
  engineering" posture FORTIFIED's own paperwork-not-proof character wants — most of
  §2.5's continuous load path and Silver/Gold's Continuous Load Path sections, already
  built. `structural.fortified_roof_load_path` re-presents its roof-bearing findings under
  this checklist's name rather than re-deriving them.

## Roof structure — §2.5

**Gap:** the house uses a structural ridge beam (`RB-HOUSE`), which eliminates rafter
thrust and is the standard's own "engineered alternative" to collar ties — but that is
documented only as engineering narrative in `notes/ridge_beam_detail.md`, not a stamped PE
letter.

**Fix:** procurement — a PE letter citing §2.5/Appendix B1, covering the ridge-beam
alternative.

## Deck attachment — §4.2.2

**Gap:** the outer 5/8" OSB deck is **screwed** (10" SDWH191000DB through the foam into
the rafters), not nailed — RSRS-01 ring-shank nailing at 4" o.c. max does not apply to a
screwed nailbase assembly. This is exactly the standard's "other attachment method"
branch, not a deviation from it.

**Fix:** procurement — a PE letter per §2.5/Appendix B1 covering the screwed-nailbase
attachment as an alternative to RSRS-01 nailing. Not a modeled field: nothing else in this
model would consume an authored `nail_spacing_in`, and "this deck is screwed and needs a
PE letter" is the whole honest answer.

## Sealed roof deck — §4.4

**Gap (closed by spec, 2026-08-30):** the taped layer is the *inner* ZIP nailbase; the
*outer* OSB deck (the one actually under the covering) had an untaped-seam generic
synthetic underlayment with no ASTM/ICC citation or fastening schedule stated.

**Fix, applied:**
- `plan/assemblies.py`'s `CATLIN_ROOF` top-deck layer now notes OSB seams taped with ASTM
  D1970 or AAMA 711 Level 3 tape — Method 1, since the AC266/Zip factory-taped exemption
  only covers the panel directly under the covering, and the taped ZIP here is an inner
  air-barrier layer, not that panel.
- The `roof-underlayment-synthetic` material's `source` now cites ASTM D226 Type II /
  ICC-ES AC188 compliance and a 6" o.c. lap / 12" o.c. field cap-nail fastening schedule.
- `structural.fortified_roof_sealed_deck` grades presence of a MEMBRANE layer with a WATER
  control on any conditioned-envelope roof at 2:12 or steeper; catlin's roof carries one
  (`underlayment`), so the check reports UNKNOWN — presence, not inspected compliance.

Documentation/spec only: no layer thickness, assembly R-value, or geometry changed.

## Drip edge / flashing — §4.5, §4.6

**Gap (closed by spec, 2026-08-30):** the eaves (west/east) already carried a full
drip-edge/gutter chain (`params/roof_trim.py`); the rakes (south/north gables) only got the
derived corner-trim angle (`resolve/roof_trim.py::_corner_trim_members`), which follows the
roof slope but is not a `Flashing(kind=DRIP_FLASHING)` element FORTIFIED's checklist can
point a photo at.

**Fix, applied:** `params/roof_trim.py::_rake_drip` adds a short drip-edge return at each
rake corner, at the same deck-plane elevation the eave piece bears at. It is deliberately
**not** a sloped member — this model's authored `Flashing` has one elevation per run and
cannot re-derive the corner trim's own slope-following geometry — so it coexists with the
corner trim rather than replacing it: the corner trim still carries the sloped run up to
the ridge, and this gives the rake its own modeled part of record at the corner.
`structural.fortified_roof_drip_edge` now finds a `DRIP_FLASHING` on all four footprint
edges (N/S rake, E/W eave) and reports UNKNOWN on each — presence only; gauge and fastener
spacing are documentation facts this model does not carry.

## Metal roof design-pressure rating — §4.7.3

**Gap:** the `standing-seam` material has no manufacturer, gauge-matched test report, or
DP rating on record.

**Fix:** procurement — the panel manufacturer's UL 580/1897 (or ICC-ES/FL/Miami-Dade/TDI)
test report matched to the as-specified clip spacing and deck. Once a specific
manufacturer/gauge is selected, retag the roofing layer's `material_ref` off the generic
`standing-seam` to a named material citing the report in its `source`, the same way
`metal-fascia-regal-blue` cites a manufacturer page today. **Not done yet** — this is
procurement-gated and the retag should not happen before the SKU is chosen.

## Hail Supplement — §7.2.3

**Gap:** no UL 2218 Class 4 documentation on file for the chosen panel.

**Fix:** procurement — the manufacturer's UL 2218 Class 4 letter. Commonly already true for
24ga steel panels; confirm against the specific SKU rather than assuming it.

## PV load path — §4.10

**Gap:** no PE letter confirming the S-5! clamp → standing seam → structure load path
resists the site's C&C wind loads.

**Fix:** procurement — a PE letter. `structural.fortified_roof_load_path` covers the
roof's own bearing chain but does not reach the PV attachment, which is a different load
path than the ones `uplift_path.py` walks.

## Hail Supplement, PV — §7.5

**Gap:** the Aptos 440W modules' FM 4478/UL 1703 hail rating is not confirmed.

**Fix:** procurement — pull the manufacturer's spec sheet.

## Open items

| # | Section | Item | Status | Owner |
|---|---|---|---|---|
| 1 | §2.5 | PE letter: structural ridge beam vs. collar ties | open | procurement |
| 2 | §4.2.2 | PE letter: screwed-nailbase deck attachment vs. RSRS-01 | open | procurement |
| 3 | §4.4 | Sealed deck spec (tape + underlayment citation) | **closed 2026-08-30** | spec |
| 4 | §4.5/4.6 | Drip edge at eaves AND rakes | **closed 2026-08-30** | spec |
| 5 | §4.7.3 | Manufacturer UL 580/1897 DP test report | open | procurement |
| 6 | §7.2.3 | Manufacturer UL 2218 Class 4 hail letter | open | procurement |
| 7 | §4.10 | PE letter: PV load path | open | procurement |
| 8 | §7.5 | Manufacturer FM 4478/UL 1703 hail rating (Aptos 440W) | open | procurement |

Once items 1, 2, 5, 6, 7, 8 are in hand: engage a FORTIFIED-certified Home Evaluator and a
FORTIFIED Wise Roofing Contractor. Designation requires third-party verification, not
self-attestation — nothing above substitutes for that walk-through.

This table is meant to map 1:1 to the evaluator's own photo-documentation checklist
(`fortifiedhome.org`'s "New Roof Checklist") so nothing is missed when a real evaluator is
engaged; read it end to end against that checklist before scheduling the walk-through.
