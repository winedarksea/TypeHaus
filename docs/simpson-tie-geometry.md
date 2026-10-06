# Simpson ties: visual geometry sources and datums

`packages/engine/src/typehaus/resolve/connector_geometry/ties.py` describes folded
steel, rather than solid volume markers. All dimensions below are inches; the
returned `GMesh` uses metres. Black is a presentation material, independent of
the product's actual coating. The steel remains its nominal sheet thickness.

The primary source is Simpson's [2026–2027 Wood Construction Connectors catalog,
C-C-2026](https://www.strongtie.com/resources/literature/wood-construction-connectors-catalog),
downloaded from its [official PDF](https://ssttoolbox.widen.net/content/orplhjaqw1/pdf/C-C-2026.pdf).
Page numbers below are printed catalog pages. Drawings were inspected visually,
including the installation diagrams; table labels alone can confuse an exposed
strap length with the complete embedded part.

| Model | Published dimensions retained | Source pages |
| --- | --- | --- |
| H2.5A / H2.5AZ / H2.5ASS | 1⅜ leaf width; 6 overall height; plate line splits height into 3¹³⁄₁₆ above and 2³⁄₁₆ below; 18 gauge | 299–301 |
| H10A / H10ASS | 5 backing width; 6¼ overall height; 3½ upper leaves; 1⁹⁄₁₆ member opening; 1³⁄₁₆ folded returns; 18 gauge | 299–301 |
| MASA | 4¼ developed nailing legs; 4 embedded horizontal projection; 3⅜ embedment; 16 gauge | 32–35 |
| STHD14 / STHD14RJ | 3 width; exposed strap L = 26⅛ / 39⅝; 14 embedment; spoon projection within 4¾–5¼; 12 gauge | 66–68 |
| STHD10 / STHD10RJ | 3 width; exposed strap L = 24⅝ / 38⅛; 10 embedment; 12 gauge | 66–68 |
| HETA20 / HETA20Z | 1⅛ width; H = 16 above embedment; 4 embedment; 16 gauge | 276–277 |
| LSTA24 | 1¼ width; 24 developed length; 20 gauge | 290–291 |
| MSTA12 / MSTA12Z | 1¼ width; 12 length; 18 gauge | 290–291 |
| CS16 | 1¼ width; authored cut length; 16 gauge | 295–296 |
| DTT2Z | 3¼ upper width; 6¹⁵⁄₁₆ height; 1⅝ seat width and depth; 14 gauge | 60–61 |
| SP4 / SP6 | 3⁹⁄₁₆ / 5⁹⁄₁₆ openings; 7¼ / 7¾ leaf lengths; 1¼ nailing leaves; 20 gauge | 303–304 |
| A35 / A35Z | 1⁷⁄₁₆ leaves; 3 upper plus 1½ lower sections; 18 gauge | 309–310 |
| LS30 / LS30Z | 2¼ leaves; 3⅜ length; 18 gauge | 313 |
| LTP4 / LTP4Z | 3 width; 4¼ height; 20 gauge | 309–310 |
| HGAM10 | 3 vertical and horizontal legs; 3½ along the heel; 14 gauge | 274–275 |
| APVKB45-6 | 5 width; two 4⅞ leaves at a 45° bend; 12 gauge | 349 |
| KBS1Z | Uses the existing four-leaf, perforated `resolve/kbs_geometry.py` body | That module's ER-280 / C-C-2019 citations |

The H2.5A perpendicular leaves and diagonal neck are also visible in Simpson's
[European H2.5A technical sheet](https://pim.strongtie.eu/api/v1/public/download/gb/en/product/89/H2-5A.pdf).
US catalog inch dimensions control this implementation; the regional metric
table is not substituted for them.

`STEEL_THICKNESS_IN` uses nominal Manufacturers' Standard Gauge thicknesses:
12: 0.1046, 14: 0.0747, 16: 0.0598, 18: 0.0478, 20: 0.0359. The catalog specifies
gauge, rather than manufacturing tolerances or coating build.

Local coordinates use x along the supporting line, y transverse, z up:

- Hurricane tie zero is the **top of the supporting plate**. The H2.5A lower
  leaf lies in xz at y = 0, extending along negative x. Its upper leaf lies in
  yz at x = 0, extending into positive y; placement moves that leaf onto the
  rafter's side. H10A's U backing is in xz at y = 0, centered on x; the two
  returns project into positive y. Their fixed stock opening is preserved.
- MASA, STHD and HETA zero is **the concrete pour top**. The embedded spoon
  projects into positive y. MASA's two nailing leaves rise to the supplied sill
  height and bend toward positive y; their total developed length stays 4¼.
  The top nailing arms and embedded spoon both turn inward from the same sill
  face, as shown in the standard installation on catalog page 33.
  The default sill height is 1½. STHD and HETA exposed attachment faces lie in
  xz at y = 0.
- Flat straps have their **length along y**, centered on zero, with width along
  x. LSTA24's zero is also the ridge crest: a supplied slope produces two
  descending leaves, with the 24-inch developed length unchanged. Vertical
  installations of MSTA12 or CS16 rotate this body at placement.
  Authored fixed-length straps with `Connector.roof_mount` instead seat on the named
  roof's structural top plane, directly beneath its deck, with length parallel to
  the ridge. The centre strap folds across its width when it straddles the ridge.
  This mounting reference supplies elevation and orientation and cannot be combined
  with an explicit `elevation` or `axis`. It establishes no nailing capacity; the
  canopy joint's missing nailing members are recorded separately on its delivery.
- A35 and LS30 use the **bottom of the inner heel**. Their heel runs up z and
  the two leaves project into positive x and positive y. These bodies depict a
  90° installed angle. LS is shipped at 45° and can be field skewed; the API
  does not infer a custom field bend from a product name.
- HGAM10 uses the **inner bearing heel**: the base lies just below z = 0,
  extending positive y; the upright runs above it at y = 0.
- DTT2Z uses the **bottom of its bearing seat** at zero, with the back at y = 0
  and the seat projecting positive y. The fork remains open.
- SP4/SP6 use the **upper plate bearing surface** at zero: the top bridge
  spans the fixed opening along y; its two nailing leaves descend below it.
- APVKB45-6 uses its **bend line**, centered along x at zero; one leaf extends
  negative y and the other descends 45° toward positive y.

The library's unsized `STHD` family designation has no unique dimensions. Its
display representative is explicitly **STHD14**, with 26⅛ above the pour and
14 below; this neither selects an engineering capacity nor rewrites the part.
STHD14RJ retains its additional 13½ of exposed strap. `CS16` without a cut
length returns `None`; a coil's 150-foot stock length is not an installed strap.
Unsupported names also return `None`.

Nail holes, stamped text, embossments and small bend radii are omitted. The
catalog does not dimension the exact contour of the diagonal necks, nailing
tabs, the DTT upper slot, or spoon curls. `TieSilhouetteConfig` names those
visual approximations separately from the published envelopes. In particular,
MASA's 3-inch transverse width and ¾-inch fork widths are illustration-based
estimates; HETA's one-inch spoon projection and DTT's ⁹⁄₁₆ hole are also visual
approximations. These are intentionally documented uncertainty, not dimensions
read from CAD. The broad folds and open spaces are retained, and these meshes
are not fabrication templates. Downloaded vendor CAD has not been copied into
the repository.

Tests check published envelopes and datums, fixed stock openings, the open DTT
anchor hole, the MASA fork, constant developed ridge strap length, and closed
steel components with outward winding. They use no real-house fixtures.
