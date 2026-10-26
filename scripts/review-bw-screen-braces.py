"""Draw the thin-brick screen brace study; run with .venv/bin/python.

Drawing datums follow canopy_west_band.md §1/§3a and the finish comparison.
Alternative brace faces are visual envelopes, not engineered substitutions.
"""
from __future__ import annotations

import html
import math
import runpy
from pathlib import Path
from types import SimpleNamespace

from typehaus.resolve.slat_cuts import clipped_slat_profile

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / 'plans/assets/bw-screen-brace-comparison.svg'
FINISH = runpy.run_path(str(ROOT / 'houses/catlin/plan/entry_screen_finish_spec.py'))

# Inches, measured south-to-north from the lower screen's south edge.
GEOMETRY = SimpleNamespace(
    run=78.875, post_south=10.25, post_north=70.0, post_face=5.5,
    panel_top=48.0, header_soffit=76.125, header_top=88.0,
    header_south=1.375, header_length=77.5, plate_face=1.5,
    bay_width=24.375, bay_height=25.125, slat_face=1.5, slat_gap=2.25,
    scale=5.0, deck_y=600.0, screen_x=53.0,
    stair_rise=6.6, stair_treads=4, stair_projection_x=10.0,
    stair_projection_y=5.0, landing_projection_x=22.0, landing_projection_y=10.0,
)
COLORS = SimpleNamespace(ink='#2c3031', muted='#646b68', wood='#b88c57',
                         wood_edge='#86613c', mortar='#98958e')
parts = []


def emit(markup):
    parts.append(markup)


def text(x, y, value, size=15, color=COLORS.ink, weight=400):
    emit(f'<text x="{x}" y="{y}" font-size="{size}" fill="{color}" '
         f'font-weight="{weight}">{html.escape(value)}</text>')


def rect(x, y, width, height, fill, stroke='none', extra=''):
    emit(f'<rect x="{x}" y="{y}" width="{width}" height="{height}" '
         f'fill="{fill}" stroke="{stroke}" {extra}/>')


def polygon(points, fill, stroke=COLORS.wood_edge):
    emit('<polygon points="' + ' '.join(f'{x:.3f},{y:.3f}' for x, y in points)
         + f'" fill="{fill}" stroke="{stroke}" stroke-width="0.7"/>')


def point(u, z):
    return GEOMETRY.screen_x + u * GEOMETRY.scale, GEOMETRY.deck_y - z * GEOMETRY.scale


def member(u, z, width, height, fill='url(#wood)'):
    x, y = point(u, z + height)
    rect(x, y, width * GEOMETRY.scale, height * GEOMETRY.scale, fill)


def brace_bays(option):
    geometry = GEOMETRY
    bay_bottom = geometry.panel_top + geometry.plate_face
    bay_left = geometry.post_south + geometry.post_face / 2
    bay_right = geometry.post_north - geometry.post_face / 2
    layout = SimpleNamespace(width=geometry.bay_width, height=geometry.bay_height)
    pitch = (geometry.slat_face + geometry.slat_gap) * math.sqrt(2)
    indices = range(-3, 4) if option == 0 else (0,)
    face = geometry.slat_face if option < 2 else 3.5
    for bay in range(2):
        for index in indices:
            slat = SimpleNamespace(c=(layout.width - layout.height) / 2 + index * pitch)
            ring = clipped_slat_profile(slat, layout, face)
            if option != 0:
                # The bays are slightly taller than wide: use their actual corner axis.
                slope = layout.height / layout.width
                half_vertical = face * math.sqrt(1 + slope * slope) / 2
                horizontal_inset = half_vertical / slope
                ring = ((0, 0), (horizontal_inset, 0),
                        (layout.width, layout.height - half_vertical),
                        (layout.width, layout.height),
                        (layout.width - horizontal_inset, layout.height),
                        (0, half_vertical))
            polygon([point(bay_left + u if bay == 0 else bay_right - u,
                           bay_bottom + z) for u, z in ring], 'url(#wood)')
    member(bay_left + layout.width, bay_bottom, geometry.post_face, layout.height)
    member(bay_left, geometry.panel_top, bay_right - bay_left, geometry.plate_face)
    member(bay_left, geometry.header_soffit - geometry.plate_face,
           bay_right - bay_left, geometry.plate_face)


def stairs():
    geometry = GEOMETRY
    left, top = point(0, 0)
    right, _ = point(geometry.run, 0)
    dx, dy = geometry.landing_projection_x, geometry.landing_projection_y
    polygon([(left, top), (right, top), (right + dx, top + dy),
             (left + dx, top + dy)], '#d5d2c7', '#8f948b')
    left += dx
    right += dx
    top += dy
    rise = geometry.stair_rise * geometry.scale
    for _ in range(geometry.stair_treads):
        polygon([(left, top), (right, top), (right, top + rise),
                 (left, top + rise)], '#b1b7ac', '#858d82')
        polygon([(right, top), (right + 10, top + 5),
                 (right + 10, top + rise + 5), (right, top + rise)], '#959d90', '#858d82')
        top += rise
        polygon([(left, top), (right, top), (right + 10, top + 5),
                 (left + 10, top + 5)], '#d1d5c9', '#858d82')
        left += geometry.stair_projection_x
        right += geometry.stair_projection_x
        top += geometry.stair_projection_y
    polygon([(left, top), (right, top), (right, top + rise),
             (left, top + rise)], '#b1b7ac', '#858d82')


