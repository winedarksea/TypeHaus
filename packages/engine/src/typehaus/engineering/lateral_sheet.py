"""The calculation-sheet declaration of ``lateral_system``: labels, free body, not covered.

Split from ``lateral_system`` to keep it under 500 lines. Everything here reads the record,
never the model, so the sheet cannot disagree with the numbers under it.
"""

from __future__ import annotations

from typehaus.engineering.item import EngineeringRecord, Figure, NotCovered, num
from typehaus.engineering.sketch import diaphragm_on_joint

#: Plain words for an input whose name carries a tag after a prefix (``panel_shear_<wall>``).
_PREFIX_LABELS = {
    "panel_shear_": "wind shear on the shear panel on {tag}, worse direction",
    "panel_uplift_": "overturning tension at the end post of {tag}",
    "panel_anchor_fc_": "concrete strength under the hold-down anchor of {tag}",
    "band_height_": "height of the band between {tag}'s top and its collector",
    "strap_tension_": "tension in the band straps on {tag}",
    "chord_tension_": "chord tension from overturning, full height, {tag}",
    "overturning_height_": "height from collector top to chord bases, {tag}",
    "slat_force_": "force along one braced slat of {tag}",
    "slats_crossing_mid_": "braced slats of one bay crossing mid-band, {tag}",
    "slat_bay_width_": "width of one bay of {tag}",
    "slat_bay_height_": "height of one bay of {tag}",
    "collector_clip_each_": "load on one eave collector clip on {tag}",
    "receiving_": "wind shear delivered to {tag}",
    "summed_": "every delivery into {tag} added",
    "collector_reaction_": "in-plane collector force at {tag}",
    "diaphragm_shear_": "wind shear on the deck, direction {tag}",
    "diaphragm_deflection_": "deck deflection under the shear, direction {tag}",
    "chord_force_": "chord force in the deck's chords, direction {tag}",
    "torsion_eccentricity_": "offset between the load and the lines' centre of rigidity, "
                             "direction {tag}",
    "torsion_moment_": "torsional moment left over by the rigid split, direction {tag}",
}
_EXACT_LABELS = {
    "delivered_shear_x": "wind shear on the deck, E-W, handed across the joint (ASD)",
    "delivered_shear_y": "wind shear on the deck, N-S, handed across the joint (ASD)",
    "joint_couple_lb_ft": "rotation couple of the along-joint shear about the strap line",
    "joint_couple_ns_lb_ft": "N-S couple: the screen at 100% against the deck's resultant",
    "chord_force_open_front_lb": "chord force M / W' in each chord of the open front",
    "collector_strap_line_lb": "line reaction collected by the strap line",
}


class _Labels(dict):
    """A label table that also resolves the tagged families above."""

    def get(self, key, default=""):  # type: ignore[no-untyped-def]
        if key in self:
            return self[key]
        for prefix, text in _PREFIX_LABELS.items():
            if key.startswith(prefix):
                tag = key.removeprefix(prefix)
                if tag.endswith("_end_tension_lb"):
                    return (f"overturning tension at the panel end of "
                            f"{tag.removesuffix('_end_tension_lb')}")
                return text.format(tag=tag.removesuffix("_lb"))
        return default


LABELS = _Labels(_EXACT_LABELS)


def figure(record: EngineeringRecord) -> Figure | None:
    """The deck on its joint, from the record's own states and inputs."""
    depth = next((s.demand for s in record.limit_states if s.name == "open front, L'"), None)
    ratio = next((s.demand for s in record.limit_states if s.name == "open front, L'/W'"), None)
    vx, vy = record.value("delivered_shear_x"), record.value("delivered_shear_y")
    if depth is None or not ratio or vx is None or vy is None:
        return None
    couple = record.value("joint_couple_lb_ft") or 0.0
    chord = record.value("chord_force_open_front_lb") or 0.0
    chord_y = record.value("chord_force_y")
    return diaphragm_on_joint(
        title=f"{record.key}, held on one edge by its joint",
        depth_ft=depth, width_ft=depth / ratio, along=f"{num(vx)} lb (E-W)",
        across=f"{num(vy)} lb (N-S)", couple=f"{num(couple)} lb-ft",
        chord=f"{num(chord)} lb", chord_across=f"{num(chord_y)} lb" if chord_y else "",
        caption="Every part of the path is graded at 100% of the deck shear: the joint "
                "straps and nailing, the receiving roof, and each receiving wall. The "
                "decks' unit-shear allowables are the SDPWS table reads under Stated bases.")


NOT_COVERED = (
    NotCovered("the deck's chords in tension, with their splice",
               "a truss top chord with a splice in it is the component designer's chart, "
               "because the chord force has to be combined with the roof gravity case at "
               "that section; the N-S chord force is printed, not graded",
               "the truss fabricator", "the sealed truss design and reaction schedule"),
    NotCovered("the collector beams' own capacity",
               "a header dragging a few hundred pounds is a tiny axial stress; the joint at "
               "its end is what fails, and that connection is graded",
               "the sealing engineer",
               "accepting the connection as the governing check of the collector"),
    NotCovered("movement between the canopy and the garage",
               "the two structures stand on separate foundations on presumed soil; the "
               "headers are simple spans between them, so a differential rotates each as a "
               "rigid body, within the 3/16 in the H2.5ASS ties and the LSTA24 strap line take",
               "the sealing engineer",
               "a soils report predicting more than that tolerance reopens "
               "canopy_garage_diaphragm.md §8"),
    NotCovered("stiffness across the joint (rigid or flexible split)",
               "both paths are graded at 100% of the shear with no stiffness judgement, so "
               "the splice slip enters no ratio",
               "the sealing engineer", "accepting the 100% envelope in place of a split"),
)
