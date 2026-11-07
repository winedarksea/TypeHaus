# Flex lead bend — hand-worked basis (W3-FLEX, 2026-11-07)

Oracle for `resolve/flex_bend.py`, `routing/duct_fittings.kit_lead` (bent lead), `cli/route_ports`
and `checks/mep/erv_static_terms._flex_bend_loss`; pinned by `tests/test_flex_lead_bend.py`.
Context: `plans/TODO.md` "ERV OA/EA/RET hold", `notes/erv_static_budget.md` §10.9,
`notes/mep_duct_routing_basis.md` §8 (the straight lead this replaces where it does not fit).

## 1. The rule, and where it was read

**ADC, *Flexible Duct Performance & Installation Standards*, 4th edition (2004)**, read from the
Quietflex 440C manual's reprint (gtsanders.com/userfiles/ad/documents/Quietflex_440C_Manual.pdf,
8 pages, PDF title "ADC Green Book 4th Edition"). The 5th edition was NOT available to read; a
search excerpt of it words the same rule "Keep bends greater than or equal to one (1) duct
diameter bend radius" (unread in full; confirm against the 5th edition before a submittal cites
it).

* **s.4.2, printed p.13** (installation guidelines): "Avoid bending ducts across sharp corners or
  incidental contact with metal fixtures, pipes or conduits. Radius at center line shall not be
  less than one duct diameter." Same section: "the number of bends, the number or degrees in each
  bend ... will have serious effects on system performance"; "Use the minimum length of flexible
  duct to make connections"; "Install duct fully extended".
* **s.4.8, printed pp.18-19** (supporting): a connection to rigid duct or equipment is a support
  joint; "Support the duct between a metal connection and bend by allowing the duct to extend
  straight for a few inches before making the bend. This will avoid possible damage of the flexible
  duct by the edge of the metal collar." Sharp bends take supports "approximately one duct diameter
  from the center line of the bend".

**What is not published:** "a few inches" has no number; no rule says how far the run must be
extended for a bend beyond "minimum length". So `PortKit.bend_start` is a **stated allowance,
2"**, not a datasheet value (house-overridable), and the flex is cut to what the arc needs.
Broan's own sheet (B210E75RT manual pp.10-11, `notes/air_distribution_products.md` "Port kits")
says only "install a 12-in. section of flexible duct"; it states no bend radius. The kit's 12" is
therefore a nominal length, and the flex is cut longer where the arc needs it.

## 2. Geometry (centreline radius R = D; theta = 90)

A lead is `start` straight, an arc, `tail` straight. Arc length `a = R theta`; tangent length
`t = R tan(theta/2)` (= R at 90). Flex as cut `L = max(12, start + a)`, `tail = L - start - a`.
As a polyline the lead is port -> **corner** -> rigid start: the corner stands `transition +
start + t` from the port face along the port's axis, and the rigid duct starts `t + tail` past it
along the new heading (`out`).

