# `WIN-M-DINING-E` header — published-table read

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Structure:** the 63" x 48" picture window in `W-M-E1` (bearing), centred at y=18'-0",
headed with a 2-ply 9 1/2" LVL.
**Written:** 2026-10-16, from the manufacturer's guide, when the window replaced
`WIN-M-LIV-E3` and `WIN-M-EAST-MID`.
**Oracle for:** nothing in `typehaus/engineering/` — a PRESCRIPTIVE read, graded by
`structural.header_prescriptive` through `checks/structural/published.py`, and pinned by
`tests/test_window_header_spec.py` (the mechanism) and the catlin check run.
**Companions:** `notes/garage_door_header.md` — the same idiom for `D-G-OVERHEAD`.
**What is asked of the reviewer:** whether the envelope argument in §3 is acceptable — the
row is read at a heavier condition than the wall, not at the wall's own condition — and the
double-1 3/4" substitution at the next stocked depth.

> ⚠ **R602.7 could size this header and the house chose not to let it.** The window is
> 63", inside R602.7's 8', so the table would answer with a 2-2x10. The house authors an LVL
> and the row that sizes it instead, and `structural.header_prescriptive` grades an opening
> within 8' only when it authors BOTH. Drop either and the header goes back to R602.7.

---

## 1. The opening, and what it carries

| Term | Working | Value |
|---|---|---|
| Rough opening | `WT-6348-FIX` | **5'-3"** (63") |
| Header authored | `Window.header_spec` | **2-ply 9.5" LVL**, resolved 66" long, 82"..91 1/2" |
| Roof | `RF-HOUSE`, ridge beam, zero overhang, 17'-9 3/4" run | ~8'-11" to W-M-E1 |
| Floor above | `FS-S-EAST`, 11 7/8" I-joists, x 18'-0 3/4"..35'-10 1/4" | 17'-9 1/2", ~8'-11" to W-M-E1 |
| Wall above | the second storey's east wall, 10' | ~100-120 plf |
| Flat-roof snow | Ps, ASCE 7-16 §7.3 at Pg 50, Ce/Ct/Is = 1.0 | 35 psf |

## 2. The row, read verbatim

Boise Cascade EWP, **VERSA-LAM 1.7 2650 Header Guide** (Eastern), 06/2009 r 07/21/2011, p.5,
**"3 1/2" VERSA-LAM 1.7 2650 Header Look Up Tables"**, Door and Window Headers,
**Roof Only + 1 Floor (no mid support)**, roof load **50 PSF Snow (115%), 15 PSF Dead**,
**32'-0" structure width**, clear span **5'-8"** → **8 5/8"**, not bolded (single trimmers).

Table notes: L/360 live and L/240 total; trusses bearing on the exterior wall with 2'-0"
max overhang; exterior wall 80 plf; uniform loads only; "Double 1 3/4" VERSA-LAM 1.7 2650
may be substituted in these tables".

    5'-3" RO  <=  5'-8" row        margin 5"

## 3. Why the row covers this wall

The row's own load on the header, at 32' and no mid support: roof (50 + 15) x 18' = 1,170 plf,
floor (40 + 12) x 16' = 832 plf, wall 80 plf — **~2,080 plf**.

This wall: roof (35 + 15) x 8.9' = 445 plf, floor (40 + 12) x 8.9' = 463 plf, wall ~120 plf
— **~1,030 plf**.

Roof and floor are each about half the row's; only the wall term exceeds its row value, by
~40 plf. The total is under half. The `PublishedSpan.load_psf` is the row's roof basis, 65,
which the check compares against its own 50 psf demand.

## 4. The member

1 3/4" VERSA-LAM is stocked at 9 1/2", 11 7/8", 14" and 16" (p.3), not 8 5/8". The
substitution is taken at the next stocked depth, **2-ply 1 3/4" x 9 1/2"**: same width and
grade as the tabulated 3 1/2" x 8 5/8", 7/8" deeper. A one-piece 3 1/2" x 8 5/8" VERSA-LAM
header is the equally good buy; the model would author it as the same 3 1/2" x 8 5/8"
section, which the spec parser does not spell.
