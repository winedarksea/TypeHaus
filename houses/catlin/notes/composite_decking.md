# Trex Enhance Basics decking (2026-10-15)

FS-BW-FLOOR, FS-SG-PORCH and ST-G-SERVICE use the main library's
`TREX_ENHANCE_BASICS` and `TREX_ENHANCE_BASICS_DECK_LAYER`: square-edge
0.94 x 5.5 inch scalloped capped composite. Color remains unselected. Generic
`composite-deck` remains available for other products. Product properties and dimensions
live in `typehaus.library.decking`, not house-local copies.

## Elevations and the door

The entry stays at 0'-0 finished: wood joist tops -0.94 inch, seat-beam tops -8.19 inch,
pier bearing tops -15.44 inch. The porch keeps wood joist tops at 0'-0 and finishes at
+0.94 inch; its guard and ST-SG-PORCH arrival follow that surface. ST-SG-PORCH's treads
stay KDAT, and the unmodeled wall-top threshold strip matches the porch's Trex stock.
Roof elevations and ST-BW-ENTRY's concrete tiers do not change.

W-G-S sill-0 and its cripple remain KDAT, carrying the door threshold on a sloped,
back/end-dammed pan per opening_flashing_spec.md section 6. Matching composite finishes
stop at the threshold, with an open pan discharge and movement gap. No board through the
rough opening, no composite replacing a structural rough sill, and no caulk closing the
pan outlet. The modeled entry deck stops 1/2 inch off both house and garage faces. The independent structures are
not tied together by a continuous finish board.

## Service-stair cut and support schedule

Four complete 36 x 11 inch treads, each made from two square-edge boards:
front 5.5 inch + 1/4 inch drainage gap + rear ripped to 5.25 inch. Eight 36 inch pieces
in total. The existing model represents each complete tread envelope; the gap and scallops
are fabrication details, not extra modeled treads. No nosing. Five finished risers remain
6.8 inch, base -34 inch and arrival 0 inch. KDAT risers are 3/4 x 5.86 inch.

Five KDAT 2x12 stringers, 9 inch interior spacing and 8.25 inch outer bays, all seated on the garage
stem core at -12 inch through 316 stainless shim packs. Trim EPS back only at the seats.
The end stringers retain their existing seats; three intermediate packs follow their
stringer centres. Fit the head seat cuts to the actual shim thickness and stem top;
positive kick-out restraint remains the field/EOR detail in garage_service_door_outswing.md.

## Durability and purchasing

Butyl tape over deck joists, rims, blocking and specified beam tops, and over all stepped
stringer bearing cuts. Tape is a quantified membrane, not a second geometric deck layer;
field-set the framing to maintain finished levels. Tape the notch horizontals and adjoining
vertical cuts; the stair order measures their sawtooth length, not the shorter rake.
Retain AWPA M4 treatment of every cut, notch and bore in treated framing.

Both decks and all service treads: Starborn Cap-Tor xd #10 x 2-3/4 inch **316 stainless**
composite screws, two per board at EVERY joist/stringer, driven flush. Do not countersink.
Predrill and maintain manufacturer's end/edge distances; support every board end. No
substitution of coated screws or plug systems. Stainless face screws are included once in
the decking/tread installed rates. Existing structural hardware keeps its specified
connector-compatible fasteners; decking screws are not structural connector screws.

Landing/porch board courses run across the joists. Use 3/16 inch minimum width gaps and
manufacturer's temperature-dependent end gaps; maintain the 1/2 inch wall gap. Stair gaps
are 1/4 inch. Board ends need backing; maximum permitted board overhang is 3/4 inch.

Decks bill under sheet_goods/trex-enhance-basics using the existing 32 SF equivalent
pricing convention; treads bill under stair_treads/trex-enhance-basics:tread as four
complete assemblies. Their material allowance is the deck rate scaled by 2.75/32;
installation retains the prior stair rate per three-foot tread, including stainless screws.
KDAT risers and stringers remain lumber. Tape and the five bearing packs bill separately.
The porch threshold strip remains within the porch's existing installation allowance.

Sources: [Trex dimensions](https://www.trex.com/professionals/products/decking/),
[Trex 2026 stair installation](https://online.flippingbook.com/view/63974767/36/),
[Trex fastener approvals](https://online.flippingbook.com/view/63974767/14/),
[Starborn Cap-Tor xd](https://starbornindustries.com/starborn_product/cap-tor-2/).
