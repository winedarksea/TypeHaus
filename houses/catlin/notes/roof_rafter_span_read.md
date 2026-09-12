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

    LSSR2.37Z, with web stiffeners, allowable   **1,060 lb**    d/c 0.92

**That is tight, and it is the number in front of the reviewer.** The 600 lb figure in
`ridge_beam_detail.md` is superseded by this line. Web stiffeners are not optional at this
reaction.

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
- **Simpson Strong-Tie LSSR2.37Z** — the sloped/skewed hanger allowable in §4.
