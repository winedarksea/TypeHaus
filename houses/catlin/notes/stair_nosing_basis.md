# Stair nosings: tread depth measured nosing to nosing (2026-09-28)

Graded by `code.R311_7_5_2_tread_depth` (`checks/code/mn_residential/stair_nosings.py`) and
`code.R311_7_6_stair_head_landing` (`checks/code/mn_residential/stair_arrival.py`).
`tests/test_stair_nosings.py` reproduces §3 and §4.

## 1. The rules

- **R311.7.5.2**: tread depth ≥ 10", measured horizontally between the vertical planes of the
  foremost projection of adjacent treads. **R311.7.5.2.1**: within a flight, the greatest
  depth may exceed the smallest by 3/8" at most.
- **R311.7.5.3**: nosing projection 3/4"–1 1/4" where the tread is under 11". The greatest
  projection may exceed the smallest by 3/8" at most "between two stories, including the
  nosing at the level of floors and landings".
- **R311.7.6**: a landing at the top of each stairway, as wide as the stairway and 36" in the
  direction of travel.

## 2. What was wrong

Every riser board stands behind its riser line (face on the line), except the head riser.
That one stood in FRONT of the framing it faced, its face 3/4" short of its line. Measured
from the nose of the tread below to the head riser's face:

| Flight | the other steps | the head step | 
|---|---|---|
| going 10", nosing 1" (oak, carpet) | 10 + 1 = 11" | 10 + 1 − 0.75 = 10.25" |
| going 11", no nosing (exterior) | 11" | 11 − 0.75 = 10.25" |

With a 1" nosing at the landing or floor edge, the last tread is 10.25 − 1 = **9.25"**
against 10". That is 0.75" of spread, over the 3/8" limit. The exterior flights come out
10.25" against 11": also 0.75".

Also, the U-stair's **upper** flight boards sat one nosing toward the head. Each ran from its
own riser line back 11", with no overhang past its own riser.

## 3. Built, by hand

The head riser's face is now on its line and the board stands past it, so the framing it
meets sits one board beyond the line (one board plus the carpet on ST-B2M):

- ST-M2S / ST-B2M: both half-landings start 3/4" (1 1/4") past their flights and the upper
  flight hangs that far off the stairhead header.
- ST-S2A: FO-A-STAIR's west edge moved 22'-5 3/8" → 22'-4 5/8".
- ST-G-SERVICE start 50'-9 5/8" → 50'-10 3/8"; ST-SG-PORCH start 32.167' → 32.229'.

A lip over every riser that climbs onto a landing or floor projects the flight's nosing past
that riser's finished face.

| Flight | depths | projections (incl. landing / stairhead lips) |
|---|---|---|
| ST-B2M | 12 × 10" | 14 × 1" (6 + 6 treads, lower landing (carpet over the nose), LVP stairhead) |
| ST-M2S | 14 × 10" | 16 × 1" (7 + 7 treads, lower landing, oak stairhead) |
| ST-S2A (straight run) | 12 × 10" | 13 × 1" (12 treads, oak stairhead) |
| ST-G-SERVICE, ST-SG-PORCH | 4 × 11" | 4 × 0" |

ST-B2M's split step, up onto the upper half-landing, gets a lip too. It is a sideways riser,
so no straight run reads it.

## 4. The stairhead landing

ST-S2A's head is the tightest. It climbs west. The header is at x = 268.625" and the lip
reaches 0.75" riser + 1" nosing east of it, so the top nosing is at x = 270.375". RM-A-STUDY's
west clear face is at x = 219.38", which leaves 270.375 − 219.38 = 51.0" of floor past the
nosing against 36", across the 36" stair width.
