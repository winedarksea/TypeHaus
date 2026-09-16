# Closed-cell spray foam — performance spec, qualifying products, application

Researched 2026-09-16 from the evaluation reports, TDSs and application guides themselves.
Covers every ccSPF line: the truss wall (4" exterior, `EXT_2X6`), the roof flash (5" under
the deck, `notes/roof_flash_and_batt.md`), the garage bays (2") and the rims (3").

**The spec is the requirement, not the brand.** Any product that meets §1 may be bought.

## 1. Requirements

Required:

1. **2 lb HFO closed-cell SPF with a CURRENT evaluation report** (ICC-ES, IAPMO UES or
   Intertek CCRR). A lapsed report does not qualify, whatever the product was.
2. **High lift: ≥ 4" in a single pass by the report** (or its TDS where the report defers
   to it). A 2"/pass product (e.g. Heatlok HFO *Pro*, ESL-1372) forces a cooling wait or a
   second visit on the wall, and the pricing assumes neither.
3. **Air-impermeable** at ≥ 1" — ASTM E2178 (material) / E283. This is what R806.5 item
   5.1.3 reads on the roof, and the wall has no other air barrier.
4. **R316.3 surface burning:** ASTM E84 flame spread ≤ 75 / smoke ≤ 450. Note every report
   below tests at ≤ 4"; **the roof's 5" exceeds the tested thickness** — confirm the report's
   thickness allowance behind the gypsum thermal barrier (R316.4) at submittal.
5. **Class II vapour retarder at design thickness** (all qualifiers reach it by 2").
6. **≥ 4" on a vertical surface with no backing**, by the report. The one-tier truss wall
   carries nothing in the foam on ESR-4073 §4.4.2's 7-1/4" (`catlin_truss_engineering.md`
   §1 item 2). SealTite: 7.5" (ER-720). OnePass, OPTIMAXX: confirm at submittal.

Strongly preferred, in this order:

7. **WRB recognition in the evaluation report** (ASTM E331 / ICC-ES AC71). The wall has no
   sheet WRB, so without it the water plane is a Minn. R. 1300.0110 alternate-approval
   request on the maker's own data. A report listing closes that item outright.
8. ABAA Evaluated Material (air and water).
9. NFPA 285. **Not an IRC requirement** (IBC Type I-IV walls only). No report found lists an
   assembly matching this wall — 4" exterior foam, no WRB, metal panel on girts — so it is
   informative only unless the AHJ asks.

## 2. Qualifying products

| Product | Report (valid to) | Max/pass | WRB (7) | Notes |
|---|---|---|---|---|
| Holcim **Enverge OnePass HFO** | IAPMO ER-859 (2027-02) | 4" | **In report**, ≥ 1.5", E331 | ABAA evaluated per TDS; NFPA 285 masonry/stucco only |
| Huntsman **Heatlok HFO High Lift** | ICC-ES ESR-4073 (2027-08) | 6.5" ≤ 70 F, 4" 70-80 F, 3.25" > 80 F | **No** — open 1300.0110 item | E84 tested ≤ 4"; back-to-back 3.25" + 3.25"; min 1"/pass |
| Carlisle **SealTite PRO HFO** | IAPMO ER-720 (2027-02) | 4" | Not in report; **ABAA air + WRB** cert (2023) | back-to-back 3" + 2.5"; min 0.5". Not "SealTite PRO Closed Cell" (ER-621) |
| NCFI **InsulStar OPTIMAXX 11-036** | IAPMO UES 667 | 4" (TDS) | AC71 + AATCC 127 per TDS | **report not yet read** — verify per-pass and WRB in it before accepting |

Not qualifying today:

- **JM Corbond IV** — IAPMO ER-146 lapsed 2026-07-31 (not renewed as of 2026-09-16). Also
  3.5"/pass in the report (4" in the TDS; the report governs). Re-admit on renewal.
- **BASF WALLTITE Max** (ESR-2642) and **UPC 2.0 High Lift HFO** (CCRR-0375) — 4"/pass not
  verified in a report; ESR-2642's WRB listing covers WALLTITE LWP, not Max.

Enverge OnePass is the only qualifier that closes item 7 in its own report, which makes it
the strongest fit for the wall. Heatlok High Lift stays acceptable on items 1-6.

## 3. Application

**Weather is a hold, not a preference.** Spray only on a dry day with substrate and ambient
**60-80 F**, sheathing / deck **< 16% MC** on a pin meter, bay by bay. In that window every
qualifier's single-pass limit is ≥ 4".

**Recommended: two back-to-back passes in one visit.** Pass 1 picture-frames every framing
edge, block side, buck and hanger flange (fillet, never butt square — BSI-048) and lays the
field at 1" — never thinner, whatever lower minimum a TDS allows; pass 2 brings the full depth as soon as pass 1's
surface is back under the maker's re-coat temperature (Carlisle: 10 min or ≤ 100 F; Huntsman:
core < 100 F). The point is corners: a thin first pass tacked into every inside corner is
more likely to seal them than one thick lift that bridges them.

| Line | Pass 1 | Pass 2 | Single pass allowed? |
|---|---|---|---|
| Wall, 4" | 1" | 3" | yes, where 4" ≤ the product's limit at the day's temperature |
| Roof, 5" (overhead) | **1.5-2"** (full deck adhesion, `roof_flash_and_batt.md` §9) | balance, ≤ the back-to-back limit (Heatlok 3.25") | no — 5" exceeds every limit above 70 F |

**No thin flash coat under 1".** Huntsman: "Flash coating to warm the surface is not a
recommended practice … may not have enough exothermic reaction present to properly cure."
JM ER-146 §3.2.3: a pass "of less than 1 inch … on cold surfaces [is] to be avoided and may
result in loss of adhesion of subsequent passes." Picture-framing itself is contractor
practice (BSC GM-2103), not in any maker's guide — it is fine as the first pass, not as a
separate sub-1" coat.

**Never exceed a pass limit to save time.** All three makers name over-thick lifts as a
charring and spontaneous-combustion risk, hours after application.

## Sources

- ESR-4073; Heatlok HFO High Lift Application Guide (20.00062) and TDS (20.00063)
- IAPMO ER-720; SealTite PRO HFO Application Guide and Submittal packet (2024-10-11)
- IAPMO ER-859; Enverge OnePass HFO TDS
- IAPMO ER-146; Corbond IV Installation Guide (BID-391) and data sheet
- NCFI InsulStar OPTIMAXX 11-036 TDS (2023-02-02)
- BSC GM-2103, Commercial Spray Foam Guide
