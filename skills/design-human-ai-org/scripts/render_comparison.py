#!/usr/bin/env python3
"""Render paired organisation comparisons from a version 1 workbook record.

The comparison extension is documented in references/comparison-record.md.
This module uses only Python's standard library and bundled, offline assets.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import html
import importlib.util
import json
from pathlib import Path
import sys
import textwrap
from types import SimpleNamespace
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location('_comparison_workbook', Path(__file__).with_name('render_workbook.py'))
_base = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_base)

INK = '#191714'
MUTED = '#655F55'
RULE = '#D9D2C4'
PAPER = '#FFFDF9'
ORANGE = '#A84D24'
TEAL = '#08776E'
MODES = {'human': 'Human only', 'agent': 'Agent only', 'hybrid': 'Human + agent', 'software': 'Ordinary software', 'unknown': 'Execution not established', 'none': 'No activity in this workflow'}
STATUSES = {'changed': 'Changed', 'retained': 'Retained', 'clarified': 'Newly specified', 'unassessed': 'Not assessed'}
REPORTING = {'known_parent': 'Formal manager recorded', 'known_root': 'Top of the recorded structure', 'unknown': 'Reporting not established', 'outside_scope': 'Manager outside this scope'}


def validate(data):
    """Validate the original record and comparison extension without mutation."""
    errors = _base.validate(data)
    if not isinstance(data, dict):
        return errors
    draft = data.get('status') == 'draft'
    role_sets = {}
    for side in ('current', 'proposed'):
        roles = data.get(side + '_roles', [])
        roles = roles if isinstance(roles, list) else []
        role_sets[side] = {r['id']: r for r in roles if isinstance(r, dict) and isinstance(r.get('id'), str)}
        for i, role in enumerate(roles):
            if not isinstance(role, dict):
                continue
            path = f'{side}_roles[{i}]'
            if 'node_type' in role and role['node_type'] not in ('person', 'role', 'team', 'unit'):
                errors.append(f'{path}.node_type must be person, role, team or unit.')
            if 'size' in role and not isinstance(role['size'], str):
                errors.append(f'{path}.size must be participant-supplied text, not an inferred number.')
            state = role.get('reporting_status', 'known_parent' if role.get('parent_id') else 'unknown')
            if not isinstance(state, str) or state not in REPORTING:
                errors.append(f'{path}.reporting_status is invalid.')
            elif state == 'known_parent' and role.get('parent_id') is None:
                errors.append(f'{path}.reporting_status requires a recorded parent_id.')
            elif state != 'known_parent' and role.get('parent_id') is not None:
                errors.append(f'{path}.reporting_status contradicts parent_id.')
    def reject_group_owner(value, side, path):
        if isinstance(value, str) and role_sets[side].get(value, {}).get('node_type') in ('team', 'unit'):
            errors.append(f'{path} must identify a human role, not an aggregated team or unit.')

    for key, fields in [('outcomes', ('owner_id',)), ('work_changes', ('owner_id',)), ('readiness', ('owner_id',))]:
        items = data.get(key, [])
        for i, item in enumerate(items if isinstance(items, list) else []):
            if isinstance(item, dict):
                for field in fields:
                    reject_group_owner(item.get(field), 'proposed', f'{key}[{i}].{field}')
    pilot = data.get('pilot')
    if isinstance(pilot, dict):
        reject_group_owner(pilot.get('owner_id'), 'proposed', 'pilot.owner_id')
    services = data.get('services', [])
    for i, service in enumerate(services if isinstance(services, list) else []):
        if not isinstance(service, dict):
            continue
        for field in ('outcome_owner_id', 'supervisor_id', 'service_owner_id'):
            reject_group_owner(service.get(field), 'proposed', f'services[{i}].{field}')
        agents = service.get('agent_roles', [])
        for j, agent in enumerate(agents if isinstance(agents, list) else []):
            if isinstance(agent, dict):
                reject_group_owner(agent.get('escalation_to_id'), 'proposed', f'services[{i}].agent_roles[{j}].escalation_to_id')
    workflows = data.get('workflows', [])
    for i, workflow in enumerate(workflows if isinstance(workflows, list) else []):
        if not isinstance(workflow, dict):
            continue
        for side in ('current', 'proposed'):
            steps = workflow.get(side, [])
            for j, step in enumerate(steps if isinstance(steps, list) else []):
                if isinstance(step, dict):
                    for field in ('owner_id', 'approval_by_id'):
                        reject_group_owner(step.get(field), side, f'workflows[{i}].{side}[{j}].{field}')
    outcomes = data.get('outcomes', [])
    outcome_ids = {o.get('id') for o in outcomes if isinstance(o, dict) and isinstance(o.get('id'), str)} if isinstance(outcomes, list) else set()
    comparison = data.get('comparison')
    if not isinstance(comparison, dict):
        return errors + ['comparison must be an object.']
    for field in ('perspective', 'scale'):
        if not isinstance(comparison.get(field), str):
            errors.append(f'comparison.{field} must be text.')
    for kind in ('division', 'decisions'):
        rows = comparison.get(kind)
        if not isinstance(rows, list):
            errors.append(f'comparison.{kind} must be a list.')
            continue
        ids = set()
        for i, row in enumerate(rows):
            path = f'comparison.{kind}[{i}]'
            if not isinstance(row, dict):
                errors.append(f'{path} must be an object.')
                continue
            for field in ('id', 'label', 'outcome_id', 'reason'):
                if not isinstance(row.get(field), str) or not row[field].strip():
                    errors.append(f'{path}.{field} must be non-empty text.')
            ident = row.get('id')
            if isinstance(ident, str):
                if ident in ids:
                    errors.append(f'{path}.id must be unique within {kind}.')
                ids.add(ident)
            if not isinstance(row.get('outcome_id'), str) or row['outcome_id'] not in outcome_ids:
                errors.append(f'{path}.outcome_id must refer to a recorded outcome.')
            status = row.get('status')
            if not isinstance(status, str) or status not in STATUSES:
                errors.append(f'{path}.status is invalid.')
            for side in ('current', 'proposed'):
                item = row.get(side)
                if not isinstance(item, dict):
                    errors.append(f'{path}.{side} must be an object.')
                    continue
                mode = item.get('mode')
                if not isinstance(mode, str) or mode not in MODES:
                    errors.append(f'{path}.{side}.mode is invalid.')
                if 'ai_kind' in item and item['ai_kind'] not in ('assistant', 'agent', 'unknown'):
                    errors.append(f'{path}.{side}.ai_kind must be assistant, agent or unknown.')
                if mode == 'agent' and item.get('ai_kind') == 'assistant':
                    errors.append(f'{path}.{side}: a manually directed AI assistant cannot establish agent-only execution.')
                for field in ('human_work', 'agent_work', 'basis'):
                    if not isinstance(item.get(field), str):
                        errors.append(f'{path}.{side}.{field} must be text.')
                for field in ('software_work', 'handoff', 'condition'):
                    if field in item and not isinstance(item[field], str):
                        errors.append(f'{path}.{side}.{field} must be text.')
                if mode == 'software' and (not isinstance(item.get('software_work'), str) or not item['software_work'].strip()):
                    errors.append(f'{path}.{side}.software_work must describe ordinary software execution.')
                if mode == 'none' and any(item.get(field) for field in ('human_work','agent_work','software_work')):
                    errors.append(f'{path}.{side}: an absent activity cannot also assign execution work.')
                owner = item.get('owner_id')
                if 'owner_id' not in item:
                    errors.append(f'{path}.{side}.owner_id is required; use null if unknown in a draft.')
                elif mode == 'none' and owner is not None:
                    errors.append(f'{path}.{side}.owner_id must be null for an absent activity.')
                elif owner is None:
                    if side == 'proposed' and not draft and mode != 'none':
                        errors.append(f'{path}.{side}.owner_id must name a human for confirmed work.')
                elif not isinstance(owner, str) or owner not in role_sets[side]:
                    errors.append(f'{path}.{side}.owner_id must refer to a human on the {side} side.')
                elif role_sets[side][owner].get('node_type', 'role') in ('team', 'unit'):
                    errors.append(f'{path}.{side}.owner_id cannot assign human accountability to an aggregated team or unit.')
                required = ('human_work', 'agent_work') if mode == 'hybrid' else ('human_work',) if mode == 'human' else ('agent_work',) if mode == 'agent' else ()
                for field in required:
                    if isinstance(item.get(field), str) and not item[field].strip():
                        errors.append(f'{path}.{side}.{field} must describe the contribution for {mode} execution.')
            if status == 'retained' and isinstance(row.get('current'), dict) and isinstance(row.get('proposed'), dict):
                if row['current'].get('mode') != row['proposed'].get('mode'):
                    errors.append(f'{path}: retained execution cannot have different current and proposed modes.')
    reporting = comparison.get('reporting')
    if not isinstance(reporting, dict):
        return errors + ['comparison.reporting must be an object.']
    if not isinstance(reporting.get('status'), str) or reporting['status'] not in STATUSES:
        errors.append('comparison.reporting.status is invalid.')
    for field in ('reason', 'current_context', 'proposed_context'):
        if not isinstance(reporting.get(field), str):
            errors.append(f'comparison.reporting.{field} must be text.')
    links = reporting.get('links')
    if not isinstance(links, dict):
        errors.append('comparison.reporting.links must contain current and proposed lists.')
    else:
        for side in ('current', 'proposed'):
            items = links.get(side)
            if not isinstance(items, list):
                errors.append(f'comparison.reporting.links.{side} must be a list.')
                continue
            for i, link in enumerate(items):
                path = f'comparison.reporting.links.{side}[{i}]'
                if not isinstance(link, dict):
                    errors.append(f'{path} must be an object.')
                    continue
                for field in ('from_id', 'to_id'):
                    if not isinstance(link.get(field), str) or link[field] not in role_sets[side]:
                        errors.append(f'{path}.{field} must refer to a role on the {side} side.')
                if link.get('kind') not in ('coordination', 'functional'):
                    errors.append(f'{path}.kind must be coordination or functional.')
                if not isinstance(link.get('label'), str):
                    errors.append(f'{path}.label must be text.')
    if reporting.get('status') == 'retained':
        before = {i: r.get('parent_id') for i, r in role_sets['current'].items()}
        after = {i: r.get('parent_id') for i, r in role_sets['proposed'].items()}
        if before != after:
            errors.append('comparison.reporting: retained reporting cannot change roles or formal parents.')
    org_view = comparison.get('organisation')
    if org_view is not None:
        if not isinstance(org_view, dict):
            errors.append('comparison.organisation must be an object.')
        else:
            for side in ('current', 'proposed'):
                if not isinstance(org_view.get(side+'_note'), str):
                    errors.append('comparison.organisation.'+side+'_note must be text.')
                groups = org_view.get(side)
                if not isinstance(groups, list):
                    errors.append('comparison.organisation.'+side+' must be a list.')
                    continue
                ids = set(role_sets[side])
                for group in groups:
                    if not isinstance(group, dict):
                        errors.append('Organisation AI group must be an object.')
                        continue
                    for field in ('id','label','summary','detail'):
                        if not isinstance(group.get(field),str) or not group[field].strip():
                            errors.append('Organisation AI group '+field+' must be non-empty text.')
                    ident=group.get('id')
                    if isinstance(ident,str):
                        if ident in ids: errors.append('Organisation group IDs must be unique and distinct from human IDs.')
                        ids.add(ident)
                    supervisor=group.get('supervisor_id')
                    if supervisor is not None and (not isinstance(supervisor,str) or supervisor not in role_sets[side]):
                        errors.append('Organisation group supervisor must belong to the same side.')
                    reject_group_owner(supervisor,side,'Organisation group supervisor')
                    if group.get('supervisor_post_id') is not None:
                        posts = comparison.get('staffing', {}).get(side, [])
                        post = next((p for p in posts if p.get('id') == group['supervisor_post_id']), None)
                        if post is None or post.get('role_id') != supervisor:
                            errors.append('Organisation supervisor_post_id must name a same-side post of the recorded supervisor role.')
                    if not isinstance(group.get('status'),str) or group['status'] not in STATUSES: errors.append('Organisation group status is invalid.')
                    if group.get('ai_kind') not in ('agent','assistant','mixed','unknown'): errors.append('Organisation group AI type is invalid.')
                    if group.get('relationship','supervises') not in ('supervises','uses'): errors.append('Organisation relationship must be supervises or uses.')
                    count=group.get('instances')
                    if count is not None and (type(count) is not int or count<1): errors.append('Organisation instances must be null or a positive integer.')
    return errors


def checked(data):
    errors = validate(data)
    if errors:
        raise ValueError('Invalid comparison record:\n' + '\n'.join(errors))


def esc(value):
    return html.escape(str(value), quote=True)


def lines(value, width):
    result = []
    for paragraph in str(value).splitlines() or ['']:
        result.extend(textwrap.wrap(paragraph, width=max(1, width), break_long_words=True, break_on_hyphens=False) or [''])
    return result


def text(value, x, y, width=60, size=18, colour=INK, weight=400, serif=False, anchor='start', lh=None):
    lh = lh or size * 1.4
    body = ''.join(f'<tspan x="{x}" dy="{0 if i == 0 else lh}">{esc(line)}</tspan>' for i, line in enumerate(lines(value, width)))
    family = 'Georgia, serif' if serif else 'Avenir Next, Avenir, Arial, sans-serif'
    return f'<text x="{x}" y="{y}" font-family="{family}" font-size="{size}" font-weight="{weight}" text-anchor="{anchor}" fill="{colour}">{body}</text>'


def height(value, width=60, size=18):
    return len(lines(value, width)) * size * 1.4


def icon(name, x, y, size=30, colour=ORANGE):
    source = ET.fromstring((ROOT / 'assets' / 'sketchyicons' / f'{name}.svg').read_text(encoding='utf-8'))
    paths = ''.join(f'<path d="{esc(child.attrib["d"])}"/>' for child in source if child.tag.endswith('path'))
    return f'<g transform="translate({x} {y}) scale({size / 24})" stroke="{colour}" stroke-width="1.65" stroke-linecap="round" stroke-linejoin="round" fill="none">{paths}</g>'


def actor(mode, x, y, size=48):
    if mode == 'human':
        return f'<circle cx="{x + size/2}" cy="{y + size/2}" r="{size/2}" fill="#F9E9DB" stroke="{ORANGE}"/>' + icon('user-round', x + size * .19, y + size * .15, size * .65)
    if mode == 'agent':
        return clipped(x, y, size, size, '#E6F2ED', TEAL) + icon('bot', x + size*.17, y + size*.14, size*.68, TEAL)
    if mode == 'hybrid':
        return actor('human', x, y, size) + text('+', x + size + 7, y + size * .68, size=22, colour=MUTED) + actor('agent', x + size + 30, y, size)
    if mode == 'software':
        return f'<rect x="{x}" y="{y+size*.1}" width="{size}" height="{size*.8}" fill="#EFEEE9" stroke="{MUTED}"/><path d="M{x+1} {y+size*.33} H{x+size-1} M{x+size*.2} {y+size*.55} H{x+size*.8} M{x+size*.2} {y+size*.72} H{x+size*.6}" stroke="{MUTED}" fill="none"/>'
    if mode == 'none':
        return f'<circle cx="{x+size/2}" cy="{y+size/2}" r="{size/2}" fill="none" stroke="{RULE}"/><path d="M{x+size*.27} {y+size/2} H{x+size*.73}" stroke="{MUTED}" stroke-width="2"/>'
    return f'<rect x="{x}" y="{y}" width="{size}" height="{size}" fill="none" stroke="{MUTED}" stroke-dasharray="5 4"/>' + text('?', x + size/2, y + size*.72, size=30, colour=MUTED, anchor='middle')


def clipped(x, y, width, tall, fill=PAPER, stroke=TEAL, sw=1.2):
    cut = min(16, width / 5, tall / 5)
    return f'<path d="M{x+cut} {y} H{x+width-cut} L{x+width} {y+cut} V{y+tall-cut} L{x+width-cut} {y+tall} H{x+cut} L{x} {y+tall-cut} V{y+cut} Z" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>'


def document(prefix, title, description, width, tall):
    license_path = ROOT / 'assets' / 'sketchyicons' / 'NOTICE.md'
    notice = license_path.read_text(encoding='utf-8') if license_path.exists() else 'Sketchyicons static 0.5.0. Original icons used under the bundled licence.'
    notice += '\nVisual reference: Editorial Magazine Interface, StyleRef.io; adapted for explicit human and agent semantics.'
    return [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{tall}" viewBox="0 0 {width} {tall}" role="img" aria-labelledby="{prefix}-title {prefix}-description"><title id="{prefix}-title">{esc(title)}</title><desc id="{prefix}-description">{esc(description)}</desc><metadata>{esc(notice)}</metadata><rect width="{width}" height="{tall}" fill="{PAPER}"/>']


def legend(y, width=1400):
    parts = [f'<path d="M44 {y-29} H{width-44}" stroke="{RULE}"/>']
    for mode, x, label in [('human', 45, 'Human'), ('agent', 238, 'Agent work'), ('hybrid', 474, 'Human + agent'), ('software', 853, 'Software'), ('unknown', 1085, 'Unknown')]:
        parts.append(actor(mode, x, y-9, 30))
        parts.append(text(label, x + (101 if mode == 'hybrid' else 43), y+13, size=17, colour=MUTED))
    parts.append(text('Shapes identify human and AI contributions. Text distinguishes agents from manually directed AI assistants.', 45, y+56, width=132, size=16, colour=MUTED))
    parts.append(text('One AI shape does not specify an instance count or a coordinated swarm. “No activity” means known absence; “Unknown” means it was not established.', 45, y+81, width=145, size=15, colour=MUTED))
    return ''.join(parts)


def owner_label(data, side, ident):
    if ident is None:
        return 'Accountable human: to confirm'
    role = next(r for r in data[side+'_roles'] if r['id'] == ident)
    return 'Accountable human: ' + role['label']


def contribution_blocks(item):
    if item['mode'] == 'none':
        return [('Activity status', 'This activity is absent from this version of the workflow.', MUTED)]
    result = []
    if item['human_work']:
        result.append(('Human contribution', item['human_work'], ORANGE))
    if item['agent_work']:
        label = 'AI assistant contribution' if item.get('ai_kind') == 'assistant' else 'AI contribution (type to confirm)' if item.get('ai_kind') == 'unknown' else 'Agent contribution'
        result.append((label, item['agent_work'], TEAL))
    if item.get('software_work'):
        result.append(('Software', item['software_work'], MUTED))
    if item.get('handoff'):
        result.append(('Handoff', item['handoff'], MUTED))
    if item.get('condition'):
        result.append(('Permission boundary', item['condition'], MUTED))
    if not result:
        result.append(('Work allocation', 'The executor and contribution have not been established.', MUTED))
    return result


def accountability_label(data, side, item):
    return 'No accountability assignment for an absent activity.' if item['mode'] == 'none' else owner_label(data, side, item['owner_id'])


def card_height(data, side, item):
    total = 98
    for _, value, _ in contribution_blocks(item):
        total += 31 + height(value, 54, 18) + 17
    total += 28 + height(accountability_label(data, side, item), 56, 17)
    total += 27 + height('Basis: ' + (item['basis'] or 'Not recorded.'), 59, 16) + 20
    return total


def allocation_card(data, side, item, x, y, tall, emphasise):
    mode = item['mode']
    colour = TEAL if mode == 'agent' else ORANGE if mode == 'human' else MUTED
    fill = '#EDF5F0' if emphasise else PAPER
    stroke = TEAL if emphasise else RULE
    if mode == 'agent':
        parts = [clipped(x, y, 632, tall, fill, stroke, 2 if emphasise else 1)]
    else:
        dash = ' stroke-dasharray="6 5"' if mode == 'unknown' else ''
        parts = [f'<rect x="{x}" y="{y}" width="632" height="{tall}" fill="{fill}" stroke="{stroke}" stroke-width="{2 if emphasise else 1}"{dash}/>']
    mode_label = MODES[mode]
    if mode == 'hybrid' and item.get('ai_kind') == 'assistant':
        mode_label = 'Human + AI assistant'
    elif mode == 'hybrid' and item.get('ai_kind') == 'unknown':
        mode_label = 'Human + AI (type to confirm)'
    parts += [actor(mode, x+24, y+22, 44), text(mode_label, x+(158 if mode == 'hybrid' else 86), y+50, width=38, size=21, colour=colour, weight=600)]
    cursor = y + 98
    for label, value, label_colour in contribution_blocks(item):
        parts += [text(label, x+24, cursor, size=15, colour=label_colour, weight=600), text(value, x+24, cursor+29, width=54, size=18)]
        cursor += 31 + height(value, 54, 18) + 17
    parts.append(f'<path d="M{x+24} {cursor-6} H{x+608}" stroke="{RULE}"/>')
    parts.append(text(accountability_label(data, side, item), x+24, cursor+22, width=56, size=17, colour=ORANGE if item['owner_id'] else MUTED))
    cursor += 28 + height(accountability_label(data, side, item), 56, 17)
    parts.append(text('Basis: ' + (item['basis'] or 'Not recorded.'), x+24, cursor+25, width=59, size=16, colour=MUTED))
    return ''.join(parts)


def _render_allocation(data, kind):
    checked(data)
    rows = data['comparison'][kind]
    title = 'Division of work' if kind == 'division' else 'Decision authority'
    description = 'The same work is shown before and after. Execution, human accountability and the reason for each allocation are shown separately.' if kind == 'division' else 'The current and proposed decision arrangements are paired. A new specification is distinguished from a confirmed change in authority.'
    cursor = 166
    layouts = []
    for row in rows:
        heading_height = max(38, height(row['label'], 80, 24))
        card_tall = max(card_height(data, side, row[side]) for side in ('current', 'proposed'))
        reason_height = height('Reason: ' + row['reason'], 125, 17)
        layouts.append((row, cursor, heading_height, card_tall))
        cursor += heading_height + 24 + card_tall + 38 + reason_height + 42
    if not rows:
        cursor += 105
    tall = int(cursor + 142)
    parts = document(kind, title, description, 1400, tall)
    parts += [text(title, 45, 56, size=35, serif=True), text(description, 45, 94, width=124, size=19, colour=MUTED), f'<path d="M45 128 H1355" stroke="{RULE}"/>']
    for row, y, heading_height, card_tall in layouts:
        status = row['status']
        row_colour = TEAL if status == 'changed' else ORANGE if status == 'clarified' else MUTED
        content = [text(row['label'], 45, y+25, width=80, size=24, serif=True), text(STATUSES[status], 1355, y+25, size=16, weight=600, colour=row_colour, anchor='end')]
        top = y + heading_height + 24
        content += [text('Current', 45, top, size=17, colour=MUTED), text('Proposed', 722, top, size=17, colour=MUTED)]
        content += [allocation_card(data, 'current', row['current'], 45, top+17, card_tall, False), allocation_card(data, 'proposed', row['proposed'], 722, top+17, card_tall, status == 'changed')]
        content.append(text('Reason: ' + row['reason'], 45, top+card_tall+50, width=125, size=17, colour=MUTED))
        parts.append(f'<g data-comparison-id="{esc(row["id"])}" data-change="{status}">' + ''.join(content) + '</g>')
    if not rows:
        parts.append(text('No ' + ('division of work' if kind == 'division' else 'decision authority') + ' comparison has been recorded.', 45, 212, size=22, colour=MUTED))
    parts += [legend(cursor+15), text('Prepared by Dr. Shiva Kakkar', 1355, tall-13, size=14, colour=MUTED, anchor='end'), '</svg>']
    return ''.join(parts)


def compact_allocation(data, kind):
    """Draw actor contributions; keep the complete rationale in accessible details."""
    checked(data)
    rows=data['comparison'][kind]
    title='Division of work' if kind=='division' else 'Decision authority'
    layouts=[]; cursor=138
    for row in rows:
        summaries=[row[s].get(k,'') for s in ('current','proposed') for k in ('human_summary','agent_summary','software_summary','short_condition')]
        label_h=max(32,height(row['label'],84,23))
        node_h=max(100,max([height(v,25,18)+57 for v in summaries]+[100]))
        why=row.get('short_reason','Select the activity to read the allocation rationale.')
        why_h=height(why,128,17)
        layouts.append((row,cursor,label_h,node_h,why))
        cursor+=label_h+node_h+why_h+123
    if not rows:
        cursor = 218  # Reserve the empty-state line before the legend.
    parts=document(kind,title,'Paired actor shapes show who does each activity. Select an activity for complete responsibilities and reasons.',1400,cursor+112)
    parts.extend([text(title,45,53,size=34,serif=True),text('Current',45,105,size=21,serif=True),text('Proposed',740,105,size=21,serif=True)])
    for row,y,label_h,node_h,why in layouts:
        status=row['status']; colour=TEAL if status=='changed' else MUTED
        parts.append(f'<g data-comparison-id="{esc(row["id"])}" data-change="{status}"><desc>'+esc(json.dumps(row,ensure_ascii=False))+'</desc>')
        parts.append(f'<a href="#work-{kind}-{esc(row["id"])}" class="diagram-link"><title>Select to read responsibilities and rationale</title>')
        parts.extend([f'<path d="M45 {y-10} H1355" stroke="{RULE}"/>',text(row['label'],45,y+19,width=84,size=23,serif=True),text(STATUSES[status],1355,y+19,size=16,colour=colour,anchor='end')])
        for side,x in [('current',45),('proposed',740)]:
            item=row[side];mode=item['mode'];top=y+label_h+10
            mode_name='Human + AI assistant' if mode=='hybrid' and item.get('ai_kind')=='assistant' else MODES[mode]
            parts.append('<desc>'+esc(side.capitalize()+': '+mode_name)+'</desc>')
            atoms=['human','agent'] if mode=='hybrid' else [mode]
            for index,atom in enumerate(atoms):
                nx=x+index*302;nw=282 if len(atoms)==2 else 580
                summary=item.get(atom+'_summary','')
                if not summary:
                    summary={'human':'Human contribution','agent':'AI contribution','software':'Fixed software rules','unknown':'Executor not established','none':'Activity absent'}[atom]
                if atom=='agent':parts.append(clipped(nx,top,nw,node_h,'#EDF5F0',TEAL,2 if side=='proposed' and status=='changed' else 1))
                else:parts.append(f'<rect x="{nx}" y="{top}" width="{nw}" height="{node_h}" rx="{18 if atom=="human" else 0}" fill="{ "#FBF1E8" if atom=="human" else PAPER}" stroke="{ORANGE if atom=="human" else RULE}"/>')
                parts.append(actor(atom,nx+15,top+17,36))
                label='AI assistant' if atom=='agent' and item.get('ai_kind')=='assistant' else 'AI type unknown' if atom=='agent' and item.get('ai_kind')=='unknown' else MODES.get(atom,atom)
                if mode=='hybrid' and atom=='human':label='Human'
                if mode=='hybrid' and atom=='agent' and item.get('ai_kind','agent')=='agent':label='Agent'
                parts.extend([text(label,nx+63,top+39,width=25,size=17,weight=600,colour=TEAL if atom=='agent' else ORANGE if atom=='human' else MUTED),text(summary,nx+17,top+75,width=25 if len(atoms)==2 else 52,size=18)])
                if index==0 and len(atoms)==2:parts.append(text('+',nx+292,top+node_h/2+7,size=22,anchor='middle',colour=MUTED))
            owner=accountability_label(data,side,item)
            parts.append(text(owner,x,top+node_h+26,width=60,size=16,colour=MUTED))
        parts.append(text(why,45,y+label_h+node_h+69,width=128,size=17,colour=MUTED))
        parts.append('</a></g>')
    if not rows:parts.append(text('This comparison has not been recorded.',45,173,size=22))
    parts.extend([text('Circle: human. Clipped shape: AI. Paired shapes: shared execution. Select an activity for its full record.',45,cursor+28,width=140,size=16,colour=MUTED),text('Prepared by Dr. Shiva Kakkar',1355,cursor+87,size=14,anchor='end',colour=MUTED),'</svg>'])
    return ''.join(parts)


def work_details(data,kind):
    parts=['<section class="work-details" aria-label="Activity details">']
    for row in data['comparison'][kind]:
        parts.append(f'<details id="work-{kind}-{esc(row["id"])}"><summary>{esc(row["label"])}: contributions and rationale</summary><div class="role-columns">')
        for side in ('current','proposed'):
            item=row[side]
            parts.append('<div><h3>'+side.capitalize()+'</h3><dl>')
            for label,value,_ in contribution_blocks(item):parts.append('<dt>'+esc(label)+'</dt><dd>'+esc(value)+'</dd>')
            parts.append('<dt>Accountability</dt><dd>'+esc(accountability_label(data,side,item))+'</dd><dt>Basis</dt><dd>'+esc(item['basis'])+'</dd></dl></div>')
        parts.append('</div><p>'+esc(row['reason'])+'</p></details>')
    parts.append('</section>')
    return ''.join(parts)


def render_division_svg(data):
    return compact_allocation(data, 'division')


def render_decisions_svg(data):
    return compact_allocation(data, 'decisions')


def organisation_module(data=None):
    filename = 'staffing_view.py' if data and data.get('comparison', {}).get('staffing') else 'organisation_view.py'
    spec=importlib.util.spec_from_file_location('_organisation_view',Path(__file__).with_name(filename))
    module=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def render_organisation_svg(data):
    checked(data)
    return organisation_module(data).render_organisation_svg(data,SimpleNamespace(**globals()))


def workflow_module():
    spec = importlib.util.spec_from_file_location('_workflow_view', Path(__file__).with_name('workflow_view.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def workflow_step_id(workflow_id, side, step_id):
    return workflow_module().workflow_step_id(workflow_id, side, step_id)


def role_detail(role):
    """Show a person's supplied position; count labels belong to aggregate scope."""
    if role.get('node_type') == 'person':
        return role['scope'] or 'Human role not supplied'
    kind = role.get('node_type', 'role').capitalize()
    return kind + (' · ' + role['size'] if role.get('size') else '')


