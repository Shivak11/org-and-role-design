#!/usr/bin/env python3
"""Create, check and render a participant record without modifying its input."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys


def module(name):
    spec = importlib.util.spec_from_file_location('_session_' + name, Path(__file__).with_name(name + '.py'))
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


contract = module('session_contract')


def build(record, stage):
    data = contract.prepare(record, stage)
    comparison = module('render_comparison')
    errors = comparison.validate(data)
    if stage == 'current' and not data.get('current_roles'):
        errors.append('current_roles: record the known current people before rendering')
    if stage == 'split':
        errors.extend(module('render_decomposition').validate(data))
        if not data.get('comparison', {}).get('division'):
            errors.append('comparison.division: record examined activities before the split')
    if errors:
        raise ValueError('\n'.join(dict.fromkeys(errors)))
    if stage == 'current':
        outputs = {'current-structure.html': comparison.render(data, current_only=True)}
    elif stage == 'split':
        outputs = {'role-decomposition.html': module('render_decomposition').render(data)}
    else:
        outputs = {'comparison.html': comparison.render(data),
                   'workbook.html': module('render_workbook').render(data),
                   'organisation.svg': comparison.render_organisation_svg(data),
                   'decisions.svg': comparison.render_decisions_svg(data)}
    counts = {}
    for side in ('current', 'proposed'):
        posts = data.get('comparison', {}).get('staffing', {}).get(side)
        roles = data.get(side + '_roles', [])
        explicit = [r.get('post_count') for r in roles]
        counts[side] = {'role_types': len(roles), 'human_posts': len(posts) if posts is not None
                       else sum(explicit) if explicit and all(type(x) is int for x in explicit) else None}
    report = {'stage': stage, 'revision': data['revision'], 'ready_for_confirmation': stage == 'final',
              'counts': counts, 'files': list(outputs),
              'limit': 'Checks record consistency and completeness, not participant facts or operational feasibility.'}
    outputs['snapshot.json'] = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    outputs['check.json'] = json.dumps(report, ensure_ascii=False, indent=2) + '\n'
    return outputs, report


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    subs = parser.add_subparsers(dest='command', required=True)
    init = subs.add_parser('init', help='Create an empty draft; never overwrite an existing record')
    init.add_argument('input', type=Path)
    for name in ('check', 'render'):
        cmd = subs.add_parser(name)
        cmd.add_argument('input', type=Path)
        if name == 'render':
            cmd.add_argument('output', type=Path, help='A new directory for this stage/revision')
        cmd.add_argument('--stage', choices=['current', 'split', 'final'], required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'init':
            args.input.parent.mkdir(parents=True, exist_ok=True)
            with args.input.open('x', encoding='utf-8') as handle:
                json.dump(contract.blank_record(), handle, ensure_ascii=False, indent=2)
                handle.write('\n')
            print('Created draft ' + str(args.input))
            return 0
        record = json.loads(args.input.read_text(encoding='utf-8'))
        outputs, report = build(record, args.stage)
        if args.command == 'render':
            # All validation and rendering succeeds before any output is written.
            # Exclusive directory creation preserves every earlier stage snapshot.
            if args.output.resolve() == args.input.resolve() or args.output.exists():
                raise ValueError('Use a new output directory; previous stage files are preserved')
            args.output.mkdir(parents=True, exist_ok=False)
            for name, body in outputs.items():
                (args.output / name).write_text(body, encoding='utf-8')
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, TypeError, KeyError) as exc:
        print('Session check failed:\n' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
