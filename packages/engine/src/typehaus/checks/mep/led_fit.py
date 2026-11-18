"""``electrical.light_run_fit``: the tape fits what holds it (decision #137).

A surface run's tape must fit its channel's inner width and depth; a shadow-gap run's tape
must fit the reveal's clear width; a rigid-bar run must take at least one module. A run
whose type states no ``LedStrip`` (or a surface run with neither channel nor modules) is
UNKNOWN: the section is the generic placeholder, not the product.
"""

from __future__ import annotations

from typehaus.checks._authoring import advisory, passed, unknown
from typehaus.checks.registry import CheckContext, Tier, check
from typehaus.findings import Finding, Result
from typehaus.resolve.led_sections import led_channels
from typehaus.resolve.trim_bands import FLANGE_SKIN_M

_CID = "electrical.light_run_fit"
_MM = 1000.0
_TOL_M = 1e-4


@check(Tier.ADVISORY, _CID)
def light_run_fit(ctx: CheckContext) -> list[Finding]:
    runs = ctx.model.light_runs
    if not runs:
        return [unknown(_CID, "no light runs modeled")]
    types = {t.tag: t for t in ctx.plan.library.electrical_device_types}
    channels = led_channels(ctx.plan)
    out: list[Finding] = []
    fitted = 0

    def fail(msg: str, *tags: str) -> None:
        out.append(advisory(_CID, msg, tags, Result.FAIL))

    for run in runs:
        strip = getattr(types.get(run.type_ref), "strip", None)
        if strip is None:
            out.append(unknown(_CID, f"{run.tag}: {run.type_ref} states no LedStrip, so its "
                                     "tape width is unread", (run.tag,)))
            continue
        tape = strip.tape_width.meters
        if run.profile == "shadow_gap":
            clear = (run.aperture_m or 0.0) - 2.0 * FLANGE_SKIN_M
            if tape > clear + _TOL_M:
                fail(f"{run.tag}: {tape * _MM:.1f} mm tape is wider than its reveal's "
                     f"{clear * _MM:.1f} mm clear", run.tag)
            else:
                fitted += 1
            continue
        if strip.channel_ref is not None:
            channel = channels.get(strip.channel_ref)
            if channel is None:
                fail(f"{run.tag}: {run.type_ref} names channel {strip.channel_ref}, which is "
                     "not an LedChannel in this plan", run.tag)
                continue
            inner = channel.inner_width_m()
            room = channel.outer_depth.meters - channel.back_m()
            if tape > inner + _TOL_M:
                fail(f"{run.tag}: {tape * _MM:.1f} mm tape is wider than {channel.tag}'s "
                     f"{inner * _MM:.1f} mm inner width", run.tag, channel.tag)
            elif strip.tape_height and strip.tape_height.meters > room + _TOL_M:
                fail(f"{run.tag}: {strip.tape_height.meters * _MM:.1f} mm tape stands proud of "
                     f"{channel.tag}'s {room * _MM:.1f} mm inside depth", run.tag, channel.tag)
            else:
                fitted += 1
            continue
        if strip.modules:
            if run.modules_m:
                fitted += 1
            else:
                fail(f"{run.tag}: {run.length_m / 0.0254:.1f}\" is shorter than every module "
                     f"{run.type_ref} ships in", run.tag)
            continue
        out.append(unknown(_CID, f"{run.tag}: surface tape names no channel, so its section "
                                 "is the generic placeholder", (run.tag,)))
    if fitted and not any(f.result is Result.FAIL for f in out):
        out.append(passed(_CID, f"{fitted} runs' tape fits its channel, reveal or modules"))
    return out
