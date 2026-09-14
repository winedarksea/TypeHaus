"""Draw the derived connectors — the 500-odd parts that were specified but invisible.

Only *authored* ``Connector`` elements drew a solid. Everything ``typehaus.joints`` locates
— the roof hurricane ties, the mudsill anchors, the ridge straps — was billed by part number
and graded by the load-path check and could not be seen, because the derivation lived
downstream of ``resolve`` and geometry is made here.

**These are markers, not models of the parts.** A ``ResolvedSolid`` is a plan polygon
extruded vertically: any shape in plan, nothing but a prism in elevation, so an L-shaped tie
is not drawable and should not be. What has to read, among five hundred siblings, is *there
is a tie of this family at this joint* — and what makes that read is orientation, which
``joints`` derives at every one of them from the support line, the run, the carrier or the
ridge. None of it is guessed.

Every solid here is ``derived=True``, which is the double-billing guard:
``structural_solids_takeoff`` bills **every** solid by volume, so without the skip these
markers would become a phantom "connector" volume row standing beside the hardware rows that
already bill the same parts by part number. See ``ResolvedSolid.derived``.
"""

from __future__ import annotations

from typehaus.findings import Finding, Result, Severity
from typehaus.joints.markers import MARKER_RULES
from typehaus.joints.model import marker_uid
from typehaus.quantities import inch
from typehaus.resolve.model import ResolvedModel, ResolvedSolid

_CHECK_ID = "resolve.connector_markers"


def _marker_outline(point: tuple[float, float], axis: str,
                    along_m: float, across_m: float):
    """A rectangle at ``point``, long in ``axis``'s direction.

    Orientation is the whole reason these are legible, so it is applied here rather than
    left to a viewer: a tie straddling a plate and a strap running over a ridge are the same
    box until one of them is turned.
    """
    half_x, half_y = (along_m, across_m) if axis == "x" else (across_m, along_m)
    x, y = point
    return (
        (x - half_x, y - half_y),
        (x + half_x, y - half_y),
        (x + half_x, y + half_y),
        (x - half_x, y + half_y),
    )


def resolve_connector_markers(model: ResolvedModel) -> list[Finding]:
    """Append one marker solid per drawn derived joint. Returns findings, not geometry.

    Imported function-locally by the pipeline, as ``geometry_build`` is, because
    ``typehaus.joints`` reads ``resolve.model``.
    """
    from typehaus.hardware.config import DEFAULT_HARDWARE_TAKEOFF_CONFIG
    from typehaus.joints import derived_joints

    findings: list[Finding] = []
    authored_uids = {solid.uid for solid in model.solids}
    seen: dict[str, str] = {}
    ordinals: dict[str, int] = {}

    for joint in derived_joints(model, DEFAULT_HARDWARE_TAKEOFF_CONFIG):
        rule = MARKER_RULES.get(joint.role)
        if rule is None or not rule.draw:
            continue
        uid = marker_uid(joint.key)
        # Two parts at one joint — ``ties_per_bearing`` above 1, or two holdowns at one
        # sill-run end — are co-located by construction and share a key. They are one marker:
        # the model has nothing to say about which face each is on, and two coincident boxes
        # would z-fight rather than inform.
        if uid in seen:
            continue
        if uid in authored_uids:
            # Cannot happen by construction — an authored uid is minted by ``haus fmt`` and
            # this one is a digest of a role and a place — but a silent overwrite would
            # delete an authored connector from the model, so it is stated rather than
            # trusted.
            findings.append(Finding(
                check=_CHECK_ID, result=Result.FAIL, severity=Severity.ERROR,
                message=(f"derived connector marker uid {uid} collides with an authored "
                         f"solid at {joint.part} / {joint.members}"),
                fix_hint="re-run `haus fmt` to re-mint the authored uid"))
            continue
        seen[uid] = joint.key

        ordinals[joint.part] = ordinals.get(joint.part, 0) + 1
        anchor = joint.members[0] if joint.members else joint.role
        outline = _marker_outline(
            joint.point, joint.axis,
            inch(rule.along_in).meters, inch(rule.across_in).meters)
        if rule.half_h_in is None:
            # A hanger is a saddle: it starts at the carrier's soffit and carries the
            # member's own depth up from there, so its height comes from the joint. A joint
            # that somehow has none falls back to the shallowest honest box rather than
            # inventing a depth.
            depth_m = joint.height_m or inch(1.5).meters
            z0_m, z1_m = joint.z_m, joint.z_m + depth_m
        else:
            half_h_m = inch(rule.half_h_in).meters
            z0_m, z1_m = joint.z_m - half_h_m, joint.z_m + half_h_m
        model.solids.append(ResolvedSolid(
            uid=uid,
            tag=f"CN~{joint.part}~{anchor}~{ordinals[joint.part]:02d}",
            storey=joint.storey, category=rule.category,
            outline=outline, z0_m=z0_m, z1_m=z1_m,
            # The Simpson part, so a click in the Inspector names it. "connector ·
            # CN~H2.5A~W-A-E2~07" says where; the Part row says what.
            product=joint.part,
            derived=True,
        ))
    return findings
