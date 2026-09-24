"""Catlin MEP — the storey element lists the manifest consumes.

The 2,515-line original was split by system (AGENTS.md §1.1 keeps files under 500 lines):

- ``plan/mep_sleeves.py``        — concrete penetrations: sleeves, slab stubs
- ``plan/mep_drainage.py``       — waste and condensate runs, TPR discharge, radon sump
- ``plan/mep_venting.py``        — vent branches, the shared riser and its clamps
- ``plan/mep_supply.py``         — house entry, hot/cold distribution, hydrant branches
- ``plan/mep_supply_devices.py`` — in-line valves, stops and arrestors
- ``plan/mep_supply_plant.py``   — RM-S-PLANT's watering stub and the balcony hydrant sleeve
- ``plan/mep_hvac.py``           — System 1's conditioned-air chase, equipment, terminal types
- ``plan/mep_hvac_branches.py``  — System 1's bedroom branches: a riser and a bay leg each
- ``plan/mep_erv_l1.py``         — the ERV system header (the machine, the home-run
  argument, the routing declarations), the basement plenums and their six radials
- ``plan/mep_erv_l2.py``         — the two RM-M-MECH plenums and the thirteen FS-S-WEST radials
- ``plan/mep_erv_l3.py``         — the attic plenum, the mixing box and the FS-ATTIC radials
- ``plan/mep_erv_outdoor.py``    — the two north-facade hoods and their wall penetrations
- ``plan/mep_erv_risers.py``     — the three chase risers and the two outdoor legs
- ``plan/mep_erv_types.py``      — the ERV catalog: the Broan, the two manifold sizes, the
  mixing box, the exterior hood, the over-bench capture hood
- ``plan/mep_registers.py``      — the air terminals themselves, storey by storey
- ``plan/mep_electrical.py``     — panel, per-storey devices, exterior boxes and clamps

Those sixteen are ``# haus: editable``; this file is not, and must not become so — the dialect
forbids ``from plan import ...``, which is exactly what an aggregator needs. It authors no
element of its own, so the writeback rule (which binds files that *declare* UI-movable
elements) does not reach it.

The lists below are the originals with a module prefix added and one entry per line, so
element order — and therefore model.json — is unchanged.
"""

from __future__ import annotations

from plan import (mep_drainage, mep_electrical, mep_erv_l1, mep_erv_l2, mep_erv_l3,
                  mep_erv_outdoor, mep_erv_risers, mep_erv_types, mep_hvac, mep_hvac_branches,
                  mep_registers, mep_sleeves, mep_supply, mep_supply_devices, mep_supply_plant,
                  mep_venting)

# Catalogs, re-exported so ``manifest.py``'s Library(...) call is untouched by the split.
REGISTER_TYPES = (*mep_hvac.REGISTER_TYPES, *mep_erv_types.REGISTER_TYPES_ERV)
EQUIPMENT_TYPES = (*mep_hvac.EQUIPMENT_TYPES, *mep_erv_types.EQUIPMENT_TYPES_ERV)
ELECTRICAL_DEVICE_TYPES = mep_electrical.ELECTRICAL_DEVICE_TYPES

MAIN_ELEMENTS = [*mep_sleeves.SLEEVES,
                 *mep_sleeves.SUPPLY_SLEEVES,
                 *mep_sleeves.STACK_SLEEVES,
                 *mep_drainage.SECOND_DRAINS,
                 *mep_drainage.SECOND_BRANCH_DRAINS,
                 *mep_drainage.STUDIO_DRAINS,
                 *mep_supply.STUDIO_SUPPLY,
                 *mep_drainage.CONDENSATE_MAIN,
                 *mep_drainage.LAUNDRY_MAIN,
                 *mep_venting.VENT_BRANCHES_MAIN,
                 *mep_electrical.MAIN_DEVICES,
                 *mep_supply.WATER_SUPPLY,
                 *mep_supply.HYDRANT_BRANCH_MAIN,
                 *mep_supply.KITCHEN_STUB_MAIN,
                 *mep_supply_plant.PLANT_STUB_MAIN,
                 # The hole FX-M-PORCH-HYD's barrel goes through. A PipeAccessory
                 # bills the escutcheon but resolves no void, so the wall carried
                 # none — the same gap AO-M-ERV-OA answers for the ERV hood.
                 *mep_supply.PENETRATIONS_HYDRANT_MAIN,
                 *mep_supply_devices.SUPPLY_DEVICES_MAIN,
                 *mep_hvac.DUCTS_MAIN,
                 *mep_erv_l2.EQUIPMENT_ERV_MAIN,
                 # The outdoor-air INTAKE hood, on the west face of RM-M-MECH. Filed on a
                 # different storey from its EXHAUST partner because the pair is stacked,
                 # which is what makes it legal without ten feet of facade.
                 *mep_erv_outdoor.EQUIPMENT_ERV_HOODS_MAIN,
                 # The hole that hood sits over. A RoughOpening, because an Equipment
                 # placeable resolves no solid and the wall carried no void — see the
                 # penetration note in mep_erv_outdoor.py.
                 *mep_erv_outdoor.PENETRATIONS_ERV_MAIN,
                 *mep_erv_risers.DUCTS_ERV_RISERS,
                 *mep_registers.REGISTERS_MAIN]

