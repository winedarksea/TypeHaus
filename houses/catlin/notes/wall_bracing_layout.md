# Wall bracing — the R602.10 layout, and the readings behind it

**2026-09-22. A READING, not an oracle.** Nothing here is hand-worked arithmetic verifying a
calculation: every number below is a TABLE LOOKUP, and the code that reads the table is a
transcription of the table itself (`checks/structural/_r602_bracing_table.py`). A second
hand pass over a lookup would only re-read the same row. So this note carries no
`oracled_by`, and none should be added — the PBR cladding precedent
(`board_batten_girt_span.md` before it became a published read) is the same shape. What it
DOES carry is the judgement: the story count, the factors taken and not taken, the panel
layout, and the three places a reviewer should push back.

---

## 1. The basis, measured

| Input | Value | Where it comes from |
|---|---|---|
| Ultimate design wind speed | 115 mph | `Site.design_wind_speed_mph`, MN statewide |
| Exposure category | B | `Site.wind_exposure` |
| Seismic design category | A | `profile.py` — MN statewide, no amendment |
| Method | **CS-WSP** everywhere | continuous structural sheathing, above and below every opening |
| House wall height | 9'-0" (108") | the line's own plates, main and second |
| Garage wall height | 8'-4" (100") | ditto |
| Braced wall line spacing | 36'-0" house / 24'-0" garage | line to line, measured |
| Braced wall lines per direction | 2 | counted |
| Eave-to-ridge height | 11'-3" house / 5'-1" garage | ridge less the TOP STOREY'S PLATE (§3) |

