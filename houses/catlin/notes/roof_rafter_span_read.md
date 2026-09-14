# `RF-HOUSE` rafter span — published-table read

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Structure:** the house roof's 11-7/8" TJI 230 rafters at 24" o.c., 6:12, hung on the ridge
beam `RB-HOUSE` with LSSR2.37Z hangers.
**Written:** 2026-09-11, from the specifier's guide, before the check was pointed at it.
**Oracle for:** nothing in `typehaus/engineering/` — a PRESCRIPTIVE read, graded by
`structural.rafter_span` through `checks/structural/published.py`, pinned by
`tests/test_snow_checks.py`.
**What is asked of the reviewer:** two things — the high-end support condition in §3, which
is genuinely unresolved, and the hanger re-strike in §4. The span read itself is a table
lookup with 6-1/4" of margin.

> ⚠ **The 19'-3" this house quoted in five places was WRONG, and it is corrected here.**
> It was an interpolation between two published rows to this site's 35 psf roof snow.
> `checks/structural/snow.py` refuses exactly that move for its own sawn-lumber table —
> *"interpolating between two published rows is not a lookup, it is a design"* — and the
> same rule has to bind a manufacturer's table. The honest read of the published row is
> **18'-4"**. The roof still passes, by 6-1/4" instead of by an imagined 17-1/4".

---

## 1. The span, and which span it is

| Term | Working | Value |
|---|---|---|
| Horizontal run | ridge to bearing, perpendicular to the ridge | **17'-9 3/4"** (17.81') |
| Sloped length | the run at 6:12, x 1.118 | 19.91' |
| Spacing | resolved, not authored | **24" o.c.** |
| Profile | `ROOF` assembly | **11.875 TJI 230** |
| Flat-roof snow | Ps, ASCE 7-16 §7.3, Pg 50 at Ce/Ct/Is = 1.0 | 35 psf |
| Roof dead | the table's own basis | 15 psf |

**The comparison is the HORIZONTAL projection and the check enforces it.** An I-joist roof
table is indexed by horizontal clear span. At 6:12 the sloped length is 11.8% longer, so
comparing `member.length_m` against the row would fail a roof the table passes — and the
error grows with the pitch, which is exactly backwards.

## 2. The row, read verbatim

Weyerhaeuser **TJ-4000** *Trus Joist TJI Joist Specifier's Guide* (Jul 2019), p.12,
**"Maximum Horizontal Clear Spans"**, roof, low slope:

> 11-7/8" **TJI 230** at **24" o.c.**, **40 psf snow + 15 psf dead** → **18'-4"**

    17'-9 3/4"  <=  18'-4"        margin 6-1/4"

The row is read at 40 psf snow against this site's 35 psf, so the read is conservative on
load as well as inside on span.

## 3. The high-end support condition — UNRESOLVED, and it is the one open item

TJ-4000's roof-span table carries a general note about what has to be at the **high end** of
the joist. **Two transcriptions of that note in this house disagree, and the guide was not
re-read to settle it.** Stated rather than smoothed over:

- `notes/roof_flash_and_batt.md` §8 quotes it as *"a support beam or wall at the high end —
  ridge beam applications do not provide adequate support"*, which on its face excludes
  this roof outright.
- The 2026-09-11 reading behind this note has it excluding a ridge **BOARD** — a
  non-structural plate that only aligns the two slopes, leaving the rafters to work as a
  couple. On that reading `RB-HOUSE`, a real beam carrying the upslope reaction in bending
  to its own posts, is exactly the support the note asks for.

**What is not in dispute, and is the real condition:** these joists **HANG** off `RB-HOUSE`
on 38 LSSR2.37Z hangers rather than **bearing** on it, and every printed span table assumes
bearing. That is what makes the row indicative rather than final here, whichever way the
transcription goes.

**So the row is read, the margin is recorded, and ForteWEB owns the last word.** The check's
PASS is a prescriptive read of a published row, and the `condition` on the element says the
high-end support is unconfirmed. Somebody has to open TJ-4000 p.12's general notes and
settle §3 before this goes out; that is a five-minute job and it has not been done.

## 4. The hanger, re-struck — and this is the part to check

`notes/ridge_beam_detail.md` worked the hanger reaction at **600 lb**, at 4:12. The roof is
6:12 and the run is longer than that pass assumed. Re-struck here:

    tributary  = 17.81' / 2 x 2.0' o.c.        = 17.81 ft2
    reaction   = 17.81 x (35 + 15) psf          = ~890 lb
    with the ridge's share of the unbalanced case, take       **~980 lb**

    LSSR2.37Z, with web stiffeners, allowable   **1,090 lb**    d/c 0.90

