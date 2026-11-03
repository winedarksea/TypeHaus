# W-BW-SCREEN — white MDO and lower centre timber, 2026-11-02

**Coordination model; lower timber attachment is NOT accepted for construction.**
The geometry implements the selected three-ply appearance. New checks block acceptance
until the ply load transfer, bent A35Z end connections, local plate/sill/hanger effects,
and final installed-hardware door sweep are verified. Passing existing canopy checks
alone does not approve the added detail. See `entry_screen_mdo_calculations.json`.

## Sheet notes
### General
- Lower centre timber: coordination geometry only; attachments are not released for construction.
- Three KDAT 2x6 plies, six 2x4 MDO edge nailers; retain west plywood, plates and cap.
- White 3/4-inch exterior MDO with removable stainless screws; leave 1/8-inch timber gaps.
- Keep the north tie-access relief and bottom drainage open.


## Installation geometry

- Retain the west 5/8-inch shear plywood, corrugated skin, field studs, upper brace band,
  horizontal plates, upper cap and drainage below. No additional roof support or shear chord.
- Replace `TR-BW-MDO-NAILER-3` with three vertical KDAT Southern Pine No. 2 nominal 2x6s,
  each actual 1.5 x 5.5 inches, cut 44.44 inches long. Stack west-to-east at
  x=73.625–75.125, 75.125–76.625 and 76.625–78.125 inches. All three occupy stations
  37.875–43.375, elevations +0.56 to +45. The upper timber's exposed east face is also
  x=78.125. Match its pigmented penetrating-oil finish; do not paint the timber white.
- The original centre nailer is removed; the other four retain their tags and locations.
  Add KDAT 2x4 edge nailers `-6` and `-7` at stations 37.000 and 44.250. All six nailers
  are x=73.625–77.125 and +0.56 to +45; retained stations 7.125, 14.375, 66.875, 74.125.
- White-painted nominal 3/4-inch Roseburg DuraGard Premium exterior MDO, directly screwed
  to framing, face x=77.875, 1/4 inch behind exposed timber. No east WRB or cavity.

| Panel | Stations from south node, in | Width, in | Height, in |
|---|---|---|---|
| 1 | 0.125–7.875 | 7.750 | 45.5 |
| 2 | 13.625–37.750 | 24.125 | 45.5 |
| 3 | 43.500–67.625 | 24.125 | 45.5 |
| 4 | 73.375–79.250 | 5.875 | 45.5 |

Panels run +2 to +47.5. Leave 1/8 inch beside the centre timber; keep joints open.
The top plates support panel tops. The north panel retains the open-ended 2.625 x
3.750-inch tie-access relief, stations 76.625–79.250, +22.125 to +25.875. Keep tool
access and straight-out panel removal possible. Net MDO area is 19.4824 sf (was 21.2598).

Removable No. 8 x 2-1/2-inch 304 stainless pan-head white-head screws: maximum 6 inches
at vertical edges, 12 inches at intermediate studs; minimum 3/8-inch panel edge distance.
Pilot drill; seat heads without crushing the overlay and reserve 1/8-inch head projection.
Retain the six nailers' three stainless 8d toenails per end, staggered against splitting.
This retained fastening is not a newly verified guard-infill attachment design.

Prime and paint MDO on both faces, cut edges and holes: compatible exterior primer and
two white exterior acrylic topcoats. Fill edge voids and ease edges. Recoat field cuts.
No MDF. Field-treat treated timber cuts/holes with 2% copper naphthenate per AWPA M4.
Keep the existing cap crossing between upper and lower timbers. Do not dam drainage.

## Candidate hardware and acceptance blockers

The shared source is `plan/entry_screen_finish_spec.py`; dimensions, cuts, support mass,
procurement, hardware reserve and local checks all read it. Supplemental supports remain
trim solids; they are not roof columns. Their modeled volume is not charged a second time.

- Ply-fastening candidate: eight **SDWS22300DB**, driven west into side grain, four per
  adjacent-ply interface. West/middle interface elevations +6.56, +14.56, +30.56, +38.56;
  middle/east +7.56, +15.56, +29.56, +37.56. All at station 40.625. Assemble the concealed
  interface first. Actual main-member/thread penetration is 1.5 inches; thread does not
  engage the clamped 1.5-inch side ply. Interface screw shanks are staggered to avoid collision.
- ER-192 Table 7: W=164 lb/in, Wmax=245 lb, giving **171.5 lb wet-service withdrawal**
  at CD=1. Table 8 spacing, edge and end distances pass. A conservative full 200 lb
  transfer on one screw does not pass. A verified group/load-distribution calculation or
  revised schedule is needed. Dividing by four without a load-transfer model is not accepted.
