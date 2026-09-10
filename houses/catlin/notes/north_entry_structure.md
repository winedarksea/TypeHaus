# North entry — the bearing map, 2026-09-10

Implements [the selected concept](../../../plans/north-gable-extension.md). **This note is
the bearing map: what carries what, and what the drawings must say that the model cannot.**
The arithmetic lives in `notes/north_entry_piers.md`, which is the oracle for
`engineering/roof_beam.py` and the pier calcs.

> ⚠ **This file described a schematic on 2026-09-10 and no longer does.** Every "off-model
> structural package", "custom fabrication" and "sizes provisional" phrase it carried was
> describing structure that did not exist. The six-foot south roof extrusion stood on
> nothing; the landing hung off the house basement walls on six invented connectors with a
> part number in no catalog; and two engine escapes converted the whole of that into five
> tidy UNKNOWNs and two priced rows. All of it is now built and graded.

The garage keeps its 24-foot square frost-depth ICF foundation. What changed is that the
passage between house and garage is **its own roof on its own structure**, not a cantilever
off the garage's gable.

## 1. The canopy — freestanding

`RF-BW-CANOPY` — four 24'-span trusses at 24" o.c. on two headers, each header on **two**
columns of its own. `CANOPY_ROOF` is `GARAGE_ROOF`'s structure with **no insulation and no
ceiling**: an open outdoor bay has no thermal boundary to hold, and billing one over it
would order 144 sf of R-38 blown fiberglass and 5/8" gypsum nobody installs.

> ⚠ **The headers bore on `W-G-W` / `W-G-E` until 2026-09-10 and that was never a detail.**
> A ~3,130 lb point reaction on the END of a stud wall wants a bearing post through the
> plate, the stud bay, the sill and the ICF stem, and no such post was authored, drawn or
> billed. `bearing_refs` naming a wall is this engine's idiom for a beam landing ALONG a
> wall; it grades nothing about one landing on a wall's terminus. **The canopy now carries
> its own gravity load to its own piers and shares nothing structural with the garage but
> the sheathing plane.**

| Member | Support | What the drawings must say |
|---|---|---|
| `RF-BW-CANOPY` | `BM-BW-RW`, `BM-BW-RE` | Sheathing runs **continuous** across the garage south wall line. Two `Roof` elements, one diaphragm — and that diaphragm is the canopy's only connection to the garage. |
| truss-to-header | `CN-BW-TRTIE-W1..4`, `-E1..4` | One **stainless `H2.5ASS`** each end of every truss. Not the galvanized H2.5A the rest of the house buys: these land on treated southern pine at an entry that is salted every winter. |
| `BM-BW-RW` / `-RE` | `PT-BW-CW`/`-CNW` and `PT-BW-CE`/`-CNE` | 3-ply 2x12 KDAT, top at +7'-4" = the garage plate. 4'-11" between columns, running 8" past the north column so the roof plane reaches the garage wall. |
| `PT-BW-CW` / `-CE` | `PT-BW-W` / `PT-BW-RE` | 6x6 KDAT, 7'-8 1/4". `ABU66SS` standoff base on a cast-in `AB-058-10-SS`; `CCQ46SDS2.5` cap at the header. |
| `PT-BW-CNW` / `-CNE` | `PT-BW-GW` / `PT-BW-RNE` | Identical. `PT-BW-CNW` shares its pier with the garage-side seat beam exactly as `PT-BW-CW` shares one with the house-side seat. |

> ⚠ **No ladder framing anywhere at this joint, and there used to be thirty lookouts.**
> `RF-GARAGE`'s south gable and both ends of `RF-BW-CANOPY` are **close rakes** — the roof
> deck cantilevers past the gable truss and the fascia hangs on it. The garage's south
> projection is 1 9/16", at a line where the roof does not even end, and the canopy's own
> south drip edge is 3 3/8". Neither is built with a 2x4 lookout and a 2x6 barge rafter, and
> the engine framed both until `_FLUSH_RAKE_TOLERANCE_M` went from 1/2" to 6".

