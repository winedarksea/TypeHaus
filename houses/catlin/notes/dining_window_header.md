# `WIN-M-DINING-E` header — published-table read

**House:** catlin, Ramsey County, Minnesota (MN Residential Code 2020, adopting the 2018 IRC).
**Structure:** the 84 1/2" x 48" mulled triad in `W-M-E1` (bearing), centred at y=18'-0",
headed with a 2-ply 11 7/8" LVL on double jacks.
**Written:** 2026-10-16, from the manufacturer's guide, when a 63" picture replaced
`WIN-M-LIV-E3` and `WIN-M-EAST-MID`. **Re-read 2026-11-16** for the triad, from the public
PDF (Boise's media CDN, file `LVL-E2300 E versa-lam 1_7e 2650 header guide.pdf`, PDF dated
2011-07-22), p.5, lower table.
**Oracle for:** nothing in `typehaus/engineering/` — a PRESCRIPTIVE read, graded by
`structural.header_prescriptive` through `checks/structural/published.py`, and pinned by
`tests/test_window_header_spec.py` (the mechanism) and the catlin check run.
**Companions:** `notes/garage_door_header.md` — the same idiom for `D-G-OVERHEAD`.
**What is asked of the reviewer:** whether the envelope argument in §3 is acceptable — the
row is read at a heavier condition than the wall, not at the wall's own condition — and the
double-1 3/4" substitution at the next stocked depth.

> ⚠ **R602.7 could size this header and the house chose not to let it.** The window is
> 84 1/2", inside R602.7's 8', so that table could answer too. The house authors an LVL
> and the row that sizes it instead, and `structural.header_prescriptive` grades an opening
> within 8' only when it authors BOTH. Drop either and the header goes back to R602.7.

---

## 1. The opening, and what it carries

| Term | Working | Value |
|---|---|---|
| Rough opening | `WT-8448-FIX` | **7'-0 1/2"** (84 1/2") |
| Header authored | `Window.header_spec`, `header_jacks=2` | **2-ply 11.875" LVL**, resolved 90 1/2" long, 82 1/4"..94 1/8"; 11" clear under the plates |
| Roof | `RF-HOUSE`, ridge beam, zero overhang, 17'-9 3/4" run | ~8'-11" to W-M-E1 |
| Floor above | `FS-S-EAST`, 11 7/8" I-joists, x 18'-0 3/4"..35'-10 1/4" | 17'-9 1/2", ~8'-11" to W-M-E1 |
| Wall above | the second storey's east wall, 10' | ~100-120 plf |
| Flat-roof snow | Ps, ASCE 7-16 §7.3 at Pg 50, Ce/Ct/Is = 1.0 | 35 psf |

## 2. The row, read verbatim

Boise Cascade EWP, **VERSA-LAM 1.7 2650 Header Guide** (Eastern), 06/2009 r 07/21/2011, p.5,
**"3 1/2" VERSA-LAM 1.7 2650 Header Look Up Tables"**, Door and Window Headers,
**Roof Only + 1 Floor (no mid support)**, roof load **50 PSF Snow (115%), 15 PSF Dead**,
**32'-0" structure width**, clear span **7'-2"** → **11 1/4"**, **bolded** (set in the
table's red bold face): "Bolded beam depths require double 2x trimmers at each end", so the
window authors `header_jacks=2`.

The rest of that row's 50 psf / 32' column, for context: 5'-8" → 8 5/8" (the 63" picture's
read, not bolded), 6'-2" → 8 5/8", 6'-8" → 9 1/2", 8'-2" → 11 1/4" (bolded).

Table notes: L/360 live and L/240 total; trusses bearing on the exterior wall with 2'-0"
max overhang; exterior wall 80 plf; uniform loads only; "Double 1 3/4" VERSA-LAM 1.7 2650
may be substituted in these tables".

    7'-0 1/2" RO  <=  7'-2" row        margin 1 1/2"

## 3. Why the row covers this wall

The opening changed and the loads did not: the tributaries below are the 63" read's.

The row's own load on the header, at 32' and no mid support: roof (50 + 15) x 18' = 1,170 plf,
floor (40 + 12) x 16' = 832 plf, wall 80 plf — **~2,080 plf**.

This wall: roof (35 + 15) x 8.9' = 445 plf, floor (40 + 12) x 8.9' = 463 plf, wall ~120 plf
— **~1,030 plf**.

Roof and floor are each about half the row's; only the wall term exceeds its row value, by
~40 plf. The total is under half. The `PublishedSpan.load_psf` is the row's roof basis, 65,
which the check compares against its own 50 psf demand.

## 4. The member

1 3/4" VERSA-LAM is stocked at 9 1/2", 11 7/8", 14" and 16" (p.3), not 11 1/4". The
substitution is taken at the next stocked depth, **2-ply 1 3/4" x 11 7/8"**: same width and
grade as the tabulated 3 1/2" x 11 1/4", 5/8" deeper. A one-piece 3 1/2" x 11 1/4" VERSA-LAM
header is the equally good buy; the spec parser does not spell that section.
