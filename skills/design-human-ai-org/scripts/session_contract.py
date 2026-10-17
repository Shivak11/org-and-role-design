"""Explicit projections and final-stage checks for participant sessions.

No language-model inference: sequence, actor, authority and staffing choices
must be authored. Legacy records remain valid outside the opt-in session path.
"""
from copy import deepcopy


def blank_record():
    return {
        'schema_version': 1, 'title': '', 'status': 'draft', 'revision': 1,
        'confirmation': {'accepted': False, 'revision': 1, 'wording': ''},
        'organisation': dict.fromkeys(['label', 'scope', 'horizon', 'context', 'exclusions'], ''),
        'evidence_note': '', 'outcomes': [], 'current_roles': [], 'proposed_roles': [],
        'services': [], 'workflows': [], 'work_changes': [], 'levers': [], 'readiness': [],
        'pilot': dict(scope='', owner_id=None, measure='', baseline='', success='', stop='', review_date=''),
        'open_questions': [], 'history': [],
        'comparison': {
            'perspective': '', 'scale': '', 'division': [], 'decisions': [],
            'reporting': {'status': 'unassessed', 'reason': '', 'current_context': '',
                          'proposed_context': '', 'links': {'current': [], 'proposed': []}},
        },
        'exercise': {'version': 1, 'stage': 'current', 'staffing_review': ''},
    }


def _words(side):
    return ' '.join(side.get(key, '') for key in ('human_work', 'agent_work', 'software_work')
                    if side.get(key)) or ('No activity in this workflow.' if side.get('mode') == 'none'
                                          else 'Execution not established.')


def prepare(record, stage):
    """Copy the input and fill exact, missing presentation records only.

    Explicit decision_ids is a selection, never classification from prose.
    service_id links disambiguate custom groups; labels cannot establish identity.
    Conflicting explicit fields fail instead of being silently overwritten.
    """
    data = deepcopy(record)
    if not isinstance(data, dict):
        raise ValueError('record must be an object')
    meta = data.setdefault('exercise', {'version': 1, 'staffing_review': ''})
    if not isinstance(meta, dict) or meta.get('version') != 1:
        raise ValueError('exercise.version must be 1')
    meta['stage'] = stage
    comp = data.get('comparison', {})
    if not isinstance(comp, dict):
        raise ValueError('comparison must be an object')
    rows = comp.get('division', [])
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError('comparison.division must contain activity objects')
    selected = comp.get('decision_ids')
    if selected is not None:
        index = {row.get('id'): row for row in rows if isinstance(row.get('id'), str)}
        if (not isinstance(selected, list) or any(not isinstance(x, str) or x not in index for x in selected)
                or len(set(selected)) != len(selected)):
            raise ValueError('comparison.decision_ids must be unique recorded division IDs')
        derived = [deepcopy(index[ident]) for ident in selected]
        if comp.get('decisions') and comp['decisions'] != derived:
            raise ValueError('comparison.decisions conflicts with decision_ids; keep one source for selected decisions')
        comp['decisions'] = derived

    # Count only explicit integers. Never parse size, role title or scope prose.
    for side in ('current', 'proposed'):
        for role in data.get(side + '_roles', []):
            if 'post_count' in role:
                count = role['post_count']
                if type(count) is not int or count < 1:
                    raise ValueError(side + '_roles.post_count must be a positive integer')
                role['size'] = f'{count} human ' + ('post' if count == 1 else 'posts')
                role['chart_caption'] = role['size']

    if stage == 'current':
        return data

    if not data.get('work_changes'):
        modes = {'human': 'Human', 'agent': 'Agent', 'hybrid': 'Human and AI',
                 'software': 'Ordinary software', 'unknown': 'Not established', 'none': 'No execution'}
        for row in rows:
            current, proposed = row.get('current', {}), row.get('proposed', {})
            if not isinstance(current, dict) or not isinstance(proposed, dict):
                continue  # Structural validator reports the invalid side.
            data.setdefault('work_changes', []).append({
                'source_activity_id': row.get('id'), 'current_work': row.get('label', '') + ': ' + _words(current),
                'change': row.get('status', ''), 'future_work': _words(proposed),
                'executor': modes.get(proposed.get('mode'), 'Not established'),
                'owner_id': proposed.get('owner_id'), 'capability': row.get('capability', 'Not assessed.'),
                'basis': row.get('reason', '') + ' ' + proposed.get('basis', ''),
            })

    if not data.get('levers'):
        reporting = comp.get('reporting', {})
        if reporting.get('reason'):
            data.setdefault('levers', []).append({
                'name': 'Formal reporting', 'current': reporting.get('current_context', ''),
                'proposed': reporting.get('proposed_context', ''), 'reason': reporting['reason'],
                'basis': reporting.get('status', 'unassessed'),
            })
        for row in comp.get('decisions', []):
            data.setdefault('levers', []).append({
                'name': row.get('label', ''), 'current': _words(row.get('current', {})),
                'proposed': _words(row.get('proposed', {})), 'reason': row.get('reason', ''),
                'basis': row.get('proposed', {}).get('basis', ''),
            })

    services = data.get('services', [])
    if not isinstance(services, list):
        raise ValueError('services must be a list')
    organisation = comp.setdefault('organisation', {})
    if not isinstance(organisation, dict):
        raise ValueError('comparison.organisation must be an object')
    # Empty associations with an explicit unknown note do not assert no current AI.
    organisation.setdefault('current', [])
    organisation.setdefault('current_note', 'Current AI associations have not been established.')
    organisation.setdefault('proposed_note', 'Proposed AI associations have not been established.')
    groups = organisation.setdefault('proposed', [])
    if not isinstance(groups, list) or any(not isinstance(g, dict) for g in groups):
        raise ValueError('comparison.organisation.proposed must contain group objects')
    for service in services:
        ident = service.get('id')
        if not isinstance(ident, str):
            raise ValueError('services.id must be text')
        linked = [g for g in groups if g.get('service_id') == ident or g.get('id') == 'service-' + ident]
        if len(linked) > 1:
            raise ValueError('More than one organisation group represents service ' + ident)
        if linked:
            group = linked[0]
            if group.get('supervisor_id') != service.get('supervisor_id') or group.get('relationship') != 'supervises':
                raise ValueError('Organisation supervision conflicts with service ' + ident)
            continue
        agents = service.get('agent_roles', [])
        if not isinstance(agents, list) or any(not isinstance(a, dict) for a in agents):
            raise ValueError('service.agent_roles must contain agent objects')
        groups.append({
            'id': 'service-' + ident, 'service_id': ident, 'label': service.get('label', ''),
            'supervisor_id': service.get('supervisor_id'), 'relationship': 'supervises',
            'summary': '; '.join(a.get('label', '') for a in agents),
            'detail': '\n'.join(a.get('autonomy', '') for a in agents),
            'status': 'clarified', 'ai_kind': 'agent',
            'instances': agents[0].get('instances') if len(agents) == 1 else None,
        })
    if services:
        # A previously written note can contradict a later service correction.
        # Display canonical supervisors in nodes; avoid generating a second prose assertion.
        organisation['proposed_note'] = 'Proposed agent services and their recorded supervisors.'
    return data


