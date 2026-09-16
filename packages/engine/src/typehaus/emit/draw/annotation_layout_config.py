"""Printed-space policy for deterministic drawing annotation placement."""

from __future__ import annotations

# All values are paper points.  Keeping them here makes the collision policy independent
# of a view's model scale and keeps site, plan, section, and detail annotations consistent.
LABEL_CLEARANCE_PT = 1.5
HARD_OBSTACLE_CLEARANCE_PT = 1.0
SOFT_OBSTACLE_CLEARANCE_PT = 0.35
POINT_OFFSET_PT = 9.0
LINE_OFFSET_PT = 10.0
LEADER_THRESHOLD_PT = 10.0
MAX_LOCAL_REFLOW = 2
