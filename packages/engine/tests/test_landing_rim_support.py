"""ST-B2M's landing framing on the well posts, against notes/stair_landing_post_hangers.md."""

from __future__ import annotations

import re

from shapely.geometry import Polygon

from typehaus.checks.structural.landing_rim_support import landing_rim_support
from typehaus.findings import Result
from typehaus.hardware.connector_fastening import connector_fastening
from typehaus.resolve.framing.footprint import member_footprint


def test_hung_ends_match_the_hand_note(catlin_ctx):
    """§4: 293 lb on each edge joist, 180 lb (lever-ruled joists) and 26 lb on the rims."""
    findings = landing_rim_support(catlin_ctx)
    assert all(f.result is Result.PASS for f in findings), [
        f.message for f in findings if f.result is not Result.PASS]
    demands = {}
    for f in findings:
        hit = re.search(r"ST-B2M:(\S+) on \S+ \(LUC26Z\): (\d+) lb", f.message)
        if hit:
            demands.setdefault(re.sub(r"-(lower|upper)", "", hit[1]), set()).add(int(hit[2]))
    assert demands == {"landing-joist-000": {293}, "landing-rim-0-seg0": {26},
                       "landing-rim-1-seg0": {26}, "landing-rim-0-seg1": {180},
                       "landing-rim-1-seg1": {180}}


def test_post_hangers_are_screwed_not_nailed():
    """§3: opposite faces of a 4x4 at one seat; 3 1/2" nails would meet, SD screws do not."""
    for part in ("LUC26Z", "LUC210Z"):
        models = {model for _n, model, _into in connector_fastening(part).fasteners}
        assert models == {"SD10112", "SD9112"}, part


def test_nothing_of_the_stair_stands_in_the_posts(catlin_model_ro):
    """§2 and §7: rims, joists, the landing riser and both decks stop at the post faces."""
    posts = [s for s in catlin_model_ro.solids if s.tag.startswith("P-M-STRWELL-")]
    [stair] = [s for s in catlin_model_ro.stairs if s.tag == "ST-B2M"]
    assert len(posts) == 2
    for member in stair.members:
        if member.category not in ("landing", "landing_framing", "riser"):
            continue
        ring, z0, z1 = member_footprint(member)
        for post in posts:
            if z1 <= post.z0_m or z0 >= post.z1_m:
                continue
            lap = Polygon(ring).intersection(Polygon(post.outline)).area
            assert lap < 1e-6, (member.child_key, post.tag, lap)