**RE-SOURCED 2026-09-14, and the allowable moved for a reason worth reading.** This line
said **1,060 lb** until today. That is a real published number and it is the wrong row: it
is the **sloped AND skewed** case (Weyerhaeuser TJ-4000, Jul 2025, p. 15, TJI 230 /
LSSR2.37Z; the same 1,060 appears in IAPMO-ES ER-280 Table 11 at C_D = 1.00). Every document
that publishes this hanger splits the two — C-C-2026 pp. 178 vs 179, ER-280 Table 11,
TJ-4000 p. 15 — because skewing costs fasteners: CSG-TJUS25 p. 10, "All holes must be filled
except for the LSSR hanger **when skewed**", which takes the header schedule from 14 nails to
13 and the joist from 12 to 9. **`RB-HOUSE` is a straight ridge and these rafters land square
on it.** The joint is sloped only, and its row is **1,090 lb**.

**And 1,090 is the right KIND of number, which 1,565 was not.** TJ-4000 p. 15's general note:
"Hanger capacities shown are either joist bearing capacity or hanger capacity — **whichever
is less**." On a TJI the joist's own end bearing governs, not the hanger's steel, so the
1,565 lb that `ridge_beam_detail.md` §2 argued against is the hanger side alone and is not
available here at any fastener schedule. 1,090 is the connection.

    demand ~980 lb  /  1,090 lb at 100% duration            d/c 0.90
    with TJ-4000 p.16 fn.1's +15% snow-roof increase, 1,254 d/c 0.78

**Still tight, and still the number in front of the reviewer.** The 600 lb figure in
`ridge_beam_detail.md` is superseded by this line. Web stiffeners are not optional at this
reaction, and above 1/4:12 they are **beveled**, not square (TJ-4000 p. 14).

**No slope reduction applies.** ER-280 Table 11 note 4 bounds the tabulated loads at +45 to
-45 degrees of slope and skew and publishes no multiplier inside that range; 6:12 is 26.57
degrees. The 0.85 factor above 45 degrees belongs to the **LRUZ**, and CSG-TJUS25 p. 3's
sloped-joist reductions belong to hangers with no sloped seat (ITS, IUS, MIT, MIU, BA, HB,
WP, HU). Neither is this part.

**One open edge, and it is inside the margin.** Nothing published gives a sloped-only TJI
value by joist depth — TJ-4000's 1,090 is flat across 9-1/2" to 16", while CSG-TJUS25's
*skewed* numbers do vary with depth (1,080 / 1,105 / 1,105). CSG-TJUS25 p. 5 tabulates only
the skewed case and disagrees with TJ-4000 on it by ~4% (1,105 vs 1,060), attributable to the
header nail (2-1/2" 10DN there, 3" 10d in TJ-4000). At d/c 0.90 that spread does not decide
anything; a design sitting at the cap is a call to Weyerhaeuser, not a table read.

## 5. What is NOT graded here

- **The hanger.** §4 is a hand re-strike printed for a reader, not a check: nothing in this
  engine grades a hanger allowable against a computed reaction.
- **The eave oversail and the birdsmouth.** The row is a clear span between bearings.
- **Deflection beyond the row's own L/240**, and vibration, which a roof has no criterion for.
- **The high-end support condition of §3**, which no check can settle and which the element's
  `condition` string names for the reviewer.
- **The unbalanced and drift snow cases** on the gable. S-001 carries the drift number for
  the canopy; the house roof's own unbalanced case is inside the 40 psf column by inspection
  and has not been worked.
- **The two TRUSSED roofs.** `RF-GARAGE` and `RF-BW-CANOPY` resolve no rafter member at all,
  so no table describes them and they stay deferred to the fabricator
  (`notes/catlin_truss_engineering.md`).

## Sources

- **Weyerhaeuser TJ-4000**, *Trus Joist TJI Joist Specifier's Guide*, Jul 2019 — p.12
  "Maximum Horizontal Clear Spans". Cite the edition actually read.
- **ASCE 7-16 §7.3** — the flat-roof snow this site's 35 psf comes from.
- **Weyerhaeuser TJ-4000**, Jul 2025, p. 15 (Variable Slope Seat Joist Hanger) and p. 16
  footnote 1 — the LSSR2.37Z-on-TJI-230 **sloped-only** allowable in §4, and the snow
  increase on it. **Simpson C-C-2026** pp. 178-179 and **IAPMO-ES ER-280** Table 11 are the
  two other places the sloped-only/skewed split is published; **CSG-TJUS25** (Aug 2025)
  pp. 3, 5 and 10 gives the web-stiffener rule and the skewed-hole clause.
