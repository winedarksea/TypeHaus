"""Framing lumber, engineered wood and steel studs."""

from __future__ import annotations

from typehaus.library.materials._common import _UAF
from typehaus.model import Material

MATERIALS: tuple[Material, ...] = (
    Material(
        tag="spf",
        name="SPF framing lumber",
        r_per_inch=1.25,
        density=460.0,
        perm_rating=2.9,
        hatch="lumber",
        color="#d8c9a6",
        # NDS 2018 Table 12.3.3A, "Spruce-Pine-Fir". The stud is the MAIN member every
        # long standoff screw lands in, and withdrawal goes as G squared, so this is a
        # structural input and not a description.
        specific_gravity=0.42,
        source=f"{_UAF}: 'Wood, sugar pine' permeability 0.4-5.4 perm-in "
        "(the table's softwood entry); midpoint of the published range",
    ),
    # No published permeance/permeability located for laminated strand lumber; the field is
    # deliberately unset so an assembly that puts LSL in the vapour path reports UNKNOWN.
    Material(
        tag="lsl",
        name="Laminated strand lumber",
        r_per_inch=1.25,
        density=650.0,
        hatch="lumber",
        color="#cbb98e",
        source="R-value per ifcplot port; no published ASTM E96 rating located, so "
        "the vapour fields stay unset (Glaser reports UNKNOWN, never a guess)",
    ),
    # Laminated VENEER lumber, the sibling of ``lsl`` and a different product: rotary-peeled
    # veneers laid parallel and glued, rather than stranded flakes. It is authored here and
    # not left to the ``solid_material_ref`` fallback (which calls every non-round beam
    # "spf") because an LVL beam costs three to five times a sawn one by the foot, and a
    # takeoff that cannot tell them apart cannot price either.
    # Same discipline as ``lsl`` on vapour: no published ASTM E96 rating located, so both
    # fields stay unset and the Glaser walk names this material in an UNKNOWN.
    Material(
        tag="lvl",
        name="Laminated veneer lumber",
        r_per_inch=1.25,
        density=670.0,
        hatch="lumber",
        color="#c2ab7c",
        source="R-value shares the engineered-lumber value used for lsl; density is "
        "the midpoint of the 640-720 kg/m3 (40-45 pcf) band published for "
        "softwood LVL; no ASTM E96 rating located, so the vapour fields "
        "stay unset (Glaser reports UNKNOWN, never a guess)",
    ),
    # Kiln-dried-after-treatment southern yellow pine — the exterior framing species. KDAT
    # rather than plain PT is a real distinction and not a label: the treatment leaves the
    # stick soaked, and drying it *after* is what stops a deck frame shrinking, cupping and
    # backing its fasteners out over its first season. It is a separate tag from ``spf``
    # because it is a denser species, costs more by the foot, and must not be substituted
    # into an interior wall by a takeoff that only knows "lumber".
    Material(
        tag="kdat",
        name="KDAT southern yellow pine (treated exterior framing)",
        r_per_inch=0.95,
        density=600.0,
        perm_rating=2.9,
        hatch="lumber",
        color="#bfa06a",
        preservative_treated=True,
        # NDS 2018 Table 12.3.3A, "Southern Pine". The withdrawal of every screw
        # driven into a KDAT girt goes as G squared, so this is a structural input
        # and not a description.
        specific_gravity=0.55,
        source="SYP is the densest of the framing softwoods (SG ~0.55 green vs SPF "
        "~0.42), and R/inch falls as density rises, so it sits below the "
        "df-select-s4s 0.99-1.06 band already authored in catlin; "
        f"permeability shares the softwood midpoint used for spf ({_UAF})",
    ),
    # Treated structural glulam — the balcony's three beams (Anthony Power Preserved /
    # Boise 24F-V5M1/SP, southern yellow pine laminations, preservative-treated after
    # lay-up and clear-finished). A separate tag from ``kdat``: it is a manufactured
    # member with published engineered values, not sawn stock built up in plies, and a
    # takeoff that priced it as 2x KDAT would under-bill it by half.
    #
    # NO ``perm_rating``: none is published for a treated glulam lay-up, and this member
    # never sits in a vapour stack (Glaser reports UNKNOWN rather than a guess).
    Material(
        tag="glulam-treated",
        name="Preservative-treated SYP structural glulam",
        r_per_inch=0.95,
        density=560.0,
        hatch="lumber",
        color="#c8a877",
        preservative_treated=True,
        source="SYP glulam laminations at ~35 pcf oven-dry (560 kg/m3), the AWC "
        "NDS Supplement value for the group; R/inch shares the kdat SYP "
        "figure, since the laminations are the same species",
    ),
    # Light-gauge steel framing (25 ga. C-stud). Like the resilient channel above it is a
    # spaced section, not a skin, so the vapour path through the layer is the still air
    # between studs — the same 120 perm-in the channel carries, and for the same reason.
    # R per inch is zero: a steel stud is a thermal bridge, not an insulator, and stating
    # any positive number here would credit the wall for the worst part of it.
    Material(
        tag="steel-stud",
        name="25 ga. steel C-stud",
        r_per_inch=0.0,
        density=7850.0,
        perm_rating=120.0,
        hatch="metal",
        color="#91979d",
        source=f"{_UAF}: 'Air, still' 120 perm-in — the vapour path through a spaced "
        "metal section is the air between the sections, not the steel",
    ),
    Material(
        tag="df-select-s4s",
        name="Douglas fir Select Structural S4S, eased corners",
        r_per_inch=1.00,
        density=530.0,
        perm_rating=2.9,
        hatch="lumber",
        color="#d9b077",
        finish="clear-satin-hardwax-oil",
        source="Douglas-fir lumber thermal/permeance reference values.",
    ),
)
