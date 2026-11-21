# HL angle site bolts and lags — hand-worked lengths

**House:** catlin
**Structure:** the landing's four HL angles, `params/landing_tie.py`: CN-BW-GSTIE-LO/-HI
(HL43HDG, BM-BW-FE into W-G-S) and CN-BW-GWTIE-LO/-HI (HL33HDG, W-BW-SCREEN into W-G-W).
**Written:** 2026-11-21, by hand from the drawings' dimensions and the catalog page, before
`takeoff/site_bolts.py` was run against it.
**Oracle for:** `takeoff/site_bolts.py` (decision #147); reproduced by
`tests/test_fastening_schedules.py::test_hl_site_bolt_lengths_match_the_hand_note`.
**Companions:** `notes/north_entry_piers.md` §10 — what the ties carry and why they are there.
**What is asked of the reviewer:** §2's grips, and whether §4's far-face condition on line 2
is acceptable.

---

## 1. Rule

Bolt length = grip (wood the bolt crosses from the leg face) + the angle's steel + one USS
washer under the nut + heavy-hex nut height + two threads past the nut, rounded up to the next
stocked HDG A307 length (1/2" steps to 6", then 7, 8, 10, 12). The lag into the garage wall is
HL fn 7's minimum: a lag of the bolt's diameter, >= 5" long.

| term | 1/2" bolt | 3/4" bolt |
|---|---|---|
| USS washer (ASME B18.22.1 Type A, W) | 0.097 | 0.134 |
| heavy-hex nut (ASME B18.2.2) | 31/64 = 0.484 | 47/64 = 0.734 |
| two threads (13 / 10 TPI) | 2/13 = 0.154 | 2/10 = 0.200 |
| allowance | 0.735 | 1.068 |

Steel (C-C-2024 p. 303): HL33 7 ga = 0.1793"; HL43 3 ga = 0.2391".

## 2. Grips

| angle | leg on | wood crossed | grip |
|---|---|---|---|
| HL43 (line 1) | BM-BW-FE east face, x = 115" | FE 3-ply 4 1/2" (x 115 to 110 1/2), then the deck's last joist line, 1 1/2" (x 110 1/2 to 109), at the hole 2 3/4" (D3) off the heel | 6.000 |
| HL33 (line 2) | W-BW-SCREEN end pack east face, x = 75 15/16" | the 2x4 KDAT pack, 3 1/2", then the 7/16" ZIP behind it; stops at the corrugated | 3.9375 |

## 3. Lengths

| angle | working | need | stocked |
|---|---|---|---|
| HL43 bolt | 6.000 + 0.2391 + 1.068 | 7.307 | **8"** 3/4" bolt, 2 ea |
| HL33 bolt | 3.9375 + 0.1793 + 0.735 | 4.852 | **5"** 1/2" bolt, 2 ea |
| HL43 lag | fn 7 | 5.000 | **5"** 3/4" lag, 2 ea |
| HL33 lag | fn 7 | 5.000 | **5"** 1/2" lag, 2 ea |

## 4. Not graded here

- The bolt's capacity, edge and end distances: `deck_tie/FS-BW-FLOOR` and
  `north_entry_piers.md` §10 (line 1's 3.7D end distance stays an EOR item).
- Line 2's far face is corrugated over the ZIP: the nut and washer bear on the ZIP through a
  cut-out in the corrugated flute, sealed. The bolt is not run through the cladding.
- The lags' thread penetration past each filler is the EOR's (fn 7 states only the 5").

## Sources

- Simpson Strong-Tie Wood Construction Connectors C-C-2024 p. 303, HL table and fn 7-8.
- ASME B18.2.2 (nuts), ASME B18.22.1 (plain washers; B18.21.1 is lock washers) — dimensions
  as transcribed above, not re-read at review (2026-11-21). The stocked lengths do not hang
  on them: §3 leaves 0.148" (HL33) and 0.693" (HL43) of slack, more than any washer or nut
  tolerance.
