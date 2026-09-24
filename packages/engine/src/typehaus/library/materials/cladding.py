"""Cladding, siding, glazing panels and deck surfaces."""

from __future__ import annotations

from typehaus.library.materials._common import _UAF
from typehaus.model import Material

_BASE_ROWS: tuple[Material, ...] = (
    # Solid PVC tongue-and-groove wall/ceiling panel (Trusscore-class): concealed screw
    # flange, mounts direct to furring, no cellulose substrate anywhere in it, third-party
    # mould-tested to ISO 846. The lining of choice for a room that is deliberately wet.
    #
    # `vapor_permeance_perms` is deliberately UNSET and that is the finding, not a gap: no
    # manufacturer in this product class — Crane, Marlite, Nudo, Trusscore, Extrutech —
    # publishes an ASTM E96 number, so an assembly using it reports UNKNOWN naming this
    # material rather than crediting a panel nobody measured as vapour control. The barrier
    # is `humid-room-membrane` above, behind it.
    #
    # Chosen over FRP, which is disqualified rather than merely worse: FRP's own published
    # product limitations require 60-75 F and 35-55% RH and forbid installing it over studs,
    # and non-compliance voids the warranty.
    Material(
        tag="pvc-panel",
        name='Solid PVC T&G wall/ceiling panel (1/2")',
        r_per_inch=1.0,
        density=700.0,
        hatch="rigid",
        color="#f2f4f3",
        source='Trusscore-class 1/2" T&G interlocking PVC panel, concealed screw '
        "flange, ISO 846 mould-tested; no ASTM E96 permeance published in "
        "this product class, so none is authored",
    ),
    # No published ASTM E96 rating located for modern fibre-cement lap siding; the closest
    # published entry is asbestos-cement board, a different binder/fibre system, so the
    # field is left unset rather than substituted.
    Material(
        tag="fiber-cement",
        name="Fiber-cement lap siding",
        r_per_inch=0.15,
        density=1700.0,
        hatch="siding",
        color="#b8bcc0",
        source="no published ASTM E96 rating located for fibre-cement lap siding; "
        "vapour fields unset so the Glaser walk reports UNKNOWN",
    ),
    Material(
        tag="standing-seam",
        name="Standing-seam steel",
        r_per_inch=0.0,
        density=7800.0,
        vapor_permeance_perms=0.0,
        hatch="metal",
        color="#6b7076",
        skin_family="standing-seam",
        source=f'{_UAF}: metal foil at 0.001" reads 0 perm; continuous sheet steel is '
        "vapour-impermeable. Normally installed over a vented rainscreen, which "
        "truncates the Glaser walk before it",
    ),
    # 7/8" corrugated, the third profile in the site's one white steel skin, and the
    # detached garage's wall panel — GARAGE_WALL_2X6 over 5/8" CDX. A sinusoidal
    # exposed-fastener sheet: 7/8" deep on a 2-2/3" pitch, 32" net coverage, screwed
    # through the crowns into the studs.
    #
    # `finish="corrugated"` is the whole dispatch. `isStandingSeam` (ui materials.ts) and
    # `_is_standing_seam` (emit/gltf/palette.py) are substring tests, and this tag carries
    # neither "seam" nor "standing" — so the metal treatment is reached ONLY through the
    # authored finish, exactly as `pbr-panel-26` does it. That is the documented design,
    # not a workaround; a material that says what it is beats a tag that hints at it.
    #
    # `skin_family="standing-seam"` keeps the garage's wall and its nail-strip roof reading
    # as one continuous skin at the flush roof edge (`continuous_skin_cladding`), which is
    # the one thing tag equality gets wrong about a building wearing one white in three
    # specifications. It changes no quantity and no building-science number.
    #
    # `exposed_fastener=True` is the double-billing guard: it is what lets
    # `takeoff.fasteners` bill the panel screws as a counted part instead of leaving them
    # inside a $/SF rate. Without it the screws simply vanish from the bill.
    Material(
        tag="corrugated-panel-26",
        name='7/8" corrugated exposed-fastener steel panel, 26 ga.',
        r_per_inch=0.0,
        density=7800.0,
        vapor_permeance_perms=0.0,
        hatch="metal",
        # 26 ga. is 0.0179" of steel = 3.55 kg/m2 flat; the corrugation's developed
        # length runs about 10% over its coverage, so 3.9. The 7/8" `thickness` above
        # is the PROFILE DEPTH — it is what the panel occupies in the wall, not what it
        # is made of, and a dead load taken off it reads a sheet of solid steel.
        areal_density_kg_m2=3.9,
        color="#6b7076",
        finish="corrugated",
        skin_family="standing-seam",
        exposed_fastener=True,
        source=f"{_UAF}: continuous sheet steel is vapour-impermeable, as `standing-seam` "
        'above. 26 ga. PVDF-coated steel, 7/8" corrugation depth on a 2-2/3" '
        'pitch, 34-2/3" net WALL coverage (32" is the ROOF figure, one more '
        'corrugation of side lap; this row read 32" until 2026-09-14), '
        "face-fastened with gasketed screws through the "
        "crowns. TWO KNOWN APPROXIMATIONS, recorded here rather than fixed: "
        "hardware/config.py::ExposedFastenerCladdingRules is one frozen "
        'dataclass with PBR geometry hard-coded (12" rib pitch, 36" coverage), so '
        "the field screw count is a fair proxy but the sidelap count runs slightly "
        'low on 36" vs this panel\'s 34-2/3"; and its support_embedment_in=1.4" is '
        "satisfied by no sheathing thickness at all — the rule presumes penetration "
        "into framing, which is what these screws do",
    ),
    # The vent strip that closes a rainscreen cavity's base: a corrugated polypropylene
    # section whose flutes run *across* the cavity, so the cavity keeps draining and
    # venting while nothing insect-sized gets in. It is a spaced section, not a skin — the
    # vapour path through it is the open air in its flutes, exactly like the resilient
    # channel above.
    Material(
        tag="corrugated-vent-strip",
        name="Corrugated rainscreen vent/insect strip",
        r_per_inch=0.0,
        density=910.0,
        perm_rating=120.0,
        hatch="rigid",
        color="#3c4045",
        source=f"{_UAF}: 'Air, still' 120 perm-in — the vapour path through a "
        "corrugated vent strip is the open flute, not the polypropylene; "
        "density is the published bulk density of polypropylene. No ASTM E96 "
        "test is published for the strip itself",
    ),
    Material(
        tag="cedar-tg",
        name="Cedar T&G paneling",
        r_per_inch=1.0,
        perm_rating=2.9,
        hatch="lumber",
        color="#c98d5f",
        source=f"{_UAF}: 'Wood, sugar pine' permeability 0.4-5.4 perm-in (the table's "
        "softwood entry); midpoint of the published range",
    ),
    Material(
        tag="stucco",
        name="Portland-cement stucco",
        r_per_inch=0.20,
        density=1900.0,
        perm_rating=10.0,
        hatch="concrete",
        color="#d9d2c4",
        source="Portland-cement stucco / parge coat over mesh, a standard exterior masonry finish",
    ),
    Material(
        tag="composite-deck",
        name="Composite decking (capped PVC/wood)",
        r_per_inch=1.0,
        density=1000.0,
        perm_rating=0.5,
        hatch="lumber",
        color="#8a7f70",
        source="capped composite decking walking surface; PVC-capped composite ~0.5 perm-in (low)",
    ),
    Material(
        tag="aluminum-deck",
        name="Aluminum deck board (Wahoo AridDeck-style)",
        r_per_inch=0.0,
        density=2700.0,
        perm_rating=0.05,
        hatch="metal",
        color="#b9bcc0",
        source="waterproof aluminum plank decking; metal is effectively vapor-impermeable",
    ),
    # 16mm five-wall polycarbonate. `color` is authored, not inferred: the palette's
    # substring-ordered family inference matches ("poly","rigid") first and would render this
    # as bright-yellow rigid foam otherwise. The alpha byte is what reads as glazing rather
    # than a solid panel (alphaMode BLEND below 1.0 in emit/gltf/scene.py).
    # Permeance ~0.012 perms, from EN 16153's 3.8e-5 mg/(m·h·Pa) converted and stored as
    # product permeance across the 16mm sheet (not divided again by thickness) — Class I.
    Material(
        tag="polycarbonate-multiwall",
        name="Multiwall polycarbonate glazing (16mm)",
        r_per_inch=1.54,
        density=1200.0,
        vapor_permeance_perms=0.012,
        hatch="glass",
        color="#cfe3e8b0",
        finish="polycarbonate",
        source="SABIC LEXAN THERMOCLEAR multiwall declaration EN 16153:2013+A1:2015 "
        "https://ff.sabic.eu/uploads/resources/DoP%20LT2UV329X38%20-%202023.pdf",
    ),
    # Clear SOLID polycarbonate sheet — one monolithic ply, not a walled extrusion. A
    # windblock wants transparency, not the multiwall's insulating flutes, and the two are
    # separate materials rather than one with a thickness: the multiwall's R and permeance
    # are *product* figures for a 16mm five-wall section and say nothing about solid stock.
    # `r_per_inch` from k ~= 0.2 W/(m.K): 1"/0.2 => 0.72 h.ft2.F/Btu per inch, so 1/4" is
    # R-0.18 — a windbreak, and the energy model must not read it as glazing insulation.
    # `perm_rating` is a PROXY: solid PC datasheets publish WVTR around 0.3 perms at 1/8",
    # which is ~0.04 perm-in. Class I either way, and there is no conditioned assembly in
    # this house that depends on the figure.
    # Colour is authored for the same reason the multiwall's is (the family inference would
    # paint anything matching "poly" as rigid foam), and the alpha is LIGHTER than the
    # multiwall's: clear stock reads through, opal five-wall does not.
    Material(
        tag="polycarbonate-solid",
        name="Solid polycarbonate glazing (clear sheet)",
        r_per_inch=0.72,
        density=1200.0,
        perm_rating=0.04,
        hatch="glass",
        color="#dceff488",
        finish="polycarbonate",
        source="clear monolithic polycarbonate sheet (Lexan/Makrolon class), "
        'k~0.2 W/(m.K), density 1.20 g/cm3; WVTR ~0.3 perms at 1/8" is a '
        "datasheet-class proxy, not a product declaration",
    ),
    # Mill-finish extruded aluminium: U/H/F channels, glazing bars, panel fasteners' washers.
    # "alum" matches no needle in the family inference at all, so this colour is authored
    # for the same reason the polycarbonate's is.
    Material(
        tag="aluminum-extrusion",
        name="Extruded aluminium glazing bar / channel",
        r_per_inch=0.0007,
        density=2700.0,
        perm_rating=0.0,
        hatch="metal",
        color="#b6bac0",
        source="mill-finish 6063-T5 extruded aluminium glazing trim",
    ),
    Material(
        tag="siding-303-mdo",
        name='5/8" APA Rated Siding 303, MDO smooth face (Exterior)',
        r_per_inch=1.25,
        density=600.0,
        perm_rating=0.30,
        hatch="osb",
        color="#b9a583",
        source="APA Rated Siding 303 exterior MDO product data; SDPWS Table 4.3B.",
    ),
    Material(
        tag="sauna-shiplap",
        name="Basswood/aspen shiplap sauna liner (5/4)",
        r_per_inch=1.3,
        perm_rating=20.0,
        hatch="lumber",
        color="#e6d4ae",
        finish="shiplap",
        species="basswood",
        source="Factory sauna-liner product specification; a house that site-mills it "
        "declares a custom material locally.",
    ),
    Material(
        tag="brick",
        name="Face brick",
        r_per_inch=0.20,
        density=1920.0,
        perm_rating=1.0,
        hatch="concrete",
        color="#9c5a4a",
        finish="brick",
        source="Face-brick thermal and vapour reference values.",
    ),
)

