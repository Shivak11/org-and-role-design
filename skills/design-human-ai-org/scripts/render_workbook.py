#!/usr/bin/env python3
"""Validate a version 1 exercise record and render a portable HTML workbook.

Public API: validate(data) -> list[str]; render(data) -> str. render raises
ValueError for invalid data. Python's standard library is the only dependency.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from html import escape
import importlib.util
import json
from pathlib import Path
import sys
from urllib.parse import quote

_workflow_spec = importlib.util.spec_from_file_location(
    "_workbook_workflow_contract", Path(__file__).with_name("workflow_contract.py")
)
_workflow_contract = importlib.util.module_from_spec(_workflow_spec)
_workflow_spec.loader.exec_module(_workflow_contract)

_staffing_spec = importlib.util.spec_from_file_location(
    "_workbook_staffing_contract", Path(__file__).with_name("staffing_contract.py")
)
_staffing_contract = importlib.util.module_from_spec(_staffing_spec)
_staffing_spec.loader.exec_module(_staffing_contract)


def _removed_activity(data, change):
    comparison = data.get('comparison', {})
    division = comparison.get('division', []) if isinstance(comparison, dict) else []
    if not isinstance(division, list) or not change.get('source_activity_id'):
        return False
    return any(isinstance(row, dict) and row.get('id') == change['source_activity_id']
               and isinstance(row.get('proposed'), dict) and row['proposed'].get('mode') == 'none'
               for row in division)


def validate(data):
    """Return all detected structural and reference errors without changing data."""
    errors = []

    def error(path, message):
        errors.append(f"{path}: {message}")

    def obj(value, path, fields):
        if not isinstance(value, dict):
            error(path, "must be an object")
            return {}
        for field in fields:
            if field not in value:
                error(f"{path}.{field}", "is required")
        return value

    def string(value, path, nonempty=False):
        if not isinstance(value, str):
            error(path, "must be a string")
            return False
        if nonempty and not value.strip():
            error(path, "must not be empty")
            return False
        return True

    def integer(value, path):
        if type(value) is not int or value < 1:
            error(path, "must be a positive integer, not a boolean")
            return False
        return True

    def array(value, path):
        if not isinstance(value, list):
            error(path, "must be a list")
            return []
        return value

    def strings(value, path):
        for i, item in enumerate(array(value, path)):
            string(item, f"{path}[{i}]")

    def fields(record, path, names):
        for name in names.split():
            string(record.get(name), f"{path}.{name}")

    def enum(value, path, choices):
        if not isinstance(value, str) or value not in choices:
            error(path, "must be one of " + ", ".join(choices))

    def records(value, path, names, indexed=True):
        result, ids = [], set()
        for i, item in enumerate(array(value, path)):
            item_path = f"{path}[{i}]"
            item = obj(item, item_path, names.split())
            result.append((item, item_path))
            if indexed and string(item.get("id"), f"{item_path}.id", True):
                if item["id"] in ids:
                    error(f"{item_path}.id", "duplicates an ID in this list")
                ids.add(item["id"])
        return result, ids

    def ref(value, path, ids, nullable=False):
        if value is None and nullable:
            return
        if string(value, path, True) and value not in ids:
            error(path, "must refer to an existing human role in the relevant reporting structure")

    top = "schema_version title status confirmation revision organisation evidence_note outcomes current_roles proposed_roles services workflows work_changes levers readiness pilot open_questions history"
    if not isinstance(data, dict):
        return ["record: must be an object"]
    obj(data, "record", top.split())
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        error("schema_version", "must be the integer 1")
    string(data.get("title"), "title")
    string(data.get("evidence_note"), "evidence_note")
    enum(data.get("status"), "status", ["draft", "confirmed"])
    is_draft = data.get("status") == "draft"
    revision_ok = integer(data.get("revision"), "revision")
    confirmation = obj(data.get("confirmation"), "confirmation", ["accepted", "revision", "wording"])
    if type(confirmation.get("accepted")) is not bool:
        error("confirmation.accepted", "must be a boolean")
    confirmation_revision_ok = integer(confirmation.get("revision"), "confirmation.revision")
    string(confirmation.get("wording"), "confirmation.wording", confirmation.get("accepted") is True)
    if revision_ok and confirmation_revision_ok and confirmation["revision"] != data["revision"]:
        error("confirmation.revision", "must match the current revision")
    if data.get("status") == "confirmed" and confirmation.get("accepted") is not True:
        error("confirmation.accepted", "must be true for a confirmed record")
    if data.get("status") == "draft" and confirmation.get("accepted") is not False:
        error("confirmation.accepted", "must be false for a draft record")

    organisation = obj(data.get("organisation"), "organisation", "label scope horizon context exclusions".split())
    fields(organisation, "organisation", "label scope horizon context exclusions")
    role_sets = {}
    for side in ["current_roles", "proposed_roles"]:
        roles, ids = records(data.get(side), side, "id label parent_id scope responsibilities change reason")
        role_sets[side] = ids
        parents = {}
        for role, path in roles:
            fields(role, path, "label scope reason")
            strings(role.get("responsibilities"), path + ".responsibilities")
            enum(role.get("change"), path + ".change", ["retained", "changed", "proposed", "unknown"])
            ref(role.get("parent_id"), path + ".parent_id", ids, nullable=True)
            if isinstance(role.get("id"), str) and (role.get("parent_id") is None or isinstance(role.get("parent_id"), str)):
                parents[role["id"]] = role.get("parent_id")
        # Walk parent chains iteratively, so validation imposes no depth limit.
        completed = set()
        for role_id in parents:
            if role_id in completed:
                continue
            chain, local = [], set()
            cursor = role_id
            while cursor in parents and cursor not in completed:
                if cursor in local:
                    error(side, f"contains a reporting cycle involving {cursor!r}")
                    break
                local.add(cursor)
                chain.append(cursor)
                cursor = parents[cursor]
            completed.update(chain)

    proposed_ids = role_sets["proposed_roles"]
    outcomes, outcome_ids = records(data.get("outcomes"), "outcomes", "id name owner_id success basis")
    for outcome, path in outcomes:
        fields(outcome, path, "name success basis")
        ref(outcome.get("owner_id"), path + ".owner_id", proposed_ids, nullable=is_draft)

    services, _ = records(data.get("services"), "services", "id label outcome_owner_id supervisor_id service_owner_id availability shared_with agent_roles")
    agent_ids = set()
    for service, path in services:
        fields(service, path, "label availability shared_with")
        for name in ["outcome_owner_id", "supervisor_id", "service_owner_id"]:
            ref(service.get(name), path + "." + name, proposed_ids, nullable=is_draft or name == "service_owner_id")
        agents, _ = records(service.get("agent_roles"), path + ".agent_roles", "id label tasks autonomy inputs outputs tools escalation_to_id escalation_condition instances")
        for agent, agent_path in agents:
            fields(agent, agent_path, "label autonomy inputs outputs escalation_condition")
            strings(agent.get("tasks"), agent_path + ".tasks")
            strings(agent.get("tools"), agent_path + ".tools")
            ref(agent.get("escalation_to_id"), agent_path + ".escalation_to_id", proposed_ids, nullable=is_draft)
            if agent.get("instances") is not None:
                integer(agent["instances"], agent_path + ".instances")
            if isinstance(agent.get("id"), str):
                if agent["id"] in agent_ids:
                    error(agent_path + ".id", "agent role IDs must be unique across all services")
                agent_ids.add(agent["id"])

    workflows, _ = records(data.get("workflows"), "workflows", "id label outcome_id coverage current proposed")
    for workflow, path in workflows:
        fields(workflow, path, "label coverage")
        if string(workflow.get("outcome_id"), path + ".outcome_id", True) and workflow["outcome_id"] not in outcome_ids:
            error(path + ".outcome_id", "must refer to an existing outcome")
        for side in ["current", "proposed"]:
            relevant_roles = role_sets[side + "_roles"]
            steps, _ = records(workflow.get(side), path + "." + side, "id action actor_type actor_id actor_label owner_id input output approval_by_id condition")
            for step, step_path in steps:
                fields(step, step_path, "action actor_label input output condition")
                enum(step.get("actor_type"), step_path + ".actor_type", ["human", "agent", "software", "external", "unknown"])
                ref(step.get("owner_id"), step_path + ".owner_id", relevant_roles, nullable=is_draft)
                ref(step.get("approval_by_id"), step_path + ".approval_by_id", relevant_roles, nullable=True)
                actor_type = step.get("actor_type")
                if actor_type == "human":
                    ref(step.get("actor_id"), step_path + ".actor_id", relevant_roles,
                        nullable="eligible_actor_ids" in step)
                elif actor_type == "agent":
                    if side == "current":
                        if step.get("actor_id") is not None:
                            error(step_path + ".actor_id", "must be null for an existing agent in a current workflow")
                        string(step.get("actor_label"), step_path + ".actor_label", True)
                    elif string(step.get("actor_id"), step_path + ".actor_id", True) and step["actor_id"] not in agent_ids:
                        error(step_path + ".actor_id", "must refer to an existing agent role")
                elif actor_type in ["software", "external", "unknown"]:
                    if step.get("actor_id") is not None:
                        error(step_path + ".actor_id", "must be null for software, external or unknown actors")
                    string(step.get("actor_label"), step_path + ".actor_label", True)

    changes, _ = records(data.get("work_changes"), "work_changes", "current_work change future_work executor owner_id capability basis", indexed=False)
    for change, path in changes:
        fields(change, path, "current_work change future_work executor capability basis")
        ref(change.get("owner_id"), path + ".owner_id", proposed_ids, nullable=is_draft or _removed_activity(data, change))
    levers, _ = records(data.get("levers"), "levers", "name current proposed reason basis", indexed=False)
    for lever, path in levers:
        fields(lever, path, "name current proposed reason basis")
    readiness, _ = records(data.get("readiness"), "readiness", "need status owner_id validation", indexed=False)
    for need, path in readiness:
        fields(need, path, "need status validation")
        ref(need.get("owner_id"), path + ".owner_id", proposed_ids, nullable=True)
    pilot = obj(data.get("pilot"), "pilot", "scope owner_id measure baseline success stop review_date".split())
    fields(pilot, "pilot", "scope measure baseline success stop review_date")
    ref(pilot.get("owner_id"), "pilot.owner_id", proposed_ids, nullable=is_draft)
    strings(data.get("open_questions"), "open_questions")
    history, _ = records(data.get("history"), "history", "revision initial_choice ai_proposal participant_decision note", indexed=False)
    for item, path in history:
        if integer(item.get("revision"), path + ".revision") and revision_ok and item["revision"] > data["revision"]:
            error(path + ".revision", "cannot be later than the current revision")
        fields(item, path, "initial_choice ai_proposal participant_decision note")
    if not errors:
        errors.extend(_workflow_contract.validate_workflows(data))
        errors.extend(_staffing_contract.validate_staffing(data))
    if not errors and 'exercise' in data:
        spec = importlib.util.spec_from_file_location('_session_contract', Path(__file__).with_name('session_contract.py'))
        contract = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(contract)
        errors.extend(contract.validate_marked(data))
    return errors


def text(value):
    """Escape every participant-controlled string at the HTML boundary."""
    return escape(str(value), quote=True)


def para(value, css_class=""):
    content = text(value) if value else "Not recorded."
    attribute = f' class="{css_class}"' if css_class else ""
    return f"<p{attribute}>{content}</p>"


def pairs(items, css_class="facts"):
    return f'<dl class="{css_class}">' + "".join(
        f"<div><dt>{text(label)}</dt><dd>{text(value) if value else 'Not recorded.'}</dd></div>"
        for label, value in items
    ) + "</dl>"


def bullets(items, empty="Not recorded."):
    if not items:
        return para(empty, "empty")
    return '<ul class="plain-list">' + "".join(f"<li>{text(item) if item else 'Not recorded.'}</li>" for item in items) + "</ul>"


def icon(kind):
    # Inline SVGs have no external references and convey the same types as text.
    drawings = {
        "human": '<circle cx="18" cy="18" r="17" fill="#FFF0E5" stroke="#B54E09" stroke-width="1.5"/><circle cx="18" cy="12" r="4" fill="#B54E09"/><path d="M10 27v-3a8 8 0 0 1 16 0v3" fill="#B54E09"/>',
        "agent": '<path d="M10 2h16l9 16-9 16H10L1 18Z" fill="#E4F5F2" stroke="#007B72" stroke-width="1.5"/><rect x="9" y="11" width="18" height="15" rx="3" fill="none" stroke="#007B72" stroke-width="2"/><path d="M18 7v4M14 22h8" stroke="#007B72" stroke-width="2"/><circle cx="14" cy="17" r="1.5" fill="#007B72"/><circle cx="22" cy="17" r="1.5" fill="#007B72"/>',
        "software": '<rect x="2" y="3" width="32" height="30" rx="4" fill="#F2F4F6" stroke="#687482" stroke-width="1.5"/><path d="M3 11h30M9 18h18M9 24h12" stroke="#687482" stroke-width="2"/>',
        "external": '<path d="M18 2 34 18 18 34 2 18Z" fill="#F2F4F6" stroke="#687482" stroke-width="1.5"/><path d="M11 18h14m-5-5 5 5-5 5" fill="none" stroke="#687482" stroke-width="2"/>',
        "unknown": '<rect x="2" y="3" width="32" height="30" rx="4" fill="#F2F4F6" stroke="#687482" stroke-width="1.5" stroke-dasharray="4 3"/><path d="M13 13a5 5 0 1 1 8 4c-2 1-3 2-3 4" fill="none" stroke="#687482" stroke-width="2"/><circle cx="18" cy="27" r="1.5" fill="#687482"/>',
    }
    return f'<svg class="actor-icon {kind}-icon" viewBox="0 0 36 36" aria-hidden="true">{drawings[kind]}</svg>'


def human_tree(roles, heading, show_change=True):
    if not roles:
        return f'<section class="tree-panel"><h3>{text(heading)}</h3><p class="empty">No human reporting roles have been recorded.</p></section>'
    children = defaultdict(list)
    lookup = {role["id"]: role for role in roles}
    for role in roles:
        children[role["parent_id"]].append(role)
    html = [f'<section class="tree-panel"><h3>{text(heading)}</h3><ul class="human-tree">']
    # A stack keeps arbitrarily deep role structures renderable without Python
    # recursion. Nested lists retain the exact structure for assistive tools.
    stack = [("role", role, 0) for role in reversed(children[None])]
    while stack:
        action, role, depth = stack.pop()
        if action == "close":
            html.append("</ul></li>")
            continue
        parent = lookup.get(role["parent_id"])
        reports_to = parent["label"] if parent else "No parent recorded within this scope"
        html.append(f'<li><details class="human-node" style="--depth:{depth}">')
        html.append(f'<summary><span class="role-summary-title">{icon("human")}<span class="role-name">{text(role["label"])}</span></span>')
        html.append(f'<span class="reports-to"><strong>Reports to:</strong> {text(reports_to)}</span></summary><div class="human-details">')
        html.append(pairs([("Scope", role["scope"])]))
        html.append(bullets(role["responsibilities"], "Responsibilities have not been recorded."))
        change_details = [("Role change", role["change"])] if show_change else []
        html.append(pairs(change_details + [("Reason", role["reason"])]))
        html.append("</div></details>")
        if children[role["id"]]:
            html.append('<ul class="human-children">')
            stack.append(("close", role, depth))
            stack.extend(("role", child, depth + 1) for child in reversed(children[role["id"]]))
        else:
            html.append("</li>")
    html.append("</ul></section>")
    return "".join(html)


def table(headers, rows, css_class=""):
    if not rows:
        return '<p class="empty">No entries have been recorded.</p>'
    return f'<div class="table-wrap"><table class="{css_class}"><thead><tr>' + "".join(
        f'<th scope="col">{text(header)}</th>' for header in headers
    ) + "</tr></thead><tbody>" + "".join(
        "<tr>" + "".join(f'<td data-label="{text(headers[i])}">{cell}</td>' for i, cell in enumerate(row)) + "</tr>"
        for row in rows
    ) + "</tbody></table></div>"


def render(data):
    """Return a self-contained HTML document; reject invalid records first."""
    errors = validate(data)
    if errors:
        raise ValueError("Invalid workbook record:\n" + "\n".join(errors))
    css = (Path(__file__).resolve().parent.parent / "assets" / "workbook.css").read_text(encoding="utf-8")
    current = {role["id"]: role for role in data["current_roles"]}
    proposed = {role["id"]: role for role in data["proposed_roles"]}
    agents = {agent["id"]: agent for service in data["services"] for agent in service["agent_roles"]}
    outcomes = {outcome["id"]: outcome for outcome in data["outcomes"]}

    def human(role_id, side=proposed, unknown="Owner to confirm"):
        return side[role_id]["label"] if role_id is not None else unknown

    favicon = quote('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40"><rect width="40" height="40" rx="8" fill="white"/><circle cx="13" cy="15" r="8" fill="#b54e09"/><path d="M23 18h10l5 9-5 9H23l-5-9Z" fill="#007b72"/></svg>')
    section_links = [("scope", "Scope"), ("outcomes", "Outcomes"), ("organisation", "Organisation"),
                     ("workflows", "Workflows"), ("work-allocation", "Work allocation"),
                     ("design-decisions", "Design decisions"), ("readiness", "Readiness"),
                     ("pilot", "Pilot"), ("open-questions", "Open questions"), ("history", "Choices and revisions")]
    navigation = '<nav class="section-navigation" aria-label="Workbook sections">' + "".join(
        f'<a href="#{anchor}">{label}</a>' for anchor, label in section_links
    ) + '</nav>'
    parts = ['<!doctype html><html lang="en"><head><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             f'<link rel="icon" type="image/svg+xml" href="data:image/svg+xml,{favicon}">',
             f'<title>{text(data["title"])}</title><style>{css}</style></head><body>',
             '<a class="skip-link" href="#workbook">Skip to workbook</a>',
             '<main id="workbook"><header class="document-header">',
             f'<h1>{text(data["title"])}</h1>',
             para(data["organisation"]["scope"], "intro"),
             '<div class="document-actions"><button type="button" id="print-workbook" hidden>Print or save PDF</button></div>',
             '<p class="attribution">Prepared by Dr. Shiva Kakkar</p>',
             f'<p class="record-status">{"Confirmed exercise record" if data["status"] == "confirmed" else "Draft exercise record"} · Revision {data["revision"]}. This record does not authorise implementation.</p>',
             '</header>', navigation,
             '<section class="document-section" id="scope"><h2>Scope and evidence</h2>',
             pairs([("Organisation", data["organisation"]["label"]), ("Planning horizon", data["organisation"]["horizon"]), ("Context", data["organisation"]["context"]), ("Outside this exercise", data["organisation"]["exclusions"])]),
             para(data["evidence_note"], "evidence-note")]
    if data["confirmation"]["accepted"]:
        parts.append(pairs([("Participant confirmation", data["confirmation"]["wording"])]))
    parts.extend(['</section><section class="document-section" id="outcomes"><h2>Outcomes and accountable owners</h2>',
        table(["Outcome", "Accountable human owner", "Success measure", "Basis"], [
            [para(item["name"]), para(human(item["owner_id"], unknown="Outcome owner to confirm")), para(item["success"]), para(item["basis"])]
            for item in data["outcomes"]
        ]), '</section>'])

    if data.get('comparison', {}).get('staffing'):
        staffing = data['comparison']['staffing']
        spec = importlib.util.spec_from_file_location('_workbook_staffing_view', Path(__file__).with_name('staffing_view.py'))
        staffing_view = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(staffing_view)
        parts.append('<section class="document-section" id="staffing"><h2>Human posts before and after</h2>')
        parts.append(para(f'{len(staffing["current"])} posts before; {len(staffing["proposed"])} proposed. Each row below is one post.'))
        removed = {item['post_id']: item for item in staffing['removed']}
        current_post_ids = {post['id'] for post in staffing['current']}
        for side in ('current', 'proposed'):
            lookup = {post['id']: post for post in staffing[side]}
            parts.append('<h3>' + side.capitalize() + '</h3>')
            rows = []
            for post in staffing[side]:
                parent = lookup.get(post['parent_post_id'])
                change = removed.get(post['id']) if side == 'current' else None
                status = ('Removed: ' + change['kind']) if change else ('New proposed post' if post['id'] not in current_post_ids else 'Retained in proposal')
                rows.append([para(post['label']), para(parent['label'] if parent else 'Top of this scope'), para(status)])
            parts.append(table(['Human post', 'Reports to', 'Proposed status'], rows))
        parts.append(staffing_view.render_capacity_details(data, text))
        parts.append('</section>')
    parts.extend(['<section class="document-section organisation-section" id="organisation"><h2>Current and proposed organisation</h2>',
        '<p>The trees show human reporting relationships within the recorded scope. A role node does not establish headcount. Agent services appear separately with named human responsibilities.</p>',
        '<ul class="legend">',
        f'<li>{icon("human")}<span>An orange circle represents a human role.</span></li>',
        f'<li>{icon("agent")}<span>A teal hexagon represents an agent role.</span></li>',
        f'<li>{icon("software")}<span>A grey rectangle represents ordinary software.</span></li>',
        f'<li>{icon("external")}<span>A grey diamond represents an external actor.</span></li>',
        '<li><span class="group-symbol" aria-hidden="true"></span><span>A violet double border groups agent roles in one service.</span></li>',
        '<li><span class="line-symbol" aria-hidden="true"></span><span>Indented human roles report to the parent named on their card. Plain grey borders enclose the wider view.</span></li>',
        '</ul><div class="organisation-overview"><figure class="tree-figure"><div class="tree-comparison">',
        human_tree(data["current_roles"], "Current human reporting structure",
                   show_change=not bool(data.get('comparison', {}).get('staffing'))),
        human_tree(data["proposed_roles"], "Proposed human reporting structure"),
        '</div><figcaption>Each human role names its reporting parent in the recorded scope.<span class="screen-only"> Select a role to read its scope, responsibilities and proposed changes.</span></figcaption></figure><div class="service-area"><h3>Human ownership of proposed agent services</h3>'])
    if not data["services"]:
        parts.append(para("No agent services have been recorded.", "empty"))
    for service in data["services"]:
        parts.append(f'<article class="service-card"><h4>{text(service["label"])}</h4>')
        parts.append(pairs([
            ("Accountable outcome owner", human(service["outcome_owner_id"], unknown="Outcome owner to confirm")),
            ("Workflow supervisor", human(service["supervisor_id"], unknown="Workflow supervisor to confirm")),
            ("Agent-service owner", human(service["service_owner_id"], unknown="Service owner to confirm")),
            ("Availability", service["availability"]), ("Shared with", service["shared_with"])
        ], "facts service-ownership"))
        labels = ", ".join(agent["label"] for agent in service["agent_roles"]) or "No agent roles recorded"
        parts.append(f'<details class="agent-group"><summary>{icon("agent")}<span>Agent roles: {text(labels)}</span></summary><div class="agent-content">')
        for agent in service["agent_roles"]:
            instance_label = str(agent["instances"]) if agent["instances"] is not None else "Unknown or variable"
            parts.append(f'<article class="agent-card"><div class="actor-heading">{icon("agent")}<h5>{text(agent["label"])}</h5></div>')
            parts.append(bullets(agent["tasks"], "Tasks have not been recorded."))
            parts.append(pairs([("Autonomy", agent["autonomy"]), ("Inputs", agent["inputs"]), ("Returned outputs", agent["outputs"]),
                                ("Escalates to", human(agent["escalation_to_id"], unknown="Escalation recipient to confirm")), ("Escalation condition", agent["escalation_condition"]),
                                ("Running instances", instance_label)]))
            parts.append('<h6>Tools and ordinary software</h6>' + bullets(agent["tools"], "Tools have not been recorded.") + '</article>')
        parts.append('</div></details></article>')
    parts.append('</div></div></section>')

    parts.append('<section class="document-section" id="workflows"><h2>Current and proposed workflows</h2>')
    if not data["workflows"]:
        parts.append(para("No workflows have been recorded.", "empty"))
    for workflow in data["workflows"]:
        parts.append(f'<article class="workflow"><h3>{text(workflow["label"])}</h3>')
        parts.append(pairs([("Outcome", outcomes[workflow["outcome_id"]]["name"]), ("Coverage", workflow["coverage"])]))
        if "policy" in workflow:
            parts.append(pairs([("Standing policy", workflow["policy"])]))
        parts.append('<div class="workflow-comparison">')
        for side in ["current", "proposed"]:
            lookup = current if side == "current" else proposed
            parts.append(f'<section class="workflow-side"><h4>{side.capitalize()} sequence</h4>')
            if side + "_note" in workflow:
                parts.append(para(workflow[side + "_note"]))
            steps_by_id = {step["id"]: step for step in workflow[side]}
            if not workflow[side]:
                parts.append(para("No steps have been recorded.", "empty"))
            else:
                parts.append('<ol class="workflow-steps">')
                for step in workflow[side]:
                    kind = step["actor_type"]
                    if kind == "human":
                        canonical_actor = (
                            "One of " + ", ".join(lookup[actor_id]["label"] for actor_id in step["eligible_actor_ids"])
                            if step["actor_id"] is None else lookup[step["actor_id"]]["label"]
                        )
                    elif kind == "agent" and side == "proposed":
                        canonical_actor = agents[step["actor_id"]]["label"]
                    else:
                        canonical_actor = step["actor_label"]
                    actor_name = canonical_actor
                    if kind in ["human", "agent"] and step["actor_label"] and step["actor_label"] != canonical_actor:
                        actor_name += " (" + step["actor_label"] + ")"
                    actor_type_label = "Existing AI agent" if kind == "agent" and side == "current" else "AI agent" if kind == "agent" else "Execution unresolved" if kind == "unknown" else kind.capitalize()
                    parts.append(f'<li class="workflow-step"><h5>{text(step["action"])}</h5><p class="step-actor">{icon(kind)}<span>{text(actor_type_label)}: {text(actor_name)}</span></p>')
                    parts.append(pairs([("Input", step["input"]), ("Returned output", step["output"]),
                                        ("Accountable human", human(step["owner_id"], lookup, "Accountable human to confirm")),
                                        ("Approval by", human(step["approval_by_id"], lookup, "No approval recorded")),
                                        ("Trigger, handoff or exception", step["condition"])]))
                    extra = [(label, step[field]) for field, label in (
                        ("summary", "Step summary"), ("task_type", "Task type"),
                        ("reasoning", "Reasoning"), ("handoff_cost", "Handoff cost")
                    ) if field in step]
                    if "eligible_actor_ids" in step:
                        extra.append(("Eligible performer", "Select one human from the named list for this instance."))
                    if "exclude_maker" in step:
                        extra.append(("Maker exclusion", "The maker cannot perform this step." if step["exclude_maker"] else "No maker exclusion is specified."))
                    if "knowledge" in step:
                        extra.extend([("Rules used", step["knowledge"]["rules"]), ("Case facts used", step["knowledge"]["facts"])])
                    if "terminal" in step:
                        extra.extend([("Completion result", step["terminal"]["label"]),
                                      ("Completion condition", step["terminal"]["condition"])])
                    if "authority" in step:
                        authority = step["authority"]
                        extra.extend([
                            ("May decide", authority["may_decide"]), ("Must escalate", authority["must_escalate"]),
                            ("May override", human(authority["override_by_id"], lookup, "Override authority to confirm")),
                            ("May stop", human(authority["stop_by_id"], lookup, "Stop authority to confirm"))
                        ])
                    if "escalation" in step:
                        escalation = step["escalation"]
                        return_id = escalation["return_to_step_id"]
                        extra.extend([
                            ("Escalates to", human(escalation["to_id"], lookup, "Escalation recipient to confirm")),
                            ("Escalation trigger", escalation["trigger"]),
                            ("Resume at", steps_by_id[return_id]["action"] if return_id is not None else "Return step to confirm")
                        ])
                    if extra:
                        parts.append(pairs(extra))
                    parts.append('</li>')
                parts.append('</ol>')
            if "relations" in workflow and workflow["relations"][side]:
                parts.append('<h5>Information, authority and escalation</h5>')
                parts.append(table(["From", "To", "Relationship", "Information or condition"], [
                    [para(steps_by_id[relation["from_step_id"]]["action"]),
                     para(steps_by_id[relation["to_step_id"]]["action"]),
                     para(relation["kind"].capitalize()), para(relation["label"])]
                    for relation in workflow["relations"][side]
                ]))
            parts.append('</section>')
        parts.append('</div></article>')
    parts.append('</section>')

    parts.extend(['<section class="document-section" id="work-allocation"><h2>How the work changes</h2>',
        table(["Current work", "Change and future work", "Executor and human owner", "Capability and basis"], [
            [para(item["current_work"]), pairs([("Change", item["change"]), ("Future work", item["future_work"])]),
             pairs([("Executor", item["executor"]), ("Human owner", "Activity discontinued" if _removed_activity(data, item) else human(item["owner_id"], unknown="Human owner to confirm"))]),
             pairs([("Capability required", item["capability"]), ("Basis", item["basis"])])]
            for item in data["work_changes"]
        ], "allocation-table"), '</section>',
        '<section class="document-section" id="design-decisions"><h2>Organisation design decisions</h2>',
        table(["Dimension", "Current arrangement", "Proposed arrangement", "Reason and basis"], [
            [para(item["name"]), para(item["current"]), para(item["proposed"]), pairs([("Reason", item["reason"]), ("Basis", item["basis"])])]
            for item in data["levers"]
        ]), '<p class="section-note">Dimensions absent from this record have not been assessed.</p></section>',
        '<section class="document-section" id="readiness"><h2>Readiness and validation</h2>',
        table(["Need", "Current status", "Human owner", "Validation required"], [
            [para(item["need"]), para(item["status"]), para(human(item["owner_id"])), para(item["validation"])]
            for item in data["readiness"]
        ]), '</section>'])
    pilot = data["pilot"]
    parts.extend(['<section class="document-section pilot-section" id="pilot"><h2>First pilot and review</h2>',
        pairs([("Pilot scope", pilot["scope"]), ("Human owner", human(pilot["owner_id"])),
               ("Measure", pilot["measure"]), ("Baseline", pilot["baseline"]), ("Success condition", pilot["success"]),
               ("Stop condition", pilot["stop"]), ("Review date", pilot["review_date"])]), '</section>',
        '<section class="document-section" id="open-questions"><h2>Questions still to resolve</h2>',
        bullets(data["open_questions"], "No open questions have been recorded."), '</section>',
        '<section class="document-section history-section" id="history"><h2>Participant choices and revisions</h2>'])
    if not data["history"]:
        parts.append(para("No choices or revisions have been recorded.", "empty"))
    for item in data["history"]:
        parts.append(f'<article class="history-entry"><h3>Revision {item["revision"]}</h3>')
        parts.append(pairs([("Participant's initial choice", item["initial_choice"]), ("AI proposal", item["ai_proposal"]),
                            ("Participant's decision", item["participant_decision"]), ("Revision note", item["note"])]))
        parts.append('</article>')
    parts.extend(['</section><footer><p>Prepared by Dr. Shiva Kakkar</p>',
        '<p><a href="https://www.shivakakkar.com/">Click here to access Dr. Shiva Kakkar’s profile and programme enquiries</a></p></footer></main>',
        '<div class="print-footer" aria-hidden="true">Prepared by Dr. Shiva Kakkar</div>',
        '''<script>
(() => {
  const printButton = document.getElementById('print-workbook');
  printButton.hidden = false;
  let savedStates = null;
  const openForPrint = () => {
    if (savedStates !== null) return;
    savedStates = Array.from(document.querySelectorAll('details'), item => [item, item.open]);
    savedStates.forEach(([item]) => { item.open = true; });
  };
  const restoreAfterPrint = () => {
    if (savedStates === null) return;
    savedStates.forEach(([item, wasOpen]) => { item.open = wasOpen; });
    savedStates = null;
  };
  window.addEventListener('beforeprint', openForPrint);
  window.addEventListener('afterprint', restoreAfterPrint);
  printButton.addEventListener('click', () => { window.print(); });
})();
</script></body></html>'''])
    return "".join(parts)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Validate an organisation-design record and render a standalone HTML workbook.")
    parser.add_argument("input", type=Path, help="Session JSON file")
    parser.add_argument("output", type=Path, nargs="?", help="HTML output path; optional with --validate-only")
    parser.add_argument("--validate-only", action="store_true", help="Check the record without writing HTML")
    args = parser.parse_args(argv)
    if not args.validate_only and args.output is None:
        parser.error("an output path is required unless --validate-only is used")
    try:
        data = json.loads(args.input.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        print(f"Cannot read session record: {exc}", file=sys.stderr)
        return 2
    errors = validate(data)
    if errors:
        print("Record validation failed:\n" + "\n".join("- " + error for error in errors), file=sys.stderr)
        return 2
    if args.validate_only:
        print("Record is valid. Real-world feasibility and implementation authority have not been established.")
        return 0
    try:
        if args.input.resolve() == args.output.resolve():
            print("Input and output must be different files.", file=sys.stderr)
            return 2
        args.output.write_text(render(data), encoding="utf-8")
    except (OSError, UnicodeError, ValueError) as exc:
        print(f"Cannot write workbook: {exc}", file=sys.stderr)
        return 2
    print(f"Workbook written to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
