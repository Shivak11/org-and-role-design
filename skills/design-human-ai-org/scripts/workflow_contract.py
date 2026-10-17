"""Validate optional decision-level workflow fields without changing the record.

The workbook validator calls this after its original structural checks succeed.
Records without these fields remain supported. This module has no renderer or
third-party dependencies.
"""

from __future__ import annotations


def validate_workflows(data):
    """Return field-path errors for the additive workflow contract."""
    errors = []

    def error(path, message):
        errors.append(f"{path}: {message}")

    def string(value, path, nonempty=False):
        if not isinstance(value, str):
            error(path, "must be a string")
            return False
        if nonempty and not value.strip():
            error(path, "must not be empty")
            return False
        return True

    def obj(value, path, names):
        if not isinstance(value, dict):
            error(path, "must be an object")
            return None
        for name in names:
            if name not in value:
                error(f"{path}.{name}", "is required")
        return value

    def array(value, path):
        if not isinstance(value, list):
            error(path, "must be a list")
            return []
        return value

    if not isinstance(data, dict):
        return ["record: must be an object"]
    workflows = array(data.get("workflows"), "workflows")
    roles = {}
    for side in ("current", "proposed"):
        supplied = array(data.get(side + "_roles"), side + "_roles")
        roles[side] = {
            role["id"]: role for role in supplied
            if isinstance(role, dict) and isinstance(role.get("id"), str)
        }

    def human_ref(value, path, side, nullable=True):
        if value is None and nullable:
            return
        if not string(value, path, True):
            return
        if value not in roles[side]:
            error(path, "must refer to a human role on the same side")
        elif roles[side][value].get("node_type", "role") not in ("person", "role"):
            error(path, "must identify a human role, not a team or unit")

    for index, workflow in enumerate(workflows):
        path = f"workflows[{index}]"
        if not isinstance(workflow, dict):
            error(path, "must be an object")
            continue
        for field in ("current_note", "proposed_note", "policy"):
            if field in workflow:
                string(workflow[field], f"{path}.{field}")
        sides = {}
        step_ids = {}
        for side in ("current", "proposed"):
            sides[side] = array(workflow.get(side), f"{path}.{side}")
            step_ids[side] = {
                step["id"] for step in sides[side]
                if isinstance(step, dict) and isinstance(step.get("id"), str)
            }

        def step_ref(value, field_path, side, nullable=False):
            if value is None and nullable:
                return
            if string(value, field_path, True) and value not in step_ids[side]:
                error(field_path, "must refer to a step in this workflow on the same side")

        for side, steps in sides.items():
            for step_index, step in enumerate(steps):
                step_path = f"{path}.{side}[{step_index}]"
                if not isinstance(step, dict):
                    error(step_path, "must be an object")
                    continue
                for field in ("summary", "task_type", "handoff_cost"):
                    if field in step:
                        string(step[field], f"{step_path}.{field}", True)
                if "reasoning" in step and (
                    not isinstance(step["reasoning"], str)
                    or step["reasoning"] not in ("evidence", "prediction", "judgement", "action", "mixed")
                ):
                    error(f"{step_path}.reasoning", "must be evidence, prediction, judgement, action or mixed")
                for field in ("owner_id", "approval_by_id"):
                    if field in step:
                        human_ref(step[field], f"{step_path}.{field}", side)
                if step.get("actor_type") == "human" and step.get("actor_id") is not None:
                    human_ref(step["actor_id"], f"{step_path}.actor_id", side, False)
                if step.get("actor_type") == "unknown":
                    if step.get("actor_id") is not None:
                        error(f"{step_path}.actor_id", "must be null for unresolved execution")
                    string(step.get("actor_label"), f"{step_path}.actor_label", True)
                    if side == "proposed" and data.get("status") != "draft":
                        error(f"{step_path}.actor_type", "unresolved proposed execution is allowed only in a draft")

                if "eligible_actor_ids" in step:
                    eligible = array(step["eligible_actor_ids"], f"{step_path}.eligible_actor_ids")
                    if not eligible:
                        error(f"{step_path}.eligible_actor_ids", "must contain at least one eligible human")
                    if step.get("actor_type") != "human" or step.get("actor_id") is not None:
                        error(f"{step_path}.eligible_actor_ids", "requires human actor_type and null actor_id")
                    seen = set()
                    for actor_index, actor_id in enumerate(eligible):
                        actor_path = f"{step_path}.eligible_actor_ids[{actor_index}]"
                        human_ref(actor_id, actor_path, side, False)
                        if isinstance(actor_id, str):
                            if actor_id in seen:
                                error(actor_path, "duplicates an eligible human")
                            seen.add(actor_id)
                if "exclude_maker" in step:
                    if "eligible_actor_ids" not in step:
                        error(f"{step_path}.exclude_maker", "requires eligible_actor_ids")
                    if type(step["exclude_maker"]) is not bool:
                        error(f"{step_path}.exclude_maker", "must be a boolean")

                if "knowledge" in step:
                    knowledge = obj(step["knowledge"], f"{step_path}.knowledge", ("rules", "facts"))
                    if knowledge is not None:
                        for field in ("rules", "facts"):
                            if field in knowledge:
                                string(knowledge[field], f"{step_path}.knowledge.{field}")
                if "terminal" in step:
                    if step_index != len(steps) - 1:
                        error(f"{step_path}.terminal", "is supported only on the final recorded step")
                    terminal = obj(step["terminal"], f"{step_path}.terminal", ("label", "condition"))
                    if terminal is not None:
                        for field in ("label", "condition"):
                            if field in terminal:
                                string(terminal[field], f"{step_path}.terminal.{field}", True)
                if "authority" in step:
                    authority = obj(step["authority"], f"{step_path}.authority",
                                    ("may_decide", "must_escalate", "override_by_id", "stop_by_id"))
                    if authority is not None:
                        for field in ("may_decide", "must_escalate"):
                            if field in authority:
                                string(authority[field], f"{step_path}.authority.{field}", True)
                        for field in ("override_by_id", "stop_by_id"):
                            if field in authority:
                                human_ref(authority[field], f"{step_path}.authority.{field}", side)
                if "escalation" in step:
                    escalation = obj(step["escalation"], f"{step_path}.escalation",
                                     ("to_id", "trigger", "return_to_step_id"))
                    if escalation is not None:
                        if "to_id" in escalation:
                            human_ref(escalation["to_id"], f"{step_path}.escalation.to_id", side)
                        if "trigger" in escalation:
                            string(escalation["trigger"], f"{step_path}.escalation.trigger", True)
                        if "return_to_step_id" in escalation:
                            step_ref(escalation["return_to_step_id"], f"{step_path}.escalation.return_to_step_id", side, True)

        if "relations" in workflow:
            relations = obj(workflow["relations"], f"{path}.relations", ("current", "proposed"))
            if relations is not None:
                for side in ("current", "proposed"):
                    if side not in relations:
                        continue
                    for relation_index, relation in enumerate(array(relations[side], f"{path}.relations.{side}")):
                        relation_path = f"{path}.relations.{side}[{relation_index}]"
                        relation = obj(relation, relation_path, ("from_step_id", "to_step_id", "kind", "label"))
                        if relation is None:
                            continue
                        for field in ("from_step_id", "to_step_id"):
                            if field in relation:
                                step_ref(relation[field], f"{relation_path}.{field}", side)
                        source, target = relation.get("from_step_id"), relation.get("to_step_id")
                        if isinstance(source, str) and isinstance(target, str) and source == target:
                            error(relation_path, "source and target steps must be different")
                        if "kind" in relation and (
                            not isinstance(relation["kind"], str)
                            or relation["kind"] not in ("information", "authority", "escalation")
                        ):
                            error(f"{relation_path}.kind", "must be information, authority or escalation")
                        if "label" in relation:
                            string(relation["label"], f"{relation_path}.label", True)
    return errors
