#!/usr/bin/env python3
"""Render current positions' proposed AI/software and remaining human work.

Public API: validate(data) -> list[str]; render(data) -> str. Uses the canonical
comparison validator and an optional explicit current-performer mapping. No
staffing result or proposed reporting structure is included in this view.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from html import escape
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    '_decomposition_comparison', Path(__file__).with_name('render_comparison.py')
)
_comparison = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_comparison)


def validate(data):
    """Validate the whole record and optional mapping without changing either."""
    errors = _comparison.validate(data)
    if not isinstance(data, dict) or not isinstance(data.get('comparison'), dict):
        return errors
    comparison = data['comparison']
    if 'decomposition' not in comparison:
        return errors
    mapping = comparison['decomposition']
    path = 'comparison.decomposition'
    if not isinstance(mapping, dict):
        return errors + [f'{path} must be an object.']
    if not isinstance(mapping.get('note'), str) or not mapping['note'].strip():
        errors.append(f'{path}.note must be non-empty text.')
    if not isinstance(mapping.get('roles'), list):
        return errors + [f'{path}.roles must be a list.']

    def ids(items):
        return {item['id'] for item in items if isinstance(item, dict)
                and isinstance(item.get('id'), str)} if isinstance(items, list) else set()

    role_ids = ids(data.get('current_roles'))
    activity_ids = ids(comparison.get('division'))
    division = comparison.get('division', [])
    absent_ids = {row['id'] for row in division if isinstance(row, dict)
                  and isinstance(row.get('id'), str)
                  and isinstance(row.get('current'), dict)
                  and row['current'].get('mode') == 'none'} if isinstance(division, list) else set()
    seen_roles = set()
    for index, entry in enumerate(mapping['roles']):
        item_path = f'{path}.roles[{index}]'
        if not isinstance(entry, dict):
            errors.append(f'{item_path} must be an object.')
            continue
        role_id = entry.get('role_id')
        if not isinstance(role_id, str) or role_id not in role_ids:
            errors.append(f'{item_path}.role_id must refer to a current role.')
        else:
            if role_id in seen_roles:
                errors.append(f'{item_path}.role_id duplicates a role mapping.')
            seen_roles.add(role_id)
        if not isinstance(entry.get('unexamined_work'), str):
            errors.append(f'{item_path}.unexamined_work must be text.')
        activities = entry.get('activity_ids')
        if not isinstance(activities, list):
            errors.append(f'{item_path}.activity_ids must be a list.')
            continue
        seen_activities = set()
        for activity_index, activity_id in enumerate(activities):
            activity_path = f'{item_path}.activity_ids[{activity_index}]'
            if not isinstance(activity_id, str) or activity_id not in activity_ids:
                errors.append(f'{activity_path} must refer to a division activity.')
            else:
                if activity_id in seen_activities:
                    errors.append(f'{activity_path} duplicates an activity within this role.')
                if activity_id in absent_ids:
                    errors.append(f'{activity_path} cannot map a current performer to an absent current activity.')
                seen_activities.add(activity_id)
    return errors


def checked(data):
    errors = validate(data)
    if errors:
        raise ValueError('Invalid decomposition record:\n' + '\n'.join(errors))


def esc(value):
    return escape(str(value), quote=True)


def paragraph(value, label=None, css_class=None):
    attr = f' class="{esc(css_class)}"' if css_class else ''
    prefix = f'<strong>{esc(label)}:</strong> ' if label else ''
    return f'<p{attr}>{prefix}{esc(value)}</p>'


def ai_label(item):
    return {'assistant': 'AI assistant', 'agent': 'AI agent',
            'unknown': 'AI contribution; type not established'}[item.get('ai_kind', 'agent')]


def contribution_cells(row):
    """Blank text never invents a human step or establishes completed automation."""
    proposed = row['proposed']
    mode = proposed['mode']
    unsettled = row['status'] == 'unassessed' or mode == 'unknown'
    if mode == 'none':
        absent = paragraph('No activity is proposed for this workflow.')
        return absent, absent

    automation = []
    if proposed['agent_work'].strip():
        label = ai_label(proposed) if mode in ('agent', 'hybrid', 'unknown') else 'AI note'
        automation.append(paragraph(proposed['agent_work'], label))
    if proposed.get('software_work', '').strip():
        automation.append(paragraph(proposed['software_work'], 'Ordinary software'))
    if not automation:
        automation.append(paragraph(
            'AI or software contribution has not been established.' if unsettled
            else 'No AI or software contribution is recorded.'
        ))
    if proposed['human_work'].strip():
        human = paragraph(proposed['human_work'], 'Human work')
    else:
        human = paragraph(
            'Remaining human work has not been established.' if unsettled
            else 'No human contribution is recorded for this activity.'
        )
    return ''.join(automation), human


def owner_text(data, side, ident):
    if ident is None:
        return 'Not established.'
    return next(role['label'] for role in data[side + '_roles'] if role['id'] == ident)


def activity_details(data, row):
    current = row['current']
    proposed = row['proposed']
    parts = ['<details><summary>Current work and reasons for the proposed allocation</summary>']
    parts.append(paragraph(_comparison.MODES[current['mode']], 'Current arrangement'))
    for field, label in (('human_work', 'Current human work'),
                         ('agent_work', 'Current AI wording'),
                         ('software_work', 'Current ordinary software work')):
        value = current.get(field, '')
        if value.strip():
            parts.append(paragraph(value, label))
    for side, item in (('Current', current), ('Proposed', proposed)):
        if item.get('agent_work', '').strip() and item['mode'] in ('agent', 'hybrid', 'unknown'):
            parts.append(paragraph(ai_label(item), side + ' AI type'))
        for field, label in (('basis', 'basis'), ('condition', 'condition'), ('handoff', 'handoff')):
            if item.get(field, '').strip():
                parts.append(paragraph(item[field], side + ' ' + label))
        if item['mode'] != 'none':
            parts.append(paragraph(owner_text(data, side.lower(), item['owner_id']),
                                   side + ' accountable human'))
    parts.append(paragraph(row['reason'], 'Reason for this allocation'))
    parts.append('</details>')
    return ''.join(parts)


def activity(data, row, index, performers, current_roles):
    title_id = f'activity-{index}'
    parts = [f'<article class="activity" data-activity-id="{esc(row["id"])}">',
             f'<h3 id="{title_id}">{esc(row["label"])}</h3>']
    if row['status'] == 'unassessed':
        state = 'This allocation has not been assessed; the contributions below are not an agreed allocation.'
    elif row['proposed']['mode'] == 'unknown':
        state = 'The proposed allocation has not been established.'
    elif row['proposed']['mode'] == 'none':
        state = 'This activity is absent from the proposed workflow.'
    else:
        state = {'changed': 'Proposed change to this activity.',
                 'retained': 'The recorded allocation is retained.',
                 'clarified': 'Proposed allocation; the earlier arrangement was not established.'}[row['status']]
    parts.append(paragraph(state, css_class='state'))
    if row['current']['mode'] == 'none':
        parts.append(paragraph('This activity is absent from the current workflow.', css_class='state'))
    if len(performers) > 1:
        names = '; '.join(current_roles[ident]['label'] for ident in performers)
        parts.append(paragraph(names, 'Shared current work', 'shared-work'))
    automation, human = contribution_cells(row)
    parts.append(f'<table aria-labelledby="{title_id}"><thead><tr>'
                 '<th scope="col" class="automation-heading">AI or software work</th>'
                 '<th scope="col" class="human-heading">Work remaining with people</th>'
                 '</tr></thead><tbody><tr>'
                 f'<td class="automation-work">{automation}</td>'
                 f'<td class="human-work">{human}</td>'
                 '</tr></tbody></table>')
    parts.append(activity_details(data, row))
    parts.append('</article>')
    return ''.join(parts)


def render(data):
    """Return standalone offline HTML, preserving the input record unchanged."""
    checked(data)
    comparison = data['comparison']
    mapping = comparison.get('decomposition', {})
    groups = {entry['role_id']: entry for entry in mapping.get('roles', [])}
    rows = {row['id']: row for row in comparison['division']}
    current_roles = {role['id']: role for role in data['current_roles']}
    performers = defaultdict(list)
    for entry in mapping.get('roles', []):
        for ident in entry['activity_ids']:
            performers[ident].append(entry['role_id'])
    css = (ROOT / 'assets' / 'decomposition.css').read_text(encoding='utf-8')
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             '<title>Work by current position</title>', f'<style>{css}</style>',
             '</head><body><main><header><h1>Work by current position</h1>',
             paragraph('Proposed AI or software contributions and remaining human work for the selected workflow.')]
    if data['organisation']['label'].strip():
        parts.append(paragraph(data['organisation']['label'], 'Organisation'))
    parts.append(paragraph(f'{data["status"].capitalize()} record, revision {data["revision"]}.', css_class='state'))
    if mapping.get('note'):
        parts.append(paragraph(mapping['note']))
    parts.append('</header>')
    index = 0
    for role_index, role in enumerate(data['current_roles']):
        role_id = role['id']
        title_id = f'position-{role_index}'
        group = groups.get(role_id)
        parts.extend([f'<section class="position" data-role-id="{esc(role_id)}" aria-labelledby="{title_id}">',
                      f'<h2 id="{title_id}">{esc(role["label"])}</h2>'])
        size = role.get('size', '')
        parts.append(paragraph(size if size.strip() else 'Position count not recorded.',
                               'Recorded size' if size.strip() else None, 'role-size'))
        if role['scope'].strip():
            parts.append(paragraph(role['scope'], 'Role scope'))
        if group and group['activity_ids']:
            for activity_id in group['activity_ids']:
                index += 1
                parts.append(activity(data, rows[activity_id], index, performers[activity_id], current_roles))
        else:
            parts.append(paragraph('Work for this position has not yet been examined.', css_class='unexamined'))
        if group and group['unexamined_work'].strip():
            parts.append(paragraph(group['unexamined_work'], 'Unexamined work', 'unexamined'))
        elif group and group['activity_ids']:
            parts.append(paragraph('Coverage of this position’s other work has not been recorded.', css_class='unexamined'))
        parts.append('</section>')
    if not data['current_roles']:
        parts.append(paragraph('Current positions have not been recorded.', css_class='unexamined'))
    unlinked = [row for row in comparison['division'] if row['id'] not in performers]
    if unlinked:
        parts.append('<section class="unlinked" aria-labelledby="unlinked-title"><h2 id="unlinked-title">Activities not yet linked to a current position</h2>')
        for row in unlinked:
            index += 1
            parts.append(activity(data, row, index, [], current_roles))
        parts.append('</section>')
    parts.append('<footer><p>Prepared by Dr. Shiva Kakkar</p></footer></main></body></html>')
    return ''.join(parts)


def same_file(left, right):
    return left.resolve() == right.resolve() or (
        left.exists() and right.exists() and left.samefile(right)
    )


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('output', type=Path, nargs='?')
    parser.add_argument('--validate-only', action='store_true')
    args = parser.parse_args(argv)
    if not args.validate_only and args.output is None:
        parser.error('OUTPUT is required unless --validate-only is used.')
    try:
        if args.output is not None and same_file(args.input, args.output):
            parser.error('An output path cannot overwrite the input record.')
        data = json.loads(args.input.read_text(encoding='utf-8'))
        checked(data)
        if args.validate_only:
            print('Valid decomposition record.')
            return 0
        content = render(data)
        # Recheck aliases immediately before the first filesystem write.
        if same_file(args.input, args.output):
            parser.error('An output path cannot overwrite the input record.')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(content, encoding='utf-8')
        print('Wrote the role decomposition.')
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
