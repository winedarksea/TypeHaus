# One condensate line, by hand — `PR-M-COND-HEADS`

**House:** catlin. **Run:** `PR-M-COND-HEADS`, the two main-storey heat-pump heads' collected
3/4" air-gap line. **Oracle for:** the condensate grade ladder in `routing/gravity.py` (`graded_route`), `mep.drain_slope`'s condensate branch (or
`trades/pipe.py`) and the `sanitary=False` path in `cli/route_cleanouts.py` / `cli/route_roots.py`
(E5). **Written:** 2026-11-07, wave 0, before the code. Companions: `mep_drain_routing_basis.md`
§2 (the head budget) and §8 (a drain searched where it falls); this note does not repeat them.

Source of every number: the authored runs in `plan/mep_drainage.py` as resolved (project-frame
inches; main-storey datum 0; basement slab top -109.4375"), not router output.

---

## 1. The run, as authored

`mep_drainage.py` `CONDENSATE_MAIN` (filed on `main`): `system=DRAIN`, **`sanitary=False`**, 3/4"
PVC, `serves=()`, path (210, 12) -> (210, 12) -> (210, 108), elevations 2'-6", -18.0055",
-20.4055". Resolved:

| leg | from (x, y, z) | to | plan (in) | 3-D (in) | fall (in) |
|---|---|---|---|---|---|
| 1 vertical | (210, 12, +30.000) | (210, 12, -18.006) | 0.000 | 48.006 | 48.006 |
| 2 north | (210, 12, -18.006) | (210, 108, -20.406) | 96.000 | 96.030 | 2.400 |

    developed 3-D = 48.006 + 96.030 = 144.036 in = 12.003 ft;   plan run = 96.000 in = 8.000 ft
    grade of leg 2 = 2.400 / 8.000 ft = 0.300 in/ft

The comment states the grade as "0.3"/ft over the 8'-0" north leg, landing on PR-B-COND's
interpolated -1'-8.41" invert at x=17'-6"".

## 2. The sources: two heads, no ports

The run has no `serves` and no head names it. Both heads are wall-mounted Gree Multi R32 12k units
(`EQ-T-GREE-HEAD-12`, `library/hvac_equipment.py`, **`ports=()`**: no drain port is modelled), at 7'-6" AFF:

| head | position (x, y) | pickup is |
|---|---|---|
| `EQ-M-HP2-BED` | (192, 11) | 18 in west of x=210 |
| `EQ-M-HP2-LIVING` | (240, 11) | 30 in east of x=210 |

So the router's source is **the authored pickup point (210, 12, +30.0)**, the first vertex, not
either head. The hoses from each head to it (a "collected" line, 30" AFF) are not drawn;
`--run` keeps the authored terminals. Open for E5: either a head gains a drain port (then
`--fixture`-style routing works) or the pickup stays a plain terminal, as here. (The comment names
a sleeve `SP-M-COND` that does not exist in the plan source: the vertical passes the floor deck
at (210, 12), 3.25" off the FS-M-WEST end support face at x=213.25.)

## 3. The receptor and the chain

The goal is an existing drain: the run ends on `PR-B-COND` (3/4" PVC, `sanitary=False`, authored
`slope_in_per_ft=0.26`) at **(210, 108, -20.406)**. `PR-B-COND`'s y=108 leg runs x 216 -> 162,
z -20.276 -> -21.446:

    fall 1.170 in over 54 in plan = 0.26 in/ft
    at x = 210 (6 in from the x=216 end):  -20.276 - 6 x (1.170 / 54) = -20.406   (authored end: -20.4055)

PR-B-COND then runs on, drops 78.119" (its comment: "inside the north wall"), and ends **9.000"
over the floor** at (162, 98.188, -100.438), the air gap over `FX-B-SAUNA-FD` (slab -109.4375;
-100.438 - -109.4375 = 9.000 ✓). The sink is a floor drain that sees water in normal use
("a trapped receptor that sees water in normal use", `mep_drainage.py`). So the line is
**indirect waste**: PR-M-COND-HEADS -> PR-B-COND -> air gap -> `FX-B-SAUNA-FD`.

## 4. The pipe, and the slope required

**Code, as read (2026-11-07).** Minn. R. 1346.0050 (revisor.mn.gov/rules/1346.0050/, read): "Chapters 2
to 15 of the 2018 edition of the International Mechanical Code ... are incorporated by reference ...
as amended in this chapter." Minn. R. 1346.0307 (revisor.mn.gov/rules/1346.0307/, read) is the whole
state amendment to IMC section 307: "IMC section 307.3 is deleted in its entirety", so 307.2 stands.
The IMC text itself: codes.iccsafe.org returned HTTP 403, so it was read at **up.codes**
(`up.codes/viewer/minnesota/imc-2018/chapter/3/general-regulations`, a secondary transcription served
through a summarising fetch, so the wording below is its paraphrase, not a quotation):

* **307.2.1 Condensate disposal**: condensate piping "shall maintain a minimum horizontal slope in the
  direction of discharge" of not less than **1/8 unit vertical in 12 horizontal (1 percent)**.
* **307.2.2 Drain pipe materials and sizes**: not less than **3/4" internal diameter**, not decreasing
  from the drain-pan connection to the point of disposal; Table 307.2.2 sizes by capacity (up to 20 tons:
  3/4"). The table carries no slope.

The repo's earlier "IMC 307.2.2" cite for the slope was the wrong section: 307.2.1 is the slope,
307.2.2 the size. (`equipment_types.py`'s "IRC M1411.3 / IMC 307.2.3" for the emergency pan is not
re-read here.) Owner decision (2026-11-07): **1/4"/ft is a target, 1/8" the floor.**

**Size.** 3/4" nominal is 3/4" ID only if the pipe is; 3/4" sch 40 PVC is 0.824" ID (1.050" OD, IPS
series, `pipe_sections.IPS_OD_IN`; PVC is not tube), so it clears 307.2.2.

**Slope.** For a `sanitary=False` drain the engine now applies **IMC 307.2.1**, not UPC 708.0, in
three places that read one owner, `resolve/mep_slope.py` (`CONDENSATE_FLOOR_IN_PER_FT` 0.125,
`CONDENSATE_PREFERRED_IN_PER_FT` 0.25):

* `mep.drain_slope`: flattest segment below 1/8 FAILs (307.2.1); from 1/8 up to 1/4 it PASSes with an
  "ADVISORY — house prefers 1/4" prefix (a house preference is not code); at or over 1/4 a plain PASS.
  A sanitary drain is unchanged (UPC 708.0, 1/4).
* `routing/gravity.graded_route`: lays at 1/4 and takes 3/16 or 1/8 only when cheaper (§5.1).
* `mep.drain_slope_margin` skips `sanitary=False` runs; `mep.drain_slope`'s advisory owns them.

(`sanitary=False` also covers the T&P relief line `PR-B-WH-TPR`, which IMC 307 does not govern; it
passes either way at 1.48"/ft, and who grades a relief discharge's fall is an open owner question.)

## 5. Fall available vs required

    developed plan run                      96.000 in = 8.000 ft
    required at 1/4 in/ft (target)          8.000 x 0.250 = 2.000 in
    required at 3/16 in/ft                  8.000 x 0.1875 = 1.500 in
    required at 1/8 in/ft (code floor)      8.000 x 0.125 = 1.000 in
    authored fall on leg 2                  2.400 in   (0.300 in/ft)
    margin                                  +0.400 in over 1/4 (0.050 in/ft); +1.400 over 1/8

The whole head is 30.000 - (-20.406) = **50.406 in**; the 48.006" vertical takes all but the
2.400" the horizontal leg spends, so slope is not the binding constraint: 2.000 / 50.406 = **4.0%**
of the head. At the target (it proposes at the grade it chose, never steeper, `gravity.py`) the
vertical lands at -20.406 + 2.000 = **-18.406** (0.400" lower than authored) and leg 2 holds exactly
0.250 in/ft: a plain PASS on `mep.drain_slope`. The authored 0.300 is also a plain PASS; a leg at
0.1875 would be the ADVISORY PASS, one at 0.10 a FAIL (8 x 0.10 = 0.800" < 1.000").

### 5.1 When the shallower grade wins

The search is run at each grade of (1/4, 3/16, 1/8) and a route scores `cost + P x (0.25 - grade)`,
`P = 768` in of equivalent travel per in/ft (`CONDENSATE_SHALLOW_PENALTY`): 48 in at 3/16 and 96 in
at 1/8, the price of two and four 24" bends. Hand-worked on the drain oracle's two lanes
(`mep_drain_routing_basis.md` §8: cheap lane L 84 in, 10 ft, under a truss web whose window floor is
115.50"; dear lane S 96 in, 6 ft; ceiling 116.50", tie 114.00"):

| grade | L: fall over its 5 ft at the web | clears 115.50"? | winner and score |
|---|---|---|---|
| 1/4 | 1.250" -> 115.25" | no | S, 96 + 0 = **96** |
| 3/16 | 0.9375" -> 115.5625" | yes | L, 84 + 48 = 132 (loses to 96) |
| 1/8 | 0.625" -> 115.875" | yes | L, 84 + 96 = 180 |

So with S as authored the target holds: shallower saves 12 in, under the 48 in it costs. Make S dearer
by 100 in (196): 3/16 gives L at 84 + 48 = **132** against S's 196, and 1/8 gives 180, so **3/16 wins**
(a saving of 112 in against a 48 in penalty). Raise the tie to 115.50": S needs 1.50 / 1.125 / 0.75" of
fall from 116.50" and arrives at 115.00 / 115.375 / 115.75", so only **1/8** fits, and it is taken
because the target refuses. `tests/test_routing_minor_systems.py` pins all three cases.

## 6. Expected outcome

**Proposes.** By hand: the nearest `PR-B-COND` point to the pickup in plan is (210, 108), 96.0 in
away (the next, vertex (216, 108), is 102 in); a straight north lane is the authored one and the
vertical drop precedes it. Expected proposal:

* plan run 96.000 in on x = 210, one vertical, one horizontal, no turn other than the drop's
  (a 90-degree elbow, a catalogued DWV pattern);
* developed 3-D within 1.1x of authored: <= 158.4 in (13.2 ft), against the authored 144.036 in;
* leg 2 at 0.250 in/ft or steeper, arrival z = -20.406 (the interpolated invert);
* 0 cleanouts and the rest of the evaluation unchanged from `PR-M-COND-HEADS`'s baseline.

A **refusal** would have to cite something other than slope: no lattice plane holds the vertical,
or the service void is full. Neither is evident by hand; the structured cause is for the router
to print (head 50.4 in available, 2.0 in required) and E5's test should pin that a refusal names
required fall and available head in inches, as the gravity searches do.

A second condensate target, worked for comparison: **`PR-B-ERV-COND`** (the harder one), plan legs
15.375 + 79.900 + 61.375 + 45.000 + 68.000 + 5.500 = 275.150 in = 22.929 ft, from 52.5" to
44.25" = 8.250 in of fall: required at 1/4 = 22.929 x 0.25 = **5.732 in**, margin **+2.518 in**
(1/8: 2.866, +5.384). Its flattest authored leg is 0.333 in/ft (45.000 in plan, 1.25 fall).

## 7. Is a condensate line sanitary? No.

* `PipeRun.sanitary` doc (`model/mep.py`): "Some indirect wastes and relief discharges use the
  drain pipe geometry but do not belong to the connected sanitary system governed by UPC 707.4."
* `mep_drainage.py`: "a collected 3/4" air-gap line, falling continuously to a receptor, never
  tied into the sanitary system." `resolve/plumbing_tables.py`: the dryer "discharges condensate
  to an indirect waste, which is not a drainage fixture."
* Every cleanout consumer already filters on it: `resolve/cleanouts.py` (a `DrainCleanout` on a
  non-sanitary host is refused), `resolve/cleanout_rules.py:178` and `checks/mep/drain_cleanouts.py`
  (`r.sanitary`). **`cli/route_cleanouts.place_cleanouts` hard-codes `sanitary=True`** on the
  stand-in run it grades, so a proposed condensate line would be given cleanouts the checks would
  then ignore. E5 passes the target's own flag.

**What to assert.** `place_cleanouts` on a `sanitary=False` run returns no cleanouts. For
`PR-M-COND-HEADS` itself the answer is 0 either way (its minimum z, -20.406, is above the lowest
floor + 1" = -108.4375", UPC 707.4 exception 3 in `run_requirements`), so the test needs a
synthetic run: a 4" drain at the lowest floor, horizontal run > 5 ft (`_SHORT_LINE_M`), which
gets an "upper terminal" requirement at `sanitary=True` and none at `sanitary=False`.

## 8. Not done

* The IMC text came from up.codes (a secondary transcription, paraphrased by the fetch), not the ICC
  site (HTTP 403); the 1/8 and 3/4" figures agree with the owner's reading and with Rheem's sheet
  (`water_service.md` §2). A printed copy of 307.2.1/307.2.2 should replace it before a permit set.
* 307.2.2's 3/4" ID is met by 3/4" sch 40 PVC; the "no decrease from the pan" rule is not graded.
* The two heads' hoses to the pickup are undrawn; their fall to the pickup (18" and 30" of plan)
  is ungraded.
* No freeze or heat-trace grading (`PipeRun.freeze_protection`): the line is inside the heated
  basement.
