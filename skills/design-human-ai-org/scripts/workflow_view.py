"""Read-only workflow diagrams and complete, native HTML step records.

The caller supplies the comparison renderer's helpers. This module does not
import that renderer, allocate authority, or turn list order into a permission.
"""
from collections import Counter
import textwrap


KINDS = {'information': 'Information', 'authority': 'Authority',
         'escalation': 'Escalation'}
ACTORS = {'agent': 'AI agent', 'human': 'Human', 'software': 'Software',
          'external': 'External service', 'unknown': 'Execution unresolved'}


def _key(prefix, *values):
    return prefix + '-'.join(str(value).encode('utf-8').hex() for value in values)


def workflow_step_id(workflow_id, side, step_id):
    """Encode each component separately so punctuation cannot create collisions."""
    return _key('workflow-step-', workflow_id, side, step_id)


def _wrap(value, width):
    return textwrap.wrap(str(value), max(8, width), break_long_words=True,
                         break_on_hyphens=False) or ['']


def _short(value, width, count=2):
    lines = _wrap(value, width)
    if len(lines) > count:
        lines = lines[:count]
        lines[-1] = lines[-1].rstrip(' .;,:') + '…'
    return '\n'.join(lines)


def _roles(data, side):
    return {role['id']: role for role in data.get(side + '_roles', [])}


def _human(lookup, ident, unknown='Unresolved'):
    return lookup[ident]['label'] if ident in lookup else unknown


def _actor(step, data, side):
    kind, ident = step['actor_type'], step.get('actor_id')
    if kind == 'human':
        if step.get('eligible_actor_ids'):
            return step.get('actor_label') or 'One eligible human approver'
        canonical = _human(_roles(data, side), ident, 'Human executor unresolved')
    elif kind == 'agent' and side == 'proposed' and ident is not None:
        agents = {a['id']: a for service in data.get('services', [])
                  for a in service.get('agent_roles', [])}
        canonical = agents.get(ident, {}).get('label', step.get('actor_label') or 'AI agent')
    else:
        return step.get('actor_label') or ACTORS.get(kind, 'Execution unresolved')
    label = step.get('actor_label')
    return canonical + (' (' + label + ')' if label and label != canonical else '')


def _lane(step):
    return step['actor_type'] if step['actor_type'] in ('human', 'agent') else 'other'


def _label(api, value, x, y, width, size=13, colour=None, weight=400):
    """Keep line lengths and backgrounds explicit for crossing connectors."""
    return '<g class="workflow-edge-label">' + api.text(
        value, x, y, width=width, size=size, colour=colour or api.MUTED,
        weight=weight, lh=size * 1.35) + '</g>'


def _relations(workflow, side):
    return workflow.get('relations', {}).get(side, [])