def _tree_layout(roles, stable_order):
    lookup = {r['id']: r for r in roles}
    children = defaultdict(list)
    for role in roles:
        children[role['parent_id']].append(role['id'])
    for group in children.values():
        group.sort(key=lambda ident: stable_order[ident])
    positions = {}
    leaf = 0
    depth_max = 0
    for root in children[None]:
        stack = [(root, 0, False)]
        while stack:
            ident, depth, visited = stack.pop()
            depth_max = max(depth_max, depth)
            if visited:
                positions[ident] = ((positions[children[ident][0]][0] + positions[children[ident][-1]][0])/2, depth)
            elif children[ident]:
                stack.append((ident, depth, True))
                stack.extend((child, depth+1, False) for child in reversed(children[ident]))
            else:
                positions[ident] = (leaf, depth)
                leaf += 1
    node_height = 155
    for role in roles:
        role_state = role.get('reporting_status', 'known_parent' if role['parent_id'] else 'unknown')
        detail = role_detail(role)
        node_height = max(node_height, 70 + height(role['label'], 25, 20) + height(detail, 30, 15) + (height(REPORTING[role_state], 30, 15) if not role['parent_id'] else 0) + 35)
    return positions, max(1, leaf), depth_max, node_height


def render_reporting_svg(data, current_only=False):
    checked(data)
    reporting = data['comparison']['reporting']
    sides = ('current',) if current_only else ('current', 'proposed')
    unique = list(dict.fromkeys(r['id'] for side in sides for r in data[side+'_roles']))
    stable = {ident: i for i, ident in enumerate(unique)}
    layouts = {side: _tree_layout(data[side+'_roles'], stable) for side in sides}
    leaf_count = max(layout[1] for layout in layouts.values())
    side_width = max(1310 if current_only else 640, leaf_count * 314 + 18)
    width = side_width + 90 if current_only else side_width * 2 + 120
    node_height = max(layout[3] for layout in layouts.values())
    level_pitch = node_height + 83
    depth = max(layout[2] for layout in layouts.values())
    context_height = max(height(reporting[side+'_context'], max(30, int((side_width-42)/9)), 17) for side in sides)
    top = 213 + context_height
    tree_bottom = top + depth * level_pitch + node_height + 35
    link_height = 0
    for side in sides:
        lookup = {r['id']: r for r in data[side+'_roles']}
        total = 0
        for link in reporting['links'][side]:
            value = lookup[link['from_id']]['label'] + ' → ' + lookup[link['to_id']]['label'] + ': ' + link['label']
            total += height(value, max(30, int((side_width-82)/9)), 17) + 29
        link_height = max(link_height, total)
    reason_text = 'Current structure recorded for review. Proposed work and reporting arrangements have not been generated.' if current_only else 'Reason: ' + reporting['reason']
    reason_height = height(reason_text, max(80, int((width-90)/9)), 17)
    tall = int(tree_bottom + (link_height + 78 if link_height else 0) + reason_height + 220)
    title = 'Current reporting structure' if current_only else 'Reporting relationships'
    description = 'The current formal reporting structure is shown for review. No proposed arrangement is implied.' if current_only else 'Current and proposed formal reporting structures are shown side by side.'
    parts = document('reporting', title, description+' Solid lines connect a role to its formal manager above. Unknown reporting and managers outside scope are labelled explicitly.', width, tall)
    parts += [text(title, 45, 56, size=35, serif=True), text('Solid lines show formal reporting. Each lower role reports to the connected role above.', 45, 97, width=150, size=19, colour=MUTED), f'<path d="M45 128 H{width-45}" stroke="{RULE}"/>']
    if not current_only:
        parts += [text(STATUSES[reporting['status']], width-45, 54, size=17, colour=TEAL if reporting['status']=='changed' else MUTED, weight=600, anchor='end'),f'<path d="M{width/2} 149 V{tree_bottom}" stroke="{RULE}"/>']
    all_roles = {side: {r['id']: r for r in data[side+'_roles']} for side in ('current', 'proposed')}
    for side, offset in ([('current', 45)] if current_only else [('current', 45), ('proposed', side_width+75)]):
        roles = data[side+'_roles']
        positions, leaves, _, _ = layouts[side]
        x_shift = (side_width - leaves*314)/2
        coords = {ident: (offset+x_shift+slot*314+157, top+level*level_pitch) for ident,(slot,level) in positions.items()}
        parts += [text(side.capitalize(), offset, 171, size=27, serif=True), text(reporting[side+'_context'] or 'Context not recorded.', offset, 207, width=max(30, int((side_width-42)/9)), size=17, colour=MUTED)]
        if not roles:
            parts.append(text('No human reporting roles recorded.', offset, top+60, width=48, size=20, colour=MUTED))
        for role in roles:
            parent = role['parent_id']
            if parent is None:
                continue
            x, y = coords[role['id']]
            px, py = coords[parent]
            opposite = all_roles['proposed' if side == 'current' else 'current'].get(role['id'])
            changed = not current_only and (opposite is None or opposite['parent_id'] != parent)
            colour = (TEAL if side == 'proposed' else ORANGE) if changed else MUTED
            parts.append(f'<path d="M{px} {py+node_height} V{y-40} H{x} V{y}" fill="none" stroke="{colour}" stroke-width="{2.8 if changed else 1.3}" data-reporting-edge="{esc(role["id"])}" data-side="{side}"/>')
        for role in roles:
            ident = role['id']
            x, y = coords[ident]
            state = role.get('reporting_status', 'known_parent' if role['parent_id'] else 'unknown')
            opposite = all_roles['proposed' if side == 'current' else 'current'].get(ident)
            changed = not current_only and (opposite is None or opposite['parent_id'] != role['parent_id'])
            colour = (TEAL if side=='proposed' else ORANGE) if changed else RULE
            dash = ' stroke-dasharray="6 5"' if state == 'unknown' else ''
            body = [f'<rect class="node-border" x="{x-139}" y="{y}" width="278" height="{node_height}" fill="{ "#EDF5F0" if changed and side == "proposed" else PAPER}" stroke="{colour}" stroke-width="{2 if changed else 1.2}"{dash}/>']
            kind = role.get('node_type', 'role')
            body.append(icon('users-round' if kind in ('team','unit') else 'user-round', x-16, y+16, 32))
            cursor = y+77
            body.append(text(role['label'], x, cursor, width=25, size=20, weight=600, anchor='middle'))
            cursor += height(role['label'], 25, 20)+6
            detail = role_detail(role)
            body.append(text(detail, x, cursor, width=30, size=15, colour=MUTED, anchor='middle'))
            cursor += height(detail,30,15)+4
            if role['parent_id'] is None:
                body.append(text(REPORTING[state], x, cursor, width=30, size=15, colour=MUTED, anchor='middle'))
            parts.append(f'<g id="reporting-{side}-{stable[ident]}" class="reporting-node" data-role-id="{esc(ident)}" data-side="{side}" tabindex="-1"><title>{esc(role["label"]+": "+role["scope"])}</title>' + ''.join(body) + '</g>')
        if link_height:
            y = tree_bottom+30
            parts.append(text('Additional relationships', offset, y, size=21, serif=True))
            y += 40
            if not reporting['links'][side]:
                parts.append(text('None recorded.',offset,y,size=17,colour=MUTED))
            for link in reporting['links'][side]:
                value = all_roles[side][link['from_id']]['label']+' → '+all_roles[side][link['to_id']]['label']+': '+link['label']
                parts += [f'<path d="M{offset} {y-5} H{offset+35}" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="{ "2 5" if link["kind"]=="coordination" else "8 4"}"/>', text(value,offset+47,y,width=max(30,int((side_width-82)/9)),size=17)]
                y += height(value,max(30,int((side_width-82)/9)),17)+29
    y = tree_bottom+(link_height+87 if link_height else 17)
    parts += [text(reason_text,45,y,width=max(80,int((width-90)/9)),size=17,colour=MUTED)]
    y += reason_height+35
    parts += [f'<path d="M45 {y} H89" stroke="{MUTED}" stroke-width="1.5"/>',text('Formal reporting',100,y+6,size=16,colour=MUTED),f'<path d="M290 {y} H334" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="2 5"/>',text('Coordination',345,y+6,size=16,colour=MUTED),f'<path d="M505 {y} H549" stroke="{MUTED}" stroke-width="1.5" stroke-dasharray="8 4"/>',text('Functional relationship',560,y+6,size=16,colour=MUTED)]
    if not current_only:
        parts.append(text('Orange / teal lines identify changed formal relationships.',865,y+6,width=56,size=16,colour=MUTED))
    final_note = 'All recorded levels are shown. Full responsibilities and unresolved relationships appear in the accompanying role record.' if current_only else 'All recorded levels are shown. Agent execution appears in the division of work; it does not create a human reporting line.'
    parts += [text('A person or role can hold human accountability. A team or unit groups people and does not identify one accountable human.',45,y+53,width=max(90,int((width-90)/9)),size=17,colour=MUTED),text(final_note,45,y+90,width=max(90,int((width-90)/9)),size=17,colour=MUTED),text('Prepared by Dr. Shiva Kakkar',width-45,tall-13,size=14,colour=MUTED,anchor='end'),'</svg>']
    return ''.join(parts)


