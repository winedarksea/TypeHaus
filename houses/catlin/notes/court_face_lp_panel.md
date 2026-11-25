# Court face: LP SmartSide smooth panel (W-B-S2-FR, W-B-S3-FR)

## Sheet layout and joint battens

Worked by hand from the model's walls, girts and openings (not from the engine's layout), and
pinned by `test_sheet_layout.py::test_catlin_court_face_matches_the_lp_panel_oracle`. Stations
are inches along W-B-S2-FR's axis from its start (x = 118"); the two walls are collinear and
laid as one run.

**Inputs.**

- Run: W-B-S2-FR x 118 to 216 (98"), W-B-S3-FR x 216 to 314 (98"): **196"**, both ends free
  (no through corner), so the walk starts at W-B-S2-FR's end, s = 0.
- Band: the panel's foot stands on the base strip, -102 3/16 (wall base) + 1" (base trim
  rise) + 0.032" (strip) = **-101.1555"**, to -13 7/16", where W-M-S1/S2's cladding begins
  over the court walls: **87.718"**. One 96" sheet stood vertically covers it, so there is
  **no horizontal joint** and no Z-flashing seam (AI 2024 p.2 is for a horizontal seam).
- Sheet 4x8 (48" module; LP's actual 47.81" plus the 1/8" gap is the module). Narrowest rip 12"
  (the house's `SheetLayoutStandard`).
- Girt courses (KDAT 2x4 flat, 3 1/2" tall), bottoms at -99 15/16 (the starter, lifted
  2 1/4" clear of the base metal), -78 3/16, -54 3/16, -30 3/16, -15 3/8; the -54 3/16
  course is broken by WIN-B-SAUNA.
- WIN-B-SAUNA: RO s 43 to 57 (x 161 to 175), z -65 7/16 to -41 7/16, sill ladder
  -68 15/16 to -65 7/16, head ladder -41 7/16 to -37 15/16.
- D-B-SUNKEN: RO 63 5/16" wide, s 106 11/32 to 169 21/32 (x 224.34 to 287.66), head
  -21 1/16, head ladder -21 1/16 to -17 9/16; its foot is below the band.

**Joints.** 48, 96, 144; a fourth at 192 would leave 4" (< 12"), so it comes back to
196 - 12 = **184**. Joints at s **48, 96, 144, 184** (x 166, 214, 262, 302). A nailer fits at
each (none lands within a nailer's half-width of an RO edge or a jamb post), so none moves.
s 48 crosses WIN-B-SAUNA 2" left of its centre; s 144 crosses D-B-SUNKEN over its head.

**Sheets.** Columns 0-48 and 48-96 (both cut round the window, W-B-S2-FR), 96-144 (cut
round the door, across the wall split), 144-184 (door, W-B-S3-FR), 184-196 (12" rip, W-B-S3-FR).
Every column needs its own strip of a sheet: 48 + 48 + 48 + 40, and the 12" rip does not fit
the 40" column's 7 7/8" offcut. **5 sheets**: W-B-S2-FR 2, W-B-S3-FR 2, one across the split.

- Gross 196 x 87.718 = 17,192.7 in2. Window 14 x 24 = 336.0; door 63.3125 x (-21.0625 +
  101.1555 = 80.093) = 5,070.9. Net **11,785.8 in2 = 81.8 ft2**.
- Bought 5 x 32 = 160 ft2: 78.2 ft2 of offcut, 49% of what is bought (the door takes most).

**Joint nailers** (KDAT 2x4 flat, 3 1/2" on the panel, cut between courses; ESR-1301 s.4.3).

| Joint | Pieces (z, in) | Length |
|---|---|---|
| s 48 | -96 7/16 to -78 3/16; -74 11/16 to -68 15/16 (sill ladder); -37 15/16 (head ladder) to -30 3/16; -26 11/16 to -15 3/8 | 18.25 + 5.75 + 7.75 + 11.3125 = 43.0625 |
| s 96 | the four bays between courses, -96 7/16 to -15 3/8 | 18.25 + 20.5 + 20.5 + 11.3125 = 70.5625 |
| s 144 | head ladder top -17 9/16 to top course -15 3/8 | 2.1875 |
| s 184 | as s 96 | 70.5625 |

**13 pieces, 186.375" = 15.53 LF.** No nailer goes under the starter course: it would stand
on the aluminium base strip (AWC DCA6). So the panel's foot, -101.1555 to -99 15/16
(**1.22"**), is bare at joints s 48, 96 and 184 (s 144 starts at the door head):
`structural.sheathing_edge_support` reads it UNKNOWN. The same 1.22" is the whole bottom
edge's overhang below the starter, which is the base detail's question, not the joints'.

**Battens** (LP 440 Series smooth 3.50" x 0.675", 16 ft, PID 46000), vertical joints only,
stopped at an opening (and at any trim hosted on it):

| Joint | Pieces (z, in) | Length |
|---|---|---|
| s 48 | -101.1555 to -65 7/16 (window sill); -41 7/16 (head) to -13 7/16 | 35.718 + 28.000 |
| s 96 | -101.1555 to -13 7/16 | 87.718 |
| s 144 | door head -21 1/16 to -13 7/16 | 7.625 |
| s 184 | -101.1555 to -13 7/16 | 87.718 |

**5 pieces, 246.8" = 20.56 LF**, cut from **2 sticks** (87.718 x 2 in one; 35.718 + 28 +
7.625 in the other). No head trim is hosted on either opening yet; when one is, the batten
stops at it instead of at the RO.
