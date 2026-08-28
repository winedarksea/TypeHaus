# Uplift load path — roof to footing (2026-08-28)

The house had connectors at the ends of the load path and nothing in the middle. The sill was
anchored (MASA at 4' o.c.), the studs were tied to their top plates (SP6), the stacked corners
were strapped (CS16), and the *hung* member ends carried hangers (LSSR at the ridge beam, LUS
and HUCQ in the sunken garden). Between those, every joint where a member **bears** on
something was gravity and nails: 56 roof rafters birdsmouthed onto the attic top plate, ~290
floor-joist bearings across five floors, 34 garage truss heels, and every beam landing on a
post outside the breezeway.

The target is a continuous path with commodity parts — roughly FORTIFIED-Home detailing, not
an engineered wind design. Cost-effectiveness was the constraint that picked the parts.

## What is derived now

`packages/engine/src/typehaus/takeoff/uplift.py`, rules in `takeoff/hardware_config.py`
(`UpliftTieRules`). Nothing below is authored in this house — it follows the geometry, so a
wall that moves takes its hardware with it.

| Joint | Part | Count | Rule |
|---|---|---|---|
| Rafter / truss heel on its bearing wall | H2.5A | 56 + 34 | one per seated end |
| Floor joist on its bearing line | H2.5A | 258 | one per bearing joint (a lap is one joint) |
| Beam landing on a wood post | KBS1Z | 18 | one per beam end |
| Bottom plate of a framed wall on a framed floor band | LTP4 | 108 | 4' o.c., min 2 per wall |
| Across the floor band where framed walls stack | CS16 | 72 straps (2 coils) | 8 at the corners + 64 along the runs at 4' o.c. |

Roughly **$590–1,160 of material** on a house whose hardware line was already $11.9k. That
ratio is the argument for doing it: it is the cheapest structural money in the estimate.

The strapping row is an *extension* of a rule that already existed, not a new one. It used to
fire only at stacked framed-exterior corners, which gave this three-storey house **eight**
straps — two per 36 ft facade, with the middle thirty-two feet of every elevation holding the
storey above it on rim-board nailing. That is where uplift is largest on a 4:12 roof.
`WallTieRules.wall_strap_pitch_ft` is the run term, set to 4 ft so the mudsill anchors, the
tie plates and the straps all read as one rhythm rather than three schedules a framer has to
hold apart.

## The decisions, and why

**H2.5A everywhere a member bears, not a bigger tie.** The catalog already stocked it and
`prices.toml` already priced it. A heavier tie (H10A, or H2.5A in pairs) is the obvious
upgrade and it is one config field away — `UpliftTieRules.ties_per_bearing` — but it doubles
the largest count in the whole job, and the cheap tie at *every* joint buys far more than an
expensive tie at some of them.

**KBS1Z, not PC6Z, at a post/beam joint.** Cheaper and, per the manufacturer's tables,
stronger. PC6Z is catalogued (`ROLE_POST_CAP`) for the joints that want a true seated cap —
the round central column, a 6x6 under an attic-level beam — and is authored, never derived.

**One strap per beam end, not the matched pair.** A pair only fits where the beam stops at the
post. The balcony beams run past their pillars and have one reachable face. This is the same
correction `KneeBraceRules` already carries, where a pair rule billed twelve unbuildable
braces.

**LTP4 only where a wall stands on a *framed* floor band.** A wall standing on concrete is a
sill, and its MASA anchors already make that connection. Including it billed 179 plates
instead of 108, 71 of them a second anchor at a joint that was already paid for.

**No anchor bolts.** `ConnectorKind.ANCHOR_BOLT` and the `AB-050-10-BP` catalog record exist
now, and S-100 can schedule a diameter and an embedment for one. This house does not use them:
MASA at 4' o.c. already exceeds IRC R403.1.6's 6' maximum on every sill run, and bolting the
same plate again would be double-anchoring. The parts are there for a house that wants bolts.

## What is still authored by hand

The derived rules skip any joint an authored `Connector` already names — that guard is what
keeps the sunken garden's and the breezeway's twenty connectors from being bought twice.

- 6 × ABU66SS under the balcony pillars, 4 × under the breezeway posts (`params/`)
- 4 × KBS1Z at the breezeway **roof** beams (its floor beams are derived)
- 4 × HUCQ410-SDS into the sunken garden's concrete beam pockets
- 3 × H2.5A at the two cast columns and the sistered porch bearing
- 4 × STHD holdowns at the exterior door jambs (main storey)

## What the model still cannot answer

`structural.uplift_load_path` reports every joint as covered or broken, and reports these as
**not evaluable** rather than pretending either way:

- **The two cast columns** (`PT-SG-COL` 12" round, `PT-SG-FCOL` 16" square) on their cast
  footings. That joint is made by reinforcement and this model carries no rebar. The user's
  own hardware notes list the intended detail — an STHD on each axis with an SM1 holder, an
  HGAM10 angle, A34/A44 angles to the beam, a KGLB5B beam seat, and stainless or G-10
  isolation between column and concrete. None of it is modelled yet.
- **Three 4x4 stairwell posts** (`P-M-STRWELL-S/N`, `P-M-STRLAND-SE`) declare no
  `supported_by`, so there is no joint to grade. Giving them one would let the ABU44 rung of
  the post-base ladder derive a base — but an interior dry post wants a different part than a
  standoff base, so this is left open deliberately rather than answered with the wrong SKU.
- **Capacity, everywhere.** The check reports coverage as UNKNOWN, never PASS. The model
  carries no design wind speed (`sheet.roof_framing.design_loads` says so), so "there is
  hardware here" is the only claim being made.

## Purchasing

Parts are catalogued as Simpson because that is what `library/hardware.py` and the published
load tables it cites already use. MiTek sells an equivalent for every one of them and is
usually cheaper:

| Simpson | MiTek | Joint |
|---|---|---|
| H2.5A | H2.5 | rafter / joist to plate |
| LTP4 | TP37 class | plate to band |
| KBS1Z | — (use the strap tie family) | beam to post |
| ABU66 / ABU44 | ABU-equivalent standoff base | post to pier |
| MASA | MA-series mudsill anchor | sill to concrete |

Swapping is a purchasing decision, not a modelling one: `prices.toml` can carry the cheaper
number under the Simpson key. Changing the catalog would mean two products per role, which
`hardware_for_role` refuses by design.

## The beam-cap interaction

Anything added at a KDAT beam top has to respect `beam_water_protection.md` §2: AWC DCA6, no
aluminium against copper-treated lumber, and the formed caps are bedded **on** the butyl tape.
The 18 derived KBS1Z straps land on the pillar faces, not the beam tops, so they do not
disturb that order — but a future cap or seat at a beam top would.
