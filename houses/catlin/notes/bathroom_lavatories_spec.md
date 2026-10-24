# Bathroom lavatories, faucets and plumbing

Owner selections implemented 2026-10-24. Replaces the Swan/Arvo allowances and the kids'
quartz/Caxton assembly. [Powder-room support and fittings](main_bath1_basin_spec.md) remain
selected. `plan/lav_types.py`, `bath2_vanity_types.py`, `lav_ports.py` and `bath_finish.py`
hold the catalog; placed elements remain in `fixtures.py`.

## Assemblies

Dimensions below are inches, width × depth. The IKEA footprint includes the ceramic top's
half-inch side overhang. SEKTION cabinets are 30 in. tall, 14¾ in. carcass depth plus fronts,
on a 2¼ in. ledger chase; the 24 and 30 in. assemblies retain their 18 in. room footprint.
Both 30 in. halves remain separate fixtures below **one 61 in. Corian top**, keeping two
bowls, two drains and two lavatory loads. The attic's separate Corian top is 24 × 18 in.

| Fixture | Primary / basin and top | Footprint | Rim AFF | Faucet / finish | Trap | Backing |
|---|---|---|---|---|---|---|
| `FX-B-BATH-LAV` | IKEA ÄNGSJÖN 36 + ORRSJÖN 37 | 37 × 21.75 | 36 | Indy KBF-1401SFS, stainless | RÄNNILEN 1-bowl | `BK-B-CW2-VANITY-*` |
| `FX-M-BATH1-LAV` | Duravit 07054500002 | 17.75 × 13.375 | 34 | B21010001U10, chrome | 707BN-1 | `BK-M-HS1-BASIN` |
| `FX-M-BATH2-SINK` | IKEA SEKTION 36x15x30 wall, 2 AXSTAD matte white doors + solid-surface undermount lavatory, 16 3/8 x 13 x 5 | 48 × 18 | 36 | Genta LX 6702, chrome | 707BN-1 | `BK-M-W3-VANITY-*` |
| `FX-S-BATH1-LAV` | IKEA ÄNGSJÖN 36 + ORRSJÖN 37 | 37 × 21.75 | 36 | Genta LX 6702, chrome | RÄNNILEN 1-bowl | `BK-S-BA-E1B-VANITY-*` |
| `FX-S-SUITEBATH-LAV` | Kohler Chulton K-REC39579-ASB-0 | 30.9375 × 22.4375 | 36 design; approximate | Genta LX 6702, chrome | 707BN-1 | `floor-standing` |
| `FX-S-VANITY-LAV1` | IKEA SEKTION 30x15x30 AXSTAD + solid-surface undermount lavatory, 16 3/8 x 13 x 5 | 30 × 18 | 36 | Genta LX 6702, chrome | 707BN-1 | `BK-S-BD-N-VANITY-*` |
| `FX-S-VANITY-LAV2` | IKEA SEKTION 30x15x30 AXSTAD + solid-surface undermount lavatory, 16 3/8 x 13 x 5 | 30 × 18 | 36 | Genta LX 6702, chrome | 707BN-1 | `BK-S-BD-N-VANITY-*` |
| `FX-A-STUBATH-LAV` | IKEA SEKTION 24x15x30 AXSTAD + solid-surface undermount lavatory, 16 3/8 x 13 x 5 | 24 × 18 | 36 | Indy KBF-1401SFS, stainless | 707BN-1 | `BK-A-HALL-S-VANITY-*` |
| `FX-A-STUDIO-BAR-SINK` | IKEA SUNNERSTA integral sink | 18 × 14 | 36 | Indy KBF-1401SFS, stainless | 707BN-1 | `SUNNERSTA frame` |

The theme parameter `finish.bath_theme` accepts `chrome` or `brushed-nickel` and changes
five Genta LX 6702 faucets to 6702BN, including the two occurrences of the SEKTION 30 type.
The three utility Indy KBF-1401SFS faucets remain stainless; B.2 remains chrome. The declared
`brushed-nickel` variant demonstrates the switch. Invalid values raise `KeyError` at import.

**Chulton drilling gate:** the manufacturer's dimensioned image for **REC39579-ASB-0** says
single-hole and gives **30 15/16 × 22 7/16 in.**, with **39 5/16 in. overall height including
backsplash**. The retailer's grouped listing says 8 in. widespread. The white model's own
manufacturer image controls this selection, so **6702 fits**. Confirm the ordered SKU
against that image; the maker's installation drawing and drain/supply stations remain
unavailable, and the model deliberately marks all three ports APPROXIMATE.