# ** THE GARAGE'S MEP AT THE MAIN DATUM, NOT THE HOUSE'S (2026-09-13). ** These two rode in
# ``MAIN_ELEMENTS`` because that was the only storey at 0'-0" and a storey key was carrying
# both "which level" and "which structure". They belong to the GARAGE, and now say so: the
# manifest files them on ``g-deck``, the garage's own level at the main datum.
#
# The datum is the point. ``g-deck.elevation`` is ``main_deck.MAIN_DATUM`` — the same constant
# object ``main`` reads — so nothing moves. Filing them on the ``garage`` storey instead would
# have been the obvious move and a silent 1'-0" error: a ``PipeRun``'s inverts are
# storey-relative while a ``ConduitRun``'s are absolute, the garage storey sits at -1'-0", and
# no check in the repo grades a sleeve's absolute invert against anything.
GARAGE_DECK_ELEMENTS = [*mep_sleeves.GARAGE_SLEEVES,
                        *mep_supply_devices.SUPPLY_DEVICES_GARAGE]

BASEMENT_ELEMENTS = [*mep_drainage.DRAINS,
                     *mep_drainage.CONDENSATE,
                     *mep_drainage.ERV_CONDENSATE,
                     *mep_drainage.TPR_DISCHARGE,
                     *mep_supply.SUPPLY,
                     *mep_supply.HYDRANT_BRANCH_BASEMENT,
                     *mep_supply_devices.SUPPLY_DEVICES_BASEMENT,
                     *mep_supply_devices.SUPPLY_STOPS,
                     *mep_sleeves.WALL_SLEEVES,
                     *mep_sleeves.SLAB_STUBS,
                     *mep_venting.VENT_BRANCHES_BASEMENT,
                     *mep_hvac.EQUIPMENT,
                     *mep_electrical.PANEL,
                     *mep_electrical.BASEMENT_DEVICES,
                     *mep_drainage.RADON_SUMP, *mep_drainage.SUMP_DISCHARGE,
                     *mep_venting.VENT_RISERS,
                     *mep_venting.VENT_CLAMPS,
                     *mep_hvac.DUCTS_BASEMENT,
                     *mep_erv_l1.EQUIPMENT_ERV_BASEMENT,
                     *mep_erv_l1.DUCTS_ERV_BASEMENT,
                     *mep_registers.REGISTERS_BASEMENT]
SECOND_ELEMENTS = [*mep_hvac.DUCTS,
                   *mep_erv_l3.EQUIPMENT_ERV_SECOND,
                   # The stale-air DISCHARGE hood, 13 ft over the intake.
                   *mep_erv_outdoor.EQUIPMENT_ERV_HOODS_SECOND,
                   *mep_erv_outdoor.PENETRATIONS_ERV_SECOND,
                   # Filed here, not on `main`, though their manifolds hang in RM-M-MECH one
                   # storey down: these run in FS-S-WEST's cavity and the bay check matches a
                   # segment against sibling floors ON THE DUCT'S OWN STOREY.
                   *mep_erv_l2.DUCTS_ERV_LEVEL2,
                   *mep_hvac.DUCTS_HVAC_SECOND,
                   *mep_hvac_branches.DUCTS_HVAC_BRANCHES_SECOND,
                   *mep_registers.REGISTERS,
                   *mep_registers.REGISTERS_SECOND,
                   *mep_registers.REGISTERS_HVAC_SECOND,
                   *mep_venting.VENT_BRANCHES_SECOND,
                   *mep_electrical.SECOND_DEVICES,
                   *mep_supply.HYDRANT_BRANCH_SECOND,
                   *mep_supply.PENETRATIONS_HYDRANT_SECOND,
                   *mep_supply_devices.SUPPLY_DEVICES_SECOND,
                   *mep_supply_plant.PLANT_STUB_DEVICES_SECOND,
                   *mep_supply_plant.HYDRANT_SLEEVE_SECOND]
ATTIC_ELEMENTS = [*mep_venting.VENT_BRANCHES_ATTIC,
                  # STUDIO_SUPPLY and STUDIO_DRAINS are NOT here — both are filed on `main`
                  # with the rest of the project-frame plumbing (see MAIN_ELEMENTS). Only the
                  # two accessible stops, which really do stand on the attic deck, stay.
                  *mep_supply_devices.STUDIO_SUPPLY_DEVICES,
                  *mep_erv_l3.EQUIPMENT_ERV_ATTIC,
                  *mep_erv_l3.DUCTS_ERV_ATTIC,
                  *mep_erv_l3.DUCTS_ERV_MIX_FEED,
                  *mep_electrical.NEMA_BOX,
                  *mep_electrical.NEMA_CLAMP,
                  *mep_electrical.LEADER_CLAMPS,
                  *mep_electrical.ATTIC_DEVICES,
                  *mep_hvac.DUCTS_ATTIC,
                  *mep_hvac.DUCTS_HVAC_ATTIC,
                  *mep_registers.REGISTERS_ATTIC,
                  *mep_registers.REGISTERS_HVAC_ATTIC]