> ⚠ **The canopy has no lateral system of its own, and that is unchanged by going
> freestanding.** All four column bases are standoffs on a 5/8" cast-in bolt — uplift ties,
> not moment connections. East-west wind goes into the roof sheathing and spans north across
> the garage south wall line into the garage roof diaphragm; north-south wind runs axially
> along the two headers. **Both paths die if that sheathing joint ever becomes a structurally
> separate plane.** If it does, put a `KBS1Z` knee brace at each column — a live, rated,
> priced row in this house at $3.50–6.50.

## 2. The landing

`FS-BW-FLOOR` retains uid `BWFS01AAAA`. Finished surface 0" at both thresholds; framing one
inch lower for the composite. Five exterior rises from −34" are exactly 6.8".

**The landing touches nothing on the house.** Grep `params/breezeway.py` for `W-B-` and
expect nothing but comments. Its house-side bearing is two cast piers on the pier line at
y=37'-6", not brackets standing off the basement concrete.

| Member | Support | What the drawings must say |
|---|---|---|
| `BM-BW-HOUSE-SEAT` | `PT-BW-W`, `PT-BW-E` | 5'-6" between two 12" round piers, soffit −1'-3 1/2". `SS316-SHIM-35` pack under it (bearing, and the dielectric off the pour), `HGAM10` gusset (the tie). |
| `BM-BW-GARAGE-SEAT` | `PT-BW-GW`, `PT-BW-GE` | Identical span, elevation and detail. |
| `BM-BW-FW` | Both seat beams | Off the column line at x=6'-6" — `PT-BW-CW` occupies the deck's own framing band on x=6'-0". |
| `BM-BW-FC` / `-FE` | Both seat beams **and** `PT-BW-IC` / `-IE` | Continue into the garage to the interior landing. The tips are POSTED. |
| `FS-BW-FLOOR` joists | FW / FC / FE | Flush hangers at 12" max centres, joist tape, stainless fasteners. |

> ⚠ **`PT-BW-IC`/`-IE` bear on `SL-G-FLOOR` and the thickening under them is a NOTE, not an
> element.** Thicken the slab to 10" over a 2'-0" square under each, cast monolithic. A `Pad`
> was tried and is the wrong element: a thickening is one pour with the slab, and modelling
> it separately reports a `concrete_interference` lap with the slab it is part of.
> `structural.deck_footing_size` reports NOT_APPLICABLE and names this as what it excludes.

> ⚠ **Hold the deck boards 1/2" off the house cladding and let the gap drain.** Boards run
> tight to a rainscreened wall dam the drainage plane and hold water against it. Abutting is
> not bearing, so this costs the "touches nothing" rule nothing — but it must be DRAWN,
> because a carpenter will otherwise close it.

The garage-side floor system is the structural zone inside the door, not a second concrete
landing; a 1/4" drainage/movement break separates its board field at the threshold. It
extends three clear feet beyond the ICF inner face, `ST-G-SERVICE` arrives at its north
edge, and `SL-G-STEP-0` is retired.

## 3. The tiers — four cast pours on a compacted base

`SL-BW-TIER1..4`, 18" going, one riser (6.8") thick each, **wedding-caked**: tier *i* runs
from the landing edge east to the front of its own tread, so every tier above the first is
fully bedded on the one below it and nothing here spans. EXPOSED_MIX (ACI 318-19 F3 + C2),
broom finish, 1/4" per foot of cross-fall east. `ST-BW-ENTRY` carries the flight's *code*
geometry — rise, going, width, the guard it serves — and frames nothing (`carriage="cast"`).

This is the third scheme and the two it replaced are worth keeping, because each failed for
a reason that is easy to walk back into.