def final_issues(data):
    """Missing final-stage records, beyond the backwards-compatible type checks."""
    issues = []
    comp = data.get('comparison', {})
    if not isinstance(comp, dict):
        return ['comparison must be an object']
    def require(value, path):
        if value is None or value == '' or value == [] or (isinstance(value, str) and not value.strip()):
            issues.append(path + ': record the supplied answer or an explicit unresolved fact')
    for path in ('title', 'current_roles', 'proposed_roles', 'outcomes', 'workflows', 'work_changes', 'levers'):
        require(data.get(path), path)
    require(comp.get('division'), 'comparison.division')
    require(comp.get('decisions'), 'comparison.decisions (or select comparison.decision_ids)')
    require(data.get('exercise', {}).get('staffing_review'), 'exercise.staffing_review')
    if comp.get('reporting', {}).get('status') == 'unassessed':
        issues.append('comparison.reporting: record the participant staffing/reporting choice before final confirmation')
    for i, workflow in enumerate(data.get('workflows', [])):
        if len(workflow.get('proposed', [])) > 1 and not workflow.get('relations', {}).get('proposed'):
            issues.append(f'workflows[{i}].relations.proposed: record explicit handoffs and conditional routes; list order alone is insufficient for a final workflow')
        for side in ('current', 'proposed'):
            steps = workflow.get(side, [])
            if not steps:
                require(workflow.get(side + '_note'), f'workflows[{i}].{side}_note')
                if side == 'proposed':
                    issues.append(f'workflows[{i}].proposed: the proposed work sequence is missing')
            for j, step in enumerate(steps):
                for field in ('action', 'input', 'output'):
                    require(step.get(field), f'workflows[{i}].{side}[{j}].{field}')
                if side == 'proposed':
                    require(step.get('owner_id'), f'workflows[{i}].proposed[{j}].owner_id')
                    if step.get('actor_type') == 'unknown':
                        issues.append(f'workflows[{i}].proposed[{j}]: performer remains unresolved')
                activity_id = step.get('activity_id')
                if activity_id is not None:
                    row = next((r for r in comp.get('division', []) if r.get('id') == activity_id), None)
                    if row is None:
                        issues.append(f'workflows[{i}].{side}[{j}].activity_id: unknown division ID')
                    elif row[side].get('mode') == 'none':
                        issues.append(f'workflows[{i}].{side}[{j}]: activity is marked absent in the division view')
                    elif row[side].get('owner_id') != step.get('owner_id'):
                        issues.append(f'workflows[{i}].{side}[{j}]: accountability conflicts with the division view')
                    elif (row[side].get('mode') in ('human', 'agent', 'software', 'hybrid')
                          and step.get('actor_type') not in {
                              'human': {'human'}, 'agent': {'agent'}, 'software': {'software'},
                              'hybrid': {'human', 'agent'},
                          }[row[side]['mode']]):
                        issues.append(f'workflows[{i}].{side}[{j}]: performer conflicts with the division view')
    for row in comp.get('decisions', []):
        for side in ('current', 'proposed'):
            item = row.get(side, {})
            if side == 'proposed' and item.get('mode') == 'unknown':
                issues.append('decision ' + row.get('id', '') + ': proposed execution remains unresolved')
            if side == 'proposed' and item.get('mode') not in ('none', 'unknown'):
                require(item.get('condition'), 'decision ' + row.get('id', '') + '.proposed.condition')
    groups = comp.get('organisation', {}).get('proposed', [])
    posts = comp.get('staffing', {}).get('proposed', [])
    service_ids = {service.get('id') for service in data.get('services', [])}
    for group in groups:
        # An unlinked custom agent group can silently duplicate a projected
        # service. Require identity, not a heuristic match on label or supervisor.
        if group.get('ai_kind', 'agent') in ('agent', 'mixed'):
            linked_id = group.get('service_id')
            if linked_id not in service_ids and not any(group.get('id') == 'service-' + sid for sid in service_ids):
                issues.append('organisation group ' + group.get('id', '') + ': link the proposed agent to a recorded service using service_id')
    for removal in comp.get('staffing', {}).get('removed', []):
        for ident in removal.get('work_ids', []):
            row = next((r for r in comp.get('division', []) if r.get('id') == ident), None)
            if row and row.get('proposed', {}).get('mode') == 'unknown':
                issues.append('removed post ' + removal.get('post_id', '') + ': proposed handling of ' + ident + ' remains unresolved')
    for side in ('current', 'proposed'):
        roster = comp.get('staffing', {}).get(side)
        if roster is not None:
            for role in data.get(side + '_roles', []):
                if role.get('post_count') is not None:
                    actual = sum(p.get('role_id') == role.get('id') for p in roster)
                    if role['post_count'] != actual:
                        issues.append(side + '_roles.' + role.get('id', '') + ': post_count conflicts with counted staffing posts')
    for service in data.get('services', []):
        sid = service.get('id', '')
        for field in ('outcome_owner_id', 'supervisor_id', 'agent_roles'):
            require(service.get(field), 'service ' + sid + '.' + field)
        linked = [g for g in groups if g.get('service_id') == sid or g.get('id') == 'service-' + sid]
        if len(linked) != 1:
            issues.append('service ' + sid + ': record its organisation group using service_id')
        elif linked[0].get('supervisor_id') != service.get('supervisor_id'):
            issues.append('service ' + sid + ': diagram and service supervisors disagree')
        elif posts and len([p for p in posts if p['role_id'] == service.get('supervisor_id')]) != 1 and not linked[0].get('supervisor_post_id'):
            issues.append('service ' + sid + ': identify supervisor_post_id; a multi-post role does not identify one supervisor')
        for agent in service.get('agent_roles', []):
            for field in ('tasks', 'autonomy', 'inputs', 'outputs', 'escalation_to_id', 'escalation_condition'):
                require(agent.get(field), 'agent ' + agent.get('id', '') + '.' + field)
    pilot = data.get('pilot', {})
    for field in ('scope', 'owner_id', 'measure', 'success', 'stop', 'review_date'):
        require(pilot.get(field), 'pilot.' + field)
    # Linked work changes have to cover the same activity; legacy hand-authored
    # descriptions without IDs remain readable and require editorial review.
    for change in data.get('work_changes', []):
        ident = change.get('source_activity_id')
        if ident is not None:
            row = next((r for r in comp.get('division', []) if r.get('id') == ident), None)
            if row is None or change.get('owner_id') != row.get('proposed', {}).get('owner_id'):
                issues.append('work_changes: linked activity ownership conflicts with division')
    linked_changes = [change.get('source_activity_id') for change in data.get('work_changes', [])
                      if change.get('source_activity_id') is not None]
    if linked_changes and set(linked_changes) != {row.get('id') for row in comp.get('division', [])}:
        issues.append('work_changes: linked readback does not cover every division activity')
    return issues


def validate_marked(data):
    """Called by all ordinary validators; incomplete legacy records stay compatible."""
    meta = data.get('exercise')
    if meta is None:
        return []
    if not isinstance(meta, dict) or type(meta.get('version')) is not int or meta.get('version') != 1:
        return ['exercise.version must be the integer 1']
    if meta.get('stage') not in ('current', 'split', 'final'):
        return ['exercise.stage must be current, split or final']
    if data.get('status') == 'confirmed' and meta.get('stage') != 'final':
        return ['Only a final-stage exercise can be confirmed']
    if meta.get('stage') == 'final' or data.get('status') == 'confirmed':
        return final_issues(data)
    return []
