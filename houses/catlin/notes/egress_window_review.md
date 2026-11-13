# Egress window review: the nine R310 escape windows

Design reasoning, not a calc oracle. The escape units are `WIN-M-BED-S1`/`S2`, `WIN-S-BED1`,
`WIN-S-BED2`, `WIN-S-HALL-N`, `WIN-S-SUITE1`/`2`, `WIN-A-S-JUL-W`/`E`. Lines, prices and the rest
of the schedule are in [window_and_door_procurement.md](window_and_door_procurement.md). The first
section is the current basis; the Andersen 400 basis below it is history and the documented revert.

## Max Light escape units (2026-11-13)

Owner: as few window brands as possible, Polish wherever practical. The 9 moved from Andersen 400
casements to **Aliplast Max Light Modern tilt-turns** (fabricator Słowińscy, NFRC STO-M-20,
U 0.20 / SHGC 0.40 / VT 0.58). Tags WT-2748 / WT-2748-T / WT-2754 / WT-3048 are kept. The house
is now **Drutex 29 + Max Light 12**, both Polish, one Max Light fabricator: 23 tilt-turns, 0
casements, and the Juliets open inward.

| Window | Type | Wall | Role | Unit (Max Light) | Est. clear W×H | Clear area |
|---|---|---|---|---|---|---|
| WIN-S-BED1 | WT-2748-T | W-S-E2 | BEARING | 26.21×46.805 | 20.15×44.05 | 6.16 sf |
| WIN-S-BED2 | WT-2748 | W-S-E3 | BEARING | 26.21×46.805 | 20.15×44.05 | 6.16 sf |
| WIN-S-HALL-N | WT-2748 | W-S-N1 | nonbearing | 26.21×46.805 | 20.15×44.05 | 6.16 sf |
| WIN-S-SUITE1/2 | WT-2754 | W-S-W3 | BEARING | 26.21×52.805 | 20.15×50.05 | 7.00 sf |
| WIN-A-S-JUL-W/E | WT-2754 | W-A-S2/S3 | nonbearing | 26.21×52.805 | 20.15×50.05 | 7.00 sf |
| WIN-M-BED-S1/S2 | WT-3048 | W-M-S1 | — | 28.71×46.805 | 22.65×44.05 | 6.93 sf |

### The clear opening is an estimate, not a credit

No published figure was found. A web search on 2026-11-13 read Aliplast's fiche: 35 mm frame +
35 mm sash visible on inward-opening units, frame depth 75 mm, sash depth 84 mm, glazing to
68 mm, a concealed-hinge option on the Invisible variant, and **no opening angle**.

The model authors `net_clear_width_deduction` = 2×35 + 84 = **154 mm** (two frames plus the 84 mm
sash standing at 90° on the hinge side) and `net_clear_height_deduction` = 2×35 = **70 mm** on the
resolved unit (`plan/window_types.py`, `_MAXLIGHT_CLEAR_W/H`). Width margin is **0.15"** over
R310's 20".

- `haus check` passes R310 in every graded sleeping room on these figures. RM-A-STUDIO is a craft
  room, so the Juliets are not graded.
- Energy is unchanged: 30,212 heating and 16,296 cooling Btu/h.
- Performance is a wash: Max Light 0.20/0.40/0.58 against Andersen 0.20/0.40/0.51. The swap also
  clears three Andersen holds: the triple was sold in the Northeast only, the face split was
  unpublished, and the frame was vinyl rather than powder coat.
- Prices: the four rows scale from WT-1424-TT the way it was set (size-matched operable band,
  ratio 1.0, so they equal WT-2748-TT etc.). No dealer quote is implied.

### Ruled out (NFRC directory, 2026-11-13)

- **One Max Light order for all 41 units.** Max Light fixed is best U 0.17 (STO-M-19). The plant
  room needs U ≤ 0.14 for `glazing_dew_point`, and Drutex fixed is 0.14-0.15.
- **Drutex for egress.** DRU-K-25 (Alucover casement, U 0.18) exists, but a 74 mm frame + 50 mm
  sash leaves about 17" clear at a 27½" RO.
