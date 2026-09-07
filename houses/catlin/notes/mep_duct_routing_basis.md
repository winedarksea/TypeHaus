# One ERV branch in a bay — the duct routing basis

**House:** catlin. **Run:** `DU-M-ERV-R-KITCH`, a 3" round ERV supply riding `FS-S-WEST`.
**Oracle for:** `typehaus/routing/trades/duct.py` and the corridor half of
`routing/corridors.py`. Reproduced by `tests/test_routing_oracle.py`.
**Companion:** `mep_drain_routing_basis.md`, which does the same job for gravity drainage.
Read §4 there for the escape graph and the A* expansion — this note does not repeat it.

**Why a second note at all.** A drain oracle covers gravity, and gravity is the thing a duct
does not have. What a duct has instead is a **section that must fit a bay** and a crossing
rule that is not the drain's, so an oracle covering only drains would overclaim on exactly
the constraint that decides a duct's route.

---

## 1. The terminal and the bay it has to reach

`DU-M-ERV-R-KITCH` is authored `DuctRouting.JOIST_BAY` with `floor_ref="FS-S-WEST"`, which is
the model saying out loud that this run is a corridor rider rather than a free route. Its
register is in the main floor's ceiling and its trunk is at the ERV; everything between is
one bay.

`resolve/mep_ducts` resolves it to a round section, so the radius the router inflates
obstacles by is `diameter / 2 = 1.5"`. For a **rectangular** duct the corresponding number is
half the larger plan dimension, because a rectangular duct turning a corner sweeps its own
diagonal and the router has no fitting model to say otherwise. That is the whole of
`trades/duct.py`'s radius rule and it is deliberately conservative.

---

## 3. The bay, and what "fits" means for a section rather than a pipe

Same derivation as the drain note's §3, and the same authored `JoistSpec` — repeated here in
the terms a duct is graded in.

    spacing 16" o.c., 2x4 flat chords 3.5" wide      ⇒  clear bay 12.5"
    bay centres                                       y = 8 + 16n
    truss depth 11 7/8", chord-to-chord 8 7/8"        ⇒  crossing window 109.625 .. 118.5

A 3" duct on a bay centre leaves (12.5 − 3)/2 = **4.75" either side.** Two 3" ducts in one
bay leave 12.5 − 6 = 6.5" between them if they are both centred on their own lanes, which is
buildable — and is exactly what `mep.duct_joist_bay_occupancy` reports UNKNOWN about on this
floor today, because the model gives each run **one centreline per bay** and so cannot place
two lanes side by side. **The router inherits that limit and must not paper over it:** a
proposal that puts a second duct in an occupied bay has to say so, not price it as free.

**The crossing rule is where duct and pipe part company.** A pipe crossing the trusses is
admissible when its outside fits the 8 7/8" window. A duct crossing is admissible only within
`open_web_opening_m` — the round hole the truss's own web geometry permits, which
`mep.duct_bay_occupancy` already grades and which is smaller than the chord-to-chord gap. A
router that reused the pipe rule here would propose crossings a fabricator would refuse.

---

## 4. What the escape graph inherits, and the one thing it does not

The lattice, the `(node, incoming axis)` state, the bend penalty and the admissible Manhattan
heuristic are all §4 of the drain note, unchanged — a duct bends for the same reason a pipe
does and the search does not care which trade is asking.

One term is different and it is a **negative** one. `corridors.py` seeds candidate lines from
`joist_line_stations()` + `clear_bay_width_m()`, so every bay centreline is already a
candidate line, and a segment lying on one is priced **below** free travel. That is what makes
a duct proposal come out *in a bay* rather than merely *not through a joist* — the difference
between a route that passes `mep.duct_joist_bay` and one that was aimed at it.

`soffit_occupancy` supplies the same thing for a bulkhead: it reports each soffit's
*remaining* clear section, so a route into a box that is already full is priced out rather
than proposed. Neither discount may make a segment's cost negative in total — the heuristic
is admissible only if no edge is cheaper than its Manhattan length, so the discount is capped
at the travel term and never applied to the bend penalty.

---

## 6. What this note does not do

* **No fittings, no pressure drop.** Everything here is centrelines and sections. Whether the
  proposed route's total equivalent length fits the fan is `mep_erv`'s question, and the ERV
  static budget is its own recorded fight (0.4", not 0.2" — see `plans/TODO.md`).
* **No balancing.** A route that reaches a register says nothing about the register getting
  its design cfm.
* **No claim about two ducts in one bay.** The model cannot place two lanes; §3 says so and
  the router says so.
