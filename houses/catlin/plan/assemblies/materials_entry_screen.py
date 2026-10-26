"""Thin veneer materials; laid brick weight includes pointing, not a full brick wythe."""
from typehaus import Material

MATERIALS_ENTRY_SCREEN = [
    Material(tag="thin-brick-brown", product_ref="PROD-BW-THIN-BRICK", name='1/2" brown thin brick, grey pointed joints',
             density=1920, areal_density_kg_m2=31.74, hatch="masonry", color="#a07c5c",
             finish="brown-brick", r_per_inch=0.2,
             source="ASTM C1088 Exterior modular slips, 7-5/8 x 2-1/4 x 1/2in. "
                    "House brown blend; purchased matching slips, sample match pending. "
                    "6.50 psf laid allowance: Hanley Classics 0.8lb/unit x 6.86/SF plus "
                    "1.012 psf grey pointing (included in this layer, not a second bed). "
                    "Glen-Gery Hanley Classics technical data; revise to accepted lot weight."),
    Material(tag="mvis-thin-brick-mortar", product_ref="PROD-BW-MVIS-MORTAR", name='LATICRETE MVIS Thin Brick Mortar, 1/8" bed',
             density=1800, hatch="masonry", color="#8c8982",
             source="MVIS DS-248, ANSI A118.4/118.15; direct bond to prepared exterior cement "
                    "board, full back coverage. "
                    "1800 kg/m3 design dead-load allowance, verify cured installed mass."),
    Material(tag="permabase-exterior", product_ref="PROD-BW-PERMABASE", name='1/2" PermaBASE Cement Board, exterior CBMV',
             areal_density_kg_m2=14.65, hatch="concrete", color="#b5b1a7",
             source="PermaBASE exterior applications guide: 1/2in board ~3 psf. "
                    "Use 4in alkali-resistant mesh tape embedded in mortar at exterior joints, "
                    "primary plywood sheathing, and retained movement joints."),
    Material(tag="entry-screen-wrb", product_ref="PROD-BW-WRB", name="DuPont Tyvek HomeWrap behind drained veneer",
             areal_density_kg_m2=0.07, hatch="membrane", color="#deded8",
             source="One primary WRB plus separate drainage mat; shingle-lap to base "
                    "flashing. This protects wood outdoors; screen is not conditioned envelope."),
    Material(tag="thin-brick-drainage-mat", product_ref="PROD-BW-DRAINAGE", name='1/4" Keene Driwall Rainscreen 020-1 drainage mat',
             areal_density_kg_m2=0.5, color="#353b3c",
             source="1/4in drainage-space design basis; confirm current 020-1 thickness "
                    "and compatibility behind cement board in the system submittal."),
    Material(tag="entry-screen-exterior-plywood", name='5/8" APA Exterior plywood, 4x9 stock',
             density=610, hatch="lumber", color="#b29a76", r_per_inch=1.25,
             source="Exterior bond, not Exposure 1. Primary sheathing over 1-1/8in packing; "
                    "4x9 stock provides continuous 49in height without an unsupported strip."),
]
