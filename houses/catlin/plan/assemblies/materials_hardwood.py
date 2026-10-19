# haus: editable
# Catlin assemblies — the owner-milled hardwood stock, plus the bought white-oak stools
# and the bought Douglas fir sauna bench frame.
# Split out of materials.py 2026-10-16, when the oak pile turned out to be red oak.
from typehaus import (
    Material,
)


MATERIALS_HARDWOOD = [
    # --- owner-milled red-oak stock -----------------------------------------------------
    #
    # ** RED OAK, NOT WHITE OAK (2026-10-16). ** The owner's pile is red oak, effectively
    # unlimited, off family land in southern Minnesota: boards commonly 12"+ wide and out to
    # 18", in 4/4 to 8/4. The `oak-*` tags stay (a retag reaches prices, tasks and tests);
    # `species` and `name` say what the wood is. Red oak's pores are OPEN, so it gets no
    # wet-room job here: the bath shelves are locust and the wet-room stools locust.
    #
    # ** ONE FINISH SYSTEM ON EVERY RED-OAK SURFACE: ** two-part A/B wood bleach,
    # neutralised and dried; Bona NordicSeal; then a waterborne topcoat. Floors, treads,
    # trim and shelves alike, so every red-oak face reads as one pale, slightly cool tone
    # (`#d6c9b3`) beside the bleached white-oak stools. It is a look, not moisture
    # resistance.
    #
    # These are PIECE goods, not coverage goods: each one is cut to a finished T x W x L, so
    # they carry `nominal_quarters` and no `stock_bf_per_sqft`. `haus millwork` orders them.
    Material(tag="oak-floor-custom", name='3/4" red-oak strip flooring, site-milled',
             hatch="lumber", color="#d6c9b3", species="red-oak", finish="plank-floor",
             stock_bf_per_sqft=1.0, nominal_quarters=4, milling_profile="T&G",
             finish_thickness_in=0.75, requires_custom_milling=True,
             source="Catlin owner-milled red oak floor. Two-part A/B bleach, Bona NordicSeal, then Bona Traffic HD (waterborne). Local rather than the factory library product so only this house enters the custom milling schedule."),
    # 4/4 dressed to 3/4" (2026-10-16, was 5/4 to 1"): Finnish panel is 1/2"-5/8", the foil
    # polyiso does the insulating, and less board is less heat store to warm. 1.0 x 1.1 bf/sf.
    # The WALLS: basswood, made up from one more owner log. The ceiling is aspen (below).
    Material(tag="catlin-sauna-shiplap",
             name="Basswood/aspen shiplap sauna liner (4/4), site-milled",
             r_per_inch=1.3, perm_rating=20.0, hatch="lumber", color="#e5dcc4",
             finish="shiplap", species="basswood", wood_surface="unfinished", stock_bf_per_sqft=1.1,
             nominal_quarters=4, milling_profile="shiplap", requires_custom_milling=True,
             source="Catlin site-milled sauna wall liner: owner basswood, made up from one more owner basswood or aspen log (notes/wood_supply.md). Unfinished."),
    # The ceiling: aspen since 2026-10-18 (willow before; weak and warp-prone). Light, stable,
    # resin-free and a classic sauna board; dry to 8-10% MC, 5 1/2" face.
    Material(tag="catlin-sauna-ceiling-shiplap",
             name="Aspen shiplap sauna ceiling liner (4/4), site-milled",
             r_per_inch=1.3, perm_rating=20.0, hatch="lumber", color="#e3d6bd",
             finish="shiplap", species="aspen", wood_surface="unfinished", stock_bf_per_sqft=1.1,
             nominal_quarters=4, milling_profile="shiplap", requires_custom_milling=True,
             source="Catlin site-milled sauna ceiling liner: owner aspen, made up from one more owner log (notes/wood_supply.md). Dried to 8-10% MC, 5 1/2\" face over 5\" coverage, unfinished."),
    # --- window stools (5/4, 1" dressed; plan/millwork.py MW-STANDARD and plan/window_stools.py)
    # All oak stools use BOUGHT white oak heartwood for lower liquid-water permeability.
    Material(tag="oak-stool", name="White oak window stool, 5/4 S4S (bought)", hatch="lumber",
             color="#d6c9b3", finish="oak-board", species="oak",
             nominal_quarters=5, milling_profile="eased", requires_custom_milling=True,
             source="Bought white oak heartwood, no sapwood, rough 5/4, select widths of 11\" and up; rift or quartered stock. Dressed to 1\", front edge eased. Same finish system as the red oak (A/B bleach, Bona NordicSeal, waterborne topcoat) on all six faces, so the two sit together."),
    # Wet rooms, splash and snowmelt: the baths and the mudroom. Kitchen stools are quartz.
    Material(tag="locust-stool-5q", name="Black locust window stool, 5/4 S4S", hatch="lumber",
             color="#b9aa68", finish="oak-board", species="locust",
             nominal_quarters=5, milling_profile="eased", requires_custom_milling=True,
             max_board_width_in=7.0,
             source="Owner-milled black locust heartwood, no sapwood, dressed to 1\"; a glue-up (Type III PVA) where the stool is wider than a board. Waterborne film on all six faces before install; stainless fasteners."),
    # The suite, beside its cherry headboard band and cherry base.
    Material(tag="cherry-stool-5q", name="Black cherry window stool, 5/4 S4S", hatch="lumber",
             color="#b77d60", finish="oak-board", species="cherry",
             nominal_quarters=5, milling_profile="eased", requires_custom_milling=True,
             source="Milled black cherry, dressed to 1\". Oil every face before install so it darkens evenly, as the cherry base."),
    # The living room: all five stools are ash, matching the ash counters they border, and
    # all 6/4 to 1 1/4" like the slab and the dining top: one ash thickness at the mill.
    Material(tag="ash-stool-6q", name='White ash window stool, 1 1/4", 6/4 S4S', hatch="lumber",
             color="#d9cbb0", finish="oak-board", species="ash",
             nominal_quarters=6, milling_profile="eased", requires_custom_milling=True,
             max_board_width_in=6.0,
             source="Owner's ash, quarter- or rift-sawn preferred, 6/4 dressed to 1 1/4\": the east three meet the ash slab's back edge in one plane, the south pair match. Saw 6/4 full, ~1 5/8\" green: at a bare 1 1/2\" it will not dry and flatten to 1 1/4\". A two-board glue-up (Type II PVA): quartered boards off 12-16\" logs run 4-6\" wide. Waterborne urethane on all six faces, end grain included, before install; stainless fasteners. Ash is not rot-resistant: the film is what keeps condensation out."),
    # WIN-B-SAUNA. At 190 F what matters is how hot the wood feels, and that tracks density:
    # cedar at ~350-370 kg/m3 is as cool as the basswood liner; locust, oak and cherry read hot.
    Material(tag="cedar-sauna-stool", name="Cedar sauna window stool, 5/4 S4S, clear heartwood",
             hatch="lumber", color="#b98a63", finish="solid-board", species="cedar",
             wood_surface="unfinished", density=360.0,
             nominal_quarters=5, milling_profile="eased", requires_custom_milling=True,
             source="Owner's western red or northern white cedar, clear heartwood only (no sapwood, no knots), 5/4 dressed to 1\", one board. Unfinished: no oil or film, and a 1/8\" gap at the glass so condensate drains rather than wicks. Stainless fasteners only: cedar extractives stain black against iron in standing water. Soft: ease every edge. Reads reddish against the pale liner, accepted. Fallback: bought thermo-aspen 5/4."),
    # --- shelving --------------------------------------------------------------------------
    Material(tag="oak-shelf-8q", name="Red oak shelving, 8/4 S4S", hatch="lumber",
             color="#d6c9b3", finish="oak-board", species="red-oak",
             nominal_quarters=8, milling_profile="S4S", requires_custom_milling=True,
             source="The bought mud bench's seat record only (SB-M-MUD-BENCH). Owner red oak would be 8/4 dressed to 1 1/2\"; the house red-oak system."),
    Material(tag="oak-shelf-6q", name="Red oak shelving, 6/4 S4S", hatch="lumber",
             color="#d6c9b3", finish="oak-board", species="red-oak",
             nominal_quarters=6, milling_profile="S4S", requires_custom_milling=True,
             source="Owner-milled red oak, 6/4 dressed to 1 1/4\": the climbable pantry shelves, graded as a floor at L/360 (notes/pantry_climbable_shelving.md). A/B bleach, Bona NordicSeal, waterborne topcoat."),
    Material(tag="oak-shelf-5q", name="Red oak shelving, 5/4 S4S", hatch="lumber",
             color="#d6c9b3", finish="oak-board", species="red-oak",
             nominal_quarters=5, milling_profile="S4S", requires_custom_milling=True,
             source="Owner-milled red oak, 5/4 dressed to 1\": the attic study's book shelves, ~31\" bays at 0.024\" sag against 0.052\" allowed (3/4\" would sag over the years). A/B bleach, Bona NordicSeal, waterborne topcoat."),
    Material(tag="oak-shelf-4q", name="Red oak shelving, 4/4 S4S", hatch="lumber",
             color="#d6c9b3", finish="oak-board", species="red-oak",
             nominal_quarters=4, milling_profile="S4S", requires_custom_milling=True,
             source="Red oak, 4/4 dressed to 3/4\": the bought theatre bookcases' shelf record. A/B bleach, Bona NordicSeal, waterborne topcoat."),
    # The tub-end cases' exposed edges (FT-BATH1-SHELF-2030, FT-SUITEBATH-SHELF-1130): shelf
    # nosings and face strips, a few bf. Fallbacks: `cherry-shelf-4q`, then bought white oak.
    Material(tag="locust-shelf-4q", name="Black locust shelving, 4/4 S4S", hatch="lumber",
             color="#b9aa68", finish="oak-board", species="locust",
             nominal_quarters=4, milling_profile="S4S", requires_custom_milling=True,
             max_board_width_in=7.0,
             source="Owner-milled black locust heartwood only, no sapwood, 4/4 dressed to 3/4\". A wet-area film (catalysed or waterborne poly) on all six faces, end grain included, before install; stainless fasteners."),
    # The tub-end shelves themselves (2026-10-18): bought sheet, not glue-ups. Veneer core
    # because an MDF or particleboard core swells at a cut edge beside a tub.
    Material(tag="maple-ply-prefin-34", name='Prefinished maple plywood, 3/4" veneer core',
             hatch="lumber", color="#e3d3b4",
             source="Bought sheet, e.g. Columbia PureBond prefinished maple or equal: 23/32\", veneer core, A-1 face, HPVA Type II glue, UV-cured clear both faces. Seal every cut edge with the wet-area poly before install; the locust nosing covers the front edge; stainless pins."),
    Material(tag="cherry-shelf-4q", name="Black cherry shelving, 4/4 S4S", hatch="lumber",
             color="#b77d60", finish="oak-board", species="cherry",
             nominal_quarters=4, milling_profile="S4S", requires_custom_milling=True,
             source="The bath shelf nosings' fallback if locust runs short: milled black cherry, 4/4 dressed to 3/4\", film on all six faces, stainless fasteners."),
    # --- stairs and trim -------------------------------------------------------------------
    Material(tag="oak-tread", name="Red oak stair tread, 5/4 bullnose", hatch="lumber",
             color="#d6c9b3", finish="oak-board", species="red-oak",
             nominal_quarters=5, milling_profile="bullnose", requires_custom_milling=True,
             source="Owner-milled red oak, 5/4 dressed to 1\", the stock tread thickness; the stringers are 22\" o.c. or closer. Tread and landing nosings share the bullnose setup; the landing nosing also gets a groove to meet the T&G field. A/B bleach, Bona NordicSeal, Bona Traffic HD."),
    Material(tag="oak-riser", name="Red oak stair riser, 4/4 S4S", hatch="lumber",
             color="#d6c9b3", finish="oak-board", species="red-oak",
             nominal_quarters=4, milling_profile="S4S", requires_custom_milling=True,
             source="Owner-milled red oak, 3/4\" dressed: a riser carries no load, and at ~6\" high it comes off one board and stays flat. A/B bleach, Bona NordicSeal, waterborne topcoat."),
    # Door casing (plan/millwork.py TRIM-STANDARD): plain S4S, so no knife and no molder —
    # planer work off the 4/4 stack, ripped from the wide boards.
    Material(tag="oak-trim", name='Red oak trim, 3/4" x 3 1/2" S4S', hatch="lumber",
             color="#d6c9b3", finish="oak-board", species="red-oak",
             nominal_quarters=4, milling_profile="S4S", requires_custom_milling=True,
             source="Owner-milled red oak, 4/4 dressed to 3/4\" and ripped to 3 1/2\". Butt-jointed, flush with the cherry base where they meet. A/B bleach, Bona NordicSeal, waterborne topcoat."),
    # The base (TRIM-STANDARD.base_material_ref); casing stays `oak-trim`, so the flush
    # base-to-leg butt joint is two species. Same 3/4" x 3 1/2" S4S off 4/4.
    Material(tag="cherry-trim", name='Black cherry base, 3/4" x 3 1/2" S4S', hatch="lumber",
             color="#b77d60", finish="oak-board", species="cherry",
             nominal_quarters=4, milling_profile="S4S", requires_custom_milling=True,
             source="Milled black cherry, 4/4 dressed to 3/4\" and ripped to 3 1/2\"; hardwax oil. Cherry darkens with light: oil every face before install so the back and edges age with the front."),
    # RM-B-SAUNA's base (TRIM-STANDARD room_trims). Locust for rot resistance at a wet
    # floor; left unfinished, as the liner is.
    Material(tag="locust-trim", name='Black locust sauna trim, 3/4" x 3 1/2" S4S',
             hatch="lumber", color="#b9aa68", finish="solid-board", species="locust", wood_surface="unfinished",
             nominal_quarters=4, milling_profile="S4S", requires_custom_milling=True,
             source="Milled black locust, 4/4 dressed to 3/4\" and ripped to 3 1/2\". Unfinished: no oil or film in a 190 F room. Stainless fasteners."),
    # RM-B-SAUNA's inside door casing (2026-10-18; locust before). Hands touch it at the door,
    # so it wants the stool's cool cedar, not the dense locust the base needs at the floor.
    Material(tag="cedar-sauna-trim", name='Cedar sauna door casing, 3/4" x 3 1/2" S4S',
             hatch="lumber", color="#b98a63", finish="solid-board", species="cedar",
             wood_surface="unfinished", density=360.0,
             nominal_quarters=4, milling_profile="S4S", requires_custom_milling=True,
             source="Owner's western red or northern white cedar, clear heartwood only, 4/4 dressed to 3/4\" and ripped to 3 1/2\". Unfinished. Stainless fasteners only: cedar extractives stain black against iron. Ease every edge. Laps the liner at the jamb; butts the locust base."),
    # WP-S-SUITE-HEADBOARD. The study wainscot stays `walnut-shiplap`.
    Material(tag="cherry-shiplap", name="Black cherry shiplap wainscot (4/4)", r_per_inch=1.1,
             density=560.0, hatch="lumber", color="#b77d60",
             finish="clear-satin-hardwax-oil", species="cherry", stock_bf_per_sqft=1.1,
             nominal_quarters=4, milling_profile="shiplap", requires_custom_milling=True,
             source="Milled black cherry shiplap, 5 1/2\" face over 5\" coverage; the suite headboard band"),
    # --- ash ------------------------------------------------------------------------------
    # FT-CATLIN-DINING-ASH's top (plan/dining_types.py); its legs are bought metal. 6/4 off
    # the owner's ash logs (12-16" DBH), whose boards run to ~11": provisional until the
    # sawyer tallies them.
    Material(tag="ash-6q", name="White ash, 6/4 S4S", hatch="lumber", color="#d9cbb0",
             finish="oak-board", species="ash", nominal_quarters=6, milling_profile="S4S",
             requires_custom_milling=True, max_board_width_in=11.0,
             source="Owner-milled white ash for the dining table top, 6/4 dressed to 1 1/4\", glued up; hardwax oil. Saw 6/4 full, ~1 5/8\" green."),
    # --- the sauna seating (plan/sauna_types.py) -------------------------------------------
    # Touched surfaces: the clearest basswood, mostly off the 24" log; clear aspen is equal.
    Material(tag="basswood-bench-5q", name="Basswood/aspen sauna bench slat, 5/4 S4S", hatch="lumber",
             color="#e5dcc4", finish="solid-board", species="basswood",
             wood_surface="unfinished", nominal_quarters=5, milling_profile="eased",
             requires_custom_milling=True,
             source="Owner basswood (or clear aspen), the clearest boards, 5/4 dressed to 1\" x 3 1/2\", every edge eased, unfinished. On bearers at 24\" o.c. or closer (notes/sauna_seating.md)."),
    # The frame nobody touches: bought Douglas fir since 2026-10-18 (owner aspen before), so
    # it is off the mill order. Kiln-dried sets the pitch. Posts/stretchers not designed yet.
    Material(tag="df-sauna-frame", name="Douglas fir sauna bench framing, KD S4S (bought)",
             hatch="lumber", color="#d9b077", finish="solid-board", species="douglas-fir",
             wood_surface="unfinished",
             source="Bought kiln-dried Douglas fir, clear/VG or Select, S4S: 2x4 (1 1/2\" x 3 1/2\") bench bearers under the slats, and the legs, posts and stretchers once designed. Unfinished, never pressure-treated. Every edge eased."),
]
