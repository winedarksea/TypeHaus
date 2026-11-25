"""LP SmartSide panel siding on the sunken court's house face (notes/court_face_lp_panel.md).

House-local; promoting it to the shared library is a CONTRIBUTING step. Tags name the product,
not the colour. Every value is read from LP's own documents (out/lp_reads, cited per row):
AI = LP Application Instructions LPZB0512, 38/76/190 Series panel siding, 2024-04-26;
ESR = ICC-ES/APA ESR-1301, reissued 2026-02; CAT = LP SmartSide Product Catalog 2025.
"""

from typehaus import Material, inch
from typehaus.model.cladding_trim import TrimCondition
from typehaus.model.published_cladding import PublishedCladdingLoad

#: Benjamin Moore Potters Clay, 1221 (CC-360): hex B98766, LRV 28.25 (benjaminmoore.com, read
#: 2026-11-24). The panel and its trim are field-painted in it.
POTTERS_CLAY = "#b98766"

#: The panel's own trim kit; the court's two walls have no outside corner, eave or rake.
#: D-B-SUNKEN takes D-M-PORCH's dark custom door head; no door jamb trim, since the panel butts
#: the Captivate casing with LP's 3/16" gap and sealant (AI 2024 p.11). WIN-B-SAUNA takes the
#: generic Z drip flashing. Each vertical joint takes a 440 3.50" batten over its 2x4 nailer.
LP_PANEL_KIT = {
    TrimCondition.DOOR_HEAD: "DOOR_HEAD_CUSTOM",
    TrimCondition.OPENING_HEAD: "OPENING_HEAD_DRIP_FLASHING",
    TrimCondition.VERTICAL_JOINT: "LP_440_BATTEN_3_5",
}

#: ESR-1301 Table 3A row, read at the court face's own 24 in girts. The row is at 16 in studs,
#: so `structural.cladding_wind` is UNKNOWN by design: the owner kept the girts at 24 in
#: off-label (2026-11-24). Arithmetic: notes/court_face_lp_panel.md "Wind read".
_LP_WIND_ROW = PublishedCladdingLoad(
    source="ICC-ES/APA ESR-1301 reissued Feb 2026 p.6 (APA PR-N124 rev. 2026-07-02 Table 3a)",
    table='Table 3A, "PANEL SIDING INSTALLED VERTICALLY WITH 0.113-INCH NAILS": 3/8, 7/16 and '
          '19/32 | max wall stud spacing 16 in | fastener spacing edges 6 in, field 12 in | '
          'max ultimate wind pressure 71 psf | Vult B 170, C 140, D 130',
    member="LP SmartSide 38 Series",
    basis="ultimate",
    allowable_outward_psf=71.0,
    allowable_inward_psf=71.0,
    fastener_spacing=inch(16),
    condition='fn 1 "Fasteners shall be hot dip galvanized plain (smooth) shank nails, with a '
              'minimum shank diameter of 0.113 inch, and long enough to penetrate structural '
              'framing or wood structural panels and structural framing a minimum of 2 inches '
              'for the tabulated values"; fn 2 "Wall studs must have a minimum specific gravity '
              'of 0.42"; fn 3 three-second gust, 30 ft height, Zone 5, smallest effective area; '
              'the one pressure is read for suction and push; panel long side vertical, joints '
              'on framing (s.4.3)',
    panel_fastener="0.113 in HDG plain shank nail",
    support_material="structural framing, 2 in minimum nail penetration, SG 0.42 or more",
    min_support_thickness=inch(2.0),
    excludes="the table is for studs; LP does not recommend panel siding over furring or "
             "strapping and will not warrant buckling there (AI 2024 p.2)",
    demand_psf=19.94,
    wind_speed_mph=170.0,
    exposure="B",
    fastener_governed=True,
    off_label="the girts are 1-1/2 in strapping over a vented cavity, not studs: the 38 "
              "Series label rating is 16 in o.c. (CAT 2025 p.35, ESR s.4.3) and the nail "
              "bites only the 1-1/2 in girt, short of the row's 2 in penetration",
    off_label_note="Owner accepted off-label 2026-11-24: sheltered under the porch roof, small "
                   "and cheap to replace. Cross-checks: 71 psf x 0.6 x (16 x 12 in) = 57 lbf "
                   "ASD, PR-N124's own per-fastener floor, so the row is nail-governed; here "
                   "19.93 psf x (24 x 12 in) = 39.9 lbf, d/c 0.70. Panel bending off the 133 "
                   "psf 6/6 row scaled by (16/24)^2 is 59 psf ultimate, d/c 0.56.")

MATERIALS_LP = [
    Material(tag="lp-smartside-smooth-panel",
             name='LP SmartSide 38 Series 3/8" Brushed Smooth primed panel siding, 4x8, vertical',
             r_per_inch=0.0, hatch="siding", color=POTTERS_CLAY, finish="paint",
             trim_kit=LP_PANEL_KIT, published_cladding=_LP_WIND_ROW,
             panel_fastener="0.113 in HDG plain shank nail, 2-1/2 in 8d box, 6 in edge / 12 in "
                            "field",
             panel_fastener_diameter_in=0.113, panel_fastener_length_in=2.5,
             open_framing_source='AI 2024 p.2: "LP does not recommend panel siding for use over '
                                 'furring strips/strapping ... If used, LP will NOT warrant for '
                                 'Buckling." ESR-1301 s.4.3: direct to framing "the maximum '
                                 'spacing of the framing must be consistent with the span '
                                 'rating", 16 in for the 38 Series. OFF-LABEL; the owner '
                                 'accepted it 2026-11-24',
             source="CAT 2025: 38 Series Brushed Smooth panel, 3/8 nominal (0.354 in actual), 47.81 in "
                    "wide, square edge, primed 4x8/4x10 special order. AI 2024 p.4: 6 in o.c. edges, "
                    "12 in field, 3/8 in from a square edge, 1/8 in joint gap; seal every cut edge; "
                    "paint within 180 days, 100% acrylic. No panel weight read, so no density; no LP "
                    "R-value read, so r_per_inch 0: outboard of the vented cavity it is credited nothing."),
    Material(tag="lp-smartside-trim-smooth",
             name='LP SmartSide 440 Series 3/4" Brushed Smooth primed trim',
             density=570.0, hatch="wood", color=POTTERS_CLAY, finish="paint",
             source="CAT 2025 p.43: 440 Series Brushed Smooth trim, 3/4 nominal, 0.675 in actual, "
                    "primed widths 1.50/2.50/3.50/5.50/7.21/9.21/11.21 in, 16 ft; AI 2024 p.2: 440 or "
                    "540 trim so the panel does not stand past the trim face; 3/16 in gap and sealant "
                    "at the panel (p.11). Painted with the panel. Density = CAT's 2 psf / 0.675 in."),
    Material(tag="lp-panel-paint-exterior",
             name="100% acrylic exterior paint, Benjamin Moore Potters Clay 1221, 2 coats",
             r_per_inch=0.0, coating=True, color=POTTERS_CLAY, finish="paint",
             source="AI 2024: LP SmartSide is painted within 180 days of installation with a 100% "
                    "acrylic exterior paint (flat, satin or semi-gloss on smooth); colour Benjamin "
                    "Moore Potters Clay 1221 / CC-360 (owner, 2026-11-24)."),
]