- **Other fabricator.** Słowińscy: STO-M-20 carries the 0.20/0.40/0.58 row. Plastixal's PLX-K-17
  low-U row is SN63HT solar-control glass (SHGC 0.22).

### Supplier gate (a construction hold)

Ask Słowińscy for a **written** net clear opening, W × H, for the turn sash at the three unit
sizes (26.21×46.805, 26.21×52.805, 28.71×46.805), and the hinge's maximum opening angle. Confirm
also:

- NAFS DP ≥ 20 and a nail-fin option.
- The 16 CFR 1201 mark on WIN-S-BED1 (-T).
- RAL and gloss match to the Drutex caps.
- An **exterior screen that releases from inside without tools** on all 9 (R310.4; an inward sash
  cannot take an interior screen): retractable or push-out.

### If the figure holds, and if it does not

If the written figure is ≥ 20" W / 24" H / 5.7 sf at 27½", write it into the type as
`net_clear_width`/`net_clear_height` and cite the document. If it falls short at 27½":

- HALL-N and the two Juliets are on nonbearing walls, where the RO ladder allows 30". The Juliets
  then need a rake recheck (2¼" margin), and HALL-N loses its one-width column with WIN-A-N2.
- BED1/2 and SUITE1/2 are on bearing walls and have no fallback. Andersen 400 is the documented
  revert on those four (the brand count then does not fall). That is an owner decision.

## Andersen 400 basis (2026-10-23), superseded 2026-11-13 and kept as the documented revert

Every figure below is the Andersen 400 casement's; none applies to the Max Light units above.

**Every 27" RO is now 27½", the full jack-to-jack clear of a one-stud break** (30½" bay
less two 1½" jacks, `preferences.toml`). The owner asked for one buck pattern across the
family, so all eighteen former 27" openings widened, not only the seven escape casements.
Centres, studs broken, headers, sills and heads are unchanged; each `from_node` jamb offset
dropped ¼" to hold its centre, and each adjoining braced panel gave up ¼". The perimeter
detail is unchanged: ⅜" buck, 0.020" membrane and ¼" shim gap at each jamb and the head;
the sill consumes about 0.550" (buck + pan fall + 0.060" membrane). Only the unit grows.

The resolved seat now sizes an orderable unit where the type states one
(`WindowType.frame_size_increment` and `minimum_rough_opening_allowance`). The four
Andersen types carry ⅛" and ½": the unit must clear both the shim gaps and Andersen's
RO = unit + ½" inside the **flashed** opening, rounds **down** to ⅛", stays centred between
the jambs and bears on the pan; the head takes the remaining slack. Schedule, IFC, renders
and R310 all read that one seat. Drutex types state no step (made to the mm) and keep the
continuous envelope.

| RO | Modeled unit / frame |
|---|---|
| 14×24 | 12.710×22.805 (Drutex) |
| 27½×36 | 26.210×34.805 (Drutex) |
| 27½×48 | 26.210×46.805 (Drutex) · **26⅛×46½ (Andersen)** |
| 27½×54 | 26.210×52.805 (Drutex) · **26⅛×52½ (Andersen)** |
| 30×48 | 28.710×46.805 (Drutex) · **28⅝×46½ (Andersen)** |
| 63×48 | 61.710×46.805 |

The two garage frames are 13.460×23.553" (14×24 RO less a 0.270" jamb/head and 0.177" sill seat). **WIN-B-SAUNA is unresolved:** its
manual court-opening detail supplies no modeled seat. Its schematic placeholder is not a
frame dimension; A-602 prints UNRESOLVED and IFC leaves overall frame dimensions unset.
Add a dimensioned buck/pan/seat detail before ordering it. Stool heights still require the
supplier's sill adaptor and sash-overlap section (procurement note §2.6).

For the selected Andersen 400 widest-opening hinge, the engine applies the published
**unit-width deduction of 5.81"** to the resolved unit. The height deduction is 4.43" for
WT-3048's unit (inside 28⅜"–31½" × 40 13/16"–48") and 4.85" for the narrower types. Exact
published clear openings remain supported for other catalog products. A selected product
without clear-opening data (including the Drutex tilt-turns) receives no nominal-RO credit.

| Escape windows | RO | Unit | Calculated clear | Area |
|---|---|---|---|---|
| WIN-M-BED-S1/S2 | 30×48 | 28⅝×46½ | 22.815×42.070 | 6.67 sf |
| WIN-S-BED1, BED2, HALL-N | 27½×48 | 26⅛×46½ | 20.315×41.650 | 5.88 sf |
| WIN-S-SUITE1/2, WIN-A-S-JUL-W/E | 27½×54 | 26⅛×52½ | 20.315×47.650 | 6.72 sf |

All six sleeping rooms pass `code.R310_egress` (20" × 24", 5.7 sf). This is **calculated
compliance with procurement confirmation outstanding.** Before ordering, obtain written
confirmation of the exact units, widest-opening hinges, glazing, operator and any opening-
control device, the actual net clear openings, and the installation requirements; the
installer must confirm the finished flashed openings and attachment detail accept those
units. If confirmation fails, the thinner-buck path below is the fallback to revisit.
The 63" dining picture window stays an owner-approved exception with its own LVL header
(`preferences.toml`, `notes/dining_window_header.md`).

Sources checked 2026-10-23:
[Andersen 400 opening specifications](https://www.andersenwindows.com/-/media/Project/AndersenCorporation/AndersenWindows/AndersenWindows/files/technical-docs/area-and-opening-specifications/area-openingspecifications-windows--400series-casement.pdf),
[Minnesota R310](https://www.revisor.mn.gov/rules/1309.0310/).

### Fallback, not taken: a thinner buck at the 27" RO (investigated 2026-10-23)

Superseded by the 27½" RO above; kept in case supplier confirmation fails.

The narrowest product path found is the already-selected Andersen 400 casement with its
widest-clear-opening hinge, paired with a thinner buck detail. Andersen's 2025–26 guide
allows custom widths in ⅛" increments, gives clear width as unit width minus 5.81", and
specifies minimum RO as unit width plus ½". At the current 25.710" modeled frame envelope,
the largest size that rounds down is 25⅝", for 19.815" clear. The next size, 25⅞", gives
20.065" clear and fits a 27" RO only if the combined buck and membrane thickness is at most
⅝", preserving Andersen's ½" installation allowance. With the 0.020" membrane each side,
that means buck thickness no greater than about 9/32" per jamb; the current buck is ⅜".

This is a concrete supplier/installer question, not an approved detail. Confirm that a
25⅞" unit is available with the specified hinge and glass, that its actual egress opening
meets R310 with the selected operator and any opening-control device, and that a 9/32" buck
can be securely fastened and flashed in the outie wall. The 27×48 units would then have
about 20.065" × 41.955" clear (5.84 sf); the 27×54 units about 20.065" × 47.955" (6.68 sf).
The existing 30×48 pair remains ample. The check must use the supplier's confirmed ordered
dimensions, not these screening calculations.

No second catalog product was verified to fit the present 27" RO/frame envelope and
provide the required clear width. Andersen 100 Series' published widest-opening formula
loses 7.790" from unit width; it does not help at this size. Do not treat fixed jamb width
as opening width: the sash swings outside, but the jambs stay in the passage. Andersen's
published 400-series clear-opening formula already captures that distinction. The adopted
2020 Minnesota Residential Code (2018 IRC base) requires a 20" net clear width, 24" height,
the applicable minimum area, and dimensions achieved by normal operation from inside; the
Minnesota amendments do not change R310.2.1.

Sources checked 2026-10-23:
[Andersen 400 opening specifications](https://www.andersenwindows.com/-/media/Project/AndersenCorporation/AndersenWindows/AndersenWindows/files/technical-docs/area-and-opening-specifications/area-openingspecifications-windows--400series-casement.pdf),
[Andersen 100 opening specifications](https://www.andersenwindows.com/-/media/Project/AndersenCorporation/AndersenWindows/AndersenWindows/files/technical-docs/area-and-opening-specifications/area-openingspecifications-windows--100series-casement.pdf),
[Minnesota R310](https://www.revisor.mn.gov/rules/1309.0310/).
