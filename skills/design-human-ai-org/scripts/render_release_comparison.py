#!/usr/bin/env python3
"""Render a bounded current/proposed release-authority comparison offline."""
from __future__ import annotations
import argparse
import html
import json
import textwrap
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
INK = '#20354b'
MUTED = '#607083'
ORANGE = '#bd612b'
TEAL = '#167b7a'


def esc(value):
    return html.escape(str(value), quote=True)


def validate(data):
    if not isinstance(data, dict):
        return ['Input must be an object.']
    errors = []
    for key in ('title', 'subtitle', 'initiative', 'rule_owner', 'eligible_change_label', 'human_approval_scope', 'rule_owner_note'):
        if not isinstance(data.get(key), str) or not data[key].strip():
            errors.append(f'{key} must be non-empty text.')
    for key in ('eligible_approvers', 'unresolved'):
        if not isinstance(data.get(key), list) or not all(isinstance(v, str) and v.strip() for v in data.get(key, [])):
            errors.append(f'{key} must be a list of non-empty text.')
    if isinstance(data.get('eligible_approvers'), list) and not data['eligible_approvers']:
        errors.append('At least one eligible approver must be recorded.')
    return errors


def lines(value, width):
    result = []
    for paragraph in str(value).splitlines() or ['']:
        result.extend(textwrap.wrap(paragraph, width=width, break_long_words=True, break_on_hyphens=False) or [''])
    return result