Minnesota adopts IRC R602.10 through Minn. R. 1309 **without amendment**, which is why this
is a prescriptive path at all and why Tables R602.10.3(3)/(4) — the seismic pair — are not
implemented: SDC A never reaches them (decision #79).

## 2. The story count is DERIVED, and the dwelling is two stories

The tables are indexed on where a story sits in the stack, so the count is the first
decision and the engine makes it from the model rather than from an authored number: a
storey is a story for R602.10 when it carries a `braced` braced wall line.

- **Basement — not a story.** Its perimeter is an 8" R404 concrete box. Concrete braces by
  being concrete and R602 is the light-frame chapter.
- **Main — first story of two.**
- **Second — the top story.**
- **Attic — not a story.** IRC R325.6: a habitable attic complying with its four conditions
  "shall not be considered a story". The model says the same thing structurally: its east
  and west sides are 1-1/2" rafter plates, not knee walls, so neither can carry a panel and
  the storey has no `braced` line at all.

The attic's wind area does not vanish with the story count — it rides the **eave-to-ridge
factor**, §3.

## 3. Eave-to-ridge is measured from the top plate, not the eave

Table R602.10.3(2) item 2 adjusts for "roof eave-to-ridge height". RF-HOUSE's own eave is at
+20.948' and its ridge at +30.250' — 9'-4", which reads as the 10-foot row at a factor of
1.00. This engine measures from the **top of the topmost braced story's wall** instead:
30.250' − 19.000' = **11'-3"**, which rounds up to the 15-foot row.

Everything between that plate and the ridge is wind area the second storey's bracing
carries: 10 feet of attic gable wall and the roof above it. Taking the 10-foot row would
credit this house for a roof that starts at its top plate, which is not this building. The
cost is honest and small: main ×1.15 instead of ×1.00 (12.56 ft required against 10.93), and
second ×1.30 instead of ×1.00 (7.41 against 5.70). Every line clears either way.

The garage is measured the same way for consistency — 12.396' − 7.333' = 5'-1", the 10-foot
row at ×1.00, where its own eave-to-ridge of 4'-5" would have bought the ≤5-foot row's 0.70.

## 4. Required against provided, line by line

Base length from Table R602.10.3(1), CS-WSP column, at 115 mph. Factors from Table
R602.10.3(2): exposure B ×1.00, eave-to-ridge per §3, story height 9'-0" ×0.95, two lines
×1.00, and item 6's ×1.40 where the panels on a line carry no gypsum inside.

| Storey | Line | Base | Factors | **Required** | **Provided** | Margin |
|---|---|---|---|---|---|---|
| main | BWL-W-A-E1 | 11.5 | 1.15 × 0.95 | **12.56'** | 19.58' | 1.56× |
| main | BWL-W-A-N1 | 11.5 | 1.15 × 0.95 | **12.56'** | 28.17' | 2.24× |
| main | BWL-W-A-S1 | 11.5 | 1.15 × 0.95 | **12.56'** | 23.50' | 1.87× |
| main | BWL-W-A-W1 | 11.5 | 1.15 × 0.95 | **12.56'** | 26.92' | 2.14× |
| second | BWL-W-A-E1 | 6.0 | 1.30 × 0.95 | **7.41'** | 26.67' | 3.60× |
| second | BWL-W-A-N1 | 6.0 | 1.30 × 0.95 | **7.41'** | 28.92' | 3.90× |
| second | BWL-W-A-S1 | 6.0 | 1.30 × 0.95 × **1.40** | **10.37'** | 16.92' | 1.63× |
| second | BWL-W-A-W1 | 6.0 | 1.30 × 0.95 × **1.40** | **10.37'** | 26.92' | 2.60× |
| garage | BWL-W-G-N | 4.5 | 1.00 × 0.95 | **4.28'** | 8.00' | 1.87× |
| garage | BWL-W-G-S | 4.5 | 1.00 × 0.95 | **4.28'** | 20.42' | 4.77× |
| garage | BWL-W-G-E | 4.5 | 1.00 × 0.95 | **4.28'** | 24.00' | 5.61× |
| garage | BWL-W-G-W | 4.5 | 1.00 × 0.95 | **4.28'** | 21.67' | 5.07× |

The worst line in the house is main E1 at 1.56×, and it is worst because the fire niche and
four windows leave it only three qualifying runs.

**The ×1.40 on the second storey's south and west lines is real and is the one factor that
bites.** Table R602.10.3(2) item 6 charges it where interior gypsum board is omitted from
the inside face of a panel, and it names CS-WSP explicitly (R602.10.4.3 exception 3 is the
companion text). `W-S-S1` and `W-S-W4` are the plant room, lined in PVC panel over furring.
A PVC liner is not gypsum and is not claimed as "an approved interior finish material with
an in-plane shear resistance equivalent to gypsum board" — nobody has tested it, so the
penalty is taken. Line up the plant room in gypsum and both lines drop to 7.41'.

### Factors NOT taken, and why

- **Item 5, ×0.80 for an additional 800-lb hold-down at each panel end.** Published for the
  intermittent methods (DWB, WSP, SFB, PBS, PCP, HPS) and for the top story only. A
  continuously sheathed line cannot have it, which is why the four devices at the NE corner
  buy an END CONDITION and never a shorter required length.
- **Item 8, ×2.00 where horizontal blocking is omitted.** It applies to WSP and CS-WSP, and
  it would double every number in the table above. It is not taken because a 9'-0" wall
  sheathed in one 9'-0" sheet has no horizontal joint to block. **If the sheathing is ever
  ordered in 8-foot sheets, this factor arrives** and main E1 goes from 1.56× to 0.78 — a
  FAIL. That is the single most expensive thing anybody could change about this wall.
- **Item 7, ×0.70 for gypsum fastened 4" o.c.** — Method GB only.

## 5. The panels

Every panel is a full-height run of wall between openings, measured off the resolved model,
and no run under Table R602.10.5's minimum is authored: it would contribute nothing and only
put a zero on the drawing. The minima here are 27"-35", read on the adjacent clear opening
height (the taller of the two openings a panel stands between, R602.10.5).

Not authored, and each is deliberate: main E1's two 25-1/2" slivers beside the fire niche
(the 30" row, adjacent opening 80"); the two 17" ends beside WIN-M-KIT-E and WIN-M-KITCH-N;
second S1's 19" beside the deck door; the garage's 7" beside D-G-SERVICE.

The garage's blind east wall and its south wall are each drawn as **two** panels rather than
one. R602.10.2.3: a braced wall line over 16 feet carries not less than two braced wall
panels. The sheathing is continuous either way; the designation is not.

## 6. The NE corner: three options, and the one taken

Both lines at the NE corner end in a 17" sliver — WIN-M-KIT-E and WIN-M-KITCH-N sit 2'-7"
off the corner on the main floor, WIN-S-BED3 and WIN-S-BED3-N on the second — so **there is
no 24" return to turn** at that corner on either storey. Figure R602.10.7's options:

1. **Move the four windows 16" inboard.** Buys the returns on both storeys, deletes all four
   devices, costs nothing in hardware. It moves four windows off the facade grid and out of
   the two-storey column WIN-S-BED3/WIN-S-BED3-N make with WIN-M-KITCH-N (the house guide's
   "Columns" rule). **This is the standing alternative** and is recorded as one.
2. **A 48" panel at each line's end (end condition 3).** Impossible: the windows are 2'-7"
   off the corner.
3. **An 800-lb hold-down at the end of the panel nearest the corner (end condition 5).**
   Four devices, two per storey. **Taken** (owner, 2026-09-22).

Never move those four windows TOWARD the corner — that is the one direction with no answer
at all.

The parts, and what they publish:

| Device | Part | Published | Report |
|---|---|---|---|
| `CN-M-BWHD-NE-E`, `-N` | STHD14RJ cast in the basement wall top | 4,410 lb (endwall, 8" stem, wind/SDC A&B) | ICC-ES ESR-2920 Table 1 |
| `CN-S-BWHD-NE-E`, `-N` | DTT2Z pair on a 1/2" rod through the floor | 1,825 lb (1-1/2" member) | ICC-ES ESR-2330 Table 4 |
| `CN-G-BWHD-SW` | STHD14 cast in the ICF-6 core | 3,065 lb (endwall, 6" stem) | ICC-ES ESR-2920 Table 1 |

All five clear the 800 lb the figure asks for by three times or more. Two caveats belong to
the reader and not to the arithmetic: the **RJ** strap is the one long enough to cross the
main floor's 13-1/2" band (its unnailed clear span limit is 17"), and ESR-2330 publishes the
DTT2Z for **SG ≥ 0.50 lumber only** — the two second-floor corner posts are specified DF-L
for that reason, and this house otherwise frames SPF.

## 7. The garage SW corner takes a fifth device

`D-G-SERVICE` sits 7" off that corner, so `W-G-S` has no 24" return to give `W-G-W`'s end
panel, and the 29" panel at that end therefore meets end condition **2** (panel at the end
of the line with a hold-down) rather than 1. The alternative is to move the service door 17"
east, which `plan/storeys/garage.py` warns drags the landing, both carriers, two backing
bands, three lighting stations and a section cut along with it. One cast-in strap is
cheaper. Note the asymmetry that makes this corner odd: the same 29" panel IS the return
that satisfies the SOUTH line's own end (condition 4), so the corner is short in one
direction only.

## 8. The 16' overhead door needs no portal frame

Its two piers are 4'-0" wide. Table R602.10.5, CS-WSP, adjacent clear opening height 84",
read at the more onerous of the 8-foot and 9-foot columns for an 8'-4" wall: **35"**. The
piers clear it by 13". `OVERHEAD_DOOR_OFFSET` is therefore a graded fact rather than an
undefended constant — at 3'-0" the piers would still clear (36" against 35"), and below that
the garage would have to adopt Method CS-PF (R602.10.6.4), whose own minimum is 16"-18" but
which brings a portal frame's straps, header and anchorage with it.

## 9. The three places this can go wrong

1. **The transcription.** 90 cells of Table R602.10.3(1), the whole of R602.10.5, and eight
   adjustment rows. Four independent renderings agreed on every numeric cell (the module
   header lists them), so what remains is the risk that all four render the same edition
   wrongly. A printed ICC copy would settle it.
2. **The citation strings.** The 2018 text was read end to end before the first `code=`
   shipped, which is how `R602.10.2.2`'s "within 10 feet" survived its own SI erratum
   ("3810 mm" = 12.5 ft, a fossil of the 2012 edition's deleted "total combined distance"
   rule) and how `R602.10.11` — which does not exist in the 2018 IRC — never got quoted.
3. **The 24" × 24" service-penetration threshold.** `resolve/braced_walls.py` treats a
   `RoughOpening` no larger than that as a service penetration that does NOT split a panel.
   **No code section states it.** Three holes in this house depend on it: AO-M-ERV-OA (9"),
   AO-S-ERV-EA (9") and AO-M-PORCH-HYD (2-1/2"). The reasoning is that an ERV port or a hose
   bibb is not an opening a panel is bounded by, and that the sheathing is continuous across
   it; a reviewer who disagrees would split BWP-M-N3B-0000 (78" → 27" + 42") and
   BWP-S-N3B-0000, both of which still clear their minima. It is the softest number in this
   whole pass and it is stated rather than buried.
