"""Interior paint systems (decision #113): the PaintStandard's materials and their products.

Benjamin Moore is the basis of design; each BM product names its Sherwin-Williams and then
its Home Depot counterpart in ``equals``, because a painter sticks to one brand. Lines are
chosen on chemistry per dollar (acrylic, volume solids, MPI listing), not brand: Ultra Spec
500 and ProMar 200 HP are twins. One colour, ``interior_palette.WHITE``, tinted in any line.
Not ``# haus: editable``: a catalog. Data sheets, rejects and the vapour basis:
``notes/paint_selection.md``.

Vapour: walls, ceilings and wet rooms keep the library's 5.0 perm Class III band. The SW
data sheets publish 25.8 (primer) / 27.6 (ProMar 200 HP) perms but state neither the coat
count nor the test method, so they cannot replace it; at 25 perms no envelope Glaser grade
moves (note §3). The code's Class III listing of latex paint on gypsum is what complies.
"""

from __future__ import annotations

from typehaus import Material, PaintSpec, Product

from plan.interior_palette import WHITE

_NOTE = "notes/paint_selection.md"
_PERM = 5.0
_PERM_SOURCE = ("IRC R702.7.1: latex paint over gypsum is the canonical Class III retarder "
                "(1.0-10 perm). 5.0 is a prescriptive band value, not a published test: the "
                "SW sheets' 25.8/27.6 perms state no coat count or method (" + _NOTE + " §3).")


def _sw(tag: str, model: str, name: str, source: str) -> Product:
    return Product(tag=tag, brand="Sherwin-Williams", model=model, name=name,
                   source=source + f" Equal to the BM basis of design ({_NOTE}).")


def _hd(tag: str, brand: str, model: str, name: str, source: str) -> Product:
    return Product(tag=tag, brand=brand, model=model, name=name,
                   source=source + f" Home Depot line, equal to the BM basis ({_NOTE}).")


# --- the alternates ---------------------------------------------------------------------
SW_PRIMER = _sw("PROD-SW-PM200-ZERO-PRIMER", "ProMar 200 Zero VOC Primer B28W02600",
                "ProMar 200 Zero VOC interior latex primer",
                "Vinyl acrylic, 26% VS, 1.0 mil dry at 350-400 SF/gal, WVP 25.8 perms (data "
                "sheet; no method or coat count stated).")
SW_WALL = _sw("PROD-SW-PM200HP-ZERO-EGGSHELL", "ProMar 200 HP Zero VOC Eggshell",
              "ProMar 200 HP Zero VOC interior acrylic, eggshell",
              "Acrylic, ~42% VS, MPI 52/145; 27.6 perms published.")
SW_CEILING = _sw("PROD-SW-PM200-ZERO-FLAT", "ProMar 200 Zero VOC Flat",
                 "ProMar 200 Zero VOC interior latex, flat",
                 "Vinyl acrylic; fine on a ceiling. 70.8 perms published.")
SW_WET = _sw("PROD-SW-DURATION-HOME-SATIN", "Duration Home Satin A97",
             "Duration Home interior acrylic latex, satin",
             "Mildew-resistant film for the baths and laundry.")
SW_ENAMEL = _sw("PROD-SW-EMERALD-URETHANE-SG", "Emerald Urethane Trim Enamel, semi-gloss",
                "Emerald Urethane Trim Enamel, semi-gloss",
                "Waterborne urethane-modified alkyd; 15.9 perms published. Slow cure: 5-7 "
                "days before rehanging doors.")
HD_PRIMER = _hd("PROD-BEHR-DRYWALL-PRIMER", "Behr", "Drywall Primer & Sealer (TDS to read)",
                "Behr interior drywall primer & sealer",
                "TBD: the data sheet has not been read; confirm before accepting.")
HD_WALL = _hd("PROD-BEHR-USD-EGGSHELL", "Behr", "Ultra Scuff Defense Eggshell",
              "Behr Ultra Scuff Defense interior eggshell",
              "100% acrylic, 38% VS. The scuff claim is not why it is accepted.")
HD_CEILING = _hd("PROD-BEHR-USD-FLAT", "Behr", "Ultra Scuff Defense Flat",
                 "Behr Ultra Scuff Defense interior flat", "44% VS, MPI 53.")
HD_WET = _hd("PROD-ZINSSER-PERMA-WHITE-EGGSHELL", "Zinsser", "Perma-White Eggshell",
             "Zinsser Perma-White mold and mildew-proof interior, eggshell",
             "Mildew-proof film for the baths and laundry.")
HD_ENAMEL = _hd("PROD-BEHR-URETHANE-ALKYD-SG", "Behr", "Urethane Alkyd Semi-Gloss Enamel",
                "Behr interior/exterior urethane alkyd semi-gloss enamel",
                "Confirm the current data sheet: the one in hand is 2019.")