def panel(index, title, subtitle, notes):
    emit(f'<g transform="translate({30 + index * 570},120)">')
    rect(0, 0, 550, 855, '#fffdf8', '#d9d4c9', 'rx="10"')
    text(24, 33, title, 21, weight=700)
    text(24, 59, subtitle, 14, COLORS.muted)
    member(-6, 0, 5, GEOMETRY.header_top, '#eae8e1')
    member(GEOMETRY.run, 0, 5, GEOMETRY.header_top, '#e4e6df')
    for post in (GEOMETRY.post_south, GEOMETRY.post_north):
        member(post - GEOMETRY.post_face / 2, 0, GEOMETRY.post_face,
               GEOMETRY.header_soffit)
    brace_bays(index)
    member(GEOMETRY.header_south, GEOMETRY.header_soffit,
           GEOMETRY.header_length, GEOMETRY.header_top - GEOMETRY.header_soffit)
    member(0, -1, GEOMETRY.run, GEOMETRY.panel_top + 1, '#343b39')
    member(0, FINISH['FINISH_BOTTOM_IN'], GEOMETRY.run,
           FINISH['FINISH_TOP_IN'] - FINISH['FINISH_BOTTOM_IN'], 'url(#brick)')
    member(0, FINISH['FINISH_TOP_IN'], GEOMETRY.run, .5, '#515855')
    stairs()
    text(53, 809, '78⅞″ screen run  ·  +48″ lower wall', 14, COLORS.muted)
    text(53, 832, 'Same landing / five risers in every view', 14, COLORS.muted)
    emit('</g>')
    for row, note in enumerate(notes):
        text(54 + index * 570, 1010 + row * 25, note, 15)


def main():
    emit('<svg xmlns="http://www.w3.org/2000/svg" width="1740" height="1190" '
         'viewBox="0 0 1740 1190" role="img" aria-labelledby="title desc">')
    emit('<title id="title">W-BW-SCREEN — thin brick, three brace treatments</title>')
    emit('<desc id="desc">Matched east elevations: fourteen current slats, two slender '
         'corner-to-corner knee braces, and two wider corner-to-corner knee braces. Brown thin brick remains '
         'identical. Centre post and band plates remain. Alternatives need structural design.</desc>')
    brick_width = FINISH['BRICK_LENGTH_IN'] * GEOMETRY.scale
    brick_height = FINISH['BRICK_HEIGHT_IN'] * GEOMETRY.scale
    brick_pitch = brick_width + FINISH['MORTAR_JOINT_IN'] * GEOMETRY.scale
    course_pitch = brick_height + FINISH['MORTAR_JOINT_IN'] * GEOMETRY.scale
    emit('<defs><pattern id="wood" width="22" height="100" patternUnits="userSpaceOnUse">'
         '<rect width="22" height="100" fill="#b88c57"/>'
         '<path d="M5 0Q13 26 6 54T8 100M17 0Q10 40 18 76T16 100" '
         'fill="none" stroke="#946f43" stroke-width=".6" opacity=".55"/></pattern>')
    emit(f'<pattern id="brick" width="{brick_pitch}" height="{course_pitch * 2}" '
         'patternUnits="userSpaceOnUse">')
    rect(0, 0, brick_pitch, course_pitch * 2, COLORS.mortar)
    for row in range(2):
        for column in range(-1, 2):
            rect(column * brick_pitch + row * brick_pitch / 2, row * course_pitch,
                 brick_width, brick_height, '#79503b' if row == 0 else '#895e45')
    emit('</pattern></defs><g font-family="Arial, Helvetica, sans-serif">')
    rect(0, 0, 1740, 1190, '#f3f1eb')
    text(30, 45, 'W-BW-SCREEN  /  KEEP THE BRICK. SIMPLIFY THE BRACES.', 29, weight=700)
    text(30, 77, 'East-face comparison · 2026-10-25 · south left / garage right · matched scale', 17)
    text(30, 103, 'Brown thin brick + grey joints throughout. Roof, rails and open door omitted for clarity; hardware is on the west face.', 15, COLORS.muted)
    panel(0, 'A  /  CURRENT SLAT BAND', '7 slats per bay · 1½″ visible edge',
          ['Fine chevron rhythm; 14 pieces total.', 'Retains the current structural scheme.',
           '6 rated braces + 1 infill slat per bay.'])
    panel(1, 'B  /  ONE SLENDER KNEE EACH SIDE', '2 braces total · same 1½″ visible edge',
          ['Much more open; the braces read lightly.', 'Corner-to-corner knees, rising inward.',
           'Current force-sharing check does not apply.'])
    panel(2, 'C  /  ONE WIDER KNEE EACH SIDE', '2 braces total · 3½″ face study / depth TBD',
          ['Stronger visual balance with brick + posts.', 'Same brace axes as B; heavier face only.',
           'Section and both end joints need design.'])
    text(30, 1130, 'Visual preference: C. Keep the centre post and plates for this comparison; removing them would be a separate frame study.', 17, weight=700)
    text(30, 1160, 'The wider face is a design envelope, not a specified 4×4 or a capacity claim. No structural model changes. See companion study for sources.', 15, COLORS.muted)
    emit('</g></svg>')
    OUTPUT.write_text('\n'.join(parts) + '\n')
    print(OUTPUT)


if __name__ == '__main__':
    main()
