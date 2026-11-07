# 908.2 group wet venting — hand-worked basis for `haus route --group` (E2)

**House:** catlin, Minnesota. **Oracle for:** `routing/group_order.py`, `cli/cmd_route_group.py`,
`resolve/mep_wet_tie.py`. Written 2026-11-07 from the code text, the repo's own check walk and the authored
plan, before E2 coded. Extends `wet_vent_basis.md` (the utility sink) and `mep_drain_routing_basis.md` §14.
Units: inches, project frame, main datum 0, second datum 120. Elevations are centrelines.

---

## 1. Code read

Edition: Minn. R. 4714.0050 adopts the **2018 UPC** (PB0225's own statement). Read in full this session, from
pdftotext of the two PDFs: **IAPMO Standards Council decision on TIA UPC-001-12** (2012 UPC; sections 204.0,
206.0, 224.0, 908.2.x) and **MN Plumbing Board final interpretation PB0225** (2026-02-24, published
2026-03-10). **Not read:** the 2018 UPC itself (paywalled). The TIA is the 2012 wording and numbering; PB0225
quotes 2018 908.2.2 consistent with the TIA's "Size" paragraph, so the two editions agree on sizing. The
numbers 908.2.1.1-.5 below are the TIA's; **the 2018 numbering of the other paragraphs is unconfirmed**
(provisional, though the repo's check already cites them).

* **908.2.1 Where Permitted** (TIA): "A bathroom group located on the same floor level shall be permitted to be
  vented by a horizontal wet vent where all of the conditions ... are met." "Water closets, bathtubs, showers and
  floor drains within one or two bathroom groups located on the same floor level and for private use shall be
  permitted to be vented by a wet vent." "The wet vent shall be considered the vent for the fixtures and shall
  extend from the connection of the dry vent along the direction of the flow in the drain pipe to the most
  downstream fixture drain or trap arm connection to the horizontal branch drain." "Each wet vented fixture drain
  or trap arm shall connect independently to the wet vented horizontal branch drain. Each individual fixture drain
  or trap arm shall connect horizontally to the wet vented horizontal branch drain or shall be provided with a dry
  vent. The trap to vent distance shall be in accordance with Table 1002.2. Only the fixtures within the bathroom
  groups shall connect to the wet vented horizontal branch drain. ... Additional fixtures shall discharge
  downstream of the wet vent system and be conventionally vented."
* **908.2.1.1 Vent Connection:** "The dry vent connection to the wet vent shall be an individual vent or common
  vent for the lavatory, urinal, for the bidet, shower, or bathtub. One or two vented lavatory(s) shall be
  permitted to serve as a wet vent ... Only one wet-vented fixture drain or trap arm shall discharge upstream of
  the dry-vented fixture drain connection. All dry vent connections ... in accordance with Section 905.2 and
  Section 905.3."
* **908.2.1.2 Size** (PB0225 quotes this as 2018 908.2.2): "The wet vent shall be sized based on the fixture unit
  discharge into the wet vent. The wet vent shall be not less than 2 inches ... for 4 drainage fixture units
  (dfu) or less, and not less than 3 inches ... for 5 dfu or more. The dry vent shall be sized in accordance with
  Table 702.1 and Table 703.2 based on the total fixtures units discharging into the wet vent." PB0225: "it must
  be sized three inches (3") in diameter for its entire length", "back to the dry vent served".
* **908.2.1.3 Trap Arm:** "The length of the trap arm shall not exceed the limits in Table 1002.2. ... The vent
  pipe opening from the horizontal wet vent, except for water closets and similar fixtures, shall not be below
  the weir of the trap."
* **908.2.1.4 Water Closet:** "... connection to the wet vent shall be downstream of all fixture drain or trap
  arm connections to the horizontal wet vent." **908.2.1.5:** additional fixtures discharge downstream and are
  conventionally vented.
* **204.0 Bathroom Group** (TIA): the PDF text layer keeps the struck and the inserted words together, so
  whether a tub **and** a shower fit one group cannot be read from it. 908.2.1's "one or two bathroom groups"
  makes BATH2 (WC, lav, tub, shower) legal either way. Open: AHJ confirmation.
* Repo tables (`resolve/plumbing_tables.py`): DFU WC 3, lav 1, tub 2, shower 2; Table 703.2 1 1/2" = 3 DFU,
  2" = 6, 3" = 35; **Table 1002.2 trap arm: 1 1/2" 42", 2" 60", 3" 72"** (secondary restatement, as in
  `wet_vent_basis.md`).

## 2. What the check's walk can and cannot see (three findings)

`resolve/mep_trap_arm.developed_arm`/`grade_wet_vent` are what `mep.trap_arm_length` grades and the router
reads. Reproduced on a synthetic ladder (collector C 3" flowing +x; tub arm T joins at x = 0, the lav L with
its vent tee joins at x = 36, the WC W joins at x = 72; all 3" where it is wet vent):

| fixture graded | result |
|---|---|
| TUB (upstream of the lav's join) | 76.3" (arm 40.3" + 36" of C): `L, wet-vented (908.2 horizontal, 6 DFU, O3": ok for 6 DFU)` |
| LAV | `a vent tee`, 0" |
| **WC (last, after the join)** | **None, no vent found** |

* **F1. A water closet placed last, as 908.2.1.4 requires, is never graded vented.** The walk only looks
  *downstream* of an arm's entry; the dry-vent join is *upstream* of the WC. So `mep.trap_arm_length` returns
  UNKNOWN for it and `trap_arm_gaps` cannot reach 0 with the check as written. `mep_trap_arm.py` is in no
  agent's file list. **Request:** an arm that enters a legal wet vent downstream of the dry-vent join ends at its
  own entry (arm length = its own run to the join, graded against Table 1002.2 for its size).
* **F2. The wet-vent parent must carry only the group.** `members` counts every fixture whose path crosses the
  parent. With the 4" `PR-B-MAIN-DRAIN` as parent (17 fixtures, kitchen sink and washer among them) the walk
  rejects it ("not a bathroom-group fixture"). A group needs its **own dedicated 3" branch**, tied to the main
  downstream of the WC.
* **F3. The check walks only vents whose `serves` names the fixture**, and `mep.vent_reachability` needs a
  vent run naming it that also touches *its* wall axis. Wet-vented fixtures need their dry vent's `serves`
  extended, and the vent must touch their wall (`checks/mep/vent_path.py`), else `vent_gaps` stays > 0.
  Where the fixture's wall is not touched by that vent the check, not the design, needs the change (same
  owner problem as F1).

Also: the check classifies the dry-vented child as **908.1 vertical** when its whole run rises more than it
runs (`_is_vertical`), which changes the rules (<= 4 fixtures, <= 72", upper fixtures <= 2 DFU) and fails a
horizontal group.

## 3. Roles, from the weir rule (908.2.1.3)

A non-WC fixture may be wet-vented only if the vent opening is not below its trap weir, and its arm may not fall
more than a pipe diameter between weir and the wet vent (905.5/1002.4, the check's S-trap rule). Weirs, from the
authored runs:

| fixture | weir (relative to its datum) | read from |
|---|---|---|
| BATH2-TUB, BATH2-SH | **-3.0** (under-floor trap, `under_floor_weir_m`) | `PR-B-TUB2-DRAIN`, `PR-B-SH2-DRAIN` first drop |
| BATH2-SINK (lav) | about **+21.5** | `PR-M-BATH2-LAV-VENT` first vertex |
| SUITEBATH-TUBSH | **-3.0** (117.0 abs) | tub drain 120.75 -> 117.45 |
| SUITEBATH-LAV | **+21.5** (141.5 abs) | `PR-M-S-SUITE-LAV-DRAIN` first vertex |
| both WCs | exempt | "except for water closets" |

* A **floor-level** fixture (tub, shower) can be the dry-vented one: its tee crown is above every floor-level
  weir (1 1/2" arm at -3.5: crown -2.75 >= -3.0).
* A **wall-trapped lavatory cannot be wet-vented off a floor-level vent**: its arm would fall 25.6" from the
  weir (141.5) to a join at 115.85, against a 1.9" diameter. It keeps its own dry vent, in every layout.
* A lavatory **can** be the dry-vented fixture (opening above every weir), and then a tub below it is
  wet-vented (arm falls 1.15" <= 1.9"), at the cost of a vertical child (section 5, option X).

## 4. RM-M-BATH2 by hand

Drain points (authored): WC (30, 252.74), tub (78.49, 215.18), shower (76.62, 179.0), lav (12, 182.38); main
tie (72, 271, -16.0). Plan Manhattan distances: tub-shower **38.05"**, tub-WC 86.05", shower-WC 120.36",
WC-head **60.26"**. Existing tees: shower (98, 180.5, -3.5), tub (98, 204, -3.5), 23.5" apart on x = 98.

**Reference layout (option S):**

1. **Dry-vented drain: the SHOWER** (its `PR-M-BATH2-SH-VENT` exists). Arm to its tee, check-style from the
   first vertex: 3.0 + 21.44 = **24.44"** <= 60 (2") or 42 (1 1/2"): margin 17.6" worst.
2. **Wet-vented arm: the TUB**, downstream of the shower's connection (any number may be): the wet vent runs
   from (98, 180.5) north 23.5" to (98, 204) where the tub arm joins: arm 4.75 + 22.49 = **27.24"** <= 42,
   margin 14.76". Its `PR-M-BATH2-TUB-VENT` is dropped; the shower vent's `serves` gains the tub (F3).
3. **Water closet last**: joins the wet vent after the tub. WC arm 3" (<= **72"**): flange z = +1.5; at the
   head (72, 271) the plan reach is 60.26", so the arm is `(1.5 - z_j) + 60.26`. **At the tree's tie
   (z = -16.0) it is 77.76" > 72, over by 5.76".** It passes only if the wet vent is within the floor cavity:
   `z_j >= -10.24`; at z_j = -6.0 it is 67.76", margin 4.24". The WC cannot join the basement-ceiling collector.
4. **The lav keeps `PR-M-BATH2-LAV-VENT`** and ties conventionally downstream (908.2.1: additional fixtures).
5. **Size:** members shower 2 + tub 2 + WC 3 = **7 DFU** (8 if the lav joined), so **3" for the entire length**
   from the shower's dry-vent connection (PB0225): the child (tee to join) and the parent both 3". Dry vent 1 1/2"
   serves 7 DFU (Table 703.2 vent column per the repo: 8 at 1 1/2").
6. **Order along the flow:** shower (dry vent) -> tub (wet-vented) -> WC (last). Upstream wet-vented drains: 0.

**Option T** (tub dry-vented, shower the single upstream arm): shower arm from its trap to the tub tee,
3 + 21.38 + 25 = **49.38"**: legal only on a 2" arm (60", margin 10.6"); a 1 1/2" arm (42") fails by 7.4".
The router sizes a 2 DFU shower at 1 1/2" (Table 703.2), so option S is the one the search will find.

**Expected check outcome for option S, if F1-F3 are settled:** `trap_arm_gaps` 0 (shower 24.44", tub 27.24",
WC <= 72", lav 44" on its own vent, each under its limit), `vent_gaps` 0. **Not settled by this note:** the
lane (supplies at -6.8..-8.8 and the x = 98 riser of `PR-B-HW-WASH` at (98, 249.25) stand in the way of any wet
vent from (98, 204) to the head; `mep_tree_ripup_basis.md` §4.1), so these outcomes are conditional.

## 5. The suite bath, briefly (`FX-S-SUITEBATH-*`, second storey)

Drain points: WC flange (134.81, 252.41), lav (165.5, 264.75), tub-shower (197.62, 261.12): in a row, flow west,
**tub, then lav, then WC**. Plan distances: WC-lav 43.03", lav-tub 35.75". Authored runs: tub arm to the lav's
join `3.30 + 2.88 + 8.62 + 18.05 + 5.50 =` **38.35"**; the lav's tee-to-join child **29.25"** with rise 25.58"
against plan 7.25"; WC arm to a join at (155.75, 252.41) about **24.99"**.

* **Option X (lav dry-vented, tub wet-vented upstream, WC last)** is the layout of `mep_drain_routing_basis.md`
  §14. Tub arm 38.35" <= 42 (margin 3.65"); one wet-vented drain upstream; WC last; members lav 1 + tub 2 + WC
  3 = **6 DFU, 3" whole length** (the lav's drop included). Code: the lav's opening (142.2 crown) is above the
  tub weir (117.0). **The check rejects it: the child rises 25.58" over 7.25" of plan, so it is "vertical"
  (908.1) and fails.** A lav drain cannot be made flat (25.6" at 1/4"/ft is 102 ft) and cannot drop before its own
  vent (S-trap). Legal on paper, ungradable as written: the open AHJ/engine question.
* **Option Y (tub-shower dry-vented, lav own vent, WC wet-vented last)**: members tub 2 + WC 3 = **5 DFU, so
  3"** (exactly the 5-dfu step). WC arm ~25" <= 72. The lav stays on `PR-S-SUITEBATH-LAV-VENT`. Passes the weir
  rule (tub tee crown 118.1 over weir 117.0); child horizontal (plan 41.9" before it turns south). Needs F1.

## 6. Which of the three can be vent-free

| fixture | wet-vented? | why |
|---|---|---|
| **BATH2-TUB** | **yes** (option S, downstream of the shower's dry vent) | floor-level weir -3.0, arm 27.24" <= 42 |
| **SUITEBATH-TUBSH** | **yes only in option X** | weir -3.0; in option Y it is the dry-vented fixture |
| **SUITEBATH-LAV** | **no** | weir +21.5: either it is the dry-vented fixture, or it would fall 25.6" before the vent |

**So at most 2 of the 3 are vent-free, and the second needs option X**, which the check calls vertical. Under
option Y only BATH2-TUB is vent-free of the three (the suite's WC is the wet-vented one). **E2's acceptance
("at least 2 of the 3") is reachable only if `grade_wet_vent` stops reading a dry-vented fixture's own vertical
drop as a 908.1 section** (or the AHJ accepts it): report this to the coordinator before E2 builds to it.

## 7. Numbers a test may assert

BATH2: shower arm 24.44"; tub arm 27.24"; tub-shower plan 38.05"; WC to head 60.26"; WC arm 77.76" at -16.0
(over by 5.76"), 67.76" at -6.0; `z_j >= -10.24`; wet vent 3" for 7 DFU; option T shower arm 49.38". Suite: tub
arm 38.35"; lav child 29.25" rise 25.58" plan 7.25"; option X 6 DFU / 3"; option Y 5 DFU / 3"; WC arm ~24.99".
Roles: BATH2 dry = shower, wet = tub, last = WC; lav own vent. Synthetic ladder: WC graded None.

## 8. What this note does not do

* No lane: the wet-vent branches are not routed here, and the BATH2 reach figures are straight-line.
* No 2018 UPC text (TIA 2012 wording; 2018 numbering of the sub-paragraphs unconfirmed). 204.0's one-group
  reading of tub plus shower is not settled by the text layer.
* No grading of the vent-sizing table beyond the repo's Table 703.2 column, nor of 905.3's 6" over the rim for
  the wet-vented fixtures' reused vents.
* Option X/Y choice is a design decision (owner/AHJ); neither is claimed built.
