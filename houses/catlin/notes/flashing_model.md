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

The cap mesh describes the exposed cover and its cutouts, not fabrication seams, flexible
collars, sealant joints, or a tested waterproof connection at each penetration. Develop
those installation details around the actual connector hardware before fabrication.
The proposed east-face decorative locust assembly remains a separate implementation;
this cap is sized to current finishes and the existing sill.

Exterior windows and pedestrian doors now carry separately selectable metal heads, sill
pans, and concealed jamb/head membranes. The head flashing reads the resolved water plane,
mount plane, cladding, and head course. Its back leg rises 2″ on the outie wall or 3″ on a
conventional wall; the shedding leg slopes out to a drip and hem. The configured membrane
thickness is 60 mils at sills and 20 mils around the remaining perimeter. These are model
defaults, not a selected manufacturer's submittal.

The Catlin outie pan runs from the buck's inboard edge to the mount plane, then turns
down **behind the cladding into the vent gap**, preserving the concealed drainage outlet.
Entry door pans include back/end dams and discharge outward. Overhead garage doors get
head/perimeter flashing without a pedestrian threshold pan. Interior openings and bare
rough openings receive no derived flashing.

The shared meshes feed model.json, the live viewer, IFC, and GLB. A viewer depth bias lets
liquid flashing read on its substrate without inflating its physical thickness. Derived
opening surfaces do not add purchase quantities: the existing opening-flashing allowances
and trim-inclusive siding rates still buy them. The same formed-sheet representation
replaces the garage stem drips and balcony drip/counterflashing; gutters remain unchanged.

The existing construction specifications still govern, including their open substrate
approval item: [opening flashing specification](opening_flashing_spec.md) and
[outie-window detail](outie_window_truss_detail.md). Showing a membrane in 3D neither closes
that item nor verifies installation, adhesion, watertightness, or door hardware clearance.
