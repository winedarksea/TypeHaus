# haus: editable
# Per-window stool overrides (2026-10-16). MW-STANDARD (plan/millwork.py) derives every
# in-scope stool as bought white oak, 5/4 dressed to 1"; a WindowStool here replaces the
# derived one where the room's colour or its moisture calls for another species. Each copies
# the standard's 1" thickness, 3/4" overhang and 1" horn, and leaves depth derived.
# The living room's east three are in plan/living_east_run.py (ash, flush with the slab).

from typehaus.model import WindowStool, inch


MAIN_WINDOW_STOOLS = [
    # Wet rooms, splash and snowmelt: black locust.
    WindowStool(uid="5STRZYV0G0", tag="STOOL-WIN-M-BATH1-W", window_ref="WIN-M-BATH1-W",
                material_ref="locust-stool-5q", thickness=inch(1),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    WindowStool(uid="YMJS812EK0", tag="STOOL-WIN-M-BATH2", window_ref="WIN-M-BATH2",
                material_ref="locust-stool-5q", thickness=inch(1),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    WindowStool(uid="Z9XJDD5SWM", tag="STOOL-WIN-M-KIT-E", window_ref="WIN-M-KIT-E",
                material_ref="locust-stool-5q", thickness=inch(1),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    WindowStool(uid="GZZ0Y78PY1", tag="STOOL-WIN-M-KITCH-N", window_ref="WIN-M-KITCH-N",
                material_ref="locust-stool-5q", thickness=inch(1),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    WindowStool(uid="G8JF6NTB0Q", tag="STOOL-WIN-M-MUD", window_ref="WIN-M-MUD",
                material_ref="locust-stool-5q", thickness=inch(1),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    # The living room's south pair: ash, like the east three and the counters.
    WindowStool(uid="4ECA4GNDDF", tag="STOOL-WIN-M-LIV-S1", window_ref="WIN-M-LIV-S1",
                material_ref="ash-stool-5q", thickness=inch(1),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    WindowStool(uid="REW7HFTZ1B", tag="STOOL-WIN-M-LIV-S2", window_ref="WIN-M-LIV-S2",
                material_ref="ash-stool-5q", thickness=inch(1),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
]

SECOND_WINDOW_STOOLS = [
    # Wet rooms: black locust.
    WindowStool(uid="THJZEDDZZ7", tag="STOOL-WIN-S-BATH-W", window_ref="WIN-S-BATH-W",
                material_ref="locust-stool-5q", thickness=inch(1),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    WindowStool(uid="0XZM97P9X9", tag="STOOL-WIN-S-VANITY-W", window_ref="WIN-S-VANITY-W",
                material_ref="locust-stool-5q", thickness=inch(1),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    # The suite, beside its cherry headboard band and cherry base.
    WindowStool(uid="0P47Q0SJ09", tag="STOOL-WIN-S-SUITE1", window_ref="WIN-S-SUITE1",
                material_ref="cherry-stool-5q", thickness=inch(1),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    WindowStool(uid="5YJ6CA2KGS", tag="STOOL-WIN-S-SUITE2", window_ref="WIN-S-SUITE2",
                material_ref="cherry-stool-5q", thickness=inch(1),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    # Circulation, beside the red-oak treads and floor.
    WindowStool(uid="BM3PZ9E8YP", tag="STOOL-WIN-S-HALL-N", window_ref="WIN-S-HALL-N",
                material_ref="red-oak-stool", thickness=inch(1),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
    WindowStool(uid="V36FYER5MV", tag="STOOL-WIN-S-STAIR-N", window_ref="WIN-S-STAIR-N",
                material_ref="red-oak-stool", thickness=inch(1),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
]

# WIN-B-SAUNA sits on SAUNA_LINER_ON_GARDEN_FRAMED, outside MW-STANDARD's scope, so it is
# authored. Clear cedar heartwood, unfinished, 1/8" off the glass so condensate drains:
# low density reads cool at 190 F where locust, oak and cherry read hot.
BASEMENT_WINDOW_STOOLS = [
    WindowStool(uid="60X3KRP792", tag="STOOL-WIN-B-SAUNA", window_ref="WIN-B-SAUNA",
                material_ref="cedar-sauna-stool", thickness=inch(1),
                overhang=inch(0.75), horn=inch(1), profile="eased"),
]