def _role_register(data, current_only=False):
    parts = ['<details class="role-register"><summary>Read the complete role and unit record</summary><div class="role-columns">']
    for side in (('current',) if current_only else ('current','proposed')):
        lookup = {r['id']:r for r in data[side+'_roles']}
        parts.append('<section><h3>'+side.capitalize()+'</h3>')
        for role in data[side+'_roles']:
            parent = lookup.get(role['parent_id'])
            reporting = parent['label'] if parent else REPORTING[role.get('reporting_status','unknown')]
            parts.append(f'<details class="role-detail" data-role-record="{esc(role["id"])}"><summary>{esc(role["label"])}</summary><dl>')
            for name,value in [('Formal reporting',reporting),('Representation',role.get('node_type','role')),('Recorded size',role.get('size','Not specified.')),('Scope',role['scope']),('Reason',role['reason'])]:
                parts.append(f'<dt>{name}</dt><dd>{esc(value or "Not recorded.")}</dd>')
            parts.append('</dl><ul>'+''.join('<li>'+esc(task)+'</li>' for task in role['responsibilities'])+'</ul></details>')
        parts.append('</section>')
    parts.append('</div></details>')
    return ''.join(parts)


def _service_register(data):
    if not data['services']:
        return ''
    roles = {r['id']: r['label'] for r in data['proposed_roles']}
    def owner(ident):
        return roles.get(ident, 'To confirm')
    parts = ['<section class="service-record"><h2>Proposed agent-service responsibilities</h2><p>These are the proposed service arrangements. Their inclusion does not establish that they are currently deployed.</p>']
    for service in data['services']:
        parts.append('<details class="role-detail"><summary>'+esc(service['label'])+'</summary><dl>')
        for label,value in [('Accountable outcome owner',owner(service['outcome_owner_id'])),('Workflow supervisor',owner(service['supervisor_id'])),('Service maintenance owner',owner(service['service_owner_id'])),('Proposed availability',service['availability']),('Shared with',service['shared_with'])]:
            parts.append('<dt>'+label+'</dt><dd>'+esc(value or 'Not recorded.')+'</dd>')
        parts.append('</dl>')
        for agent in service['agent_roles']:
            parts.append('<details class="agent-detail"><summary>'+esc(agent['label'])+'</summary><ul>'+''.join('<li>'+esc(task)+'</li>' for task in agent['tasks'])+'</ul><dl>')
            for label,value in [('Permission boundary',agent['autonomy']),('Receives',agent['inputs']),('Passes onward',agent['outputs']),('Tools',', '.join(agent['tools'])),('Exception recipient',owner(agent['escalation_to_id'])),('Exception condition',agent['escalation_condition']),('Recorded instances',str(agent['instances']) if agent['instances'] is not None else 'Not specified; this symbol represents a role or collection of work.')]:
                parts.append('<dt>'+label+'</dt><dd>'+esc(value or 'Not recorded.')+'</dd>')
            parts.append('</dl></details>')
        parts.append('</details>')
    parts.append('</section>')
    return ''.join(parts)


