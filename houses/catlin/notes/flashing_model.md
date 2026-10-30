# Flashing in the model

Implemented 2026-10-15. The Views panel's **Flashing · 3D** control hides or isolates metal
flashing and opening membranes together. Construction trades remain separate: roof metal
is roofing, wall/head metal is siding, and opening membranes/pans belong to openings.
The control does not include gutters, connectors, or ordinary window casing.

`TR-BW-SCREEN-CAP` protects the **exposed upper surface of SB-BW-BAND's 2×6 sill**, above
W-BW-SCREEN's +4′-0″ top. It does not lie between the sill and wall. Its 0.032″ dark metal
falls west at ¼″/ft, with a ¾″ drop and ¼″ hem beyond the corrugated face. The east return
projects ⅛″ past the existing 2×6. Resolved wood and connector intersections cut the cap
with 1/16″ installation clearance; structural members and bearing elevations stay fixed.
It is billed once by run length under `edge_trim/beam_cap`.

Since 2026-10-16 the cap **bears on tape**: `SB-BW-BAND.top_protection = "butyl-tape-beam"`,
the porch beams' wide roll, over the whole sill and turned up 1" round each of the eight
slats and the centre post that land on it. It is the dielectric between the steel and the
KDAT and the seal at every cut-out. It bills 15.5 LF in `member_protection`, under
`scope="brace"`. It is not drawn.

The cap mesh describes the exposed cover and its cutouts, not fabrication seams, the tape
collars, sealant joints, or a tested waterproof connection at each penetration. Develop
those installation details around the actual connector hardware before fabrication.
The proposed east-face decorative locust assembly remains a separate implementation;
this cap is sized to current finishes and the existing sill.

Exterior windows and pedestrian doors now carry separately selectable metal heads, sill
pans, and concealed jamb/head membranes. The head flashing reads the resolved water plane,
mount plane, cladding, and head course. Its back leg rises 2″ on the outie wall or 3″ on a
conventional wall; the shedding leg slopes out to a drip and hem. The configured membrane
thickness is 60 mils at sills and 20 mils around the remaining perimeter. These are model
defaults, not a selected manufacturer's submittal. The 2D opening detail reads the same
numbers (`resolve/flashing_config.FLASHING`).

Revised 2026-10-16, after a review measured the built model against the specs:

- **The head** is `metal-dark-exterior` steel (`Project.opening_flashing_material`). It runs
  1″ past each casing end, or past the RO where there is no casing, with 3/4″ end dams. Its drip
  clears a window's casing face, or a door's cladding. On the outie wall it is bedded on
  membrane over the KDAT head course. A membrane strip-in seals its upstand's top edge to the
  water plane.
- **On a truss wall every membrane lies on the 3/8″ plywood buck's face.** The buck lines the
  RO, so the reveal membrane sits 3/8″ inside the RO. It used to be drawn buried in the plywood.
- **On a truss wall nothing laps onto the foam face at an opening** (2026-10-30,
  `resolve/opening_raccoon.py`). The old wrap onto the foam lay in the 1/2″ slot behind the
  KDAT posts and head course, and through the buck. Instead a pre-foam "raccoon" covers the
  buck's wall-side face and front edge and a 4″ band of sheathing round the RO (the foam laps
  over it); a 2″ band covers each jamb post's outer face; and a window pan's drip coat runs
  the sill course face and underside, across the posts' end grain. All are the same
  `opening_flashing_membrane`/`opening_sill_pan` solids, hidden in elevation.
- **The pan falls 1/4″/ft on a tapered KDAT shim**, its back dam up a 1/2″ KDAT strip
  (`sill-support`, filed with the pan). A window's outie pan turns down over the buck's
  front edge, at the outer girt face, behind the sill trim. **A door's pan runs past the
  cladding** (D-M-ENTRY, D-S-DECK-E, D-G-SERVICE): a threshold has no trim to hide behind.
- **Jamb membranes stop at the wall's base**: D-G-OVERHEAD's no longer hang over the stem
  end. Overhead doors get head and perimeter flashing without a pan.
- **Coverage**: `integrity.opening_flashing_coverage` names every exterior opening that draws
  none. Today that is D-B-PATIO and WIN-B-SAUNA, behind the court's brick veneer (spec §8);
  their hand spec prints on D-B-PATIO's starred detail (`court_opening_detail.md`).
  Interior openings and bare rough openings receive no derived flashing.
- **`integrity.derived_solid_material`** fails a derived solid whose material is not in the
  catalog. `fluid-applied-flashing` and `aluminum` dangled before, so the look fell back to
  category colours.

The shared meshes feed model.json, the live viewer, IFC, and GLB. A viewer depth bias lets
liquid flashing read on its substrate without inflating its physical thickness. Derived
opening surfaces do not add purchase quantities: the existing opening-flashing allowances
and trim-inclusive siding rates still buy them. The same formed-sheet representation
replaces the garage stem drips and balcony drip/counterflashing; gutters remain unchanged.
The stem Z (`TR-G-STEMZ-*`) is a `counter` section, its 2″ back leg standing up the CDX behind
the panel. The balcony's rear edge is two pieces across the movement gap: a deck-side
aluminium base flashing with a 3 1/2″ upstand, and a house-side steel counterflashing lapping
2″ over it with 1/2″ of air beside it. Neither is fastened across the gap, and both break at
D-S-DECK-E.

The existing construction specifications still govern, including their open substrate
approval item: [opening flashing specification](opening_flashing_spec.md) and
[outie-window detail](outie_window_truss_detail.md). Showing a membrane in 3D neither closes
that item nor verifies installation, adhesion, watertightness, or door hardware clearance.
Garage and court openings are spec §7 and §8.
