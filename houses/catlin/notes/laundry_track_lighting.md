# Laundry task light

`ED-M-LAUNDRY-TRACK` (UID `QTM000SAAA`, mark Y) is an **IKEA NYMÅNE ceiling light with 4
spotlights** (603.377.06, white, $79.99) since 2026-11-21 (owner; cost). It runs east–west,
centred at (128.4", 260"), flush on the 107 1/2" board face, on `CKT-LT-MAIN` and
`ED-M-LAUNDRY-SW`. Four GU10 LED spots (`PROD-LAMP-GU10-90-30K`: 3000 K, CRI 90+, ≤ 8 W,
short enough for the shade): the west pair aims at the sink's front interior (y=240", 34"
AFF), the east pair at the centre of the machine's north face. Spot pitch is read off the
assembly sheet's drawing (even, end spots at the bar ends); IKEA dimensions only 29 x 5 in.

**The box.** The bar's canopy is at its centre, and every bay of `FS-S-WEST` over the room
carries an ERV return lying 5/8" over the board (`DU-M-ERV-R-LAUNDRY` y=244",
`-STUDY` 248.6", `-KITCH` 261.8"), with trusses at y=240/256/272". A 2-1/8" box fits nowhere;
a 1/2" pan is too small for through-fed 12 AWG. It takes a **4" octagon, 1-1/4" deep**
(12.5 in³, external NM connectors, so 11.25 in³ needed) on a bar between the 256" and 272"
trusses, its top ~1/8" under `DU-M-ERV-R-KITCH`: lift the duct a hair on site if needed.
`electrical.box_fill` grades the depth on 314.24(A) (no device in a luminaire box).

Modelled as a `fixed_bar_120v` `TrackLightingSpec` (the bar is the "rail", the centre
canopy the "feed", the lamps the heads), so plan, canvas, GLB and IFC draw the aimed spots
and `track_lighting_materials` lists one fixture and four lamps. Tests check all four
optical axes against the tall machine and the rack, stowed and deployed. Sightlines only,
not illuminance.

**Revert:** the PureEdge 24 V magnetic rail (TS24M-2C, two Radiant Medium heads, west end
feed, a 40 W supply on `W-M-BA2E` and the Class 2 raceway `CR-M-LAUNDRY-24V`) is
`typehaus.library.track_lighting.magnetic_track_spec` + `PUREEDGE_SUPPLY`; it was never
priced (~$450–650 retail estimate). Its end feed is why it needed no ceiling box.

Sources: [NYMÅNE page](https://www.ikea.com/us/en/p/nymane-ceiling-light-with-4-spotlights-white-60337706/),
assembly sheet AA-1961877-8 (read 2026-11-21).