_BY_TAG = {m.tag: m for m in _BASE_ROWS}
_SEAM = _BY_TAG["standing-seam"]
_CORRUGATED = _BY_TAG["corrugated-panel-26"]
_PBR = {
    "finish": "ribbed-panel", "exposed_fastener": True,
}

# Profile and gauge variants of the two sheet-steel skins. Every building-science number is
# the base row's — continuous sheet steel carries no R and no permeance whatever its seam or
# gauge — so only the product (and the takeoff line it prices on) differs. The tags keep the
# gauge because the gauge is what a supplier quotes.
_VARIANTS: tuple[Material, ...] = (
    _SEAM.model_copy(update={
        "tag": "standing-seam-snaplock", "name": "Snap-lock standing-seam steel, 24 ga.",
        "source": "24 ga. PVDF-coated steel, snap-lock seam (concealed floating clips, seam "
                  "engaged by hand); building-science values as `standing-seam`"}),
    _SEAM.model_copy(update={
        "tag": "standing-seam-nailstrip", "name": "Nail-strip standing-seam steel, 24 ga.",
        "source": "24 ga. PVDF-coated steel, nail-strip seam (integral face-fastened flange, no "
                  "concealed clips; short runs only, face-fastening restricts thermal "
                  "movement); building-science values as `standing-seam`"}),
    _SEAM.model_copy(update={
        "tag": "standing-seam-nailstrip-26", "name": "Nail-strip standing-seam steel, 26 ga.",
        "source": "26 ga. PVDF-coated steel, nail-strip seam; building-science values as "
                  "`standing-seam`"}),
    _SEAM.model_copy(update={
        "tag": "pbr-panel-26", "name": "PBR exposed-fastener steel panel, 26 ga.", **_PBR,
        "source": "Metal Sales PBR-Panel Condensed Technical Reference (1/2026): 26 ga. "
                  "PVDF-coated steel purlin-bearing-rib wall panel, 36\" net coverage, "
                  "1-1/4\" major ribs at 12\" o.c., face-fastened with gasketed screws; "
                  "236 psf outward at 2'-0\" (wall table)"}),
    _SEAM.model_copy(update={
        "tag": "pbr-panel-24", "name": "PBR exposed-fastener steel panel, 24 ga.", **_PBR,
        "source": "Metal Sales PBR-Panel Condensed Technical Reference (1/2026): 24 ga. "
                  "PVDF-coated steel purlin-bearing-rib wall panel, 36\" net coverage, "
                  "1-1/4\" major ribs at 12\" o.c., face-fastened with gasketed screws; "
                  "318 psf outward at 2'-0\" (wall table)"}),
    _CORRUGATED.model_copy(update={
        "tag": "corrugated-panel-24",
        "name": "7/8\" corrugated exposed-fastener steel panel, 24 ga.",
        "areal_density_kg_m2": 5.2,
        "source": "Metal Sales 7/8\" Corrugated Wall CTR (1/2024): 24 ga. PVDF-coated steel, "
                  "7/8\" corrugation on a 2-2/3\" pitch, 34-2/3\" net wall coverage, "
                  "3'-45' lengths, over open framing or solid substrate, 412 psf outward at "
                  "2'-0\"; face-fastened with gasketed screws through the crowns. 24 ga. is "
                  "0.0239\" of steel, 4.7 kg/m2 flat, ~10% more developed length: 5.2"}),
)

MATERIALS: tuple[Material, ...] = _BASE_ROWS + _VARIANTS
