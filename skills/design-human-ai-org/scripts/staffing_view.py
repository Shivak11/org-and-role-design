"""Counted human posts and transparent workload assumptions for staffing records.

The optional extension uses the comparison renderer's existing SVG helpers.
Legacy records delegate to organisation_view without changing their output.
"""
from collections import defaultdict
import importlib.util
from pathlib import Path


REMOVED = '#A3312B'
WIDTH = 1440


def _module(name):
    spec = importlib.util.spec_from_file_location('_staffing_' + name, Path(__file__).with_name(name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _staffing(data):
    return data.get('comparison', {}).get('staffing')


def _paired(data):
    # The current-only caller deliberately removes proposed roles. Never derive
    # a future view from staffing arrays that remain in that shallow copy.
    return bool(data.get('proposed_roles'))


def _number(value):
    return f'{value:,.2f}'.rstrip('0').rstrip('.') if value % 1 else f'{value:,.0f}'


def _percent(value):
    return _number(value * 100) + '%'


def _layout(posts, left, width, removals, api, officer_ids=()):
    """Lay out the recorded tree; queue spacing never inserts reporting nodes."""
    lookup = {post['id']: post for post in posts}
    children = defaultdict(list)
    for post in posts:
        children[post.get('parent_post_id')].append(post['id'])
    depths, leaves = {}, []

    def visit(ident, depth):
        depths[ident] = depth
        if children[ident]:
            for child in children[ident]:
                visit(child, depth + 1)
        else:
            leaves.append(ident)

    for root in children[None]:
        visit(root, 0)
    gaps = sum(lookup[a].get('group_id') != lookup[b].get('group_id') for a, b in zip(leaves, leaves[1:]))
    step = (width - 36 - gaps * 24) / max(1, len(leaves))
    cursor, xs = left + 18 + step / 2, {}
    previous = None
    for ident in leaves:
        group = lookup[ident].get('group_id')
        if previous is not None and group != previous:
            cursor += 24
        xs[ident] = cursor
        cursor += step
        previous = group

    def centre(ident):
        if ident not in xs:
            values = [centre(child) for child in children[ident]]
            xs[ident] = (min(values) + max(values)) / 2
        return xs[ident]

    for root in children[None]:
        centre(root)
    labels, heights, chart_labels, row_heights = {}, {}, {}, defaultdict(int)
    for post in posts:
        ident = post['id']
        wrap = max(7, min(28, int(step / 9))) if not children[ident] else (26 if len(children[post.get('parent_post_id')]) == 1 else 17)
        suffix = post['label'].rpartition(' ')[2]
        chart_labels[ident] = suffix if ident in officer_ids and post.get('group_id') and suffix.isdigit() else post['label']
        labels[ident] = (wrap, 16 if ident in leaves else 18)
        heights[ident] = 49 + len(api.lines(chart_labels[ident], wrap)) * 21 + (23 if ident in removals else 0)
        row_heights[depths[ident]] = max(row_heights[depths[ident]], heights[ident])
    ys, cursor = {}, 137
    for depth in range(max(depths.values(), default=-1) + 1):
        ys[depth] = cursor
        cursor += row_heights[depth] + 32
    nodes = {ident: {'x': xs[ident], 'y': ys[depths[ident]], 'height': heights[ident],
                     'wrap': labels[ident][0], 'size': labels[ident][1], 'label': chart_labels[ident]} for ident in lookup}
    groups = defaultdict(list)
    for ident in leaves:
        if lookup[ident].get('group_id'):
            groups[lookup[ident]['group_id']].append(ident)
    bottom = max((node['y'] + node['height'] for node in nodes.values()), default=137)
    return {'nodes': nodes, 'groups': groups, 'step': step, 'levels': len(row_heights),
            'bottom': bottom + (65 if groups else 0), 'children': children}


def _draw_posts(data, side, layout, removals, api):
    posts = _staffing(data)[side]
    nodes = layout['nodes']
    out = []
    # Every edge is between two actual posts on the same side, even when several
    # posts share a role type. No edges are inferred from queue membership.
    for post in posts:
        parent = post.get('parent_post_id')
        if parent is None:
            continue
        start, end = nodes[parent], nodes[post['id']]
        start_y, end_y = start['y'] + start['height'] + 3, end['y'] - 8
        bend = (start_y + end_y) / 2
        out.append(f'<path class="staffing-reporting-edge" data-side="{side}" data-parent-post-id="{api.esc(parent)}" data-child-post-id="{api.esc(post["id"])}" d="M{start["x"]} {start_y} V{bend} H{end["x"]} V{end_y}" fill="none" stroke="{api.MUTED}" stroke-width="1.4"/>')
    for post in posts:
        ident = post['id']
        node = nodes[ident]
        x, y = node['x'], node['y']
        removal = removals.get(ident)
        mark = f' data-removed-kind="{removal["kind"]}"' if removal else ''
        full = post['label'] + ('; post removed in the proposal' if removal else '')
        out.append(f'<a class="diagram-link staffing-post" href="#org-post-{side}-{api.esc(ident)}" tabindex="0" data-side="{side}" data-human-post-id="{api.esc(ident)}"{mark} aria-label="{api.esc(full)}"><title>{api.esc(full)}</title>')
        out.append(api.actor('human', x - 19, y, 38))
        if removal:
            out.append(f'<circle cx="{x}" cy="{y+19}" r="25" fill="none" stroke="{REMOVED}" stroke-width="2" stroke-dasharray="5 4"/>')
        out.append(api.text(node['label'], x, y + 56, width=node['wrap'], size=node['size'], anchor='middle', weight=600, lh=21))
        if removal and (removal['kind'] == 'vertical' or not post.get('group_id')):
            out.append(api.text('Removed', x, y + node['height'] - 16, size=14, colour=REMOVED, anchor='middle'))
        out.append('</a>')
    labels = {group['id']: group['label'] for group in _staffing(data)['groups']}
    for group_id, members in layout['groups'].items():
        runs, run = [], []
        for ident in members:
            if removals.get(ident, {}).get('kind') == 'horizontal':
                run.append(ident)
            elif run:
                runs.append(run)
                run = []
        if run:
            runs.append(run)
        for run in runs:
            x1, x2 = nodes[run[0]]['x'] - 22, nodes[run[-1]]['x'] + 22
            y = max(nodes[ident]['y'] + nodes[ident]['height'] for ident in run) - 27
            out.append(f'<path class="staffing-removal-bracket" d="M{x1} {y-4} V{y} H{x2} V{y-4}" fill="none" stroke="{REMOVED}" stroke-width="1.3"/>')
            out.append(api.text(f'{len(run)} posts removed' if len(run) > 1 else 'Removed', (x1+x2)/2, y+20, size=14, colour=REMOVED, anchor='middle'))
        x1 = min(nodes[ident]['x'] for ident in members) - layout['step'] / 2 + 5
        x2 = max(nodes[ident]['x'] for ident in members) + layout['step'] / 2 - 5
        y = max(nodes[ident]['y'] + nodes[ident]['height'] for ident in members) + 10
        out.append(f'<path d="M{x1} {y} H{x2}" stroke="{api.RULE}"/>')
        out.append(api.text(labels[group_id], (x1+x2)/2, y+24, width=24, size=16, anchor='middle', weight=600))
        post_type = 'human' if _staffing(data)['capacity'] is None else 'officer'
        total = sum(post.get('group_id') == group_id for post in posts)
        count = f'{len(members)} of {total} {post_type} posts shown here' if total > len(members) else f'{len(members)} {post_type} '+('post' if len(members) == 1 else 'posts')
        out.append(api.text(count, (x1+x2)/2, y+47, size=15, anchor='middle', colour=api.MUTED))
    return ''.join(out)


def _ai_layout(data, side, layout, left, width, api):
    """Keep AI shapes separate from the counted human reporting tree."""
    groups = data.get('comparison', {}).get('organisation', {}).get(side, [])
    out, y = [], layout['bottom'] + 35
    posts = _staffing(data)[side]
    for index, group in enumerate(groups):
        box_width = min(390, width - 80)
        x = left + (width - box_width) / 2
        label_lines = len(api.lines(group['label'], 34))
        summary_lines = len(api.lines(group.get('summary', ''), 39))
        tall = 64 + label_lines * 23 + summary_lines * 21
        supervisors = [post for post in posts if post['role_id'] == group.get('supervisor_id')]
        if group.get('supervisor_post_id') is not None:
            supervisors = [post for post in supervisors if post['id'] == group['supervisor_post_id']]
        relation = group.get('relationship', 'supervises' if side == 'proposed' else 'unknown')
        word = {'supervises': 'Supervises', 'uses': 'Uses'}.get(relation, 'AI relationship not established')
        if len(supervisors) == 1 and relation in ('supervises', 'uses'):
            supervisor = supervisors[0]
            node = layout['nodes'][supervisor['id']]
            lane = left + width - 6 - index * 8
            end_y = y + tall / 2
            out.append(f'<path class="staffing-ai-link" data-side="{side}" data-supervisor-post-id="{api.esc(supervisor["id"])}" data-agent-group-id="{api.esc(group["id"])}" d="M{node["x"]+24} {node["y"]+19} H{lane} V{end_y} H{x+box_width}" fill="none" stroke="{api.TEAL}" stroke-width="1.5" stroke-dasharray="4 4"/>')
            caption = supervisor['label'] + ' ' + word.lower()
        else:
            caption = 'AI supervisor not established' if not supervisors else 'Supervisor role: ' + supervisors[0]['label']
        out.append(api.text(caption, x, y-12, width=48, size=15, colour=api.TEAL))
        out.append(f'<a class="diagram-link" href="#org-{side}-{api.esc(group["id"])}" tabindex="0" aria-label="{api.esc(group["label"])}"><title>{api.esc(group["label"])}</title>')
        out.append(api.clipped(x, y, box_width, tall, '#E6F2ED', api.TEAL))
        out.append(api.icon('bot', x+15, y+14, 27, api.TEAL))
        out.append(api.text({'assistant': 'AI assistant', 'agent': 'Agent work', 'mixed': 'Assistant + agents'}.get(group.get('ai_kind'), 'AI type to confirm'), x+51, y+34, size=15, colour=api.TEAL))
        out.append(api.text(group['label'], x+16, y+63, width=34, size=18, weight=600, lh=23))
        out.append(api.text(group.get('summary', ''), x+16, y+70+23*label_lines, width=39, size=16, lh=21))
        out.append('</a>')
        y += tall + 53
    return ''.join(out), y-25 if groups else layout['bottom']


def render_organisation_svg(data, api):
    staffing = _staffing(data)
    if staffing is None:
        return _module('organisation_view').render_organisation_svg(data, api)
    paired = _paired(data)
    removals = {item['post_id']: item for item in staffing['removed']} if paired else {}
    sides = [('current', 28, 826), ('proposed', 892, 520)] if paired else [('current', 28, WIDTH-56)]
    layouts, ai_parts, bottoms = {}, {}, []
    capacity = staffing['capacity']
    for side, left, width in sides:
        layouts[side] = _layout(staffing[side], left, width, removals if side == 'current' else {}, api,
                                capacity[side+'_officer_post_ids'] if capacity is not None else ())
        ai_parts[side], bottom = _ai_layout(data, side, layouts[side], left, width, api)
        bottoms.append(bottom)
    chart_bottom = max(bottoms)
    legend_y, tall = chart_bottom + 48, chart_bottom + 150
    title = 'Current and proposed human posts' if paired else 'Current human posts'
    description = '; '.join(f'{side.capitalize()}: {len(staffing[side])} human posts, {layouts[side]["levels"]} reporting levels' for side, _, _ in sides)
    out = api.document('staffing', title, description, WIDTH, tall)
    for side, left, width in sides:
        out.append(api.text(f'{side.capitalize()}: {len(staffing[side])} human posts', left+4, 46, size=28, serif=True))
        out.append(api.text(f'{layouts[side]["levels"]} reporting levels', left+4, 78, size=18, colour=api.MUTED))
    if paired:
        vertical = sum(item['kind'] == 'vertical' for item in staffing['removed'])
        horizontal = sum(item['kind'] == 'horizontal' for item in staffing['removed'])
        post_type = 'delivery' if capacity is None else 'officer'
        management_word = 'post' if capacity is None and vertical == 1 else 'posts'
        delivery_word = 'post' if capacity is None and horizontal == 1 else 'posts'
        out.append(api.text(f'{vertical} management {management_word} and {horizontal} {post_type} {delivery_word} removed', 32, 108, width=80, size=16, colour=REMOVED))
        out.append(api.text(f'{layouts["current"]["levels"]} → {layouts["proposed"]["levels"]} levels; {len(staffing["current"])} → {len(staffing["proposed"])} posts', 896, 108, size=18, weight=600))
        out.append(f'<path d="M873 28 V{chart_bottom+13}" stroke="{api.RULE}"/>')
    for side, _, _ in sides:
        out.append(_draw_posts(data, side, layouts[side], removals if side == 'current' else {}, api))
        out.append(ai_parts[side])
    out.append(f'<path d="M32 {legend_y-20} H1408" stroke="{api.RULE}"/>')
    out.append(f'<path d="M32 {legend_y} H70" stroke="{api.MUTED}" stroke-width="1.4"/>')
    out.append(api.text('Formal reporting', 81, legend_y+5, size=16, colour=api.MUTED))
    out.append(f'<path d="M290 {legend_y} H328" stroke="{api.TEAL}" stroke-width="1.5" stroke-dasharray="4 4"/>')
    out.append(api.text('Human supervision or use of AI', 339, legend_y+5, size=16, colour=api.MUTED))
    if paired:
        out.append(f'<circle cx="702" cy="{legend_y}" r="13" fill="none" stroke="{REMOVED}" stroke-width="2" stroke-dasharray="5 4"/>')
        out.append(api.text('Removed post; vertical = manager, horizontal = '+post_type, 729, legend_y+5, width=67, size=16, colour=REMOVED))
        out.append(api.text(staffing['basis'], 32, legend_y+39, width=153, size=16, colour=api.MUTED))
    else:
        out.append(api.text('Each human symbol is one recorded post.', 32, legend_y+39, size=16, colour=api.MUTED))
    out.append(api.text('AI shapes identify work; they do not specify running instance counts.', 32, legend_y+68, width=135, size=15, colour=api.MUTED))
    out.append('</svg>')
    return ''.join(out)


def render_organisation_details(data, api):
    legacy = _module('organisation_view').render_organisation_details(data, api)
    staffing = _staffing(data)
    if staffing is None:
        return legacy
    paired = _paired(data)
    removals = {item['post_id']: item for item in staffing['removed']} if paired else {}
    tasks = {row['id']: row for row in data['comparison']['division']}
    out = ['<div class="organisation-details staffing-post-details">']
    for side in ('current', 'proposed') if paired else ('current',):
        posts = {post['id']: post for post in staffing[side]}
        out.append(f'<h3>{side.capitalize()} human posts</h3>')
        for post in posts.values():
            removal = removals.get(post['id']) if side == 'current' else None
            target = f'org-post-{side}-{post["id"]}'
            out.append(f'<details id="{api.esc(target)}" class="organisation-node-details"><summary>{api.esc(post["label"])}: '+('post removed in the proposal' if removal else 'one human post')+'</summary>')
            parent = posts.get(post['parent_post_id'])
            out.append('<p>'+api.esc('Reports to '+parent['label']+'.' if parent else 'Top of this recorded structure.')+'</p>')
            if removal:
                out.append('<p>'+api.esc(removal['reason'])+'</p><p>Affected work:</p><ul>')
                for ident in removal['work_ids']:
                    out.append(f'<li><a href="#work-division-{api.esc(ident)}">{api.esc(tasks[ident]["label"])}</a></li>')
                out.append('</ul>')
            out.append(f'<p><a href="#org-{side}-{api.esc(post["role_id"])}">Read the role responsibilities and decision limits</a>.</p></details>')
    out.append('</div>')
    return ''.join(out) + legacy


def _table(headers, rows, esc, caption):
    # Inline extension-only styling also works in the separate workbook renderer.
    cell = 'padding:10px 12px;border-bottom:1px solid #D9D2C4;text-align:left;vertical-align:top;line-height:1.5'
    out = ['<div style="max-width:100%;overflow-x:auto"><table style="width:100%;border-collapse:collapse;font-size:1rem">',
           '<caption style="text-align:left;font-weight:600;padding:8px 12px">'+esc(caption)+'</caption><thead><tr>']
    out.extend(f'<th scope="col" style="{cell}">{esc(header)}</th>' for header in headers)
    out.append('</tr></thead><tbody>')
    for row in rows:
        out.append('<tr>'+''.join(f'<td style="{cell}">{value}</td>' for value in row)+'</tr>')
    out.append('</tbody></table></div>')
    return ''.join(out)


def render_task_transfers(data, esc):
    """Short task comparison for the visible area below the counted chart."""
    staffing = _staffing(data)
    if staffing is None or not _paired(data):
        return ''
    affected = {ident for item in staffing['removed'] for ident in item['work_ids']}
    rows = []
    for row in data['comparison']['division']:
        if row['id'] not in affected:
            continue
        current, proposed = row['current'], row['proposed']
        def summary(item, kinds):
            return '; '.join(item.get(kind+'_summary') or item.get(kind+'_work', '') for kind in kinds if item.get(kind+'_summary') or item.get(kind+'_work'))
        label = f'<a href="#work-division-{esc(row["id"])}" style="color:#191714;text-underline-offset:3px">{esc(row["label"])}</a>'
        unknown_current = current.get('mode') == 'unknown'
        unknown_proposed = proposed.get('mode') == 'unknown'
        rows.append((label, esc(summary(current, ('human', 'agent', 'software')) or ('Execution not established' if unknown_current else 'No activity')),
                     esc(summary(proposed, ('agent', 'software')) or ('AI or software contribution not established' if unknown_proposed else 'No AI or software contribution')),
                     esc(summary(proposed, ('human',)) or ('Human contribution not established' if unknown_proposed else 'No routine human handling'))))
    return '<section class="staffing-task-transfers" aria-label="Work transferred from removed posts">'+_table(
        ('Work', 'Current handling', 'Proposed AI or software work', 'Proposed human work'), rows, esc,
        'Where the work of removed posts goes')+'</section>'


def render_capacity_details(data, esc):
    """Visible assumption summary plus native disclosure; safe for either HTML."""
    staffing = _staffing(data)
    if staffing is None or not _paired(data):
        return ''
    c = staffing['capacity']
    if c is None:
        return ('<section class="staffing-capacity" aria-label="Workload basis"><h3>Workload basis</h3><p>'
                + esc(staffing['capacity_note']) + '</p></section>')
    calculate = _module('staffing_contract').capacity_summary
    result = calculate(data)
    n, pct = _number, _percent
    fit = 'fit within' if result['fits'] else 'exceed'
    out = ['<section class="staffing-capacity" aria-label="Workload and staffing assumptions"><h3>Workload and staffing assumptions</h3>',
           '<p>'+esc(f'At an assumed {pct(c["automated_share"])} automated routine completion, the required {n(result["human_hours"])} officer hours a month {fit} the proposal’s {n(result["planned_capacity"])} planned hours. The calculation requires {result["required_posts"]} officer posts; {result["available_posts"]} are proposed.')+'</p>',
           '<details class="supporting-detail"><summary>Inspect the assumptions, arithmetic and lower-automation cases</summary>',
           '<p>'+esc(c['assumption_note'])+'</p>']
    assumptions = [('Monthly cases', n(c['monthly_cases'])), ('Current human minutes per case', n(c['current_minutes_per_case'])),
                   ('Automated routine completion', pct(c['automated_share'])), ('Human minutes per exception, including peer checking', n(c['exception_minutes'])),
                   ('Automated cases sampled', pct(c['sample_share'])), ('Minutes per sampled review', n(c['review_minutes'])),
                   ('Monthly officer control and recovery hours', n(c['operating_hours'])), ('Usable monthly hours per officer', n(c['hours_per_post'])),
                   ('Planning utilisation', pct(c['planning_utilisation'])), ('Operational officer floor', n(c['minimum_posts']))]
    out.append(_table(('Assumption', 'Value'), [(esc(a), esc(b)) for a, b in assumptions], esc, 'Inputs to the officer-capacity calculation'))
    current_capacity = len(c['current_officer_post_ids']) * c['hours_per_post']
    out.append('<p>'+esc(f'Current handling: {n(c["monthly_cases"])} × {n(c["current_minutes_per_case"])} ÷ 60 = {n(result["current_hours"])} hours. The {len(c["current_officer_post_ids"])} current officers provide {n(current_capacity)} usable hours a month.')+'</p>')
    out.append('<p>'+esc(f'Proposed handling: {n(result["exceptions"])} exceptions × {n(c["exception_minutes"])} ÷ 60 + {n(result["samples"])} sampled cases × {n(c["review_minutes"])} ÷ 60 + {n(c["operating_hours"])} control hours = {n(result["human_hours"])} hours.')+'</p>')
    out.append('<p>'+esc(f'Planned capacity: {result["available_posts"]} officers × {n(c["hours_per_post"])} hours × {pct(c["planning_utilisation"])} = {n(result["planned_capacity"])} hours. Required posts are the larger of the {c["minimum_posts"]}-post operational floor and workload divided by {n(c["hours_per_post"] * c["planning_utilisation"])} planned hours per officer, rounded up.')+'</p>')
    rows = []
    for share in (.7, .5, .3):
        scenario = calculate(data, share)
        rows.append((pct(share), n(scenario['human_hours']), str(scenario['required_posts']),
                     'Fits' if scenario['fits'] else f'Short by {scenario["required_posts"]-scenario["available_posts"]} officer posts'))
    out.append(_table(('Automated routine cases', 'Human hours / month', 'Required officer posts', 'Recorded proposal'),
                      [(esc(value) for value in row) for row in rows], esc, 'Sensitivity at the same volume and service assumptions'))
    out.append('<p><strong>Head’s workload:</strong> '+esc(c['head_work_note'])+'</p>')
    out.append('<p><strong>Shared technology support ('+esc(n(c['shared_support_hours']))+' hours/month):</strong> '+esc(c['shared_support_note'])+'</p>')
    out.append('</details></section>')
    return ''.join(out)
