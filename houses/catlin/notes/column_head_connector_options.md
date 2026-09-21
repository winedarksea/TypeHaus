# Column-head beam ties — the HETA20Z, and the backups (2026-09-21)

Design reasoning, not an oracle: the arithmetic is `north_entry_piers.md` §9. This note is
why the part is a cast-in **HETA20Z pair**, and what to switch to without re-researching.

## The joints

Eight wood beams bear on 12" round cast columns over an `SS316-SHIM-35` pack (1/2"-1" gap),
tied down by a pair of parts, one each beam face. All eight are **exterior**.

| joints | beam | exposure | governing demand (ASD) |
|---|---|---|---|
| `CN-SG-SEAT-R1/R3/F1/F3` (A, B) | 3-1/2" treated SYP glulam | open court, under the deck edge | guard 200 lb lateral |
| `CN-BW-TIE-E/GE` (A, B) | 2-2x8 KDAT, 3" | salted north entry, under the landing | guard 200 lb lateral |
| `CN-BW-TIE-RE/RNE` (A, B) | 3-2x12 KDAT, 4-1/2" | under the canopy roof | wind 411 lb lateral, 433 lb uplift |

## Why the HGAM10 left

1. **Simpson forbids it here.** C-C-2021 p.252 (masonry connectors): "Products shall be
   installed such that the Titen Turbo screws and Titen HD screw anchors are not exposed to
   the exterior environment" (C-C-2019 said "the weather"). A roof or deck overhead is
   still the exterior environment. The same footnote governs the `HUC212-3` pockets
   (`beam_water_protection.md`).
2. **G90 only.** No ZMAX/HDG/SS HGAM is sold, and G90 against treated wood misses IRC
   R317.3.1.
3. FL11473 note 6 permits only Titen screws "of the same diameter and length" at the
   concrete leg; a mechanically galvanized Titen HD is exterior-rated (ESR-2713 §5.20) but
   Simpson publishes no HGAM loads with it.

## The chosen part — HETA20Z, cast in, in pairs

- FL11473 (R4, sealed 2017-10-19) **Table 3**, double HETA, concrete, 2- or 3-ply, SP,
  12 HDG 16d (6 per strap): **uplift 2,560 / F1 1,350 / F2 1,430 lb** for the PAIR, already
  +60% for wind. The single part (Table 2) is 1,810 / 340 / 770.
- Conditions: 4" embedment, >= 6" concrete, 1-1/2" edge distance (the 12" rounds give 3-3/4"
  to 4-1/2"); anchors >= 3" apart (note 6); straps <= 1/8" wider than the member (note 3);
  f'c >= 2,500 psi (the columns are 5,000); lowest four holes of each strap filled.
- Ratios at the governing joints: canopy lateral 0.304, uplift 0.169; guard columns 0.237.
- **Combined (FL11473-R4 §9 Limitations item 4, graded since 2026-09-21):** canopy
  `0.169 + 0.304 = 0.473`. The HGAM10 pair it replaced read 1.263 on the same rule — the HETA
  pair is the head fix, and no further part is needed (`north_entry_piers.md` §9b).
- ZMAX (G185) with HDG nails meets R317.3.1. Stainless was not needed: every one of these
  heads stands well clear of grade, and the owner's pattern is stainless near the ground,
  ZMAX above (`PT-BW-W`/`-GW` bases stay `ABU66SS`).
- ~$3.79 ea retail (fastenersplus). 16 ea.

### Open items for the pour — verify, not assumed

- **The glulam is "2- or 3-ply" by WIDTH, not by ply count.** The seat beams (2-ply) and
  header (3-ply) are Table 3's row as printed. Read as 1-ply, the balcony pair's lateral is
  Table 2's 340 lb, and the guard still clears at 200 / 212.5 = 0.94.
- **The lowest nail holes vs the standoff gap.** Table 2 note 2 requires the lowest four
  holes filled; the beam soffit stands 1/2"-1" off the pour on the shim pack. Check the
  HETA20's lowest hole height against the pack before setting it; hold the pack to 1/2" if
  needed.
- **Placement.** Cast-in means the straps are set in wet concrete to a beam that is not
  there yet: a plywood template of each beam's footprint and face lines, and a surveyed top.
- **Reinforcement.** Simpson's typical detail shows a #5 bar in the member near the spoon.
  The columns carry (4) #5 verticals and #3 ties @ 10"; the spoon sits inside the cage.
  Confirm with Simpson or the PE.

## Backups, ranked

1. **MiTek (USP) HGAM10KT in Triple Zinc (G185)** — a post-installed gusset, if the pour
   is already done. MiTek catalog (62nd ed.) p.254 shows the Triple Zinc mark on the row;
   the part is absent from the TZ list on pp.16-18 and no retailer stocks it, so **confirm
   the stock number with MiTek (800-328-5934)**. SPF: 575 / 630 / 635 / 575 (DF/SP 980 /
   1,075 / 1,080 / 980), 4 WS15 + 4 DeWalt 1/4" x 1-3/4" Screwbolt+. Specify **WS15-EXT**
   screws — MiTek's plain WS is "not recommended" in treated wood — and an exterior-rated
   concrete screw. MiTek prints no exposure note, but a zinc-plated concrete screw in
   weather is the same problem Simpson names.
2. **Simpson HL35HDG / HL55HDG** (7 ga, HDG) through-bolted with 1/2" bolts, 1/2"
   mechanically galvanized Titen HD into the column. Min member 3-1/2", so **not the 3"
   seat beams**. HL loads are wood-to-wood only (C-C-2019 p.287; SPF 0.85x); the concrete
   anchor is an ACI 318 Ch. 17 design, which makes each joint an engineered item. HL35HDG
   from ~$18.
3. **HL46HDG — does not fit.** 3 ga, 3/4" bolts, min member **5-1/8"**; the widest beam
   here is 4-1/2". (One retailer lists it as 7 ga; the catalog says 3.)
4. **Simpson CCQM-SDSHDG column cap** — HDG, cast-in anchor rods, ~$305, made to order,
   non-returnable, sized for a 16" pier. Far over the demand.
5. **MiTek KHGLB beam seat** — cast in on two #6 dowels, primer finish only (would need
   custom HDG), replaces the shim pack, ~10x the demand. Not pursued.
6. **Custom 316 stainless angle + stainless Titen HD** — the fully stainless route; every
   joint becomes an engineered item. Only if ZMAX is ever refused at the entry.

## Sources

- Simpson FL11473 R4 Tables 1-3: floridabuilding.org, `FL11473_R4_AE_SIM201701 Sealed
  2017-10-19.pdf`
- Simpson C-C-2021 pp.252-253; C-C-2019 HGAM and HL sheets
- ICC-ES ESR-2713 (Titen HD), §5.20
- MiTek Structural Connector Catalog (2024) pp.16-18, 59, 254; MiTek HGAM10KT sheet
