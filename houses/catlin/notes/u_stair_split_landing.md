# The U split-landing riser budget, hand-worked — ST-B2M and ST-M2S

Oracle for `resolve/stairs/u_split.py`, the way `catlin_truss_engineering.md` oracles
`wind.py`. Reproduced by `tests/test_stair_framing.py` and `tests/test_stair_tread_geometry.py`.

Written 2026-09-15, because this arithmetic had **no note and no oracle**, and a real defect
lived in it undetected: the upper flight was laid out backwards from the *lower* flight's
line, so on an odd tread split it stopped one going short of the deck it arrives at.

## 1. The budget

A split-landing U spends its risers on: `lower` treads, the lower landing, **one riser
between the two half-landings**, `upper` treads, and the arrival deck.

    lower + 1 + 1 + upper + 1 = risers        →   lower + upper = risers - 3

`flight_treads = risers - 3`, and the odd one goes to the **lower** flight:

    lower = ceil(flight_treads / 2)           upper = flight_treads - lower

| stair | risers | flight_treads | lower | upper | split |
|---|---|---|---|---|---|
| ST-B2M | 15 | 12 | 6 | 6 | even |
| ST-M2S | 16 | 13 | 7 | 6 | **odd** |

## 2. Each flight is anchored to the storey edge it meets

Run station `s` is measured from the departing deck edge, `+s` toward the landing zone.

- **Lower flight.** Springs at `s = 0`, which *is* the departing deck edge. Riser face for
  tread `i` at `s = going·i`. Ends at `flight_len = going·lower`.
- **Upper flight.** Arrives at `s = 0`, which *is* the arrival deck edge — the same plan
  line, one storey up. Counting back from its own landing: riser face for tread `i` at
  `s = upper_flight_len - going·i`, with `upper_flight_len = going·upper`.

The two lines coincide only when `lower == upper`. **Anchoring the upper flight to
`flight_len` instead of to its own length is the bug**: with `lower = 7, upper = 6` and
`going = 10"`, its top nosing landed at `s = flight_len - going·upper = 70 - 60 = 10"`,
leaving a 10" x 3'-6 3/8" strip of open floor opening at the head of ST-M2S.
`R311_7_5_1_stair_end_risers` compares *elevations* and never plan position, so it passed it.

### ST-M2S, going 10", 13 treads — hand-worked

    lower  i = 0..6 :  s = 0, 10, 20, 30, 40, 50, 60          flight_len        = 70"
    upper  i = 0..5 :  s = 60, 50, 40, 30, 20, 10             upper_flight_len  = 60"

`FO-S-STAIR`'s south edge — the second floor's deck edge — is `s = 0`. The upper flight's
walking line runs one going past its top nosing onto that edge, so the last tread at
`s = 10"` is the last *board* and `s = 0` is the arrival nosing. Flush.

In model y, the well springs at y = 312.375": lower risers y 312.375…372.375, upper risers
y 372.375…322.375, arrival edge y 312.375".

### ST-B2M, going 10", 12 treads

    lower  i = 0..5 :  s = 0, 10, 20, 30, 40, 50             flight_len       = 60"
    upper  i = 0..5 :  s = 60, 50, 40, 30, 20, 10            upper_flight_len = 60"

Equal counts, so the fix is a no-op here — which is exactly why nothing caught the odd case.

## 3. Where the odd going goes: the landing zone

The two half-landings stay **flush at the far end of the well**. That flushness is what
makes the 180° crossing work, and it holds the opening budget fixed: the well still needs
`landing_depth + going·lower`, which is what `_stair_fits_opening` validates.

    landing-lower :  s0 = flight_len,        depth = landing_depth
    landing-upper :  s0 = upper_flight_len,  depth = flight_len + landing_depth - upper_flight_len

So the **upper** half-landing absorbs the slack, one going deeper per odd tread:

| stair | landing-lower | landing-upper | far end |
|---|---|---|---|
| ST-B2M | s 60…96, 36" | s 60…96, 36" | s = 96 (y 408.375") |
| ST-M2S | s 70…106, 36" | s 60…106, **46"** | s = 106 (y 418.375") |

Both ≥ 36", so `R311_7_6_landing_depth` — which reads each landing member's own `length_m`
— passes on each independently. A landing may be deeper than the flight is wide; it may not
be shallower.

## 4. The well partition stops at the SHORTER flight

The partition's studs run `z0 → arrival` — the full storey. Its plan extent is

    s ∈ [inset, min(flight_len, upper_flight_len) - inset],   inset = 0.20 m

Carried to `flight_len` instead, on ST-M2S it would run to s = 70" while **the upper
landing's deck starts at s = 60"** — studs straight through a walking surface, at
s ∈ [60", 69.8"]. Nothing draws it and no plan shows it;
`test_member_interference.py::test_stair_support_framing_reports_no_interference` is the
only thing that sees it.

The lower flight's inner stringer loses partition bearing over that last 10";
`_bear_stair_on_walls` posts down where nothing reaches.