## Connection stations

Plan x/y are project inches. Each cell lists **(x, y; z above finished floor)**. PipeRun
heights are authored above their filing storey's datum; ports use the fixture's storey.
The selected DRAIN station is the **wall/trap-arm stub**, rather than the basin outlet
inside the trap. Adjustable RÄNNILEN tubes or cut-to-fit tubular traps join the basin to it.
The resolver uses the body's actual mount base, including finished-floor build-up, then
adds local port z and converts back to the fixture storey datum. This keeps the plumbing
connection and the 3D port at the same height.

These EXACT ports are **chosen installation setout**, not claims that a maker publishes a
fixed trap height. IKEA's assembly instructions give adjustable plumbing, not fixed outlet
coordinates. The fabricated SEKTION/Corian bowls' mouths are 16⅜ × 13 in., centered across
each cabinet, with local y = -1⅛ in.; their faucet holes are 2½ in. off the back, leaving
the 2¼ in. faucet base clear of the bowl mouth. This moves those bowls ⅝ in. forward from
the earlier generic symbol. Those dimensions do not describe the purchased ORRSJÖN,
Chulton, or SUNNERSTA basins. Their bowl and faucet setbacks must be checked against the
physical products; the model massing is illustrative. Do not fabricate a bowl template
from those meshes.

| Fixture | Drain (x, y; AFF z) | Hot (x, y; AFF z) | Cold (x, y; AFF z) | Certainty |
|---|---|---|---|---|
| `FX-B-BATH-LAV` | (144.000, 218.250; 20.000) | (147.000, 218.250; 24.000) | (141.000, 218.250; 24.000) | EXACT setout |
| `FX-M-BATH1-LAV` | (53.500, 268.000; 20.000) | (50.500, 271.385; 24.000) | (60.000, 271.385; 24.000) | EXACT setout |
| `FX-M-BATH2-SINK` | (6.510, 182.250; 20.000) | (6.510, 179.250; 24.000) | (6.510, 185.250; 24.000) | EXACT setout |
| `FX-S-BATH1-LAV` | (116.745, 374.500; 20.000) | (116.745, 377.500; 24.000) | (116.745, 371.500; 24.000) | EXACT setout |
| `FX-S-SUITEBATH-LAV` | (165.500, 264.755; 20.000) | (162.500, 264.755; 24.000) | (168.500, 264.755; 24.000) | APPROXIMATE |
| `FX-S-VANITY-LAV1` | (22.375, 316.245; 20.000) | (19.375, 316.245; 24.000) | (25.375, 316.245; 24.000) | EXACT setout |
| `FX-S-VANITY-LAV2` | (52.375, 316.245; 20.000) | (49.375, 316.245; 24.000) | (55.375, 316.245; 24.000) | EXACT setout |
| `FX-A-STUBATH-LAV` | (164.625, 265.625; 20.000) | (161.625, 265.625; 24.000) | (167.625, 265.625; 24.000) | EXACT setout |
| `FX-A-STUDIO-BAR-SINK` | (152.500, 201.740; 20.000) | (149.500, 201.740; 24.000) | (155.500, 201.740; 24.000) | APPROXIMATE |

The standard installation stations are **20 in. waste and 24 in. supply AFF**. Resolved
storey-relative elevations also include each room's finished-floor thickness; the powder
bowl's 20 in. AFF drain is authored at 20.9862 in. above the main-floor storey datum.
`mep.fixture_port_connection` checks
serving run endpoints in plan and elevation (1 in. exact tolerance; 3 in. reporting band for
approximate ports). An approximate station always returns UNKNOWN. Authored drain overrides
more than 1 in. from the port fail independently. Carrier-wall drain snapping is retained.

Each lavatory has dedicated accessible angle stops. Shared isolation stops remain upstream.
The powder-room stops retain their existing tags. The house tubular trap is Dearborn
707BN-1, 1¼ in. 17 ga chrome brass with cleanout, plus a listed 1½ in. wall transition.
RÄNNILEN is accepted for ORRSJÖN under the owner's IKEA-US compatibility policy.

## Routes and room coordination

