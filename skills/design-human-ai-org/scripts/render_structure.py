#!/usr/bin/env python3
"""Render a participant's current organisation as one offline HTML document."""
from __future__ import annotations
import argparse
import html
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MODES = {"human": "Human only", "agent": "Agent only", "hybrid": "Human + agent", "unknown": "Split to confirm"}

def esc(value):
    return html.escape(str(value), quote=True)

def validate(data):
    errors = []
    if not isinstance(data, dict):
        return ["The structure record must be an object."]
    for field in ("organisation", "title", "subtitle"):
        if not isinstance(data.get(field), str):
            errors.append(f"{field} must be text.")
    if data.get("phase") != "current":
        errors.append("phase must be current for this renderer.")
    people = data.get("people")
    if not isinstance(people, list):
        return errors + ["people must be a list."]
    ids = set()
    parents = {}
    tasks_seen = set()
    for i, person in enumerate(people):
        label = f"people[{i}]"
        if not isinstance(person, dict):
            errors.append(f"{label} must be an object.")
            continue
        ident = person.get("id")
        if not isinstance(ident, str) or not ident.strip():
            errors.append(f"{label}.id must be non-empty text.")
        elif ident in ids:
            errors.append(f"Duplicate person ID: {ident}.")
        else:
            ids.add(ident)
            parents[ident] = person.get("reports_to")
        for field in ("name", "role"):
            if not isinstance(person.get(field), str):
                errors.append(f"{label}.{field} must be text.")
        parent = person.get("reports_to")
        if parent is not None and not isinstance(parent, str):
            errors.append(f"{label}.reports_to must be a person ID or null.")
        ai = person.get("ai")
        if not isinstance(ai, dict):
            errors.append(f"{label}.ai must be an object.")
        else:
            for field in ("tools", "work"):
                if not isinstance(ai.get(field), list) or not all(isinstance(x, str) for x in ai.get(field, [])):
                    errors.append(f"{label}.ai.{field} must be a list of text.")
            count = ai.get("count")
            if count is not None and (isinstance(count, bool) or not isinstance(count, int) or count < 0):
                errors.append(f"{label}.ai.count must be null or a non-negative integer.")
        tasks = person.get("tasks")
        if not isinstance(tasks, list):
            errors.append(f"{label}.tasks must be a list.")
            continue
        for j, task in enumerate(tasks):
            task_label = f"{label}.tasks[{j}]"
            if not isinstance(task, dict):
                errors.append(f"{task_label} must be an object.")
                continue
            task_id = task.get("id")
            if not isinstance(task_id, str) or not task_id.strip():
                errors.append(f"{task_label}.id must be non-empty text.")
            elif task_id in tasks_seen:
                errors.append(f"Duplicate task ID: {task_id}.")
            else:
                tasks_seen.add(task_id)
            if not isinstance(task.get("execution"), str) or task.get("execution") not in MODES:
                errors.append(f"{task_label}.execution must be human, agent, hybrid or unknown.")
            for field in ("label", "human_work", "agent_work", "why", "basis"):
                if not isinstance(task.get(field), str):
                    errors.append(f"{task_label}.{field} must be text.")
    for ident, parent in parents.items():
        if isinstance(parent, str) and parent not in ids:
            errors.append(f"{ident} reports to an unknown person ID: {parent}.")
        seen = set()
        current = ident
        while isinstance(current, str) and current in parents:
            if current in seen:
                errors.append(f"Reporting cycle includes {current}.")
                break
            seen.add(current)
            current = parents[current]
    outcomes = data.get("outcomes")
    if not isinstance(outcomes, list):
        errors.append("outcomes must be a list.")
    else:
        for i, outcome in enumerate(outcomes):
            if not isinstance(outcome, dict) or not isinstance(outcome.get("description"), str):
                errors.append(f"outcomes[{i}] must include a text description.")
            elif outcome.get("owner_id") is not None and (not isinstance(outcome.get("owner_id"), str) or outcome.get("owner_id") not in ids):
                errors.append(f"outcomes[{i}].owner_id must identify a human or be null.")
    if not isinstance(data.get("notes"), list) or not all(isinstance(x, str) for x in data.get("notes", [])):
        errors.append("notes must be a list of text.")
    return errors

def icon(name):
    return (ROOT / "assets" / "sketchyicons" / f"{name}.svg").read_text(encoding="utf-8")

def tree_layout(people):
    children = {p["id"]: [] for p in people}
    roots = []
    for p in people:
        if p["reports_to"] is None:
            roots.append(p["id"])
        else:
            children[p["reports_to"]].append(p["id"])
    positions = {}
    next_leaf = 0
    max_depth = 0
    for root in roots:
        stack = [(root, 0, False)]
        while stack:
            ident, depth, visited = stack.pop()
            max_depth = max(max_depth, depth)
            if not visited and children[ident]:
                stack.append((ident, depth, True))
                stack.extend((child, depth + 1, False) for child in reversed(children[ident]))
            else:
                if children[ident]:
                    xs = [positions[c][0] for c in children[ident]]
                    x = (xs[0] + xs[-1]) / 2
                else:
                    x = next_leaf * 474 + 18
                    next_leaf += 1
                positions[ident] = (x, depth * 202 + 22)
        next_leaf += 0.12
    width = max([x + 462 for x, y in positions.values()] + [700])
    height = (max_depth + 1) * 202 + 20 if people else 160
    return positions, width, height

