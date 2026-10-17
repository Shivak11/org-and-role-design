"""Compact paired human hierarchy and explicitly recorded AI associations.

The caller supplies render_comparison as ``api`` so this module has no circular
imports and importing it never writes files or loads an example record.
"""
from collections import defaultdict
import textwrap


def _wrap(value, width):
    return textwrap.wrap(str(value), width=max(10, width), break_long_words=True,
                         break_on_hyphens=False) or ['']


def _tree(roles):
    lookup = {role['id']: role for role in roles}
    children = defaultdict(list)
    for role in roles:
        parent = role.get('parent_id')
        children[parent if parent in lookup else None].append(role['id'])
    order, depths, visited = [], {}, set()
    def visit(ident, depth):
        if ident in visited:
            return
        visited.add(ident)
        order.append(ident)
        depths[ident] = depth
        for child in children[ident]:
            visit(child, depth + 1)
    for ident in children[None]:
        visit(ident, 0)
    for ident in lookup:
        visit(ident, 0)
    return lookup, order, depths


def _kind(group):
    return {'assistant': 'AI assistant', 'agent': 'Agent work',
            'mixed': 'Assistant + agents',
            'unknown': 'AI type to confirm'}.get(group.get('ai_kind'), 'AI type to confirm')


def _relationship(group, side):
    return group.get('relationship') or ('supervises' if side == 'proposed' else 'unknown')


def _state(group, api):
    return api.STATUSES.get(group.get('status'), 'Not assessed')


def _role_caption(role):
    if role.get('chart_caption'):
        return role['chart_caption']
    if role.get('node_type') in ('role','person') and role.get('scope') and len(role['scope'].split()) <= 9:
        return role['scope']
    if role.get('node_type') == 'person':
        scope = role.get('scope', '')
        return scope if len(scope.split()) <= 7 else 'Human · view role details'
    kind = {'team': 'Team', 'unit': 'Unit', 'role': 'Human role'}.get(role.get('node_type'), 'Human role')
    return kind + (' · ' + role['size'] if role.get('size') else '')


def _groups(data, side):
    organisation = data.get('comparison', {}).get('organisation', {})
    return organisation.get(side, [])


def _side_note(data, side):
    organisation = data.get('comparison', {}).get('organisation', {})
    if side not in organisation:
        return 'AI associations not recorded; only the human structure is shown.'
    return organisation.get(side + '_note') or ('No AI associations recorded.' if not organisation[side] else '')


def _group_height(group):
    return 79 + 23 * len(_wrap(group['label'], 22)) + 20 * len(_wrap(group.get('summary',''),25))


def _layout(data):
    sides = ('current', 'proposed') if data.get('proposed_roles') else ('current',)
    trees = {side: _tree(data.get(side + '_roles', [])) for side in sides}
    order = list(trees['current'][1])
    if 'proposed' in trees:
        # Stable roles retain exactly the same row even if formal parents change.
        for ident in trees['proposed'][1]:
            if ident not in order:
                order.append(ident)
    depth_max = max((max(tree[2].values(), default=0) for tree in trees.values()), default=0)
    half = max(726, 642 + depth_max * 32)
    groups = {}
    for side in sides:
        by_owner = defaultdict(list)
        for group in _groups(data, side):
            owner = group.get('supervisor_id')
            by_owner[owner if owner in trees[side][0] else None].append(group)
        groups[side] = by_owner
    y, rows = 202, {}
    for ident in order:
        tall = 105
        for side in sides:
            role = trees[side][0].get(ident)
            if role:
                label_height = 25 * len(_wrap(role['label'], 25))
                caption_height = 20 * len(_wrap(_role_caption(role), 29))
                tall = max(tall, 40 + label_height + caption_height)
            owned = groups[side][ident]
            if owned:
                tall = max(tall, sum(_group_height(g) + 18 for g in owned) + 15)
        rows[ident] = (y, tall)
        y += tall
    detached = max((sum(_group_height(g) + 18 for g in groups[s][None]) for s in sides), default=0)
    height = y + (detached + 70 if detached else 0) + 132
    return sides, trees, order, half, groups, rows, y, height


