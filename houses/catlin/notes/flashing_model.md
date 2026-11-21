# Flashing in the model

Implemented 2026-10-15. The Views panel's **Flashing · 3D** control hides or isolates metal
flashing and opening membranes together. Construction trades remain separate: roof metal
is roofing, wall/head metal is siding, and opening membranes/pans belong to openings.
The control does not include gutters, connectors, or ordinary window casing.

**The west screen top (2026-11-20).** SB-BW-BAND's 2×6 KDAT sill above W-BW-SCREEN's +4′-0″ top
is bare wood under the house's KDAT finish (pigmented penetrating oil, horizontal faces recoated
every 2–3 yr; 2% copper naphthenate on every cut, AWPA M4, including the slat and post feet). It
replaced `TR-BW-SCREEN-CAP` (retired uid `PD2PPXS59S`), a steel cap pierced round both brace feet,
the centre post and the KBS1Z plates: every cut-out is a sealant joint that lets water in and
holds it against the wood, and the cap cannot go on once the band is framed.

Metal stays only where nothing passes through it. `TR-BW-SCREEN-TOP` is a 0.032″ PVDF aluminium
`counter` section over the west ZIP + corrugated, which stand 1 5/16″ proud of the sill's west
face: a 1″ upstand sealed to that face below the KBS1Z plates (they start at +50.45″), ¼″/ft
fall west, ¾″ drip and ¼″ hem over the corrugated. Post face to post face, ~4.5 LF, billed in
`edge_trim/drip_flashing`. The east MDO is already under the sill's ~1 1/16″ overhang, its edges
primed and painted (`entry_screen_mdo.md`).

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
- **Metal over membrane, never behind it** (2026-11-16). A metal-wall window's jamb, sill and
  head trim are swept off their bearing face, standing on the membrane under them, and the
  sill trim's upstand rises to the unit's sill in front of the pan's turn-down. A window pan
  behind metal trim, garage included, discharges at the mount plane; only a door's pan, or a
  cased opening's, runs to its own drip.
- **The pan falls 1/4″/ft on a tapered KDAT shim**, its back dam up a 1/2″ KDAT strip
  (`sill-support`, filed with the pan). A window's outie pan turns down over the buck's
  front edge, at the outer girt face, behind the sill trim. **A door's pan runs past the
  cladding** (D-M-ENTRY, D-S-BALCONY, D-G-SERVICE): a threshold has no trim to hide behind.
- **Jamb membranes stop at the wall's base**: D-G-OVERHEAD's no longer hang over the stem
  end. Overhead doors get head and perimeter flashing without a pan.
- **Coverage**: `integrity.opening_flashing_coverage` names every exterior opening that draws
  none. Today that is D-B-SUNKEN and WIN-B-SAUNA, behind the court's brick veneer (spec §8);
  their hand spec prints on D-B-SUNKEN's starred detail (`court_opening_detail.md`).
  Interior openings and bare rough openings receive no derived flashing.
- **`integrity.derived_solid_material`** fails a derived solid whose material is not in the
  catalog. `fluid-applied-flashing` and `aluminum` dangled before, so the look fell back to
  category colours.

The shared meshes feed model.json, the live viewer, IFC, and GLB. A viewer depth bias lets
liquid flashing read on its substrate without inflating its physical thickness. Derived
opening surfaces do not add purchase quantities: the existing opening-flashing allowances
and trim-inclusive siding rates still buy them. The same formed-sheet representation
replaces the garage stem drips and balcony drip/counterflashing; gutters remain unchanged.
The stem Z (`TR-G-STEMZ-*`) is a `counter` section, its 2″ back leg standing up the ZIP face behind
the panel, ZIP tape lapped over it. The balcony's rear edge is the house's BBD75 band trim
(2026-11-19): the band sits at +10'-5 1/2″, just over the deck, and there the 55536XX section
is braked longer (`TR-SG-BAND-W/E`), its 2″ back leg captured under the upper panel on the
band girt, its 5° shelf running 1″ past the capped deck edge to the stock 2 1/2″ face leg as
a drip, lapping the lower panel 1 3/4″ and stopping ~1.8″ above the plank. The stock trim laps
2″ under each end. Nothing crosses the movement gap fastened; it breaks at D-S-BALCONY's casing. It
replaced a deck-side base flashing and a counterflashing screwed over the battens.

The existing construction specifications still govern, including their open substrate
approval item: [opening flashing specification](opening_flashing_spec.md) and
[outie-window detail](outie_window_truss_detail.md). Showing a membrane in 3D neither closes
that item nor verifies installation, adhesion, watertightness, or door hardware clearance.
Garage and court openings are spec §7 and §8.