**A cut stringer failed three ways.** An 8'-0" horizontal span against DCA 6 Fig. 28 / IRC
R507.13.1's 6'-0"; a 4.71" throat against its 5"; and treads wanting supports closer than
12". Narrowing the going to 18" fixes the span and does *not* fix the throat — notch depth
is driven by the long going, so a flatter pitch removes *more* material, and holding 5" at
6.8:18 would want an 11.54"-wide member.

**KDAT box frames on eight 42"-deep piers failed on the piers.** They were laid out running
east from the stair foot at x=17'-6" while the flight runs **west** to x=11'-6", so all
eight stood under open ground carrying nothing at all. Nothing in the check tree noticed,
because nothing grades whether a pier is under the thing it names.

> ⚠ **These are NOT frost-founded and that is a decision, not an oversight.** Minn. R.
> 1303.1600 puts Zone II at 42"; these bear about 6" down on compacted washed rock. The
> tiers will move with the ground. A monolithic pour moves **as one piece**, so what a
> winter costs is the joints at the two ends, not the risers in between — and riser
> uniformity has only 3/8" of tolerance (R311.7.5.1). At the bottom the pavers are a
> flexible field and nothing depends on them. **The joint that matters is at the TOP**,
> where the fourth tier meets a deck landing standing on piers that will not move. Draw it,
> and expect to shim or re-pour that one riser once.
>
> The framed alternative on the same base would have been worse, not equal: a settling box
> turns the flight into a cantilever off `BM-BW-FE`, which nothing in that assembly can do.
> And the prescriptive route to a shallow section does not exist here — IRC R403.3 applies
> only to buildings kept at 64°F or warmer and says outright it "shall not be used for
> unheated spaces such as porches", Minnesota's Rules 1309.0403 amendment carries no
> exceptions, and ASCE 32 is a stamped engineered submittal. **This is an owner's decision
> to accept movement on an unheated exterior terrace, taken knowingly.**

## 4. The screen, which is now in-fill

`SC-BW-WEST` runs from `PT-BW-CW` north to the garage wall — 5'-5 1/2", under the 6'-0" post
spacing the prescriptive guidance assumes — and stops at the header soffit, so it is a
simply-supported panel rather than an 8'-0" free-standing cantilever. **That top restraint
is what deletes the unsolved base moment its old `engineering_note` was asking someone to
resolve, and it is free once the canopy is built.**

`RL-BW-WEST` is deleted; `RL-BW-SCREEN` takes its line. The screen cannot carry the guard
load itself: IRC Table R301.5 puts **200 lb concentrated** on a guard (the 50 plf line load
is IBC §1607.8.1, not a residential provision), and a 2x4 on edge cantilevered 36" is d/c
1.34 at C_D 1.6. The base is worse than the member — Virginia Tech's full-scale tests behind
DCA 6 measured 178 lb ultimate for 1/2" lag screws and 237 lb for 1/2" bolts, while resolving
this base moment needs ~1,700 lb of tension per slat. The slats now carry only Table R301.5
footnote f's 50 lb over one square foot, which also makes them **immune to the 2018-vs-2021
"in any direction" question** that would otherwise decide the whole detail.

> ⚠ **Two openings to check that are NOT the sphere between slats**: the gap under the bottom
> of the slats to the deck surface, and the end gaps where the screen meets the house and the
> garage. Both are openings in a required guard and both count.

## 5. The joint at the house, drainage, and snow

The canopy's south edge leaves a **7 3/8" gap** to the house cladding. A positively sloped
closure attaches to the **canopy only**, dying at the house in a replaceable compressible or
brush seal, inspectable from below, never filled with rigid foam or sealant. The two
buildings move independently and the joint has to. Maintain the house rainscreen.

Provide fire/draft closure at the original garage south gable plane, retain garage gypsum,
and confirm the service door's rating and self-closing requirement with the AHJ. **The
movement joint is not a fire separation.**

**Drainage, and the margin is worth stating rather than discovering.** Both garage eaves
carry a 5" trough falling north to a single 3" leader each; `params/roof_trim.py` works
~425 sf per 3" leader at the 8 in/hr design intensity. Each slope shed ~290 sf before this
change and now sheds ~366 sf, so the margin falls from about 47% to about 17%. Still inside.

