"""Optional explicit human-post comparison and assumed capacity calculation."""
import math


def capacity_summary(data, automated_share=None):
    """Calculate a scenario, without changing its recorded staffing proposal.

    Call only after validation. Capacity is an assumption, never a measured
    productivity claim or an automatic decision about an employee.
    """
    c = data['comparison']['staffing']['capacity']
    if c is None:
        raise ValueError('This staffing record has a workload note, not a capacity calculation.')
    share = c['automated_share'] if automated_share is None else automated_share
    if type(share) not in (int, float) or not math.isfinite(share) or not 0 <= share <= 1:
        raise ValueError('Automation share must be a finite number between zero and one.')
    exceptions = c['monthly_cases'] * (1 - share)
    samples = c['monthly_cases'] * share * c['sample_share']
    exception_hours = exceptions * c['exception_minutes'] / 60
    sample_hours = samples * c['review_minutes'] / 60
    total = exception_hours + sample_hours + c['operating_hours']
    per_post = c['hours_per_post'] * c['planning_utilisation']
    available = len(c['proposed_officer_post_ids'])
    required = max(c['minimum_posts'], math.ceil(total / per_post - 1e-9))
    return {
        'automated_share': share,
        'exceptions': round(exceptions, 6),
        'samples': round(samples, 6),
        'exception_hours': round(exception_hours, 6),
        'sample_hours': round(sample_hours, 6),
        'operating_hours': c['operating_hours'],
        'human_hours': round(total, 6),
        'required_posts': required,
        'available_posts': available,
        'planned_capacity': round(available * per_post, 6),
        'available_hours': available * c['hours_per_post'],
        'current_hours': c['monthly_cases'] * c['current_minutes_per_case'] / 60,
        'current_planned_capacity': len(c['current_officer_post_ids']) * per_post,
        'fits': required <= available,
    }


