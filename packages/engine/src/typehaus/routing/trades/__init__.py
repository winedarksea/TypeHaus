"""Per-trade adapters: what a radius means, what a crossing means, what may be emitted.

The search does not care which trade is asking — a bend is a bend and an obstacle is an
obstacle. What differs is three things, and each module here answers exactly those:

* **the radius** an obstacle is inflated by, which for a duct is not its diameter;
* **when a crossing of a floor's members is admissible**, which is a different rule for a
  duct than for a pipe;
* **whether the found route is expressible at all** in the element the trade authors —
  a ``ConduitRun`` cannot say what a route in full 3-D found, and ``conduit.legalize``
  splits and *discloses* rather than emitting something that resolves wrong.
"""
