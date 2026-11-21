"""Frosted A19 LED profiles, in inches along the socket axis."""

# The reference socket face is at 2.50 in. Shift the profiles to seat the same bulb
# on a shallower holder. The A19 diffuser is 19/8 in. across at its widest point.
A19_REFERENCE_SOCKET_FACE_IN = 2.50
LED_BASE_PROFILE = (
    (0, 3.64), (.74, 3.64), (.72, 3.51), (.63, 3.20), (.56, 2.96), (.56, 2.59),
    (.52, 2.56), (0, 2.56),
)
DIFFUSER_PROFILE = (
    (0, 5.50), (.23, 5.49), (.45, 5.45), (.66, 5.37), (.85, 5.25), (1.01, 5.08),
    (1.12, 4.88), (1.18, 4.65), (1.1875, 4.48), (1.16, 4.29), (1.09, 4.11),
    (.98, 3.94), (.85, 3.77), (.74, 3.64), (0, 3.64),
)

