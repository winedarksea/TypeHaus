"""Catlin MEP — the storey element lists the manifest consumes.

The 2,515-line original was split by system (AGENTS.md §1.1 keeps files under 500 lines):

- ``plan/mep_sleeves.py``        — concrete penetrations: sleeves, slab stubs
- ``plan/mep_drainage.py``       — waste and condensate runs, TPR discharge, radon sump
- ``plan/mep_venting.py``        — vent branches, the shared riser and its clamps
- ``plan/mep_supply.py``         — house entry, hot/cold distribution, hydrant branches
- ``plan/mep_supply_devices.py`` — in-line valves, stops and arrestors
- ``plan/mep_hvac.py``           — System 1's conditioned-air chase, equipment, terminal types
- ``plan/mep_erv.py``            — the ERV as placed: manifolds, mixing box, hoods, the four
  chase risers and the twenty-two semi-rigid radials
- ``plan/mep_erv_types.py``      — the ERV catalog: the Broan, the two manifold sizes, the
  mixing box, the exterior hood, the over-bench capture hood
- ``plan/mep_registers.py``      — the air terminals themselves, storey by storey
- ``plan/mep_electrical.py``     — panel, per-storey devices, exterior boxes and clamps

Those eight are ``# haus: editable``; this file is not, and must not become so — the dialect
forbids ``from plan import ...``, which is exactly what an aggregator needs. It authors no
element of its own, so the writeback rule (which binds files that *declare* UI-movable
elements) does not reach it.

The lists below are the originals with a module prefix added and one entry per line, so
element order — and therefore model.json — is unchanged.
"""

from __future__ import annotations

from plan import (mep_drainage, mep_electrical, mep_erv, mep_erv_types, mep_hvac,
                  mep_registers, mep_sleeves, mep_supply, mep_supply_devices, mep_venting)

# Catalogs, re-exported so ``manifest.py``'s Library(...) call is untouched by the split.
REGISTER_TYPES = (*mep_hvac.REGISTER_TYPES, *mep_erv_types.REGISTER_TYPES_ERV)
EQUIPMENT_TYPES = (*mep_hvac.EQUIPMENT_TYPES, *mep_erv_types.EQUIPMENT_TYPES_ERV)
ELECTRICAL_DEVICE_TYPES = mep_electrical.ELECTRICAL_DEVICE_TYPES

MAIN_ELEMENTS = [*mep_sleeves.SLEEVES,
                 *mep_sleeves.SUPPLY_SLEEVES,
                 *mep_sleeves.STACK_SLEEVES,
                 *mep_drainage.SECOND_DRAINS,
                 *mep_drainage.CONDENSATE_MAIN,
                 *mep_drainage.LAUNDRY_MAIN,
                 *mep_venting.VENT_BRANCHES_MAIN,
                 *mep_electrical.MAIN_DEVICES,
                 *mep_supply.WATER_SUPPLY,
                 *mep_sleeves.GARAGE_SLEEVES,
                 *mep_supply.HYDRANT_BRANCH_MAIN,
                 *mep_supply.KITCHEN_STUB_MAIN,
                 *mep_supply_devices.SUPPLY_DEVICES_MAIN,
                 *mep_supply_devices.SUPPLY_DEVICES_GARAGE,
                 *mep_hvac.DUCTS_MAIN,
                 *mep_erv.EQUIPMENT_ERV_MAIN,
                 *mep_erv.DUCTS_ERV_RISERS,
                 *mep_registers.REGISTERS_MAIN]

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
                     *mep_drainage.RADON_SUMP,
                     *mep_venting.VENT_RISERS,
                     *mep_venting.VENT_CLAMPS,
                     *mep_hvac.DUCTS_BASEMENT,
                     *mep_erv.EQUIPMENT_ERV_BASEMENT,
                     *mep_erv.DUCTS_ERV_BASEMENT,
                     *mep_registers.REGISTERS_BASEMENT]
SECOND_ELEMENTS = [*mep_hvac.DUCTS,
                   *mep_erv.EQUIPMENT_ERV_SECOND,
                   # Filed here, not on `main`, though their manifolds hang in RM-M-MECH one
                   # storey down: these run in FS-S-WEST's cavity and the bay check matches a
                   # segment against sibling floors ON THE DUCT'S OWN STOREY.
                   *mep_erv.DUCTS_ERV_LEVEL2,
                   *mep_hvac.DUCTS_HVAC_SECOND,
                   *mep_registers.REGISTERS,
                   *mep_registers.REGISTERS_SECOND,
                   *mep_registers.REGISTERS_HVAC_SECOND,
                   *mep_venting.VENT_BRANCHES_SECOND,
                   *mep_electrical.SECOND_DEVICES,
                   *mep_supply.HYDRANT_BRANCH_SECOND,
                   *mep_supply_devices.SUPPLY_DEVICES_SECOND]
ATTIC_ELEMENTS = [*mep_erv.EQUIPMENT_ERV_ATTIC,
                  *mep_erv.EQUIPMENT_ERV_HOODS,
                  *mep_erv.DUCTS_ERV_ATTIC,
                  *mep_erv.DUCTS_ERV_MIX_FEED,
                  *mep_electrical.NEMA_BOX,
                  *mep_electrical.NEMA_CLAMP,
                  *mep_electrical.LEADER_CLAMPS,
                  *mep_electrical.ATTIC_DEVICES,
                  *mep_hvac.DUCTS_ATTIC,
                  *mep_hvac.DUCTS_HVAC_ATTIC,
                  *mep_registers.REGISTERS_ATTIC,
                  *mep_registers.REGISTERS_HVAC_ATTIC]