Snow retention is required along the east/west roof zones over the screen, tier approach and
equipment circulation; the supplier sizes crossbars and clamps for the **drift** case, not
the ground load. **Wind seam clamps are not a substitute for snow retention.**

## 6. KDAT longevity — the house-wide spec (owner, 2026-09-10)

Stated once here and carried onto the drawings by `AN-BW-KDAT`, because it applies to every
treated member in this assembly and repeating it per element invites drift.

- **304 stainless fasteners.** IRC R317.3.1 also permits hot-dip galvanized to ASTM A153,
  silicon bronze and copper, and FPL-GTR-220's hygrothermal model puts Minneapolis in the
  bottom third of its nine cities for corrosion depth (12 µm, against 45 in Hilo) precisely
  because the wood is below freezing ~2,500 hours a year. **So 304 is a durability and
  appearance choice, not a code requirement, and 316 buys chloride resistance this site does
  not need** unless the treads get salted. Never mix stainless and galvanized in one joint.
- **Butyl joist tape** over every beam and rim top (`top_protection`). Butyl or acrylic, not
  asphalt: bitumen cold-flows at deck temperatures and its oils migrate into flexible PVC.
  **There is no code hook and no independent study** showing a service-life gain — DCA 6
  never mentions joist tape — so this is durability insurance, bought for the fastener
  penetrations. In Minnesota watch the install temperature: Trex Protect wants 50°F, while
  G-Tape and PRO-Tac go to −40°F and below.
- **AWPA M4 field treatment** of every cut end, notch and drilled hole, 2% copper naphthenate.
  **This one is not advice**: IRC R317.1.1 says "shall", and R507.2.1 repeats it for decks.
- **A pigmented penetrating oil**, applied on installation. **NOT a silicate.** Sodium and
  potassium silicate are masonry densifiers — they work by reacting with free lime, which
  wood has none of. The only credible decay result (Chen 2009, FPL, Wood and Fiber Science
  41(3)) required pressure impregnation followed by acid gelation; brush-applied, silicate
  leaches (~50% in a year of weathering), *raises* moisture uptake, and effloresces. It also
  carries no pigment, and per FPL "Finishes for Wood Decks" pigment is the single largest
  driver of service life on a deck. Expect a **2–3 year recoat on the treads and landing**;
  the risers and rails, being vertical, run 2–3x that. Never a film-forming finish here.
- **KDAT changes one thing and it is the timing.** It arrives at ~19% moisture content, so
  it can and should be finished immediately on installation rather than waiting weeks for
  wet-treated stock to dry. FPL: "most decks are retired because of cracks and checks that
  mostly could have been avoided by timely finishing." A KDAT landing left bare through one
  Minnesota winter has thrown away the advantage it was bought for.

## 7. Excavation and release conditions

> ⚠ **Sequencing, and it is worth more than any dimension in this note.** All five north
> entry piers bottom at −9'-9 7/16", the same elevation as the house footing, about ten
> inches away. Cast in the open basement excavation — the owner's stated premise, and the
> only reason reaching that depth is cheap — that is a non-issue. Cast **after** the house
> footing is in and backfilled, a shaft ten inches away bearing at the same depth is
> **undermining**, and the answer becomes benching the excavation or bearing the piers
> higher and lengthening the columns.

Excavate and waterproof the deeper house first while access is open. Confirm native garage
bearing before backfill; form garage footings and stem and coordinate sleeves while the
house cut remains accessible, then compact backfill in controlled lifts.

Still external deliverables, not model checks: the survey and zoning determination for the
complete roof projection, an actual soils report (2,000 psf is presumptive and no boring log
exists), and the truss fabricator's design — **quoted against the drift case, not the ground
snow**. See `notes/north_entry_piers.md` §7 for what the calculations themselves exclude.