def _diagram(workflow, side, data, api):
    steps = workflow[side]
    has_other = any(_lane(step) == 'other' for step in steps)
    lanes = ['agent', 'human'] + (['other'] if has_other else [])
    lane_names = {'agent': 'Agent work', 'human': 'Human work',
                  'other': 'Software / unresolved execution'}
    width, left, usable = 1160, 30, 996
    lane_width = usable / len(lanes)
    node_width = lane_width - 62
    terminal_wrap = int((node_width - 24) / 8)
    cols = {lane: left + i * lane_width + 24 for i, lane in enumerate(lanes)}
    lookup = _roles(data, side)
    layout, y = {}, 115
    for number, step in enumerate(steps, 1):
        summary = _short(step.get('summary') or step['action'], int((node_width - 83) / 9), 3)
        actor = _short(_actor(step, data, side), int((node_width - 83) / 7.7), 2)
        owner = _short('Accountable: ' + _human(lookup, step.get('owner_id')), int((node_width - 28) / 7), 2)
        h = 50 + len(summary.splitlines()) * 23 + len(actor.splitlines()) * 18 + len(owner.splitlines()) * 17
        layout[step['id']] = {'x': cols[_lane(step)], 'y': y, 'h': h,
                              'summary': summary, 'actor': actor, 'owner': owner,
                              'number': number, 'step': step}
        terminal_height = 0
        if step.get('terminal'):
            terminal_height = 52 + len(_wrap(step['terminal']['condition'], terminal_wrap)) * 19 + len(_wrap(step['terminal']['label'], terminal_wrap)) * 21
            layout[step['id']]['terminal_y'] = y + h + 40
        y += h + 78 + terminal_height
    height = y - 18
    relations = _relations(workflow, side)
    indices = {step['id']: i for i, step in enumerate(steps)}
    pair_counts = Counter((r['from_step_id'], r['to_step_id']) for r in relations)
    direct, tracks, occupied = set(), {}, []
    for number, relation in enumerate(relations, 1):
        start, end = relation['from_step_id'], relation['to_step_id']
        if indices[end] == indices[start] + 1 and pair_counts[(start, end)] == 1:
            direct.add(number)
            continue
        low, high = sorted((indices[start], indices[end]))
        track = next((i for i, intervals in enumerate(occupied)
                      if all(high < old_low or low > old_high for old_low, old_high in intervals)), len(occupied))
        if track == len(occupied):
            occupied.append([])
        occupied[track].append((low, high))
        tracks[number] = track
    side_ports = {}
    attached = {}
    for number, relation in enumerate(relations, 1):
        if number not in direct:
            for endpoint, key in [('source', 'from_step_id'), ('target', 'to_step_id')]:
                attached.setdefault(relation[key], []).append((number, endpoint))
    for ident, ports in attached.items():
        box = layout[ident]
        gap = min(24, (box['h'] - 38) / max(1, len(ports) - 1))
        for index, port in enumerate(ports):
            side_ports[port] = box['y'] + box['h'] - 19 - index * gap
    width = max(width, left + usable + 19 + max(0, len(occupied) - 1) * 24 + 38)
    prefix = _key('workflow-figure-', workflow['id'], side)
    desc = ('Steps are ordered from top to bottom. Human and agent lanes identify who performs the work. '
            'Solid information lines carry a named output; heavier authority lines grant permission; '
            'dashed escalation lines request a human decision. Select a step for its full record.')
    if not relations:
        desc = ('Steps are ordered from top to bottom. Human and agent lanes identify who performs the work. '
                'Lines show recorded sequence only; no information, authority or escalation links were supplied. '
                'Select a step for its full record.')
    out = api.document(prefix, side.capitalize() + ': ' + workflow['label'], desc, width, height)
    out.append('<defs>')
    for kind, colour in [('information', api.MUTED), ('authority', api.ORANGE), ('escalation', api.ORANGE)]:
        marker = prefix + '-' + kind
        out.append(f'<marker id="{marker}" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 Z" fill="{colour}"/></marker>')
    out.append('</defs><style>.workflow-edge-label text{paint-order:stroke;stroke:#FFFDF9;stroke-width:5px;stroke-linejoin:round}.workflow-node:focus .workflow-node-border{stroke-width:3}.workflow-node:hover .workflow-node-action{text-decoration:underline}</style>')
    for i, lane in enumerate(lanes):
        x = left + lane_width * i
        out.append(api.text(lane_names[lane], x + 24, 43, width=34, size=16,
                            colour=api.TEAL if lane == 'agent' else api.ORANGE if lane == 'human' else api.MUTED,
                            weight=600, lh=20))
        out.append(f'<path d="M{x+8} 77 H{x+lane_width-8}" stroke="{api.RULE}"/>')
        if i:
            out.append(f'<path d="M{x} 89 V{height-20}" stroke="{api.RULE}" stroke-dasharray="2 7"/>')
    side_counts = Counter()
    edge_labels = []
    for number, relation in enumerate(relations, 1):
        source, target = layout[relation['from_step_id']], layout[relation['to_step_id']]
        kind = relation['kind']
        colour = api.MUTED if kind == 'information' else api.ORANGE
        sw, dash = ('3', '') if kind == 'authority' else ('1.7', ' stroke-dasharray="7 5"') if kind == 'escalation' else ('1.5', '')
        if number in direct:
            sx, sy = source['x'] + node_width / 2, source['y'] + source['h']
            tx, ty = target['x'] + node_width / 2, target['y']
            mid = (sy + ty) / 2
            path = f'M{sx} {sy} V{mid} H{tx} V{ty-5}'
            label_x = min(sx, tx) + 14 if sx != tx else sx + 16
            label_width = min(47, int((width - label_x - 24) / 6.5))
            label = KINDS[kind] + ': ' + relation['label']
            edge_labels.append(_label(api, _short(label, label_width, 2), label_x, mid - 9,
                                      label_width, size=12, colour=colour))
        else:
            # Non-adjacent and return edges stay in a dedicated right-hand gutter.
            # Complete source/target records remain linked below the diagram.
            track = left + usable + 19 + tracks[number] * 24
            sx, sy = source['x'] + node_width, side_ports[(number, 'source')]
            tx, ty = target['x'] + node_width, side_ports[(number, 'target')]
            offset = side_counts[relation['from_step_id']] * 16
            side_counts[relation['from_step_id']] += 1
            path = f'M{sx} {sy} H{track} V{ty} H{tx+5}'
            label_width = max(15, int((track - sx - 20) / 6.5))
            label = KINDS[kind] + ': ' + relation['label']
            edge_labels.append(_label(api, _short(label, label_width, 2),
                                      sx + 13, sy - 10 - offset, label_width, size=11, colour=colour))
        target_id = _key('workflow-relation-', workflow['id'], side, number)
        out.append(f'<a href="#{target_id}" tabindex="0" aria-label="{api.esc(KINDS[kind]+": "+relation["label"])}"><title>{api.esc(KINDS[kind]+": "+relation["label"])}</title><path class="workflow-relation workflow-relation-{kind}" d="{path}" stroke="{colour}" stroke-width="{sw}"{dash} fill="none" marker-end="url(#{prefix}-{kind})"/></a>')
    # Legacy list order is preserved without inventing information or authority.
    if not relations:
        for before, after in zip(steps, steps[1:]):
            source, target = layout[before['id']], layout[after['id']]
            sx, sy = source['x'] + node_width / 2, source['y'] + source['h']
            tx, ty = target['x'] + node_width / 2, target['y']
            mid = (sy + ty) / 2
            out.append(f'<path d="M{sx} {sy} V{mid} H{tx} V{ty}" stroke="{api.RULE}" stroke-width="1" fill="none"/>')
    out.extend(edge_labels)
    for step in steps:
        box = layout[step['id']]
        x, y, h = box['x'], box['y'], box['h']
        kind = step['actor_type']
        colour = api.TEAL if kind == 'agent' else api.ORANGE if kind == 'human' else api.MUTED
        target = workflow_step_id(workflow['id'], side, step['id'])
        out.append(f'<a class="workflow-node" href="#{target}" tabindex="0" aria-label="{api.esc(str(box["number"])+". "+step["action"]+". "+ACTORS[kind]+". View details")}"><title>{api.esc(step["action"])}</title>')
        if kind == 'agent':
            out.append('<g class="workflow-node-border">' + api.clipped(x, y, node_width, h, '#F1F6F2', '#B3CDC6') + '</g>')
        else:
            dashed = ' stroke-dasharray="6 4"' if kind == 'unknown' else ''
            out.append(f'<rect class="workflow-node-border" x="{x}" y="{y}" width="{node_width}" height="{h}" fill="{api.PAPER}" stroke="{api.RULE if kind != "unknown" else api.MUTED}"{dashed}/>')
        icon_kind = kind if kind in ('agent', 'human', 'software', 'unknown') else 'software'
        out.append(api.actor(icon_kind, x + 13, y + 17, 34))
        out.append(api.text(str(box['number']), x + 29, y - 9, size=12, colour=api.MUTED, anchor='middle'))
        title_y = y + 29
        out.append(api.text(box['summary'], x + 60, title_y, width=200, size=17, weight=600, lh=23))
        actor_y = title_y + 23 * len(box['summary'].splitlines()) + 4
        out.append(api.text(box['actor'], x + 60, actor_y, width=200, size=13, colour=colour, lh=18))
        owner_y = actor_y + 18 * len(box['actor'].splitlines()) + 5
        out.append(api.text(box['owner'], x + 14, owner_y, width=200, size=12, colour=api.MUTED, lh=17))
        action_label = 'Execution unresolved · View details' if kind == 'unknown' else 'View details'
        out.append(f'<text class="workflow-node-action" x="{x+14}" y="{y+h-11}" font-family="Avenir Next,Avenir,Arial,sans-serif" font-size="11" fill="{colour}">{action_label}</text></a>')
        if step.get('terminal'):
            terminal_y = box['terminal_y']
            condition = step['terminal']['condition']
            result_y = terminal_y + len(_wrap(condition, terminal_wrap)) * 19 + 10
            cx = x + node_width / 2
            out.append(f'<path d="M{cx} {y+h} V{terminal_y-14}" stroke="{api.MUTED}" fill="none" marker-end="url(#{prefix}-information)"/>')
            out.append(api.text(condition, cx, terminal_y, width=terminal_wrap, size=13, colour=api.MUTED, anchor='middle', lh=19))
            out.append(api.text(step['terminal']['label'], cx, result_y, width=terminal_wrap, size=16, weight=600, anchor='middle', lh=21))
    out.append('</svg>')
    return ''.join(out)


