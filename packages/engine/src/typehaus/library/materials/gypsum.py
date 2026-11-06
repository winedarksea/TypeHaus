"""Gypsum boards: the regular, fire-rated and upgrade wall and ceiling boards."""

from __future__ import annotations

from typehaus.library.materials._common import _UAF
from typehaus.model import Material

MATERIALS: tuple[Material, ...] = (
    Material(
        tag="gwb",
        name="Standard-weight gypsum board",
        r_per_inch=0.9,
        perm_rating=18.8,
        gypsum_type="regular",
        gypsum_facer="paper",
        hatch="gypsum",
        color="#efeae2",
        source=f"{_UAF}: 'Gypsum wall board, plain' 50 perm at 0.375\" = 18.8 perm-in "
        '(≈30 perm at 5/8", consistent with USG\'s 34.2 perm at 1/2"). Standard weight '
        '(~1.6-1.8 lb/SF at 1/2"), not lightweight board (e.g. Sheetrock UltraLight): STC '
        "follows mass, and the cited STC presets were tested with full-weight board",
    ),
    # Type X differs from regular board in its glass-fibre core, not in any property this
    # engine calculates with — same R per inch, same permeance. It exists as a separate
    # material precisely so an assembly can *say* which board it uses, which is the whole
    # question R302.6 asks about a garage ceiling with habitable space over it.
    Material(
        tag="gwb-x",
        name="Type X gypsum board",
        r_per_inch=0.9,
        perm_rating=18.8,
        gypsum_type="type-x",
        gypsum_facer="paper",
        hatch="gypsum",
        color="#efeae2",
        source="thermal and vapour properties as 'gwb' above; the Type X core changes "
        "fire performance, not conductivity or permeance",
    ),
    # Upgrade boards. Thickness lives on the Layer; these differ from 'gwb' in core or
    # facer treatment only, not in any thermal or vapour property this engine computes.
    Material(
        tag="gwb-c",
        name="Type C gypsum board",
        r_per_inch=0.9,
        perm_rating=18.8,
        gypsum_type="type-c",
        gypsum_facer="paper",
        hatch="gypsum",
        color="#f2dcdc",
        source="thermal and vapour properties as 'gwb'; ASTM C1396 Type C (e.g. USG "
        "Firecode C, Gold Bond Fire-Shield C) — denser fibre-and-vermiculite core. USG "
        "submittal WB2965-USA-ENG rev. 11-19 pp.1-2: 1/2\" Firecode C complies with ASTM "
        "C1396 as Type X wallboard, 2.0 lb/SF (9.8 kg/m2) nominal",
    ),
    Material(
        tag="gwb-ar",
        name="Abuse-resistant gypsum board",
        r_per_inch=0.9,
        perm_rating=18.8,
        gypsum_type="regular",
        gypsum_facer="paper",
        gypsum_upgrades=("abuse-resistant",),
        hatch="gypsum",
        color="#d3dbe3",
        source="thermal and vapour properties as 'gwb'; paper-faced ASTM C1629 abuse "
        "resistance (e.g. USG Sheetrock AR, Gold Bond Hi-Abuse XP). An upgrade, not a code "
        "requirement: 1/2\" is a supply-yard item. Where it is not readily stocked at a "
        "reasonable price, standard-weight regular ('gwb') or Type C ('gwb-c') of the same "
        "thickness may be substituted",
    ),
    Material(
        tag="gwb-mr",
        name="Mold-resistant gypsum board",
        r_per_inch=0.9,
        perm_rating=18.8,
        gypsum_type="regular",
        gypsum_facer="paper",
        gypsum_upgrades=("mold-resistant",),
        hatch="gypsum",
        color="#e0d6ec",
        source="thermal and vapour properties as 'gwb'; paper-faced, ASTM D3273 score 10 "
        "(e.g. Gold Bond XP, USG Sheetrock Mold Tough, GP ToughRock Mold-Guard at 1.7 lb/SF "
        "1/2\"). Still paper: not a wet-area backer",
    ),
    # Glass mat both faces, no paper anywhere: the shower backer (R702.4.2 names ASTM C1178).
    # Its acrylic face coat is the moisture barrier, so the sheet carries its own permeance.
    Material(
        tag="gwb-glass-mat",
        name="Glass-mat gypsum tile backer",
        r_per_inch=1.12,
        vapor_permeance_perms=1.5,
        gypsum_type="regular",
        gypsum_facer="glass-mat",
        gypsum_upgrades=("mold-resistant",),
        hatch="gypsum",
        color="#c5c9c4",
        source="GP DensShield Tile Backer 1/2\" (Home Depot 855000), DensShield Technical "
        "Guide, Lit. Item #622598 (12/20), p.3 Physical Properties: ASTM C1178 coated glass "
        "mat, 2.0 lb/SF (9.8 kg/m2) nominal, R 0.56 at 1/2\" (ASTM C518), permeance <1.5 "
        "perm (ASTM E96 dry cup; the bound is used), fire classification n/a (not Type X), "
        "E84 0/0; p.4: ASTM D3273 score 10. p.6 DS001: grey face out, studs <= 16\" o.c., "
        "corners in flexible sealant, joints mesh-taped, no vapour retarder behind it",
    ),
)
