# Suite-bath extract connection

`REG-S-EXH3` is a high sidewall intake on the bathroom face of `W-S-DC2`,
not a floor intake in front of the lavatory. Its tag, UID, branch identity and
20 cfm continuous extract are retained. The valve is the existing removable
100 mm white steel disc-valve family.

## Location and route

The valve station is global y=196 in., 5 in. north of the wall's start.
Its face bottom is 95 3/4 in. above the finished tile; its centre is
98 9/32 in. above it. This is below the double top plate, above the door
leaf, and south of the robe-peg backing. The original proposed y=203 in.
station put the riser through that backing.

`DU-M-ERV-R-SUITEBATH` leaves the existing 8 in. extract trunk at
(45 3/4, 196) in., rides the lower tier at second-relative -8 3/8 in.,
then rises at (115 1/2, 196) in. inside the staggered wall cavity.
The horizontal-to-vertical turn has space for the existing 4 in. duct's
6 in. centreline-radius elbow. It does not cross a truss.

`FO-S-ERV-SUITEBATH`, explicitly listed on `FS-S-WEST`, draws the
4 1/4 in. square deck clearance centred on the riser. Bore the matching
4 1/4 in. bottom-plate hole; no stud, top plate or floor member is cut.
The opening has `cuts_ceiling_below=False`: this riser starts inside the
floor cavity, so the main-storey closet ceiling below stays continuous.
Seal the duct joints and close the annulus at the plate/deck with mineral
wool and compatible fireblocking sealant. Retain the balancing damper
at the trunk takeoff. No access panel is needed to remove the disc valve.

## TH-ERV-SUITEBATH-BOOT-01 fabrication

A 1.5D round elbow cannot turn behind the valve inside this wall. Use the
specified sealed 26ga galvanized bottom-entry box, including the front
collar and mounting tabs within its overall envelope:

| Dimension | Specification |
| --- | --- |
| Along wall | 4 in. |
| Height | 8 in. |
| Depth from valve back plane | 5 1/4 in. |
| Bottom inlet | 4 in. round, centred along wall, axis 3 1/4 in. behind front |
| Front outlet | 100 mm valve collar, centred on face |

The envelope occupies global x=113 1/2..118 3/4 in.,
y=194..198 in., and second-relative z=95 25/32..103 25/32 in.
The riser's final mouth meets the bottom inlet at z=95 25/32 in.
The box clears the first staggered stud by 1/4 in. and the lowest top
plate by 19/32 in. The front collar passes through the gypsum opening;
the room-side valve remains surface mounted and removable for cleaning.
Support the box with tabs fixed to adjacent framing, keeping the air passage
and riser clear; seal seams before closing the wall.

The solid-overlap baseline includes the new riser and box inside the wall's
gross envelope. This is cavity occupancy; the dedicated regression checks
separately require clearance from the actual studs, backing and top plates.

This is a project fabrication specification, not a manufacturer's tested
elbow or pressure-loss claim. `REG-T-ERV-SUITEBATH-WALL` reuses the valve's
published-family loss curve and adds the same conservative K=5 boot
allowance used for the former floor boot (4 Pa at 20 cfm, scaled with
flow squared). The boot is a separately named included product in the
terminal takeoff. Balance the installed branch to 20 cfm and verify noise.

The rerouted branch is 14.49 ft developed, with one catalogued 90-degree
duct elbow plus the box's internal turn. At 20 cfm the engine calculates
0.00571 in. w.g. for the duct and elbow and 11.46 Pa for the valve/box
curve, approximately 0.052 in. w.g. combined before the shared trunk and
manifold. It does not become the ERV's governing path.
