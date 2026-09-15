"""The structural-hardware catalog and the rules that select from it — a leaf package.

What a Simpson part *is* (its role, its allowable, the report the number was read out of)
and the named spacings a derivation applies are facts about products and rules, not about
this building. They were born in ``takeoff/`` and a take-off is only one of their readers:
``checks/structural``, ``emit/draw``, ``joints/`` and ``schedule/handoff`` all ask the same
questions, and none of them wants a bill of materials.

So this package is a **leaf**: it imports the standard library and ``typehaus.library``
(lazily, for the catalog items) and nothing else in the engine. Nothing here may reach for
``model``, ``resolve``, ``checks`` or ``takeoff``. ``tests/test_package_leaves.py`` walks
the imports and fails on a violation.
"""