def render_organisation_svg(data, api):
    """Return a standalone SVG; explicit AI associations are never inferred."""
    sides, trees, order, half, groups, rows, bottom, height = _layout(data)
    width = half * len(sides) + 48
    parts = api.document('organisation', 'Current and proposed human-AI organisation',
        'Aligned human roles show formal reporting with solid branches. Dashed teal lines show explicit AI use or supervision. Select a node to read its details.', width, height)
    parts.append('<style>a:focus{outline:none}a:focus circle,a:focus path{stroke-width:3}a:hover .node-action{text-decoration:underline}</style>')
    if len(sides) == 2:
        parts.append(f'<path d="M{half+24} 28 V{height-85}" stroke="{api.RULE}"/>')
    for side_index, side in enumerate(sides):
        origin = 24 + side_index * half
        left, ai_x = origin + 32, origin + half - 246
        lookup, _, depths = trees[side]
        parts.append(api.text(side.capitalize(), left, 56, size=31, serif=True))
        note = _side_note(data, side)
        if note:
            note_lines = _wrap(note, 75)
            # The complete note is available below the SVG; keep opening concise.
            visible = note if len(note_lines) <= 3 else ('AI associations recorded.' if _groups(data, side) else 'AI associations not recorded; see details.')
            parts.append(api.text(visible, left, 90, width=75, size=15, colour=api.MUTED, lh=21))
        parts.append(api.text('Human reporting', left, 163, size=15, colour=api.MUTED, weight=600))
        parts.append(api.text('AI work', ai_x + 12, 163, size=15, colour=api.TEAL, weight=600))
        parts.append(f'<path d="M{left} 178 H{origin+half-30}" stroke="{api.RULE}"/>')
        # Connectors are drawn first, behind every node.
        for ident in order:
            role = lookup.get(ident)
            if not role:
                continue
            y = rows[ident][0] + 29
            x = left + depths[ident] * 32 + 23
            parent = role.get('parent_id')
            if parent in lookup:
                py = rows[parent][0] + 29
                px = left + depths[parent] * 32 + 23
                other = trees.get('current', ({},))[0].get(ident, {})
                changed = side == 'proposed' and ident in trees['current'][0] and other.get('parent_id') != parent
                colour = api.ORANGE if changed else api.INK
                parts.append(f'<path d="M{px} {py+24} V{y} H{x-24}" fill="none" stroke="{api.INK}" stroke-width="1.4"/>')
                if changed:
                    parts.append(f'<path d="M{px} {y} H{x-24}" fill="none" stroke="{colour}" stroke-width="3"/>')
        for ident in order:
            role = lookup.get(ident)
            y, tall = rows[ident]
            if not role:
                other = next((trees[s][0][ident] for s in sides if ident in trees[s][0]), {})
                parts.append(api.text('Role absent from this structure', left + 25, y + 34, width=38, size=14, colour=api.MUTED))
                continue
            x = left + depths[ident] * 32
            label_lines = _wrap(role['label'], 25)
            label_y = y + 18
            target = f'org-{side}-{ident}'
            parts.append(f'<a href="#{api.esc(target)}" tabindex="0" aria-label="{api.esc(side.capitalize()+": "+role["label"]+". View details")}"><title>{api.esc(role["label"])}</title>')
            parts.append(api.actor('human', x, y + 5, 46))
            parts.append(api.text(role['label'], x + 58, label_y, width=25, size=19, weight=600, lh=25))
            caption_y = label_y + len(label_lines) * 25
            parts.append(api.text(_role_caption(role), x + 58, caption_y, width=29, size=14, colour=api.MUTED, lh=20))
            action_y = caption_y + 20 * len(_wrap(_role_caption(role), 29))
            state = role.get('reporting_status', 'known_parent' if role.get('parent_id') else 'unknown')
            if state in ('unknown', 'outside_scope'):
                parts.append(api.text('Manager unknown' if state == 'unknown' else 'Manager outside scope', x + 58, action_y, width=31, size=12, colour=api.MUTED))
                action_y += 19
            parts.append(f'<text class="node-action" x="{x+58}" y="{action_y}" font-family="Avenir Next,Avenir,Arial,sans-serif" font-size="12" fill="{api.ORANGE}">View details →</text></a>')
            gy = y
            for group in groups[side][ident]:
                relation = _relationship(group, side)
                gh = _group_height(group)
                connector_y = gy + 36
                from_x = x + 23
                parts.append(f'<path d="M{from_x} {y+5} V{y-12} H{ai_x-27} V{connector_y} H{ai_x}" stroke="{api.TEAL}" stroke-width="1.6" stroke-dasharray="4 4" fill="none"/>')
                parts.append(api.text({'uses': 'Uses', 'supervises': 'Supervises'}.get(relation, 'Association'), ai_x-34, gy-18, size=11, colour=api.TEAL, anchor='end'))
                parts.append(_draw_group(group, side, ai_x, gy, gh, api))
                gy += gh + 18
        if groups[side][None]:
            gy = bottom + 46
            parts.append(api.text('AI supervisor not established', left, bottom + 24, size=16, colour=api.MUTED))
            for group in groups[side][None]:
                gh = _group_height(group)
                parts.append(_draw_group(group, side, ai_x, gy, gh, api))
                gy += gh + 18
    ly = height - 83
    parts.append(f'<path d="M56 {ly-24} H{width-56}" stroke="{api.RULE}"/>')
    parts.append(api.actor('human', 57, ly-7, 28))
    parts.append(api.text('Human', 96, ly+13, size=14, colour=api.MUTED))
    parts.append(f'<path d="M203 {ly+5} H249" stroke="{api.INK}" stroke-width="1.5"/>')
    parts.append(api.text('Reports to', 260, ly+13, size=14, colour=api.MUTED))
    parts.append(f'<path d="M400 {ly+5} H445" stroke="{api.TEAL}" stroke-dasharray="4 4" stroke-width="1.5"/>')
    parts.append(api.text('Uses / supervises AI', 455, ly+13, size=14, colour=api.MUTED))
    parts.append(api.text('Each AI shape represents the labelled work; it does not imply a swarm or instance count.', 57, ly+43, width=145, size=13, colour=api.MUTED))
    parts.append(api.text('Prepared by Dr. Shiva Kakkar', width-56, height-12, size=12, colour=api.MUTED, anchor='end'))
    parts.append('</svg>')
    return ''.join(parts)