- End candidate allowance: **four A35Z and 48 SD9112**, two angles per end, six screws
  per member per angle. It has no approved installed configuration. ESR-3096 Table 5
  bent A2/C2/D directions are 260/260/150 lb at CD=1, rather than the unbent F1/F2
  695/845 lb. Directions cannot be combined. Do not use the upper band's F1 rating here.
- Coordinate the actual bent tabs and all holes. The east ply overhangs the 3.5-inch
  plate by 1 inch; its bearing strip is only 0.5 x 5.5 inches. West-side angles must
  preserve the plywood. North/south tabs encounter the adjacent nailers: the 1/8-inch
  gaps cannot accommodate a 1-7/16-inch leg. No unauthorized plywood/plate cuts are implied.
- Verify SD9112 penetration after steel thickness, edge/end distances, opposing screw
  fit and cross-grain tension/bending, and the plate-to-existing-frame load path.
- Use compatible ZMAX/SD connector and exterior Double-Barrier screw systems with the
  specified treated wood; no stainless substitution into galvanized connectors. ER-192
  treatment limits apply (ACQ-D <=0.40 pcf or less corrosive treatment). Delivered treatment,
  exposure and coating compatibility remain procurement prerequisites.

Local calculations apply the full 200 lb concentrated guard load, the 50 psf / 1 sf infill
case and the house's out-of-plane ASD wind pressure to **one ply**, with no composite
inertia or equal ply sharing. Southern Pine No.2 2x6 Fb is **1,000 psi**, E=1.4e6 psi;
wet E=0.9E. The 200 lb single-ply bending screen exceeds Fb; a justified load-sharing
model is therefore required. The 1/4-inch deflection limit is a project coordination
criterion, not a claimed statutory guard-deflection provision. Existing structural guard
and shear systems retain their roles; MDO gains no shear credit.

The gravity comparison reconstructs the previous finish's total mass within the current
house, retaining every other house decision. This is a weight-only baseline, not a claim
that the previous geometry was re-exported. The additional support wood is evaluated as
point loads on the sill separately from the finish's averaged line load. Total concentrated
sill stress, plate distribution and hanger checks remain acceptance blockers. The normal
load consumers still carry revised wall weight into canopy posts and foundations.

Run `.venv/bin/python scripts/entry_screen_mdo_report.py --output
houses/catlin/notes/entry_screen_mdo_calculations.json` on one line. It writes the report
and exits **1** for any failed or incomplete new check. A clear door sweep of the timber
and ply screw heads does not close the full installed-hardware sweep while end hardware
is unresolved. Final acceptance requires that sweep at the authored 81-degree stop,
including installation allowance and stop tolerance, with >=1/4-inch clearance.

## Purchasing and budget

Purchase one 48 x 96-inch MDO sheet, **three 8-foot KDAT 2x4s** for six nailers and
**two 8-foot KDAT 2x6s** for three plies. Two 44.44-inch cuts plus two 1/8-inch kerfs
use 89.13 inches per board, leaving 6.87 inches for cleanup. Two 24.125 x 45.5-inch
panels fit end-to-end in one strip; narrow panels fit alongside. Verify actual thickness,
framing, finish sample and tie relief before cutting. Attachment hardware is a candidate
allowance pending verification, not a released installation order.

Support wood weighs 54.1855 lb (previously 25.2866). The hardware/paint reserve is 4.6 lb:
2 lb paint and retained face/nailer fastening reserve, four 0.35 lb angle allowances,
48 x 0.02 lb connector screws and eight x 0.03 lb ply screws. All counted once through
net MDO areal density. The finish budget rate includes these materials and the timber
finish; do not bill a second hardware or lumber allowance. Prices are budget allowances,
not supplier quotes.

Sources: [Simpson A angles](https://www.strongtie.com/framinganglesandplates_anglesandplates/a_angle/p/a),
[ICC-ES ESR-3096 Table 5 and Figure 5](https://icc-es.org/wp-content/uploads/report-directory/ESR-3096.pdf),
[IAPMO ER-192 Tables 7/8](https://forms.iapmo.org/ues_reports/reports/er_0192.pdf),
[SFPA dimensional lumber design values, 5–6-inch width](https://www.anthonyforest.com/assets/pdf/dv-2013-visual-grades.pdf),
[Roseburg DuraGard](https://www.roseburg.com/resources/duragard-mdo-premium-flyer/),
[APA MDO/HDO](https://www.apawood.org/engineered-wood-products/plywood-osb/mdohdo-panels/).


## Geometry overlap review

The supplemental wood occupies the wall's continuous stud-cavity proxy; these are not
intersections with west plywood or existing field studs. The overlap golden also records
four conservative hidden screw-head envelopes extending into the next ply. Their actual
flush seating or recess detail remains unverified; pinning those envelopes does not
release the fastening design. The three timber plies themselves meet at faces without
volume overlap. Reviewed changes are limited to these two overlap categories.