def _pairs(items, api):
    return '<dl>' + ''.join(f'<div><dt>{api.esc(label)}</dt><dd>{value if safe else api.esc(value)}</dd></div>'
                           for label, value, safe in items) + '</dl>'


def _step_details(workflow, side, data, api):
    lookup = _roles(data, side)
    steps = workflow[side]
    step_lookup = {step['id']: step for step in steps}
    out = ['<div class="workflow-step-register">']
    for number, step in enumerate(steps, 1):
        target = workflow_step_id(workflow['id'], side, step['id'])
        out.append(f'<details id="{target}" class="workflow-step-details" data-workflow-step="{api.esc(step["id"])}"><summary><span class="workflow-step-number">{number}</span> {api.esc(step["action"])}</summary>')
        fields = [('Performer', ACTORS[step['actor_type']] + ': ' + _actor(step, data, side), False),
                  ('Accountable human', _human(lookup, step.get('owner_id')), False),
                  ('Input', step['input'], False), ('Returned output', step['output'], False),
                  ('Approval by', _human(lookup, step.get('approval_by_id'), 'No approver recorded for this step'), False),
                  ('Trigger, handoff or exception', step['condition'], False)]
        if step.get('eligible_actor_ids'):
            fields.append(('Eligible performers', 'One of: ' + ', '.join(_human(lookup, i) for i in step['eligible_actor_ids']), False))
            fields.append(('Independence rule', 'The maker cannot approve this change.' if step.get('exclude_maker') else 'No maker exclusion is specified.', False))
        if 'summary' in step and step['summary'] != step['action']:
            fields.append(('Diagram label', step['summary'], False))
        for key, label in [('task_type', 'Type of knowledge work'), ('reasoning', 'Reasoning'), ('handoff_cost', 'Handoff cost')]:
            if key in step:
                fields.append((label, step[key], False))
        if 'knowledge' in step:
            fields.extend([('Rules and stable knowledge', step['knowledge']['rules'], False),
                           ('Case facts', step['knowledge']['facts'], False)])
        if 'terminal' in step:
            fields.extend([('Completion result', step['terminal']['label'], False),
                           ('Completion condition', step['terminal']['condition'], False)])
        if 'authority' in step:
            authority = step['authority']
            fields.extend([('May decide', authority['may_decide'], False),
                           ('Must escalate', authority['must_escalate'], False),
                           ('May override', _human(lookup, authority['override_by_id'], 'Override authority unresolved'), False),
                           ('May stop', _human(lookup, authority['stop_by_id'], 'Stop authority unresolved'), False)])
        if 'escalation' in step:
            escalation = step['escalation']
            fields.extend([('Escalate to', _human(lookup, escalation['to_id'], 'Escalation recipient unresolved'), False),
                           ('Escalation trigger', escalation['trigger'], False)])
            return_id = escalation['return_to_step_id']
            if return_id in step_lookup:
                href = workflow_step_id(workflow['id'], side, return_id)
                value = f'<a href="#{href}">{api.esc(step_lookup[return_id]["action"])}</a>'
                fields.append(('Return after escalation', value, True))
            else:
                fields.append(('Return after escalation', 'Return step unresolved', False))
        out.append(_pairs(fields, api))
        related = [(i, relation) for i, relation in enumerate(_relations(workflow, side), 1)
                   if step['id'] in (relation['from_step_id'], relation['to_step_id'])]
        if related:
            out.append('<ul class="workflow-step-relations">')
            for i, relation in related:
                href = _key('workflow-relation-', workflow['id'], side, i)
                out.append(f'<li><a href="#{href}">{api.esc(KINDS[relation["kind"]]+": "+relation["label"])}</a></li>')
            out.append('</ul>')
        out.append('</details>')
    out.append('</div>')
    return ''.join(out)