- Basement: ORRSJÖN remains centered at x = 12 ft. The 37 in. top fits the 39.94 in. run.
  Its 21¾ in. carcass/top envelope clears the WC's required envelope; the recommended
  lavatory front zone overlaps it and remains advisory. **ERV condensate now ends 38 in.
  AFF over the basin**, about two inches above its 36 in. flood rim, through a visible air gap.
  This avoids an unverified receptor behind the drawers and keeps the discharge accessible.
- Kids bath: 37 in. top extends ½ in. past each side of the 36 in. box; east wall and tub
  return remain clear. The cabinet-mounted towel bar/pad follow the actual cabinet side, below the top overhang. The electric
  cable polygon retains 2 in. cabinet clearance and its purchased 338 W cable.
- Alcove: both drain stubs are at real trap-arm height; the shared arm drops at its existing
  connection to the stack. The 30 in. bowl spacing and existing receptacle are retained.
- Suite: the larger Chulton footprint remains clear of the WC/front zone and south wall.
- Attic: the existing floor drop is retained to avoid FO-A-HALL's trimmer and BM-S-BATH-E.
  A drawn 1½ in. upper branch reaches the new basin, with a revent at the north wall beside
  it, then joins the existing 2 in. branch. The 49 in. undrawn connection is removed.
  The upper branch crosses 2×4 studs within their bore limit and clears the exhaust riser.
- Bath2: the old hot riser moves out of the aisle. Terminal branches run in the west-wall
  service band; the new vent rises above the window head before offsetting north and tying
  into the powder-room vent. Terminal arms and under-floor branches remain distinct runs.

Rail/foot backing is explicit for every floating cabinet. Backing ends land on studs or wall
ends, rather than stopping at the cabinet edge between studs. SEKTION shelves remain
`included_in_host`; drawer cabinets and Chulton's own interior get no separate shelf banks.
The duplicated Bath2 faucet/bowl allowances are removed: role-tagged parts bill separately,
fabricated tops bill by area, and the faucet allowance buys five Genta, three Indy and one B.2.

## Source archive and remaining product facts

Read 2026-10-24:

- [IKEA US ÄNGSJÖN guide](assets/ikea-angsjon-guide.pdf), plus
  [cabinet assembly](assets/aengsjoen-bathroom-vanity-with-drawers-high-gloss-white__AA-2400655-5-100.pdf).
  Cabinet 36 × 21 × 25⅛ in.; heights count from the body base. House sets cabinet base
  8⅜ in. AFF, cabinet top 33½ in. and ceramic rim 36 in.
- [ORRSJÖN installation](assets/orrsjoen-sink-white__AA-2376395-4-100.pdf) and
  [RÄNNILEN installation](assets/raennilen-water-trap-1-bowl__AA-2141893-6-100.pdf).
  Ceramic overall basin envelope includes a deeper bowl below the 2½ in. deck rise.
  Neither sheet gives a fixed wall-stub AFF height or dimensioned bowl center setback.
- [SEKTION wall cabinet assembly](assets/ikea-sektion-wall-cabinet-install.pdf) and
  [AXSTAD care](assets/ikea-axstad-care.pdf). The US combinations are 694.614.71 (30 in.)
  and 594.645.35 (24 in., two doors); their kitchen listing is not a bathroom listing.
- [Moen 6702/6702BN specification](assets/moen-6702-spec.pdf): single-hole or optional 4 in.
  centerset plate, 3/8 in. compression, metal pop-up. Allow the published 2½ in. rear
  operating clearance when drilling fabricated tops.
- [Kraus Indy specification](assets/kraus-kbf-1401-spec.pdf) and
  [installation](assets/kraus-kbf-1401-install.pdf): 6¼ in. overall height, 5⅛ in. reach,
  4⅝ in. spout height, 23⅝ in. hoses and 3/8 in. compression; drain selected separately.
- [Kohler white Chulton dimensional image](assets/kohler-chulton-30-dimensions.jpg).
  Manufacturer rough-in PDF not obtained; ports remain approximate. SUNNERSTA's bowl
  position likewise remains approximate until measured.
- [Dearborn cleanout trap catalog](https://www.oatey.com/products/P_041193054678/dearborn-114-in-brass-tubular-ptrap-with-cleanout).
  No manufacturer dimensional PDF obtained for 707BN-1; cut-to-fit wall connection is a
  house setout rather than a fixed factory dimension.

Manufacturer dimensions and missing facts remain distinguished in `Product.source`.
