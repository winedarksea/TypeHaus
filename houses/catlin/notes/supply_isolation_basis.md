---
title: "Fixture and appliance supply isolation: UPC 606.5-606.7 and the manifold port"
applied_to:
  - check: mep.fixture_control_valve
tags: [plumbing, water-supply, code]
---

# Notes

Written 2026-11-10. Oracle for `mep.fixture_control_valve`. Minnesota adopts chapters 2-11 of the
**2018 UPC** (MN Rules 4714.0050) and has **no part amending 606**: 4714.0601-0603 and
4714.0607-0612 exist, 4714.0605/.0606 do not, and 4714.0609 touches only 609.1/.6/.10/.11. So the
IAPMO text below governs verbatim. There is **no Minnesota DLI guidance** on manifold control
valves that I could find, and no IAPMO interpretation.

## 1. The code text (primary)

Source: 2018 UPC e-pub, `epubs.iapmo.org/2018/UPC/`, printed p. 106 (Ch. 6) and p. 9 (Ch. 2). The
text was read from the e-pub's own page-text index; the two-column layout interleaves sections
but each quoted passage is intact.

> **606.5 Control Valve.** A control valve shall be installed immediately ahead of each
> water-supplied appliance and immediately ahead of each slip joint or appliance supply.
> Parallel water distribution systems shall provide a control valve either immediately ahead of
> each fixture being supplied or installed at the manifold, and shall be identified with the
> fixture being supplied. Where parallel water distribution system manifolds are located in
> attics, crawl spaces, or other locations not readily accessible, a separate shutoff valve shall
> be required immediately ahead of each individual fixture or appliance served.

> **606.6 Accessible.** Required shutoff or control valves shall be accessible.
>
> **606.7 Multiple Fixtures.** A single control valve shall be installed on a water supply line
> ahead of an automatic metering valve that supplies a battery of fixtures.

Nearby: **606.4** "Valves used to control two or more openings shall be fullway gate valves, ball
valves, or other approved valves designed and approved for the service intended." **605.14** "In
water piping, slip joints shall be permitted to be used only on the exposed fixture supply."
**606.2** requires a fullway valve on each water heater's cold supply (graded by `mep.main_shutoff`).

Ch. 2 (§203.0, p. 9):

> **Accessible.** Where applied to a fixture, connection, appliance, or equipment, "accessible"
> means having access thereto, but which first may require the removal of an access panel, door,
> or similar obstruction. **Accessible, Readily.** Having a direct access without the necessity
> of removing a panel, door, or similar obstruction.

The 2018 UPC has **no 606.5.1 "Manifolds"** or IGC 109 (later editions). "Water-supplied
appliance" and "slip joint" are not defined in Ch. 2. 606.3 (multidwelling) and 606.7
(flush-valve batteries) do not reach this house.

## 2. Answers

**1. One port for a room group?** Not on the text. A manifold port is a valid control valve only
if it is "identified with the fixture being supplied": singular, one fixture per port. A port
that isolates a lav, a sink and a WC together cannot be identified with one fixture. 606.4 lets
one valve control several openings, so a group port is not forbidden as hardware, but 606.5
asks for the per-fixture label. No source blesses a room-group port; treat it as AHJ discretion,
not code. A lav has a hot and a cold supply, so it takes two ports (hot manifold, cold manifold).

**2. Valve at each appliance?** Yes on a trunk-and-branch supply: "immediately ahead of each
water-supplied appliance" is unconditional. On a parallel system the manifold alternative is
worded for "each fixture", but the inaccessible-manifold sentence says "fixture or appliance
served", so appliances are within the manifold's scope. A labelled, readily accessible port per
appliance is a defensible reading; a stop at the appliance is the safe one. Keep the washer box,
dishwasher and RO/fridge stops.

**3. Which fixtures, trunk-and-branch?** Literally two classes: (a) water-supplied appliances,
(b) "slip joint or appliance supply" (a slip-joint fixture supply, 605.14, i.e. the exposed
chrome tube under a lav or sink; the clause is ambiguous in grammar and I read it as slip joint
supply OR appliance supply). Not named: **showers and tubs** (rigid supply, no slip joint, not an
appliance), and **WCs** (a braided or flexible connector is not a slip joint). So code does not
literally require a stop at them in a trunk-and-branch system; WC stops are the owner's choice
(flood emergency). This is my reading of the words; I found no AHJ or DLI statement either way,
and many inspectors expect a stop at every fixture. In a PARALLEL system the sentence "valve
immediately ahead of each fixture or at the manifold" covers every fixture, showers and WCs
included.

**4. "Readily accessible" manifold?** Direct access with no panel, door or similar obstruction
to remove. A manifold behind a screwed access panel, in a cabinet, or in a ceiling/attic/crawl
is "accessible" but NOT "readily accessible", so 606.5 then requires a separate shutoff
immediately ahead of EVERY fixture and appliance it serves (the port no longer counts). 606.6
separately requires the required valve itself to be "accessible". Open on a mechanical-room
wall, reachable without moving anything, qualifies. A room door to a mechanical room is not what
the definition has in mind (it speaks of the equipment's own obstruction), but that is my
reading, not text.

## 3. Rule for `mep.fixture_control_valve`

Grade each water-supplied connection (fixture or appliance supply, per supply: hot and cold):

1. **Needs a SHUTOFF immediately ahead** (nothing between the valve and the connection but pipe)
   when it is: an appliance (washer box, dishwasher, icemaker/RO/fridge, water heater cold
   stop); or a slip-joint / exposed fixture supply (lav, sink); or served by a manifold that
   is not readily accessible. "Immediately ahead" = no tee between valve and connection.
2. **A manifold port suffices** only if all hold: the manifold is a parallel (home-run)
   distribution; the port carries a valve (the manifold type declares valved outlets); the port
   is labelled with the fixture it feeds; the manifold sits where nothing must be removed to
   reach it (`readily accessible`), and not in an attic, crawl space or enclosed cavity.
   **Parallel** (reading, not text): a home-run manifold, every outlet run feeding one
   fixture with no tee. A branch header whose outlets tee (catlin's LF2821050 hot header,
   2026-11-10) is part of a trunk-and-branch system, so rule 4's exemptions hold on it.
3. **One port, one fixture.** A port serving several fixtures does NOT satisfy 606.5 (FAIL, or
   UNKNOWN if the label cannot be read from the model); give a stopless sink or lav its own port
   per supply.
4. **Exempt** (no code stop): shower/tub supplies and WC supplies on trunk-and-branch. WC stops
   are kept for owner reasons and are not required. On a parallel supply they still need a
   port.
5. N/A only with no lav, sink or appliance fixture and no supply runs; such fixtures with no
   runs to walk are UNKNOWN. An inaccessible manifold means every downstream connection needs
   its own stop.

Implementation proxies (judgement, not text): "readily accessible" is read as "a room that is
not `unconditioned` owns the manifold", and a port's label as the one fixture its run feeds.
Neither sees an access panel or a cabinet door, so a valved manifold behind one would PASS.

Cite "UPC 606.5 / 606.6 (MN Rules 4714.0050, not amended)". CODE; redundant series stops are
the separate `advisory.redundant_isolation` preference.

## Sources and limits

Primary: IAPMO 2018 UPC e-pub; MN Rules 4714 full chapter (revisor.mn.gov). Cross-checks that
agree word for word: Clark County NV guideline (2018 UPC 606.5); 2025 CPC 606.5-606.7 and §203.0
(gocodebook.com; adds 606.5.1). Not found: any IAPMO interpretation or MN DLI bulletin on
manifold valves or room-group ports; answers marked "reading" are mine.
