# S-5! canopy review — public resources, 2026-11-10

Owner direction: use online resources only; no supplier contact. The model and
component budget are resolved below. **The single row remains provisional:** public
resources do not establish a complete capacity check for this short, drift-loaded run.

## Modeled installation

East canopy clamp line: x = 31 ft, 4 inches inside the roof footprint eave
(3.80 inches inside the field metal edge). The old x = 30.5 ft line was about
10 inches inboard. [ColorGard 2.0 instructions, revision 110426](https://3482954.fs1.hubspotusercontent-na1.net/hubfs/3482954/Resources/Product%20Documents/Snow%20Retention/ColorGard%202.0/ColorGard-2-0-%20Installation%20013125%20WEB.pdf)
place clamps 3–6 inches from the eave. The 62-3/8-inch rail has four full S-5-N
supports at 16-inch centers, with a 7-15/16-inch south cantilever and a 6-7/16-inch
north cantilever. These meet the instructions' 42-inch maximum spacing, 8-inch end
cantilever and two-support minimum for cut sections. This establishes installation
geometry, not allowable snow load.

The nine remaining garage/canopy Mini clamps occupy the northwest, northeast and
southwest corners. Three southeast Minis are omitted per owner direction because
that corner carries ColorGard. This is not an engineered equivalence between
snow-retention and wind-clamp locations; the house's authored uplift schedule still
needs a wind design. Twelve house Minis remain, for **21 Minis total**.

Roof clamps and ColorGard share an open-throat clamp body. Full N length is
2 inches; Mini length is 1.18 inches. Pitch and height follow the resolved roof pan
and seam; the former garage elevation of 7 ft 11.44 in was stale.

## Compatibility and pan support

The modeled panel is Metal Sales Image II, 24 ga steel, 16-inch coverage with a
1-inch seam. The [S-5-N product page](https://www.s-5.com/products/s-5-n-clamps/)
specifies the N for 1-inch nail-flange profiles, with full clamps for snow retention.
S-5!'s hosted [Los Angeles RB12 bulletin](https://3482954.fs1.hubspotusercontent-na1.net/hubfs/3482954/Codes%20and%20Certifications/RB12%20S-5%20Clamps_01-24-22%20%28la_country%29.pdf)
explicitly lists N Mini on **Image II 24 ga**: 1,064 lb parallel ultimate and
1,577 lb uplift ultimate, at 115 in-lb installation torque. Those are ultimate
values in a jurisdiction-specific bulletin, not allowable snow-retention loads
for our full N clamps. They support the profile match without supplying the
missing full-N design value. Do not substitute Mini, another gauge, or an
ultimate value for the full N's allowable drag capacity.

SnoClip 2.0 II fits the 1-inch seam. The three modeled rubber feet bear on flat pan
intervals clear of striations, over a continuously sheathed roof with 19/32-inch
plywood and membrane. There is no unsupported purlin bay beneath them. The
[ColorGard product notice](https://www.s-5.com/products/colorgard/)
requires adequately supported toes and prohibits use where panel deflection lets
the clip rotate beneath the rail. Continuous decking and geometric clearance
support the choice; foot contact with the modeled sheet alone does not prove
acceptable loaded deflection.

## Tributary snow and row count

The garage and canopy are coplanar. Garage snow is adjacent along the ridge,
rather than dropping from a higher garage roof onto the canopy. The higher HOUSE
causes the drift. `preferences.toml` carries 73.7 psf canopy-average design snow,
including a drift extending into the southern garage. Ground snow is 50 psf and
must not replace the roof design load.

[S-5!'s calculation explanation](https://knowledge.s-5.com/knowledge/how-to-calculate-snow-retention-on-roofs-over-12/12-pitch)
gives downslope force as vertical snow weight times the sine of roof angle. Here
sin(atan(4/12)) = 0.31623. From x = 31 ft to the x = 18 ft ridge is a 13-ft
horizontal run. Even the narrow strip immediately upslope of the rail has
13 × (62.375/12) = 67.57 sf plan area. At 73.7 psf that is **1,575 lb drag**.

The MCA's [Metal Roof Design for Cold Climates, Figure 12](https://blog.s-5.com/hubfs/MCA-ColdClimates-Nov-20-2023-04-31-10-1756-PM.pdf?hsLang=en-us),
hosted by S-5!, illustrates an approximate 45-degree tributary wedge at 4:12 and
requires checking panel pinning for isolated entry guards. Applying a screening
assumption of boundaries widening 45 degrees in the roof surface gives a larger wedge: integrate the width
`62.375/12 + s + min(s, 7.625/12)` over the slope, with `s = t*sqrt(1+(4/12)^2)`
and horizontal `t = 0..13 ft`. The south boundary clips at the canopy rake;
the north boundary extends into the garage. Result: **164.71 sf plan area**,
including **87.86 sf on the garage** north of its south cladding line. Uniform
73.7 psf on that wedge gives **3,839 lb drag**. This is an explicit screening
assumption, not a confirmed tributary boundary or drift integration: 73.7 psf is
a canopy average, and actual pressure varies along the ridge. It demonstrates why
a doorway-width strip and four equally loaded clamps cannot be presumed adequate.
The full drift distribution, rail bending, end reactions and panel attachments
must all enter the final check.

The [S-5! snow calculator](https://calculators.s-5.com/snow-project) and
[load tests](https://calculators.s-5.com/load-tests) require login. Public data
reviewed did not yield the exact full-N / Image II 24 ga allowable drag load and
ColorGard 2.0 capacity needed to close this case. A 26 ga Image II listing exists
in public evaluation reports, but is not substituted for 24 ga. **No defensible
final row count follows from the available inputs.** Retain one row as provisional
geometry; resolve with the exact clamp test and a complete drift/tributary check
before ordering or treating the installation as designed. No supplier was contacted.

## Online component budget

Observed USD prices, excluding tax, freight, installation and design, on 2026-11-10:

| Component | Quantity | Unit price | Extension |
| --- | ---: | ---: | ---: |
| ColorGard 2.0 unpunched, 92 inches, splice included | 1 | $39.35 | $39.35 |
| VersaClip 2.0 | 4 | $1.95 | $7.80 |
| SnoClip II 2.0 | 3 | $3.55 | $10.65 |
| Full S-5-N | 4 | $7.05 | $28.20 |
| Hardware subtotal | | | **$86.00** |

Sources: [Big Rock ColorGard components](https://www.bigrocksupply.com/s-5-colorgard-2-0-snow-retention-system.aspx)
and [N clamps](https://www.bigrocksupply.com/store/c/3326-S-5-N.aspx). The SnoClip
page shows inconsistent base-price text; use its displayed $3.55 sale price as a
snapshot, not a guaranteed checkout price. ColorStrip remains an $8–16 allowance,
so the displayed-price assembly plus strip is **$94–102 before exclusions**.
The model budget keeps contingency in its upper unit ranges. Mini clamps are
listed at $6.08 each: 21 × $6.08 = $127.68 for the separate wind-clamp scope.
Prices cover the provisional quantities and do not establish sufficient coverage.
