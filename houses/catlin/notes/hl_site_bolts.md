# HL angle site bolts and lags — hand-worked lengths

**House:** catlin
**Structure:** the landing's site bolts, `params/landing_tie.py` (G5 layout, 2026-11-23):
CN-BW-GSTIE-LO/-HI (HL43HDG, one per face of BM-BW-FE, into W-G-S) and the DTT2Z pair's rod
(CN-BW-GSDTT-S/-N). Line 2's HL33HDG pair (CN-BW-GWTIE-LO/-HI) is retired — §5.
**Written:** 2026-11-21, by hand from the drawings' dimensions and the catalog page, before
`takeoff/site_bolts.py` was run against it.
**Oracle for:** `takeoff/site_bolts.py` (decision #147: `site_bolt_rows`, `tension_rod_rows`);
reproduced by `tests/test_fastening_schedules.py`.
**Companions:** `notes/north_entry_piers.md` §10 — what the ties carry and why they are there.
**What is asked of the reviewer:** §2's grips and §6's rod length.

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
| HL43, east (CN-BW-GSTIE-LO) | BM-BW-FE east face, x = 115" | FE 3-ply 4 1/2" (x 115 to 110 1/2), then the deck's last joist line, 1 1/2" (x 110 1/2 to 109), at the hole 2 3/4" (D3) off the heel | 6.000 |
| HL43, west (CN-BW-GSTIE-HI) | the east rim joist's west face, x = 109" | the rim 1 1/2" (x 109 to 110 1/2), then FE 4 1/2" (to 115) | 6.000 |

Both clear HL fn 5's 5 1/8" for the 4-series. The west angle sits on the rim, not on FE: on
FE's own west face its bolt would grip FE alone, 4 1/2", under fn 5 (2026-11-23).

## 3. Lengths

| angle | working | need | stocked |
|---|---|---|---|
| HL43 bolt | 6.000 + 0.2391 + 1.068 | 7.307 | **8"** 3/4" bolt, 2 ea |
| HL43 lag | fn 7 | 5.000 | **5"** 3/4" lag, 2 ea |

## 4. Not graded here

- The bolt's capacity, edge and end distances: `deck_tie/FS-BW-FLOOR` and
  `north_entry_piers.md` §10 (line 1's 3.7D end distance stays an EOR item).
- The lags' thread penetration past each filler is the EOR's (fn 7 states only the 5").

## 5. Retired 2026-11-23 (G5)

Line 2's two HL33HDG and their 5" 1/2" bolts and lags went with the screen's MSTA49Z collector
(`north_entry_piers.md` §10p). The 11-21 working was HL33 bolt 3.9375 + 0.1793 + 0.735 = 4.852
-> 5"; it bills nothing now.

## 6. The DTT2Z pair's rod

One 1/2" HDG threaded rod joins CN-BW-GSDTT-S (on FE, 4" south of the garage cladding) and
CN-BW-GSDTT-N (inside the garage, 8" north of it), on one N-S line (C-C-2026 p. 326, the
deck-to-house lateral detail: "1/2" diameter HDG threaded rod with nuts and washers").

| term | in |
|---|---|
| seat to seat | 4 + 8 = 12.000 |
| each end: 14 ga seat 0.0747 + USS washer 0.097 + heavy-hex nut 0.484 + two threads 0.154 | 0.810 |
| need | 12.000 + 2 x 0.810 = 13.620 |
| stock cut | **18"** (12 / 18 / 24 / 36), 1 ea |

## Sources

- Simpson Strong-Tie Wood Construction Connectors C-C-2024 p. 303, HL table and fn 7-8.
- ASME B18.2.2 (nuts), ASME B18.22.1 (plain washers; B18.21.1 is lock washers) — dimensions
  as transcribed above, not re-read at review (2026-11-21). The stocked lengths do not hang
  on them: §3 leaves 0.148" (HL33) and 0.693" (HL43) of slack, more than any washer or nut
  tolerance.
