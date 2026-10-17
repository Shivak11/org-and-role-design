# Record and render the exercise

Read once before the first file. In the commands below, `$SKILL` is the absolute path of this skill folder; set it once, for example `SKILL=/path/to/design-human-ai-org`. Run every command from the participant's working directory so that `session.json` and the output directories stay outside the skill folder, which a plugin install may keep read-only. Record only new answers between questions; do not regenerate the workbook or reread contracts on every turn. Run the stage command when the corresponding visual is due or its displayed facts change. The participant never edits JSON.

## Contents

- Start and show the current hierarchy
- Record the position-level split
- Record the remaining decisions and final views
- Compatibility and hosts

## Start and show the current hierarchy

From the participant's working directory, create the blank record:

```sh
python3 "$SKILL/scripts/session.py" init session.json
```

Fill `title`, the `organisation` description and scope, `comparison.perspective` (participant role and authority) and `comparison.scale`. Keep the initial `status: draft` and confirmation unchanged. Add the known current roles using this shape:

```json
{"id":"lead","label":"Team lead","parent_id":null,"reporting_status":"known_root","node_type":"role","post_count":1,"scope":"Selected workflow","responsibilities":[],"change":"unknown","reason":"Current arrangement"}
```

Use the participant's titles and IDs. `post_count` is optional and must be their explicit positive count, never the number of role labels. Known parents refer to another current role ID with `reporting_status: known_parent`. A null parent can mean `unknown` or `outside_scope`, not necessarily `known_root`. Use `team` or `unit` only for explicitly aggregated scope; such nodes cannot hold individual accountability. Omit `post_count` if unknown. The command writes count captions from supplied integers.

To record current AI, use `comparison.organisation.current` from [comparison-record.md](comparison-record.md), section “Compact organisation view”. If no current AI was reported, set both current/proposed lists empty and record the actual tools in `current_note`. ERP or Excel use is compatible with no AI. Do not turn “no AI” into “no software”. Unknown AI use stays explicitly unknown.

```sh
python3 "$SKILL/scripts/session.py" render session.json current-output --stage current
```

Show `current-output/current-structure.html` and invite correction. The `check.json` distinguishes role types from human posts; a null count means unknown. Use a new directory for each later revision; existing output directories are never overwritten.

## Record the position-level split

Keep current roles intact. Add proposed role references only as needed to record candidate accountability; this does not decide which posts remain. Add an `outcomes` entry: `{id, name, owner_id, success, basis}`. Owner is a proposed human role or null in an early draft.

Each `comparison.division` row describes the same bounded activity on both sides:

```json
{
  "id":"assess-request","label":"Assess the request","outcome_id":"service",
  "current":{"mode":"unknown","human_work":"","agent_work":"","owner_id":null,"basis":"Not established"},
  "proposed":{"mode":"unknown","human_work":"","agent_work":"","owner_id":null,"basis":"Not yet chosen"},
  "status":"unassessed","reason":"Awaiting the participant's allocation"
}
```

Replace unknowns only from answers. Modes: `human`, `agent`, `hybrid`, `software`, `unknown`, `none`. Human and agent modes require their respective contribution; hybrid requires both. Software requires `software_work`. None means known absence, with empty contributions and null owner. Hybrid `ai_kind: assistant` means human-directed AI; `agent` means delegated execution; `unknown` preserves uncertainty. Ordinary tools used by a person do not change that person's mode to software.

Use optional short `human_summary`, `agent_summary` or `software_summary` for visible labels. The full contributions remain in details. Record the actual permission in `condition` and any supplied transition in `handoff`. Owners identify accountability, not performers. Status is `changed`, `retained` (examined and kept), `clarified` (earlier practice unknown), or `unassessed`.

Map actual current performers explicitly:

```json
{"note":"Work split before deciding future posts","roles":[{"role_id":"lead","activity_ids":["assess-request"],"unexamined_work":""}]}
```

Store that object as `comparison.decomposition`. Fill `unexamined_work` from the answers: record a supplied statement that the position has no other duties, or name duties that remain unexamined. Do not insert an unknown-duty assumption when the participant already settled it. Include every examined current position. Sharing one activity across roles does not multiply its workload. Then run:

```sh
python3 "$SKILL/scripts/session.py" render session.json split-output --stage split
```

Show `split-output/role-decomposition.html` before asking about reassignment or fewer posts.

## Record the remaining decisions and final views

After the participant decides, update proposed roles and `comparison.reporting`: its `status`, `reason`, `current_context`, `proposed_context` and same-side functional/coordination `links`. Record the staffing choice and its basis in `exercise.staffing_review`, including unchanged or unresolved counts when that is their conclusion. Keep their remaining work, competence, capacity, cover, authority and other duties in the relevant role, staffing or open-question fields. Do not demand case-volume inputs for an hours-based estimate.

For counted removed posts, read only “Explicit human posts and staffing changes” in [comparison-record.md](comparison-record.md). Its `comparison.staffing` accepts `capacity: null` with `capacity_note`. Record separate owners for employee workload and absence-cover hours. The helper does not calculate a post reduction from automation percentages.

