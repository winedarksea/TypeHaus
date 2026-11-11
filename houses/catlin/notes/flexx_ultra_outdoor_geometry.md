# EQ-M-HP1-OD geometry — 2026-11-11

The FXU24HP230V1R32AO now uses a product-specific model shared by the viewer,
GLB and IFC. The model shows a front-discharge fan/guard, service panel, rear
coil face, projecting feet, fixing-point markers and side connection markers.
Fan diameter, panel divisions, foot widths/thicknesses and connection stations
are illustrative; the dimensioned cabinet and fixing pitches govern coordination.

## Drawing basis

[Gree's FXU24 submittal, GREE_FXU24_230V_R32_SUB_01272026](https://www.greecomfort.com/assets/our-products/flexx-ultra-r32/documents/flexx-ultra-r32-submittal-24mbh-a.pdf),
p.4, and [outdoor installation manual §3.1.2](https://www.greecomfort.com/assets/our-products/flexx-ultra-r32/documents/flexx-ultra-r32-installation-owner-s-manual-outdoor-a.pdf):

| Drawing dimension | Inches | Model use |
| --- | --- | --- |
| A | 39 | Cabinet width |
| F | 14 9/16 | Cabinet depth / existing placement footprint |
| C | 37 13/16 | Overall height above stand mounting plane |
| B | 16 13/16 | Overall depth including projecting feet |
| D | 29 3/4 | Fixing pitch across cabinet |
| E | 15 9/16 | Fixing pitch front to back |

The feet extend 1 1/8 inches beyond each cabinet depth face in the centred
interpretation already used by the stand. The cabinet footprint stays unchanged:
enlarging it to B would change every existing clearance measurement from the
case without identifying that datum change. The generated feet carry B explicitly.
Their fixing-point markers match the existing `PT-M-HP1-L1..4` centres after rotation.
Marker diameter is visual; no hole diameter or slot travel is claimed from this drawing.

The submittal p.2 specifies 3/8-inch liquid and 3/4-inch vapor flared tube
connections, matching the indoor unit. The model declares these two services
plus power and control entry allowances. Stations, outlet directions and valve-cover
projection are not dimensioned: all four ports remain `APPROXIMATE`, and the markers
are on the nominal cabinet face, not at verified fitting tips. Do not rough in from them.

## Orientation and clearance

Local -y is front discharge, +y rear intake and +x the valve/electrical compartment.
The existing `rotation=180` faces north, putting that compartment on the **west**.
Older siting comments call the 12-inch east gap the service side; that label does
not match the sourced front view. The gap itself and the cabinet position have not
changed. The new orientation test holds west-side ports and north-facing discharge.

Recommended planning zones show 12 inches on the service side, 4 at the rear and
opposite side, and 40 in front, from the submittal p.6 A/B/C and D cases. They are
baseline coordination aids: Gree's obstruction-specific table changes these distances,
and it must govern the canopy installation. The owner's existing open-ended-canopy
acceptance assumption is retained; these zones do not establish manufacturer acceptance.

No single defrost drain nipple is invented. The outdoor manual §3.2.1 discourages
drain connectors/plugs in snowy locations; the elevated stand and free drainage to
the existing pad remain the design. There is also a source discrepancy to retain:
the submittal calls for 2 inches above expected snow, while the outdoor manual's
snowy-area instruction says more than 20 inches above expected snowfall. The model
update does not resolve that conflict or revise the accepted stand/canopy design.