def _draw_group(group, side, x, y, height, api):
    target = f'org-{side}-{group["id"]}'
    changed = group.get('status') == 'changed'
    out = [f'<a href="#{api.esc(target)}" tabindex="0" aria-label="{api.esc(side.capitalize()+": "+group["label"]+". View details")}"><title>{api.esc(group["label"])}</title>']
    out.append(api.clipped(x, y, 216, height, '#E6F2ED' if changed else '#F1F6F2', api.TEAL if changed else '#B3CDC6', 2.2 if changed else 1))
    out.append(api.icon('bot', x+12, y+12, 24, api.TEAL))
    out.append(api.text(_kind(group), x+44, y+28, width=24, size=12, colour=api.TEAL))
    out.append(api.text(group['label'], x+14, y+56, width=22, size=16, weight=600, lh=23))
    out.append(api.text(group.get('summary',''), x+14, y+65+23*len(_wrap(group['label'],22)), width=25, size=14, colour=api.MUTED, lh=20))
    out.append(api.text(_state(group, api) + ' · View details →', x+14, y+height-12, width=36, size=11, colour=api.TEAL))
    out.append('</a>')
    return ''.join(out)


def render_organisation_details(data, api):
    """Native details stay readable offline and without JavaScript."""
    out = ['<div class="organisation-details">']
    for side in ('current', 'proposed'):
        roles = data.get(side + '_roles', [])
        if side == 'proposed' and not roles:
            continue
        out.append(f'<h3>{side.capitalize()} structure details</h3>')
        if _side_note(data, side):
            out.append(f'<p>{api.esc(_side_note(data, side))}</p>')
        lookup = {r['id']: r for r in roles}
        for role in roles:
            target = f'org-{side}-{role["id"]}'
            out.append(f'<details id="{api.esc(target)}" class="organisation-node-details"><summary>{api.esc(role["label"])}: human role details</summary>')
            parent = role.get('parent_id')
            state = role.get('reporting_status', 'known_parent' if parent else 'unknown')
            reporting = ('Reports to '+lookup[parent]['label']) if parent in lookup else {'known_root':'Top of the recorded structure.', 'outside_scope':'Formal manager is outside this scope.', 'unknown':'Formal manager not established.'}.get(state, 'Formal manager not established.')
            out.append(f'<p>{api.esc(reporting)}</p>')
            for field, label in [('scope', 'Role / scope'), ('size', 'Recorded size'), ('reason', 'Reason')]:
                if role.get(field):
                    out.append(f'<p><strong>{label}:</strong> {api.esc(role[field])}</p>')
            if role.get('responsibilities'):
                out.append('<ul>'+''.join(f'<li>{api.esc(v)}</li>' for v in role['responsibilities'])+'</ul>')
            assigned = [g for g in _groups(data, side) if g.get('supervisor_id') == role['id']]
            for group in assigned:
                verb = {'uses': 'Uses', 'supervises': 'Supervises'}.get(_relationship(group, side), 'AI association')
                out.append(f'<p>{verb}: <a href="#org-{side}-{api.esc(group["id"])}">{api.esc(group["label"])}: view details</a>.</p>')
            for kind, heading in [('division','Work allocation'), ('decisions','Decision authority')]:
                owned = [row for row in data.get('comparison', {}).get(kind, []) if row.get(side, {}).get('owner_id') == role['id']]
                if owned:
                    out.append(f'<h4>{heading}</h4><ul>')
                    for row in owned:
                        item = row[side]
                        values = [f'{key.replace("_", " ").capitalize()}: {item[key]}' for key in ('human_work','agent_work','software_work','handoff','condition') if item.get(key)]
                        out.append(f'<li><strong>{api.esc(row["label"])}.</strong> {api.esc(" ".join(values))}</li>')
                    out.append('</ul>')
            workflow_links = []
            for workflow in data.get('workflows', []):
                for step in workflow.get(side, []):
                    duties = []
                    if step.get('actor_type') == 'human' and step.get('actor_id') == role['id']:
                        duties.append('performs')
                    if role['id'] in step.get('eligible_actor_ids', []):
                        duties.append('eligible performer, excluding the maker' if step.get('exclude_maker') else 'eligible performer')
                    if step.get('owner_id') == role['id']:
                        duties.append('accountable')
                    if step.get('approval_by_id') == role['id']:
                        duties.append('approves')
                    if step.get('escalation', {}).get('to_id') == role['id']:
                        duties.append('receives exceptions')
                    if duties:
                        target_id = api.workflow_step_id(workflow['id'], side, step['id'])
                        workflow_links.append(f'<li><a href="#{api.esc(target_id)}">{api.esc(step.get("summary") or step["action"])}</a>: {api.esc(", ".join(duties))}.</li>')
            if workflow_links:
                out.append('<h4>Workflow contributions</h4><ul>' + ''.join(workflow_links) + '</ul>')
            out.append('</details>')
        for group in _groups(data, side):
            target = f'org-{side}-{group["id"]}'
            out.append(f'<details id="{api.esc(target)}" class="organisation-node-details"><summary>{api.esc(group["label"])}: {api.esc(_kind(group))}</summary>')
            owner = lookup.get(group.get('supervisor_id'))
            label = {'uses': 'Used by', 'supervises': 'Supervised by'}.get(_relationship(group, side), 'Associated human; relationship not established')
            out.append(f'<p><strong>{label}:</strong> {api.esc(owner["label"] if owner else "Not established")}.</p>')
            out.append(f'<p><strong>Comparison status:</strong> {api.esc(_state(group, api))}.</p>')
            for field in ('summary', 'detail'):
                if group.get(field):
                    out.append(f'<p>{api.esc(group[field])}</p>')
            instances = group.get('instances')
            out.append(f'<p><strong>Instances:</strong> {api.esc(instances if instances is not None else "Not specified. The shape identifies work, not an agent count or coordinated swarm.")}</p>')
            out.append('</details>')
    out.append('</div>')
    return ''.join(out)
