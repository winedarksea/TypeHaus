# Wet vent basis — FX-B-BATH-WC through PR-B-USINK-DRAIN

Oracle for `checks/mep/wet_vent.py` (`mep.trap_arm_developed`). Worked by hand from
`plan/mep_drainage.py` and `plan/mep_lavatories.py`.

## Code read

- **908.2 horizontal** (IAPMO TIA UPC-001-12, https://iapmo.org/media/vw2n0qja/2012-upc-tia-001-issued.pdf):
  - 908.2.1 "Only the fixtures within the bathroom groups shall connect to the wet vented horizontal branch drain."
  - 908.2.1.1 "Only one wet-vented fixture drain or trap arm shall discharge upstream of the dry-vented fixture drain connection."
  - 908.2.1.2 "not less than 2 inches ... for 4 [dfu] or less, and not less than 3 inches ... for 5 dfu or more."
  - 908.2.1.4 "The water closet fixture drain or trap arm connection to the wet vent shall be downstream of all fixture drain or trap arm connections."
  - 908.2.1.3 "The length of the trap arm shall not exceed the limits in Table 1002.2."
- **908.2.2 size, whole length** (MN Plumbing Board PB0225, 2026-02-24,
  https://dli.mn.gov/sites/default/files/pdf/PB0225-horizontal-wet-venting.pdf): a wet vent serving 5 dfu "must be sized three inches (3") in diameter for its entire length".
- **908.1 vertical** (MN DLI sheet, https://www.dli.mn.gov/sites/default/files/pdf/pe_list_vertical_wet_venting.pdf):
  upper fixtures 1-2 DFU, same story, wet vent ≤ 6 ft developed, section one size over the larger of the upper fixture's waste and the size for the sum served, never under 2".
- **Table 1002.2**: 1-1/4" 30, 1-1/2" 42, 2" 60, 3" 72, 4" 120 (repo `TRAP_ARM_MAX_IN`; matches a secondary
  re-statement, the 2018 table itself was not opened).

Not read: the 2018 UPC text itself (paywalled). 908.2 is the 2012 TIA wording; the Board quotes 2018 908.2.2 consistently with it.
The vertical-section split (908.1.1) is graded on the whole section.

## The model

- `PR-B-BATH-DRAIN`, Ø3", serves WC, LAV, UTIL-SINK: (12'-0", 291.8") south to y=208.75", then west to x=36".
  The WC arm *is* its first vertex (x=144"); the lav's Ø1.5" drop joins the first leg at y=224.4".
- `PR-B-USINK-DRAIN`, Ø1.5", carries the vent tee (PR-B-BATH-VENT) at x=115-120", y=229.5", drops to join `PR-B-BATH-DRAIN`'s west leg at x=120".
- DFU (Table 702.1 in `plumbing_calc`): WC 3 + lav 1 + utility sink 2 = 6.

## Developed arm

WC to the join: 8.55" (slab drop) + 83.06" (south leg, 291.8 - 208.75) + 24" (west, 144 -> 120) = 115.6" ≈ **116"**,
against 72" for Ø3". It is over, so 116" is only acceptable if the sink is a legal wet vent.

## Grade of the sink as a wet vent (908.2)

| Rule | Model | Result |
|---|---|---|
| Group fixtures only | utility sink is not in a bathroom group | FAIL |
| Size: 6 DFU -> 3" whole length | child section Ø1.5" (parent Ø3") | FAIL |
| ≤1 wet-vented drain upstream of the dry-vent connection | WC and lav both enter upstream of x=120" | FAIL (2) |
| WC downstream of all other connections | WC is the first connection | FAIL |

Vertical (908.1) is no help: the WC does not discharge into the sink's drop, and a 3-DFU closet is not a 1-2 DFU upper fixture.

**Verdict: the sink is not a legal wet vent.** The WC has no true vent tee downstream of its arm, so the arm is **unvented
in the sense of 1002.2** — the 116" figure is moot. `PR-B-BATH-VENT` serves the WC by plan distance (67", `mep.trap_arm_length`)
but does not meet the drain. A fix is house work: a true vent tee on the WC arm within 72", or a bathroom-group-only,
3" wet vent with the WC last.
