# Sheet layout oracle: W-G-S by hand (decision #146)

Worked from the framing printout (`wall.members`), not from the engine's layout, and pinned
by `packages/engine/tests/test_sheet_layout.py::test_catlin_garage_south_matches_the_oracle`.

## The house values (`plan/framing_standards.py`)

- **Edge bearing 7/16".** APA E30 (wall sheathing) puts panel-edge nails 3/8" from the
  edge. The shank must land inside the member face too, so add half an 8d common's
  0.131" shank: 0.375 + 0.0655 = 0.4405, taken as 7/16" (0.4375). A joint is therefore
  backed within `face/2 - 7/16"` of a member's centre line: 5/16" either side of a single
  2x stud (3/4" - 7/16"), 1 1/16" on a doubled pair.
- The code rule graded is IRC R602.10.4.4: "Vertical joints of panel sheathing shall occur
  over and be fastened to common studs. Horizontal joints of panel sheathing in braced wall
  panels shall occur over and be fastened to common blocking of a thickness of 1 1/2 inches
  or greater" (exception 1: item 8's factor instead, which `bracing_eval` applies).
- Narrowest rip 12" and 16" stagger are house preferences, not code.

## W-G-S: 7/16" ZIP, 4x9 sheets, vertical

- **Run.** W-G-S's sheathing runs through the SW corner (`sheathing_through` at its start)
  and stops on the back of W-G-E's at the SE corner: the framing-side face is
  0 to 288 - 7/16 = **287 9/16"** (287.5625). The walk starts at the through end, s = 0.
- **Band.** -12" (top of slab, the 2x8 plate's underside) to +88" (top plate): 100", one
  course; each 108" sheet is cut 8" short. No horizontal joint.
- **Break 1.** Target 48". Nothing covers 48 +/- 7/16" over the full height (king-0-r1 is
  46.00-47.50; backing-3-000 at 47.50 is a 2x12 block at z 29.5-40.75 only). The last face
  at or before 48 is king-0-r1: break on its centre, **46 3/4"**; each panel gets 3/4" of
  the king. Behind the joint: the 2x8 plate (-12 to -10.5), the king (-10.5 to 85), the
  top plates (85 to 88): backed full height.
- **Break 2.** Target 46.75 + 48 = 94.75. stud-002 (96) is past it; the last stud before
  it is stud-001: **72"**. A 25 1/4" rip.
- **Breaks 3-6.** 72 + 48 = **120, 168, 216, 264**, each a 24" o.c. stud centre.
- **Last piece.** 264 to 287.5625 = 23 9/16", a rip over the 12" minimum: no rebalance.
- **Pieces.** [0, 46.75] is cut by D-G-SERVICE (centre 26", 34" wide: 9 to 43, z 0 to
  81.5); [46.75, 72] rip; four full sheets; [264, 287.5625] rip.
- **Sheets.** 4 full + width-packed strips with a 1/8" kerf: 46.75 (one sheet, 1.25" left),
  25.25 (a second, 22.875" left), 23.5625 + 0.125 = 23.6875 does not fit the 22.875" left,
  so a third: **7 sheets** for 200 sf gross (5.5 sheets by area).

## What the run joins

A wall split at a tee is laid with its collinear neighbours as one run
(`resolve/sheet_layout_runs.py`): W-S-E1..E4 is one 431.5" face, not four walls each
ripping a sheet at the split.

## Open framing gaps the layout surfaced (UNKNOWN, not FAIL)

- **W-M-S1 / W-M-S2 over the framed walkout.** W-B-S2-FR and W-B-S3-FR top out at -13 7/16"
  but FS-M-WEST's rim starts at -11 7/8": a 1 9/16" band with no sill modelled under the
  sheathing (the concrete walls have their sill plate solid there).
- **W-M-N2 / W-M-N3B under FO-S-STAIR.** The second floor's stair opening reaches the north
  wall and its edge member is a trimmer set 1 7/8" inboard of the sheathing, so 11 7/8" of
  every joint over the floor band (108 1/8" to 120") has no rim behind it.