| | 6" lead | 8" lead |
|---|---|---|
| R = D | 6.000" | 8.000" |
| arc a = R pi/2 | 9.425" | 12.566" |
| start + a | 11.425" | 14.566" |
| flex as cut | 12.000" (kit's own) | **14.566"** (kit's 12" is 0.57" short of the arc alone) |
| tail | 0.575" | 0 |
| corner from the port face (start 2") | 8.000" | 10.000" |
| rigid starts past the corner (`out`) | 6.575" | 8.000" |

So the "lead length unchanged" holds for 6" and not for 8": the 8" flex is cut 2.566" past the
12" section Broan names. With a 3" start (sensitivity): 6" corner 9.0", flex 12.425"; 8" corner
11.0", flex 15.566".

**Where an authored run's first vertex is a flex bend** (`run_bend`): the vertex nearest an exact
kitted port, when (a) the leg to the port holds the arc (`d0 >= transition + start + t`), (b) the
leg after holds `out`, and (c) the straight lead would not fit: `d0 < transition + 12 + stock
elbow's take-off R tan(theta/2)`. Otherwise the straight lead stays. `fitting_records` then leaves
that vertex out, so it is neither billed nor graded as an elbow and the part list stays one kit
(the flex part's `length_m` is the flex as cut). `mep.fitting_pattern` seats the next fitting
`out` past the corner.

**Router.** `with_port_leads` bends the lead (90, toward the way the run's other end lies across
the port axis) iff the straight lead would not fit before it: `reach along the port axis <
lead + stock take-off`. Straight otherwise.

## 3. Static cost

`mep.erv_static_budget` charges `C x VP` on the flex's own velocity pressure, VP = (V/4005)^2:

* **Published loss.** Abushakra, Walker & Sherman, "A Study of Pressure Losses in Residential
  Air Distribution Systems" (LBNL, 2002, escholarship.org/uc/item/2db0m8p8), **Table 4** (PDF
  p.6 of 14): nonmetallic flex, 90 degree bend, local loss coefficient K on the downstream
  velocity pressure: 6" **1.18** (5.0% compression, r/D 2.50), 3.27 (18.6%, r/D 5.0); 8" **2.85**
  (13.6%, r/D 2.0), 2.31 (34.2%, r/D 2.5). The paper: flex elbows run far above sheet-metal ones
  (all below 1.0 in ASHRAE 2001) from the liner's roughness, "no systematic variation" with r/D.
  These were not measured fully stretched at r/D 1, so they are indicative, probably low for
  R = D; no ASHRAE flex-elbow table was read. They are NOT in the engine: a house authors
  `PortKit.flex_bend_loss_c` (the `transition_loss_c` precedent). **Request to the house owner:**
  Broan kit rows take 1.18 (6" supply/return) and 2.85 (8" outdoor/exhaust).
* **Fallback (field unset).** The DuctStandard's stock elbow at the same angle (C 0.22 stamped
  90, x Locklin K), and the check prints the gap: "charged as the stock elbow ... a measured
  flex-bend C would be higher".

At the machine's 210 cfm (203 cfm in brackets), VP 6" 0.0713 (0.0666) in. w.g.; 8" 0.02256
(0.02108):

| bend | stock C 0.22 | measured C | extra over the stock elbow |
|---|---|---|---|
| 6" (C 1.18) | 0.0157" (3.9 Pa) | 0.0842" (21.0 Pa) | 0.0685" (17.1 Pa) |
| 8" (C 2.85) | 0.0050" (1.2 Pa) | 0.0643" (16.0 Pa) | 0.0593" (14.8 Pa) |

The flex bend replaces the stock elbow the straight design needed, so the budget moves by the
last column per bend (each outdoor-side leg), against a 0.4" w.g. rated point (§10): **material**.
The flex's own friction is charged over the flex as cut (14.57" rather than 12").

## 4. Proof: EQ-B-ERV at 270 degrees, OA/EA exact (in-memory, no house edit)

Catlin loaded, EQ-B-ERV `rotation=deg(270)` and the Broan type's four ports EXACT in memory,
then `cli/route_ports.with_port_leads` on `DU-ERV-OA` / `DU-ERV-EA` (8" galvanized, 12" wrapped,
wrapped radius 6"), far end 120" west and 12" under the joists so the run must turn at once.
Ports: z = -33.838" (storey datum), joist underside of FS-M-MECH (lowest member `z0`) -11.875"
(= 97.56" AFF, as in TODO). Port-to-underside 21.963".

| | corner (first horizontal leg) centre z | top of 12" wrap z | vs underside -11.875" |
|---|---|---|---|
| straight lead, before | -33.838 + 14 + 12 = -7.838 | -1.838 | **10.04" above** (TODO figure) |
| flex bend, now | -33.838 + 10.000 = -23.838 | -17.838 | **5.96" below** |

The 270-degree gate (first horizontal leg at or below the joist underside) **passes** in this
in-memory proof for OA and EA: the lead leaves west (-x), tips at x 69.19 (the rigid duct starts
8.00" past the corner), the wrapped top clears the joists by 5.96", and the wrap's bottom
(-29.838) stands 4.00" above the case top (-33.838). The 6" supply: corner at -25.838, its 6"
wrap 10.96" under the joists. This does not separate the two 12" wrapped legs (port rows 9.75"
apart): both bend the same way here only because the test far end is on one side, so the real
layout still needs opposite bends or two tiers (the house agent's layout, not the lead).

Not done here (house layout): the rotation itself, the runs to the plenums, the EA slope, and
the `flex_bend_loss_c` values.