def text(value, x, y, width=60, size=16, colour=INK, weight=400, anchor='start', line_height=None):
    wrapped = lines(value, width)
    lh = line_height or size * 1.35
    spans = ''.join(f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{esc(line)}</tspan>' for i, line in enumerate(wrapped))
    return f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{colour}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{weight}">{spans}</text>'


def icon(name, x, y, size=40, colour=ORANGE):
    element = ET.fromstring((ROOT / 'assets' / 'sketchyicons' / f'{name}.svg').read_text())
    paths = ''.join(f'<path d="{esc(child.attrib["d"])}"/>' for child in element if child.tag.endswith('path'))
    return f'<g transform="translate({x} {y}) scale({size / 24})" fill="none" stroke="{colour}" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">{paths}</g>'


def human(x, y, radius=35):
    return f'<circle cx="{x}" cy="{y}" r="{radius}" fill="#fff2e6" stroke="#dda47c" stroke-width="1.5"/>' + icon('user-round', x - 21, y - 23, 42)


def hybrid(x, y):
    return human(x - 28, y, 30) + text('+', x + 12, y + 6, size=20, colour=MUTED, anchor='middle') + f'<rect x="{x + 29}" y="{y - 29}" width="60" height="58" rx="14" fill="#e9f6f4" stroke="#8bbfba" stroke-width="1.5"/>' + icon('bot', x + 39, y - 20, 40, TEAL)


def arrow(path, colour=INK, dashed=False):
    marker = 'teal-arrow' if colour == TEAL else 'ink-arrow'
    dash = ' stroke-dasharray="5 5"' if dashed else ''
    return f'<path d="{path}" fill="none" stroke="{colour}" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" marker-end="url(#{marker})"{dash}/>'


def render_svg(data):
    errors = validate(data)
    if errors:
        raise ValueError('\n'.join(errors))
    names = ', '.join(data['eligible_approvers'])
    provenance = (ROOT / 'assets' / 'sketchyicons' / 'NOTICE').read_text() + '\n' + (ROOT / 'assets' / 'sketchyicons' / 'LICENSE').read_text()
    current_names = lines(names, 37)
    right_names = lines(names, 24)
    boundary_lines = lines(data['eligible_change_label'], 34)
    # Content beyond the compact chart's available lines continues in a labelled
    # full-text section, rather than being silently cut or painted over a node.
    max_short = 3
    short_boundary = '\n'.join(boundary_lines[:max_short])
    if len(boundary_lines) > max_short:
        short_boundary = 'Chosen boundary\nFull wording below'
    current_people = '\n'.join(current_names) if len(current_names) <= 3 else 'Eligible human approvers\nFull list below'
    proposed_people = '\n'.join(right_names) if len(right_names) <= 2 else 'Eligible human approvers\nFull list below'
    owner_lines = lines(data['rule_owner'], 34)
    owner_label = '\n'.join(owner_lines) if len(owner_lines) <= 2 else 'Named human rule owner\nFull name below'
    title_lines = lines(data['title'], 67)
    title_label = '\n'.join(title_lines) if len(title_lines) <= 2 else 'Current and proposed release authority'
    parts = [f'''<svg xmlns="http://www.w3.org/2000/svg" width="1300" height="980" viewBox="0 0 1300 980" role="img" aria-labelledby="release-title release-desc"><title id="release-title">{esc(data['title'])}</title><desc id="release-desc">Current and proposed authority for {esc(data['initiative'])}. Current releases require independent human approval by an eligible person other than the maker. The proposal allows agent-only release within the chosen boundary after required checks pass. Other changes require independent human approval. Failed or uncertain checks confer no release permission; the response remains to be defined. Human reporting is unchanged.</desc><metadata>{esc(provenance)}</metadata><defs><marker id="ink-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M1 1 L9 5 L1 9" fill="none" stroke="{INK}" stroke-width="1.5"/></marker><marker id="teal-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M1 1 L9 5 L1 9" fill="none" stroke="{TEAL}" stroke-width="1.5"/></marker></defs><rect width="1300" height="980" fill="#fffdf9"/>''']
    parts += [text(title_label, 45, 49, width=67, size=29, weight=700), text('Scope: ' + data['initiative'], 45, 103, width=118, size=16, colour=MUTED)]
    parts += ['<path d="M45 141 H1255 M620 165 V818" fill="none" stroke="#dce1e3" stroke-width="1.2"/>', text('Current', 310, 184, size=24, weight=700, anchor='middle'), text('Proposed', 953, 184, size=24, weight=700, anchor='middle')]
    # Current route: all changes retain the existing independent human approval.
    parts += [hybrid(282, 276), text('Change prepared', 310, 339, size=20, weight=700, anchor='middle'), text('Human + agent', 310, 365, size=15, colour=MUTED, anchor='middle'), arrow('M310 385 V430'), human(310, 482, 40), text('Independent human approval', 310, 552, width=38, size=20, weight=700, anchor='middle'), text(current_people, 310, 582, width=37, size=16, anchor='middle'), text('The approver must be someone other than the maker.', 310, 655, width=49, size=14, colour=MUTED, anchor='middle'), arrow('M310 680 V707'), '<rect x="181" y="721" width="258" height="69" rx="34" fill="#f0f2f3" stroke="#c8d0d6"/>', text('Release', 310, 749, size=20, weight=700, anchor='middle'), text('Executor to confirm', 310, 773, size=14, colour=MUTED, anchor='middle')]
    # Proposed authority is defined by a human, with no invented policy executor.
    parts += [human(731, 248, 34), text(owner_label, 786, 238, width=34, size=18, weight=700), text('Owns the eligibility and check decisions', 786, 286, width=43, size=14, colour=MUTED), arrow('M731 284 V320 H681 V491 H798', TEAL, True), text('sets conditions', 696, 446, width=12, size=14, colour=TEAL)]
    parts += [hybrid(946, 353), text('Change prepared · Human + agent', 971, 406, size=15, anchor='middle'), arrow('M971 415 V429'), f'<path d="M970 432 L1135 492 L970 558 L805 492 Z" fill="#f7f7ef" stroke="#b7bcaa" stroke-width="1.5"/>', text(short_boundary, 970, 469 if len(lines(short_boundary,34)) > 1 else 480, width=34, size=14, weight=700, anchor='middle'), text('Required checks pass', 970, 528, size=14, colour=MUTED, anchor='middle')]
    parts += [arrow('M856 511 H777 V598',TEAL), text('Within the boundary', 706, 555, width=23, size=14, colour=TEAL, anchor='middle'), text('and checks pass', 706, 575, width=23, size=14, colour=TEAL, anchor='middle'), '<rect x="669" y="614" width="215" height="141" rx="25" fill="#eaf6f3" stroke="#6aa9a2" stroke-width="1.6"/>', icon('bot',748,631,56,TEAL), text('Agent only',777,712,size=20,weight=700,colour=TEAL,anchor='middle'), text('Release',777,738,size=18,colour=TEAL,anchor='middle')]
    parts += [arrow('M1098 506 H1169 V594'), text('Outside boundary',1088,553,width=19,size=14,anchor='middle'), human(1168,626,31), text('Human approval',1168,679,width=23,size=17,weight=700,anchor='middle'), text(proposed_people,1168,703,width=24,size=14,anchor='middle'), text('Someone other than the maker',1168,747,width=25,size=14,colour=MUTED,anchor='middle'), arrow('M1168 765 V783'), text('Release · executor to confirm',1168,809,width=24,size=14,anchor='middle')]
    parts += ['<path d="M45 841 H1255" stroke="#dce1e3" fill="none"/>', text('Failed or uncertain checks do not permit release.',45,871,size=17,weight=700), text('Who handles a failed or uncertain check, and how they respond, remains to be decided.',45,897,width=126,size=14,colour=MUTED)]
    parts += [icon('user-round',45,916,25), text('Human',80,936,size=14),icon('bot',169,916,25,TEAL),text('Agent',204,936,size=14),icon('user-round',287,916,25),text('+',318,936,size=16,colour=MUTED),icon('bot',336,916,25,TEAL),text('Human + agent',370,936,size=14),text('Arrows show authority and work sequence.',575,936,width=83,size=14,colour=MUTED),text('Human reporting remains the baseline. Agent counts are not specified.',45,963,width=110,size=14,colour=MUTED),text('Prepared by Dr. Shiva Kakkar',1000,963,width=37,size=14,colour=MUTED)]
    parts.append('</svg>')
    return ''.join(parts)


def render(data):
    svg = render_svg(data)
    css = (ROOT/'assets'/'release-comparison.css').read_text()
    names = ', '.join(data['eligible_approvers'])
    unresolved = ''.join(f'<li>{esc(value)}</li>' for value in data['unresolved'])
    notice = (ROOT/'assets'/'sketchyicons'/'NOTICE').read_text()
    license_text = (ROOT/'assets'/'sketchyicons'/'LICENSE').read_text()
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(data['title'])}</title><style>{css}</style></head><body><main><header class="sr-only"><h1>{esc(data['title'])}</h1></header><div class="diagram" tabindex="0" aria-label="Release authority comparison; scroll horizontally on smaller screens">{svg}</div><p>{esc(data['subtitle'])}</p><details open><summary>How the work and decisions are divided</summary><dl><div><dt>Scope</dt><dd>{esc(data['initiative'])}</dd></div><div><dt>Human rule owner</dt><dd>{esc(data['rule_owner'])}. {esc(data['rule_owner_note'])}</dd></div><div><dt>Proposed agent-only release boundary</dt><dd>{esc(data['eligible_change_label'])}. Release is permitted after the agreed checks pass.</dd></div><div><dt>Independent human approval</dt><dd>{esc(data['human_approval_scope'])}. Eligible approvers: {esc(names)}. The approver must be someone other than the maker.</dd></div><div><dt>Human + agent preparation</dt><dd>Humans and agents prepare the change. The specific contributions have not been specified in this view.</dd></div><div><dt>Reason for the proposed boundary</dt><dd>The participant chose this boundary. The required checks remain to define.</dd></div><div><dt>Execution after human approval</dt><dd>The release executor remains to be specified. Human approval does not establish who executes the release.</dd></div></dl></details><details open><summary>What remains unresolved</summary><p>A failed or uncertain check provides no permission to release. The response remains to be defined separately.</p><ul>{unresolved or '<li>No further unresolved items were supplied.</li>'}</ul></details><footer><p>Prepared by Dr. Shiva Kakkar</p><details><summary>Icon provenance and licence</summary><p>{esc(notice)}</p><pre>{esc(license_text)}</pre></details></footer></main></body></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--svg', type=Path)
    args = parser.parse_args()
    try:
        paths = [args.input, args.output] + ([args.svg] if args.svg else [])
        for i, left in enumerate(paths):
            for right in paths[i+1:]:
                if left.resolve() == right.resolve() or (left.exists() and right.exists() and left.samefile(right)):
                    raise ValueError('Input, HTML output and SVG output must be different files.')
        data = json.loads(args.input.read_text(encoding='utf-8'))
        svg = render_svg(data)
        page = render(data)
        args.output.write_text(page,encoding='utf-8')
        if args.svg:
            args.svg.write_text(svg,encoding='utf-8')
        print(args.output)
    except (OSError, ValueError) as exc:
        parser.exit(2,f'{exc}\n')

if __name__ == '__main__':
    main()