def validate_staffing(data):
    """Return errors for a present extension; leave legacy records unchanged."""
    if not isinstance(data, dict) or not isinstance(data.get('comparison'), dict):
        return []
    if 'staffing' not in data['comparison']:
        return []
    errors = []
    prefix = 'comparison.staffing'
    s = data['comparison']['staffing']
    if not isinstance(s, dict):
        return [prefix + ' must be an object.']

    def error(path, message):
        errors.append(prefix + '.' + path + ' ' + message)

    def string(value, path):
        if not isinstance(value, str) or not value.strip():
            error(path, 'must be nonempty text.')
            return False
        return True

    def array(value, path):
        if not isinstance(value, list):
            error(path, 'must be an array.')
            return []
        return value

    string(s.get('basis'), 'basis')
    groups = set()
    for i, group in enumerate(array(s.get('groups'), 'groups')):
        path = f'groups[{i}]'
        if not isinstance(group, dict):
            error(path, 'must be an object.')
            continue
        ident = group.get('id')
        if string(ident, path + '.id'):
            if ident in groups:
                error(path + '.id', 'is duplicated.')
            groups.add(ident)
        string(group.get('label'), path + '.label')

    posts = {}
    for side in ('current', 'proposed'):
        raw_roles = data.get(side + '_roles', [])
        roles = {r['id']: r for r in raw_roles if isinstance(r, dict) and isinstance(r.get('id'), str)} if isinstance(raw_roles, list) else {}
        lookup = {}
        rows = array(s.get(side), side)
        if not rows:
            error(side, 'must record at least one human post.')
        for i, post in enumerate(rows):
            path = f'{side}[{i}]'
            if not isinstance(post, dict):
                error(path, 'must be an object.')
                continue
            ident = post.get('id')
            if string(ident, path + '.id'):
                if ident in lookup:
                    error(path + '.id', 'is duplicated.')
                lookup[ident] = post
            string(post.get('label'), path + '.label')
            role_id = post.get('role_id')
            role = roles.get(role_id) if isinstance(role_id, str) else None
            if role is None:
                error(path + '.role_id', 'must identify a role on the same side.')
            elif role.get('node_type', 'role') not in ('person', 'role'):
                error(path + '.role_id', 'must identify one human role, not an aggregated unit.')
            elif role.get('reporting_status', 'known_parent' if role.get('parent_id') else 'unknown') == 'unknown':
                error(path + '.role_id', 'requires established reporting before counted levels can be shown; use the role view for unknown reporting.')
            for field in ('parent_post_id', 'group_id'):
                if field not in post or (post[field] is not None and not isinstance(post[field], str)):
                    error(path + '.' + field, 'must be a text ID or null.')
            group = post.get('group_id')
            if isinstance(group, str) and group not in groups:
                error(path + '.group_id', 'must identify a recorded group.')
        for ident, post in lookup.items():
            parent_id = post.get('parent_post_id')
            if parent_id is not None and (not isinstance(parent_id, str) or parent_id not in lookup):
                error(side + '.' + ident + '.parent_post_id', 'must identify a post on the same side.')
                continue
            role_id = post.get('role_id')
            role = roles.get(role_id) if isinstance(role_id, str) else None
            parent = lookup.get(parent_id)
            if role and role.get('parent_id') != (parent.get('role_id') if parent else None):
                error(side + '.' + ident + '.parent_post_id', 'contradicts the recorded role hierarchy.')
            seen, cursor = set(), ident
            while isinstance(cursor, str) and cursor in lookup:
                if cursor in seen:
                    error(side + '.' + ident, 'has a reporting cycle.')
                    break
                seen.add(cursor)
                cursor = lookup[cursor].get('parent_post_id')
        represented = {p.get('role_id') for p in lookup.values() if isinstance(p.get('role_id'), str)}
        if set(roles) != represented:
            error(side, 'must explicitly represent every role in this scoped structure.')
        posts[side] = lookup

    division = data['comparison'].get('division', [])
    work_ids = {row['id'] for row in division if isinstance(row, dict) and isinstance(row.get('id'), str)} if isinstance(division, list) else set()
    removed_ids = set()
    for i, removal in enumerate(array(s.get('removed'), 'removed')):
        path = f'removed[{i}]'
        if not isinstance(removal, dict):
            error(path, 'must be an object.')
            continue
        ident = removal.get('post_id')
        if isinstance(ident, str):
            if ident in removed_ids:
                error(path + '.post_id', 'is duplicated.')
            removed_ids.add(ident)
            if ident not in posts['current'] or ident in posts['proposed']:
                error(path + '.post_id', 'must be a current post absent from the proposal.')
        else:
            error(path + '.post_id', 'must identify a removed current post.')
        kind = removal.get('kind')
        if kind not in ('vertical', 'horizontal'):
            error(path + '.kind', 'must be vertical or horizontal.')
        elif isinstance(ident, str) and ident in posts['current']:
            manages = any(p.get('parent_post_id') == ident for p in posts['current'].values())
            if (kind == 'vertical') != manages:
                error(path + '.kind', 'must distinguish a removed management post from parallel delivery capacity.')
        string(removal.get('reason'), path + '.reason')
        tasks = array(removal.get('work_ids'), path + '.work_ids')
        if not tasks:
            error(path + '.work_ids', 'must name where the removed post work goes.')
        used = set()
        for j, task in enumerate(tasks):
            if not isinstance(task, str) or task not in work_ids:
                error(f'{path}.work_ids[{j}]', 'must identify a division-of-work row.')
            elif task in used:
                error(f'{path}.work_ids[{j}]', 'is duplicated.')
            else:
                used.add(task)
    if removed_ids != set(posts['current']) - set(posts['proposed']):
        error('removed', 'must account for every removed current post exactly once.')

    c = s.get('capacity')
    if 'capacity' in s and c is None:
        string(s.get('capacity_note'), 'capacity_note')
        return errors
    if not isinstance(c, dict):
        error('capacity', 'must be an object, or explicit null with a nonempty capacity_note.')
        return errors
    for field in ('assumption_note', 'shared_support_note', 'head_work_note'):
        string(c.get(field), 'capacity.' + field)
    for field in ('monthly_cases', 'minimum_posts'):
        if type(c.get(field)) is not int or c[field] < 1:
            error('capacity.' + field, 'must be a positive integer.')
    for field in ('current_minutes_per_case', 'exception_minutes', 'review_minutes', 'hours_per_post', 'operating_hours', 'shared_support_hours'):
        value = c.get(field)
        nonnegative = field in ('review_minutes', 'operating_hours', 'shared_support_hours')
        if type(value) not in (int, float) or not math.isfinite(value) or (value < 0 if nonnegative else value <= 0):
            error('capacity.' + field, 'must be a finite ' + ('nonnegative' if nonnegative else 'positive') + ' number.')
    for field in ('automated_share', 'sample_share', 'planning_utilisation'):
        value = c.get(field)
        if type(value) not in (int, float) or not math.isfinite(value) or not 0 <= value <= 1 or (field == 'planning_utilisation' and value == 0):
            error('capacity.' + field, 'must be a finite fraction within its allowed zero-to-one range.')
    for side in ('current', 'proposed'):
        field = side + '_officer_post_ids'
        identifiers = array(c.get(field), 'capacity.' + field)
        if not identifiers:
            error('capacity.' + field, 'must identify the posts covered by the capacity calculation.')
        seen = set()
        for i, ident in enumerate(identifiers):
            if not isinstance(ident, str) or ident not in posts[side]:
                error(f'capacity.{field}[{i}]', 'must identify a human post on the same side.')
            elif ident in seen:
                error(f'capacity.{field}[{i}]', 'is duplicated.')
            else:
                seen.add(ident)
                if any(p.get('parent_post_id') == ident for p in posts[side].values()):
                    error(f'capacity.{field}[{i}]', 'must identify delivery capacity, not a management post.')
        covered_roles = {posts[side][ident]['role_id'] for ident in seen
                         if isinstance(posts[side][ident].get('role_id'), str)}
        required_ids = {ident for ident, post in posts[side].items()
                        if isinstance(post.get('role_id'), str) and post['role_id'] in covered_roles}
        if seen != required_ids:
            error('capacity.' + field, 'must include every post of each represented delivery role.')
    return errors
