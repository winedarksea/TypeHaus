# Study bookcase door — flush mount, oak casing, oak infill

`D-A-STUDY` is a Murphy Door 36 x 80 nominal pre-hung flush-mount bookcase door, in-swing,
hinged west, in W-A-SN (2x4 partition, 1/2" board both faces, 4 1/2" overall since 2026-10-23). The shelf face
is the study (south); the door swings north into the loft.

## What the manufacturer says

From Murphy Door's *Pre-Hung Flush Mount Installation* sheet and its spec table:

- Rough opening = nominal + 2": **38 x 82**. Frame it with 2x4; 2x6 is out-swing only.
- The jamb is **4 9/16"** deep, installed tight to the drywall edges. The threshold "extends
  into the room toward the back of the bookcase".
- The 8 1/4" door's face frame sits flush with the jamb edge on the shelf side. The body
  protrudes **3 3/4"** on the other side, and in-swing needs 1 1/2" hinge-side wall clearance.
- The cabinet is 1 1/2"-2" narrower than the jamb. "Gaps will be covered by finish casing".
- **In-swing casing is applied with a 1/2" overhang on the face frame**, sides and head. It
  goes on after the door is hung and tested. The other face of the jamb is caulked/mudded to
  the wall.

## Geometry (inches, plan)

| Item | x | y |
|---|---|---|
| Rough opening | 223 1/2..261 1/2 | (W-A-SN, axis y=108) |
| Cabinet (face frame to back) | 225 1/8..259 7/8 | 105 3/4..114 |
| Casing, west leg | 222 1/8..225 5/8 | 105..105 3/4 |
| Casing, east leg | 259 3/8..262 7/8 | 105..105 3/4 |
| Oak infill | 262 7/8..269 3/8 | 105..105 3/4 |
| Bookcase filler starts | 269 3/8 | front 105 3/4 |

The face frame lies on the study finish (105 3/4; 105 5/8 before the 1/2" board). `FO-A-STAIR`'s north edge is that same
line, so no part of the cabinet stands over the well. Only the 3/4" casing and infill lap
past it, as trim on the wall. The back is 3 3/4" past the loft finish (110 1/4), inside the
swing clearance. The resolved framing needed no change: jack and king each side, a flat
2x4 nonbearing header, and the east king (263..264 1/2) beside the W-A-SN-WR corner post.

**Jamb depth.** The 4 9/16" jamb stands 1/16" proud of the 4 1/2" wall (it was 3/16" short
of the old 4 3/4" one). Set it flush to the study face (the cased side) and ease the 1/16" on
the loft side; no scribe or special jamb is needed. The body's back stands 3 3/4" proud.

## Casing and infill

The casing is the house's own: `TRIM-STANDARD` oak, 3 1/2 x 3/4 S4S, derived
(`resolve/interior_trim_casing.py`) on the study face only. The legs stand on the finished
floor, their inner edges 1/2" over the face frame. The head bottom is 1/2" below the
78 1/2" body top, at 78". It bills by the LF in interior trim. The Murphy factory casing ships
with the unit and is not installed.

`FURN-A-STUDY-BRIDGE-FRONT` is one owner-stock 4/4 oak board dressed to **6 1/2 x 60 x 3/4"**,
in the casing plane. It butts the east leg (glue/biscuit), fastens to W-A-SN's backing, and
is scribed at its east edge to the bookcase filler. Its top is level with the built-in's 60"
top, with painted drywall above it beside the leg. It is fixed to the wall and casing,
never to the moving door.

`haus millwork houses/catlin` lists it as one `casework board` row, 4/4 oak S4S, **3.4 rough
board feet**. The size comes from the furniture type, not a second declaration.

## Cost

The `[placeables]` row `FT-A-STUDY-BRIDGE-FRONT` is a **planning allowance, not a quote**:
$0-20 for glue, fasteners and finish, plus $60-140 to mill, fit and scribe. Owner-stock wood
costs $0. The casing legs and head are priced in interior trim as `oak-trim:door casing`.

## Open

- `ED-A-STUDY-SW` (x=260 3/8", 48" AFF) sits under the east casing leg
  (`advisory.trim_device_clash`). W-A-C1B is full with D-A-HALVES, and the framing behind
  the infill is solid (king + corner post), so there is no free stud bay beside the door.
- Verify threshold anchorage, jamb fastening and floor blocking against the delivered unit.
  The modelled swing envelope is the published clearance, not a calculated pivot sweep.