def task_markup(task):
    mode = task["execution"]
    symbols = {"human": icon("user-round"), "agent": icon("bot"), "hybrid": f'<span class="hybrid-symbols" aria-hidden="true">{icon("user-round")}<span>+</span>{icon("bot")}</span>', "unknown": '<span aria-hidden="true">?</span>'}
    fields = [("Human contribution", task["human_work"]), ("Agent contribution", task["agent_work"]), ("Why this arrangement", task["why"]), ("What this is based on", task["basis"])]
    content = ''.join(f'<div><dt>{label}</dt><dd>{esc(value) if value.strip() else "To confirm"}</dd></div>' for label, value in fields)
    return f'<article class="task-card"><div class="task-heading"><h3>{esc(task["label"])}</h3><span class="execution {mode}">{symbols[mode]}{MODES[mode]}</span></div><dl class="task-contributions">{content}</dl></article>'

def render(data):
    errors = validate(data)
    if errors:
        raise ValueError("\n".join(errors))
    people = data["people"]
    by_id = {p["id"]: p for p in people}
    positions, width, height = tree_layout(people)
    nodes, lines, panels = [], [], []
    for index, p in enumerate(people):
        ident = p["id"]
        x, y = positions[ident]
        if p["reports_to"] is not None:
            px, py = positions[p["reports_to"]]
            cx, cy, ex, ey = x + 79, y + 18, px + 79, py + 142
            middle = ey + (cy - ey) / 2
            lines.append(f'<path d="M {cx} {cy} V {middle} H {ex} V {ey + 3}" marker-end="url(#report-arrow)"/>')
        tools = ' · '.join(p["ai"]["tools"]) or "Tools to confirm"
        work = p["ai"]["work"][:3]
        ai_work = ''.join(f'<li>{esc(item)}</li>' for item in work)
        if len(p["ai"]["work"]) > 3:
            ai_work += f'<li class="more-work">+ {len(p["ai"]["work"]) - 3} more in work details</li>'
        elif not work:
            ai_work = '<li>Work to confirm</li>'
        count = "Number of agents to confirm" if p["ai"]["count"] is None else f'{esc(p["ai"]["count"])} agents reported'
        ai_present = bool(p["ai"]["tools"] or p["ai"]["work"] or p["ai"]["count"])
        ai_label = "AI tools & agents" if ai_present else "AI use to confirm"
        nodes.append(f'''<div class="org-unit" style="left:{x}px;top:{y}px" data-person-index="{index}">
<button class="human-node" type="button" data-select="{index}" aria-controls="person-panel-{index}" aria-expanded="false"><span class="human-symbol">{icon("user-round")}</span><strong>{esc(p["name"])}</strong><span class="person-role">{esc(p["role"])}</span><span class="node-action">View work</span></button>
<span class="usage-edge" aria-hidden="true"><span>uses</span><svg viewBox="0 0 44 20"><path d="M2 10 H37 M32 5 L38 10 L32 15"/></svg></span>
<button class="ai-node" type="button" data-select="{index}" aria-controls="person-panel-{index}" aria-expanded="false"><span class="ai-group-heading"><span class="agent-symbol">{icon("bot")}</span><strong>{ai_label}</strong></span><span class="tool-names">{esc(tools)}</span><ul>{ai_work}</ul><span class="agent-count">{count}</span></button></div>''')
        manager = esc(by_id[p["reports_to"]]["name"]) if p["reports_to"] else "No manager recorded in this scope"
        work_detail = ''.join(task_markup(task) for task in p["tasks"]) or '<p class="empty-state">The division of work has not been described yet.</p>'
        all_ai_work = ''.join(f'<li>{esc(item)}</li>' for item in p["ai"]["work"])
        panels.append(f'''<section class="person-panel" id="person-panel-{index}" data-panel="{index}" aria-labelledby="person-heading-{index}"><div class="detail-title"><span class="human-symbol">{icon("user-round")}</span><div><h2 id="person-heading-{index}" tabindex="-1">{esc(p["name"])}: current work</h2><p>{esc(p["role"])} · Reports to: {manager}</p></div></div><p class="detail-tools"><strong>AI tools described:</strong> {esc(tools)}. {count}.</p><div class="task-grid">{work_detail}</div><details class="full-ai-list"><summary>All AI work described for {esc(p["name"])}</summary><ul>{all_ai_work or '<li>To confirm</li>'}</ul></details></section>''')
    outcomes = ''.join(f'<li><span>{esc(o["description"])}</span><small>Human owner: {esc(by_id[o["owner_id"]]["name"]) if o["owner_id"] else "To confirm"}</small></li>' for o in data["outcomes"])
    notes = ''.join(f'<li>{esc(note)}</li>' for note in data["notes"])
    structure_rows = ''.join(f'<li><button type="button" data-select="{i}" aria-controls="person-panel-{i}"><strong>{esc(p["name"])}</strong><span>{esc(p["role"])}</span><span>{"Reports to " + esc(by_id[p["reports_to"]]["name"]) if p["reports_to"] else "No manager recorded in this scope"}</span></button></li>' for i, p in enumerate(people))
    css = (ROOT / "assets" / "structure.css").read_text(encoding="utf-8")
    js = (ROOT / "assets" / "structure.js").read_text(encoding="utf-8")
    safe_data = json.dumps(data, ensure_ascii=False).replace("&", "\\u0026").replace("<", "\\u003c").replace(">", "\\u003e").replace("\u2028", "\\u2028").replace("\u2029", "\\u2029")
    notice = (ROOT / "assets" / "sketchyicons" / "NOTICE").read_text(encoding="utf-8")
    license_text = (ROOT / "assets" / "sketchyicons" / "LICENSE").read_text(encoding="utf-8")
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{esc(data["title"])}</title><style>{css}</style></head><body>
<main><header class="page-heading"><h1>{esc(data["title"])}</h1><p>{esc(data["subtitle"])}</p></header>
<section class="outcomes" aria-label="Outcomes described"><h2>Outcomes you are responsible for</h2><ul>{outcomes or '<li>No outcomes recorded yet.</li>'}</ul></section>
<section class="chart-section" aria-labelledby="chart-heading"><div class="chart-heading"><div><h2 id="chart-heading">Current reporting and AI use</h2><p>Select a person or their AI group to see the division of work.</p></div><div class="zoom-controls" hidden><button type="button" data-zoom="out" aria-label="Zoom out">−</button><output id="zoom-label">100%</output><button type="button" data-zoom="in" aria-label="Zoom in">+</button><button type="button" data-zoom="fit" aria-label="Reset chart zoom">Reset</button></div></div>
<div class="legend"><span><i class="legend-human">{icon("user-round")}</i>Human</span><span><i class="legend-agent">{icon("bot")}</i>AI tools and agent group</span><span><i class="legend-report">↑</i>Reports to the human at the arrowhead</span><span><i class="legend-use">→</i>Uses AI; authority still to be examined</span></div>
<div class="diagram-scroll" tabindex="0" aria-label="Organisation diagram. Scroll horizontally if needed."><div class="diagram-sizer" style="width:{width}px;height:{height}px"><div class="diagram" data-width="{width}" data-height="{height}" style="width:{width}px;height:{height}px"><svg class="report-lines" viewBox="0 0 {width} {height}" aria-hidden="true"><defs><marker id="report-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto"><path d="M1 1 L9 5 L1 9"/></marker></defs>{''.join(lines)}</svg>{''.join(nodes) or '<p class="empty-state">People and reporting relationships have not been recorded yet.</p>'}</div></div></div>
<p class="chart-note">Each AI box groups the tools and agents used by that person. It does not represent one agent or a formal reporting position.</p>
<details class="role-list"><summary>Read the reporting structure as a list</summary><ul>{structure_rows}</ul></details></section>
<section class="work-details" aria-label="Current work by person"><div class="detail-prompt"><h2>How the work is divided</h2><p>Choose a person above. Human only, Agent only and Human + agent describe who performs the work. Human accountability is a separate question.</p></div>{''.join(panels)}</section>
<section class="session-notes"><h2>What still needs to be established</h2><ul>{notes or '<li>No further notes recorded.</li>'}</ul></section>
<footer><p>Prepared by Dr. Shiva Kakkar</p><details><summary>Icons and licence</summary><p>{esc(notice)}</p><pre>{esc(license_text)}</pre></details></footer></main>
<script type="application/json" id="structure-record">{safe_data}</script><script>{js}</script></body></html>'''

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--validate-only", action="store_true")
    args = parser.parse_args()
    try:
        if not args.validate_only and (args.input.resolve() == args.output.resolve() or (args.output.exists() and args.input.samefile(args.output))):
            parser.exit(2, "Output must differ from the input JSON file.\n")
        data = json.loads(args.input.read_text(encoding="utf-8"))
        errors = validate(data)
        if errors:
            parser.exit(2, "Invalid structure record:\n" + "\n".join(errors) + "\n")
        if not args.validate_only:
            args.output.write_text(render(data), encoding="utf-8")
            print(args.output)
    except (ValueError, OSError) as exc:
        parser.exit(2, f"{exc}\n")

if __name__ == "__main__":
    main()
