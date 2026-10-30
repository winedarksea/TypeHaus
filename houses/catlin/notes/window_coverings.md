# Window coverings: ceiling-track curtains and cellular shades

**Decision record · 2026-10-29.** Types: `plan/window_covering_types.py`. Placement:
`plan/window_coverings.py`. Prices: `prices.toml` (estimates). This replaces the seven
main-floor curtain rods. Nothing has been purchased.

## The seal rule

A rod leaks at the top (an open band up to the ceiling) and at both ends, so a closed
curtain becomes a convective loop against cold glass. Every run here is laid out so that
**every closed curtain edge ends against a wall**: in a room corner, in a VIDGA end-closing
curve that returns the track to the wall, or at a centre overlap. A ceiling track seals the
top, and the heading rises around the rail to hide it. The panels are floor length and the
hem just kisses the floor (the model puts the envelope ½" off it).

## Runs, as built in the model

Each track type's envelope is the **closed** curtain (run × 6" × the drop), so placeable
collision grades furniture against where the curtain closes. The 3D view draws the curtain
open, in the listed stacks. `CurtainTrackSpec.show_curtains=False` draws the rail alone.

| Run | Mount | Line | Extent | Stacks (open) | Fixing |
|---|---|---|---|---|---|
| `FURN-M-LIV-TRACK-S` | ceiling, 107½" datum | y 9 9/16" | x 301" (end-closing) → 425¼" (SE corner) | 337–352", 352–367" (mid-pier) | `FS-S-EAST` extra joist line y 9½" |
| `FURN-M-LIV-TRACK-BALC` | wall `W-M-S2`, rail top 88" AFF | 3" off wall | x 219½" (C1 corner) → 291" (end-closing) | 219½–226½", 284–291" | 3 fittings; ends on `BK-M-S2-ROD` + king packs |
| `FURN-M-BED-TRACK-W` | ceiling, 107½" datum | x 9 9/16" | y 6¾" (SW corner) → 153½" (NW corner) | y 73–88", 88–103" (W1/W2 pier) | crosses `FS-S-WEST` trusses at 16" |
| `FURN-S-STUDY-TRACK-DECK` | ceiling, 227½" | y 9 9/16" | x 219½" (corner) → 291" (end-closing) | 219½–233½" (one-way, west) | `FS-ATTIC` extra joist line y 9½" |

The two extra lines are 6½" off the y=16" line and 9½" off y=0, so both keep their own tie
(`resolve/floor_lines.extra_lines`). They add three I-joist pieces (FS-ATTIC's is in two
pieces at the centre bearing), 60 LF ordered. The FS-ATTIC line also runs over the plant
room's ceiling, which is harmless.

**The BALC middle fitting is a field item.** The run spans `D-M-BALC`'s header (x 221⅓–
290⅔"), which sits 1¼" behind the stud face; a backing band cannot cross a header. VIDGA
wants a fitting every ≤ 140 cm, so the middle one needs a ripped 2x nailer on the header's
room face at the rail line (88½" above datum). The two end fittings land on wood
(`advisory.wall_fixing_support`); the middle one is suppressed in `preferences.toml` with
this reason.

### Measured clearances (resolved model, 2026-10-29)

- Every ceiling envelope's top is exactly on its ceiling (107.5" / 227.5").
- Fiddle-leaf fig: moved 5½" north (y 25⅛"), ⁹⁄₁₆" off the closed living curtain.
- STRANDMON: moved 3" east, ¾" off the closed bedroom curtain.
- `ED-M-PORCH-FLOOD-SW` / `-SW`: 1" from the S run's west end and from BALC's east end.
- `EQ-M-HP2-LIVING`: its bottom (90" AFF) is 2" above the BALC rail top.
- `ED-S-STUDY2-SPOT1`: 1" east of the deck run's end-closing curve.
- Receptacles behind a closed curtain, at ~16–18" AFF: `ED-M-LIVING-RC5` (behind the
  mid-pier stack), `ED-M-BED-RC6`, `ED-M-BED-RC7`, `ED-S-STUDY2-RC1`. A cord there breaks
  the hem seal; prefer the room's other outlets for anything left plugged in.
- Ceiling items (cans, `ED-M-BED-FAN`, registers, heads) are all clear of every closed line.

## Shades

| Element | Opening | Type | Drive |
|---|---|---|---|
| `FURN-M-BED-BLIND-S1/-S2` | `WIN-M-BED-S1/-S2` | 30×48 | cordless |
| `FURN-S-STUDY2-SHADE-S1/-S2` | `WIN-S-STUDY1/-2` (south) | 30×48 | motorized |
| `FURN-S-STUDY2-SHADE-E` | `WIN-S-STUDY3` (east) | 27×48 | motorized |
| `FURN-A-STUDY-SHADE-JUL-E` | `WIN-A-S-JUL-E` | 27×54 | motorized |
| `FURN-A-STUDY-SHADE-S3` | `WIN-A-S3` | 14×24 | cordless (under the motor's minimum width) |

Inside mount, in the reveal. `advisory.wall_backing_present` now reads a body that sits
wholly within an opening's rough opening as fixed into the opening (N/A), which also
covers the living-room blinds.

## Products

- **Curtains: IKEA VIDGA single track, white** (rail 204.929.16, 140 cm / 55", $8.99,
  cut to length). One family has ceiling and wall fittings, gliders, a corner piece and the
  end-closing set (s594.282.60). The panels are IKEA block-out curtains on multi-heading
  tape, so the hook height sets how far the heading rises around the rail, at ~1.8–2×
  fullness. The owner's Cbsroro example is double-row; VIDGA single gives the same look.
- **Shades: SmartWings cellular, light filtering, made to measure**, with the
  **Matter-over-Thread** motor, a rechargeable battery and the **solar panel** on the glass
  side. Reviewers run it locally in Home Assistant. The cordless units are the same line,
  so one vendor covers every new shade. South (STUDY1/2, JUL-E) and east (STUDY3) panels
  charge well; the attic desk does not shade the glass side.
- **Rejected:** IKEA PRAKTLYSING/TREDANSEN (Zigbee through DIRIGERA, fixed 60/80 cm widths
  that miss 26–29" inside mounts, no solar). Lutron Serena (local, but through the Caséta
  bridge's Clear Connect rather than Matter, and about twice the price).
- **Roller vs cellular.** Cellular runs about R-2 to R-3 from its trapped air, a roller
  about R-1.3 to R-1.8. Rollers are more durable and wipeable, and screen fabrics keep the
  view and cut glare; cellular pleats catch dust. Cellular was chosen for insulation. These
  are retailer figures; no AERC rating is in hand. SmartWings sells rollers on the same
  motor.

## Exclusions

- **Plant room: no shades.** Its glass sits only 1.9 °F above the room's dew point at the
  centre of glass (`notes/plant_room.md`). A shade traps still, humid air against it and
  turns that margin into condensation.
- **Living east row**: the existing blinds, untouched.

## Home Assistant

- Matter over Thread needs a **Thread border router** on Home Assistant (e.g. HA Connect
  ZBT-2 set to Thread). That is an owner item; the house models no HA hardware.
- **Tilt-turn windows** (STUDY1/2/3): mount the headrail at the reveal's room edge so a
  tilted sash clears the lowered fabric. Turn mode needs the shade fully raised.
  **Automation rule: no auto-lowering while a sash is turned.**

## Field items

- Confirm the US article numbers, the panel sizes and the price at order.
- Fullness 1.8–2×; hem each panel to kiss the floor after the track is up.
- Confirm the motorized minimum width (WIN-A-S3 is assumed under it).
- Confirm the stack plus headrail clears the tilt-turn sash top in turn mode, and the
  Andersen folding crank (BED-S1/S2, JUL-E) clears the shade.
- The BALC header nailer (above).