def _relation_details(workflow, side, api):
    relations = _relations(workflow, side)
    if not relations:
        return ''
    lookup = {step['id']: step for step in workflow[side]}
    out = ['<details class="workflow-relation-register"><summary>Information, authority and escalation links</summary><ol>']
    for number, relation in enumerate(relations, 1):
        target = _key('workflow-relation-', workflow['id'], side, number)
        out.append(f'<li id="{target}" class="workflow-relation-detail"><strong>{api.esc(KINDS[relation["kind"]])}: {api.esc(relation["label"])}</strong><p>')
        for i, key in enumerate(('from_step_id', 'to_step_id')):
            step_id = relation[key]
            href = workflow_step_id(workflow['id'], side, step_id)
            if i:
                out.append(' → ')
            out.append(f'<a href="#{href}">{api.esc(lookup[step_id].get("summary") or lookup[step_id]["action"])}</a>')
        out.append('</p></li>')
    out.append('</ol></details>')
    return ''.join(out)


def render_workflows(data, helpers):
    """Return panel contents, preserving empty and legacy workflows faithfully."""
    api = helpers
    workflows = data.get('workflows', [])
    if not workflows:
        return '<p class="workflow-empty">No workflows have been recorded.</p>'
    outcomes = {item['id']: item for item in data.get('outcomes', [])}
    out = []
    for workflow in workflows:
        ident = _key('workflow-record-', workflow['id'])
        out.append(f'<article class="workflow-record" id="{ident}"><h2>{api.esc(workflow["label"])}</h2>')
        if workflow.get('outcome_id') in outcomes:
            out.append(f'<p class="workflow-outcome">{api.esc(outcomes[workflow["outcome_id"]]["name"])}</p>')
        if workflow.get('policy'):
            out.append(f'<details class="workflow-policy"><summary>Standing decision rules</summary><p>{api.esc(workflow["policy"])}</p></details>')
        for side in ('current', 'proposed'):
            out.append(f'<section class="workflow-side workflow-side-{side}"><h3>{side.capitalize()} sequence</h3>')
            if workflow.get(side + '_note') and not workflow.get(side):
                out.append(f'<p class="workflow-side-note">{api.esc(workflow[side+"_note"])}</p>')
            if not workflow.get(side):
                if not workflow.get(side + '_note'):
                    out.append('<p class="workflow-empty">No step-level sequence has been recorded.</p>')
                out.append('</section>')
                continue
            if _relations(workflow, side):
                out.append('<ul class="workflow-line-key" aria-label="Workflow link meanings"><li><span class="workflow-key-line information"></span>Information</li><li><span class="workflow-key-line authority"></span>Authority</li><li><span class="workflow-key-line escalation"></span>Escalation</li></ul>')
            out.append('<figure class="workflow-figure">')
            caption = workflow.get(side + '_note') or workflow.get('coverage')
            if caption:
                out.append(f'<figcaption class="workflow-side-note">{api.esc(caption)}</figcaption>')
            out.append(f'<div class="diagram-scroll workflow-diagram" tabindex="0" role="region" aria-label="{api.esc(side.capitalize()+" workflow diagram")}">')
            out.append(_diagram(workflow, side, data, api))
            out.append('</div></figure>')
            out.append(_step_details(workflow, side, data, api))
            out.append(_relation_details(workflow, side, api))
            out.append('</section>')
        out.append('</article>')
    return ''.join(out)