def render(data, current_only=False):
    """Return a complete offline HTML comparison, rejecting invalid input."""
    checked(data)
    css = (ROOT/'assets'/'comparison.css').read_text(encoding='utf-8')
    if data['workflows'] and not current_only:
        css += '\n' + (ROOT/'assets'/'workflow.css').read_text(encoding='utf-8')
    js = (ROOT/'assets'/'comparison.js').read_text(encoding='utf-8')
    organisation = data['organisation']
    comparison = data['comparison']
    staffing_current = current_only and comparison.get('staffing')
    visible_title = 'Current human posts' if staffing_current else data['title']
    visible_scope = (str(len(comparison['staffing']['current'])) + ' human posts in the recorded service unit. Each human symbol represents one post.') if staffing_current else organisation['scope']
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>'+esc(visible_title)+'</title><style>'+css+'</style></head><body><main>']
    parts.append('<header><h1>'+esc(visible_title)+'</h1><p class="intro">'+esc(visible_scope)+'</p>')
    parts.append('</header>')
    parts.append('<details class="context" aria-label="Comparison scope"><summary>Scope, outcomes and record status</summary><p class="record-state">'+('Participant-confirmed record' if data['status']=='confirmed' else 'Draft for participant review')+' · Revision '+str(data['revision'])+'</p><dl>')
    for label,value in [('Manager’s perspective',comparison['perspective']),('People and units represented',comparison['scale']),('Outcomes examined','; '.join(o['name'] for o in data['outcomes'])),('Outside this exercise',organisation['exclusions'])]:
        parts.append('<div><dt>'+esc(label)+'</dt><dd>'+esc(value or 'Not recorded.')+'</dd></div>')
    parts.append('</dl></details>')
    if current_only:
        current_data=dict(data,proposed_roles=[],workflows=[])
        current_svg=organisation_module(current_data).render_organisation_svg(current_data,SimpleNamespace(**globals()))
        current_details=organisation_module(current_data).render_organisation_details(current_data,SimpleNamespace(**globals()))
        parts.append('<section class="comparison-panel" aria-label="Current reporting structure"><div class="diagram-scroll" tabindex="0" aria-label="Scrollable current reporting diagram">'+current_svg+'</div><details class="supporting-detail"><summary>Inspect people and AI groups</summary>'+current_details+'</details></section>')
        questions = [] if staffing_current else data['open_questions']
        evidence = 'This is the current side of an illustrative employee-services example.' if staffing_current else data['evidence_note']
        parts.append('<section class="record-notes"><h2>Check the current structure</h2><p>Review the recorded contributors, formal managers and unresolved relationships before proposing a division of work.</p><ul>'+''.join('<li>'+esc(question)+'</li>' for question in questions)+'</ul><p>'+esc(evidence)+'</p></section><footer><p>Prepared by Dr. Shiva Kakkar · <a href="https://www.shivakakkar.com/">Click here to access the profile and programme enquiries</a></p></footer></main><script>'+js+'</script></body></html>')
        return ''.join(parts)
    views = [('organisation', 'Organisation')]
    if data['workflows']:
        views.append(('workflow', 'Workflow'))
    views.extend([('division', 'Division of work'), ('reporting', 'Formal reporting'), ('decisions', 'Decision authority')])
    parts.append('<nav class="view-controls" aria-label="Choose a comparison">' + ''.join(
        f'<button type="button" data-view-target="{kind}" aria-controls="view-{kind}" aria-pressed="{str(kind == "organisation").lower()}">{label}</button>'
        for kind, label in views) + '</nav>')
    parts.append('<p class="reading-note">Select a person, AI group or activity to see its responsibilities and decisions.</p>')
    for kind,svg in [('organisation',render_organisation_svg(data)),('division',render_division_svg(data)),('reporting',render_reporting_svg(data)),('decisions',render_decisions_svg(data))]:
        parts.append(f'<section id="view-{kind}" data-view-panel="{kind}" class="comparison-panel" aria-label="{esc(kind.capitalize())}">')
        if kind=='reporting':
            unique = {}
            for side in ('current','proposed'):
                for role in data[side+'_roles']:
                    unique.setdefault(role['id'],role['label'])
            options = ''.join(f'<option value="{esc(ident)}">{esc(label)}</option>' for ident,label in unique.items())
            parts.append('<div class="reporting-tools"><label for="role-focus">Locate a role or unit</label><select id="role-focus"><option value="">Show all recorded relationships</option>'+options+'</select><button type="button" id="reset-role-focus">Clear selection</button></div><p class="reading-note">Scroll across a wide structure. All recorded levels remain available. Select a role or unit to locate it in both views and read its full record below.</p>')
        parts.append('<div class="diagram-scroll" tabindex="0" aria-label="Scrollable '+kind+' diagram">'+svg+'</div>')
        if kind=='reporting':
            parts.append('<p id="role-focus-status" class="reading-note" aria-live="polite"></p>'+_role_register(data))
        if kind=='organisation':
            if comparison.get('staffing'):
                module = organisation_module(data)
                parts.append(module.render_task_transfers(data, esc))
                parts.append(module.render_capacity_details(data, esc))
            parts.append('<details class="supporting-detail"><summary>Inspect all people and AI groups</summary>'+organisation_module(data).render_organisation_details(data,SimpleNamespace(**globals()))+'</details>')
        elif kind in ('division','decisions'):
            parts.append(work_details(data,kind))
        parts.append('</section>')
    if data['workflows']:
        parts.append('<section id="view-workflow" data-view-panel="workflow" class="comparison-panel" aria-label="Workflow">'
                     + workflow_module().render_workflows(data, SimpleNamespace(**globals())) + '</section>')
    parts.append('<details class="supporting-detail"><summary>Agent service responsibilities</summary>'+_service_register(data)+'</details>')
    parts.append('<details class="supporting-detail"><summary>Open questions, evidence and comparison key</summary><section class="record-notes"><h2>What remains to be decided</h2>')
    parts.append('<ul>'+''.join('<li>'+esc(question)+'</li>' for question in data['open_questions'])+'</ul>' if data['open_questions'] else '<p>No open questions are recorded.</p>')
    parts.append('<p class="status-key"><strong>Changed:</strong> an actual proposed difference. <strong>Retained:</strong> a choice to keep the arrangement. <strong>Newly specified:</strong> earlier practice unknown. <strong>Not assessed:</strong> no redesign decision yet.</p><details><summary>Read the evidence and limits</summary><p>'+esc(data['evidence_note'])+'</p><p>'+esc(organisation['context'])+'</p><p>'+esc(organisation['horizon'])+'</p></details></section></details>')
    parts.append('<footer><p>Prepared by Dr. Shiva Kakkar · <a href="https://www.shivakakkar.com/">Click here to access the profile and programme enquiries</a></p><p>Sketchyicons are used under the bundled licence. The visual style adapts Editorial Magazine Interface by StyleRef.io. This record proposes arrangements; it does not activate agents or change company authority.</p></footer></main><script>'+js+'</script></body></html>')
    return ''.join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path)
    parser.add_argument('output',type=Path,nargs='?')
    parser.add_argument('--validate-only',action='store_true')
    parser.add_argument('--current-only',action='store_true',help='Render supplied current roles for discovery; do not imply a proposed structure.')
    for kind in ('organisation','division','reporting','decisions'):
        parser.add_argument('--'+kind+'-svg',type=Path)
    args=parser.parse_args(argv)
    if args.current_only and (args.division_svg is not None or args.decisions_svg is not None or args.organisation_svg is not None):
        parser.error('--current-only supports only the current reporting SVG export.')
    destinations=[path for path in [args.output,args.organisation_svg,args.division_svg,args.reporting_svg,args.decisions_svg] if path is not None]
    source=args.input.resolve()
    def same_file(left, right):
        return left.resolve() == right.resolve() or (left.exists() and right.exists() and left.samefile(right))
    if any(same_file(source, path) for path in destinations):
        parser.error('An output path cannot overwrite the input record.')
    if any(same_file(left,right) for i,left in enumerate(destinations) for right in destinations[i+1:]):
        parser.error('Output paths must be distinct.')
    if not args.validate_only and args.output is None:
        parser.error('OUTPUT is required unless --validate-only is used.')
    try:
        data=json.loads(args.input.read_text(encoding='utf-8'))
        checked(data)
        if args.validate_only:
            print('Valid comparison record.')
            return 0
        outputs=[(args.output,render(data,current_only=args.current_only))]
        for kind,renderer in [('organisation',render_organisation_svg),('division',render_division_svg),('reporting',render_reporting_svg),('decisions',render_decisions_svg)]:
            path=getattr(args,kind+'_svg')
            if path is not None:
                outputs.append((path,renderer(data,current_only=True) if args.current_only and kind=='reporting' else renderer(data)))
        # All input validation and rendering finish before the first write.
        for path,content in outputs:
            path.parent.mkdir(parents=True,exist_ok=True)
            path.write_text(content,encoding='utf-8')
        print('Wrote '+str(len(outputs))+' comparison artifact'+('s.' if len(outputs)!=1 else '.'))
        return 0
    except (OSError,ValueError,json.JSONDecodeError) as exc:
        print(str(exc),file=sys.stderr)
        return 1


if __name__=='__main__':
    raise SystemExit(main())