Select decision rows already recorded in division with `comparison.decision_ids: ["activity-id"]`; leave `comparison.decisions` empty. The helper creates that view without another copy. If a distinct standing rule is not an execution activity, write its comparison row directly in `decisions` instead and omit `decision_ids`. Give proposed decision rows a `condition` naming the permitted boundary, escalation and stop/override rights as supplied. The helper does not identify decisions by interpreting prose.

Review this selection against every permission the participant supplied. Include bounded agent choices such as clearing a case, routing an exception or stopping on missing evidence, as well as human exception judgements. A diagram containing only the senior human approver is incomplete when the agent or another human also has decision rights. Keep a standing stop or override right in the relevant condition/authority record; do not invent a routine approval step to display it. If a permission needs its own activity row, add it using the supplied facts before selecting it.

Record the ordered work in `workflows`. One workflow has `{id, label, outcome_id, coverage, current: [], proposed: []}`. Put each side's steps in their actual order:

```json
{"id":"review","activity_id":"assess-request","action":"Review the request","actor_type":"human","actor_id":"lead","actor_label":"Team lead","owner_id":"lead","input":"Request and supporting records","output":"Recorded decision","approval_by_id":null,"condition":"The participant's permitted boundary"}
```

Use the relevant side's human IDs. `activity_id` links to division and checks accountability and execution consistency. Proposed agent IDs refer to a service's agent role; current agent IDs are null with a descriptive label. Software and external actors have null IDs and explicit labels. Unknown historical sequence can stay empty with `current_note` explaining what is unknown. Never copy the proposed sequence into the past. Do not invent sequence from a list of roles. Record support work separately when it does not occur on every instance.

For a final workflow with multiple proposed steps, record its actual connectors in `relations: {"current": [], "proposed": [...]}`. Each connector is `{from_step_id, to_step_id, kind, label}`; IDs name steps on that side, `kind` is `information`, `authority` or `escalation`, and `label` states the supplied information or conditional permission. Connect normal and exception paths from the actual branch point, not consecutively because they happen to be listed that way. The final check rejects an unlinked multi-step proposal. Current connectors may remain empty when historical routing is unknown.

For shared human eligibility, override/stop IDs or more detailed handoffs, read only “Decision-level workflow view” in [comparison-record.md](comparison-record.md). The optional step `authority` is `{may_decide, must_escalate, override_by_id, stop_by_id}`; human IDs belong to that side. Optional `terminal` labels are supported only on the final listed step; other branches may end at their recorded output without a terminal label.

Use that branch when the participant has supplied conditional routes. An exception investigation must not appear as a compulsory step after every successfully cleared case. Preserve unknown historical routing rather than inferring it from the proposed arrangement.

For each proposed agent, add `services` using the shapes in [workbook-record.md](workbook-record.md). Essential fields are service `outcome_owner_id`, `supervisor_id`, `service_owner_id`; agent `tasks`, `autonomy`, `inputs`, `outputs`, `tools`, `escalation_to_id`, `escalation_condition`, `instances`. A proposed but unagreed external maintainer remains visible; it does not become an extra employee. Unknown running instances remain null.

The helper creates proposed AI groups from those services and their explicitly named supervisors. Do not write a second supervision claim. Preserve any separately reported AI assistant groups. For an existing custom service group, add `service_id` linking to the service. If several posts share its supervisor role, add `supervisor_post_id` to that group; do not choose a post by its array position. Current AI is never inferred from proposed services.

Leave `work_changes` and `levers` empty unless there is additional information they alone contain. The helper derives the missing readbacks from the division, reporting and selected decision records. This projection does not establish capability or truth. It rejects conflicting explicit decision selections or supervision links.

Complete `pilot` with scope, owner, evidence measure, baseline (unknown allowed), success, stop and review date/point. Preserve initial choices and revisions in `history`; put unresolved access, external approval and feasibility in `readiness` or `open_questions`. None of these fields grants live authority.

```sh
python3 "$SKILL/scripts/session.py" check session.json --stage final
python3 "$SKILL/scripts/session.py" render session.json final-output --stage final
```

Fix omissions from already supplied answers before asking another question. A structural error concerns the assistant's record, not something the participant should re-answer. A genuine missing choice receives one focused question. If the participant stops, deliver the latest valid stage as a draft. Do not remove the `exercise` marker or use an older renderer to evade the final check.

Show `final-output/comparison.html` and `workbook.html`. Inspect every view, including the workflow and agent's supervision link, before asking whether the record is accurate. Use a title that describes the comparison; do not leave an intake title saying only “current arrangement”. The check tests completeness and consistency; it cannot prove all prose matches the conversation. Confirm the exact revision only after the participant agrees. A correction increments the revision, resets acceptance and requires a new check/output directory. Continue editing the original session file, not a generated snapshot containing derived copies.

## Compatibility and hosts

Older renderers remain for previously authored records; their permissive validation is not the new exercise's completion check. The output reference covers native-artifact and text-only fallbacks when Python is unavailable. Read large contracts only for the fields needed in this case. Do not inspect renderer source during an ordinary interview unless a reproducible execution error requires diagnosis.
