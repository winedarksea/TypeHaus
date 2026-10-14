# Study bookcase door — stationary oak bridge

The resolved `D-A-STUDY` casing ends at x=263 3/4"; the fixed bookcase's west filler starts
at x=269 3/8". Its front is y=105 5/8", while the door casing's front is y=99 3/4".
The resulting 5 5/8" gap and 5 7/8" depth step are covered by four oak boards, ending at
the tallest fixed shelf's 60" top. The door, shelving, partitions and stair-pocket closure
retain their positions.

## Geometry and cut list

All dimensions are finished sizes. Use owner-stock 4/4 oak dressed to 3/4", with the same
finish as the adjacent casework and `oak-trim`.

| Board | Quantity | Finished size | Plan bounds (inches) |
|---|---:|---|---|
| Front | 1 | 5 1/2 x 60 x 3/4" | x=263 7/8..269 3/8; y=99 3/4..100 1/2 |
| West return | 1 | 5 1/8 x 60 x 3/4" | x=263 7/8..264 5/8; y=100 1/2..105 5/8 |
| East return | 1 | 5 1/8 x 60 x 3/4" | x=268 5/8..269 3/8; y=100 1/2..105 5/8 |
| Cap | 1 | 4 x 5 1/8 x 3/4" | x=264 5/8..268 5/8; y=100 1/2..105 5/8 |

The front is flush with the casing, with a 1/8" reveal on its east side. The two returns
butt behind it and run back to the partition finish and the existing bookcase filler.
The cap fits between the returns, with its underside at 59 1/4" and top at 60" above the
built-in's base. There is no back or bottom board. The four boards consume 5.03 finished
board feet; the cut list is finished stock, not a rough-stock yield allowance.

`plan/millwork.py` lists all four boards in `MW-STANDARD.board_furniture_refs`.
`haus millwork houses/catlin` includes three `casework board` rows: one front, two returns
and one cap, all 4/4 oak S4S. Finished sizes derive from the furniture types rather than a
second cut-list declaration. The usual jointing and length allowances total **8.6 rough
board feet** for the bridge. These rows carry `also_in_placeables` because their fabrication
cost remains in the three existing bridge price rows.

The editable `plan/study_bridge.py` owns the named sizes, three furniture types and four
placed boards. Its `closet-board` geometry and `oak-trim` reference feed drawings, the
viewer and GLB; each board also emits as an individual `IfcFurniture` prism.

## Installation and cost

Support the cover on stationary cleats/backing at the partition and fixed filler. Keep
its fasteners independent of the moving door, factory pivot hardware and casing attachment.
Hang and adjust the purchased unit first, then field-fit the reveal. The modeled closed
door and swing-clearance envelope do not include the factory pivot-axis sweep; follow
[Murphy Door's installation guidance](https://help.murphydoor.com/hc/en-us/articles/1260804787769-Flush-Mount-Installation)
and confirm full opening and closing travel before fastening the cover permanently.

The three `[placeables]` price rows count one front, two returns and one cap. Owner-stock
wood carries $0 purchase cost; the **planning allowance**, not a supplier quote, totals
**$0-50 for cleats, fasteners and finish, plus $120-300 for fabrication and installation**.
The bridge is outside the fixed bookcase's allowance and `SB-A-STUDY`'s twelve shelves;
neither the hardwood shelf quantity nor the purchased door price includes it.