# --- the basis of design ------------------------------------------------------------------
_BM = "Benjamin Moore"
BM_PRIMER = Product(tag="PROD-BM-US500-PRIMER-N534", brand=_BM,
                    model="Ultra Spec 500 Interior Latex Primer N534",
                    name="Ultra Spec 500 interior latex primer",
                    equals=(SW_PRIMER.tag, HD_PRIMER.tag),
                    source=f"Acrylic, 30% VS; no perm published ({_NOTE}).")
BM_WALL = Product(tag="PROD-BM-US500-EGGSHELL-N538", brand=_BM,
                  model="Ultra Spec 500 Eggshell N538", name="Ultra Spec 500 interior eggshell",
                  equals=(SW_WALL.tag, HD_WALL.tag),
                  source=f"Acrylic, ~42% VS, MPI 52/145, under Regal Select at contract "
                         f"price; no perm published ({_NOTE}).")
BM_CEILING = Product(tag="PROD-BM-US500-FLAT-N536", brand=_BM,
                     model="Ultra Spec 500 Flat N536", name="Ultra Spec 500 interior flat",
                     equals=(SW_CEILING.tag, HD_CEILING.tag),
                     source=f"Same line as the walls, flat for the ceilings ({_NOTE}).")
# The same can as the walls; its own record because its accepted equals differ.
BM_WET = Product(tag="PROD-BM-US500-EGGSHELL-N538-WET", brand=_BM,
                 model="Ultra Spec 500 Eggshell N538",
                 name="Ultra Spec 500 interior eggshell (baths and laundry)",
                 equals=(SW_WET.tag, HD_WET.tag),
                 source=f"Carries a mildewcide in the can; Aura Bath & Spa is matte-only at "
                        f"~3x the price ({_NOTE}).")
BM_ENAMEL = Product(tag="PROD-BM-ADVANCE-SG-793", brand=_BM,
                    model="ADVANCE Interior Semi-Gloss 793",
                    name="ADVANCE waterborne alkyd interior enamel, semi-gloss",
                    equals=(SW_ENAMEL.tag, HD_ENAMEL.tag),
                    source=f"Waterborne alkyd, MPI 168. Cures slowly: 5-7 days before "
                           f"rehanging doors or loading shelves, ~30 days to full hardness "
                           f"({_NOTE}).")

PAINT_PRODUCTS = (SW_PRIMER, SW_WALL, SW_CEILING, SW_WET, SW_ENAMEL, HD_PRIMER, HD_WALL,
                  HD_CEILING, HD_WET, HD_ENAMEL, BM_PRIMER, BM_WALL, BM_CEILING, BM_WET,
                  BM_ENAMEL)


def _coat(tag: str, name: str, spec: PaintSpec, product: Product, *,
          vapour: bool = True) -> Material:
    perms = dict(vapor_permeance_perms=_PERM, r_per_inch=0.0) if vapour else {}
    return Material(tag=tag, name=name, coating=True, color=WHITE.hex,
                    finish=spec.finish_recipe, paint=spec, product_ref=product.tag,
                    source=(_PERM_SOURCE if vapour else f"Trim and door system ({_NOTE})."),
                    **perms)


_PRIMER = "paint-primer"
PAINT_MATERIALS = (
    _coat(_PRIMER, "Drywall primer (PR-1), under every wall and ceiling system",
          PaintSpec(sheen="flat", colour="white, or tinted to the topcoat",
                    mark="PR-1", use="Drywall primer", coats=1), BM_PRIMER, vapour=False),
    _coat("paint-wall", "Interior wall paint (PT-1), eggshell, primer + 2 coats",
          PaintSpec(sheen="eggshell", colour=WHITE.label, mark="PT-1", use="Walls",
                    primer_ref=_PRIMER), BM_WALL),
    _coat("paint-ceiling", "Interior ceiling paint (PT-2), flat, primer + 2 coats",
          PaintSpec(sheen="flat", colour=WHITE.label, mark="PT-2", use="Ceilings",
                    primer_ref=_PRIMER), BM_CEILING),
    _coat("paint-wet", "Bath and laundry paint (PT-3), eggshell, primer + 2 coats",
          PaintSpec(sheen="eggshell", colour=WHITE.label, mark="PT-3",
                    use="Baths and laundry, walls and ceilings", primer_ref=_PRIMER), BM_WET),
    _coat("paint-enamel", "Trim and door enamel (PT-4), semi-gloss, 2 coats",
          PaintSpec(sheen="semi-gloss", colour=WHITE.label, mark="PT-4",
                    use="Trim, doors and frames"), BM_ENAMEL, vapour=False),
)
