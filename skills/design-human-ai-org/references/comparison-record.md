# Current and proposed comparison record

New interviews use [recording-guide.md](recording-guide.md) and `scripts/session.py`. With that helper, `comparison.decision_ids` selects division rows for the decision view. A proposed AI group's `service_id` links its service; `supervisor_post_id` identifies a supervising post when several posts share the role. The helper rejects conflicting supervision and never matches services by label. Optional per-role integer `post_count` is participant-supplied; the helper writes its visible caption and count readback.

## Contents

- Comparison object
- Reporting
- Intermediate decomposition by current performer
- Render and inspect
- Compact organisation view
- Decision-level workflow view
- Explicit human posts and staffing changes

The comparison renderer reads the complete version 1 record described in [workbook-record.md](workbook-record.md), with a `comparison` object added. Older renderers and records remain usable. The facilitator maintains the record; participants answer ordinary questions in conversation.

Use the same IDs for the same work and people across the two sides. Current means the arrangement the participant describes today, including agents already used. Proposed means the arrangement being considered. Do not create a historical human-only arrangement to make an agent allocation appear new.

## Comparison object

`perspective` describes the participant's role and authority in plain text. `scale` records whether the chart represents named people, human roles, teams or units and the participant-supplied scope. It must not convert one role into an inferred headcount.

`division` and `decisions` are lists with this entry shape:

```json
{
  "id": "prepare-response",
  "label": "Prepare a response to a routine service request",
  "outcome_id": "service-quality",
  "current": {
    "mode": "human",
    "human_work": "A service adviser prepares the response.",
    "agent_work": "",
    "owner_id": "service-manager",
    "basis": "Participant described the most recent request."
  },
  "proposed": {
    "mode": "hybrid",
    "human_work": "The adviser checks the draft and sends the accepted response.",
    "agent_work": "An agent drafts the response and passes it to the adviser.",
    "owner_id": "service-manager",
    "basis": "Participant-selected trial allocation."
  },
  "status": "changed",
  "reason": "Drafting is repetitive; the adviser still checks case-specific commitments."
}
```

Each entry needs non-empty `id`, `label`, `outcome_id` and `reason` text. The outcome ID refers to the complete record's outcomes. Side objects contain `mode`, `human_work`, `agent_work`, `owner_id` and `basis`. Each contribution and basis is text. Keep human and AI contributions separate. Optional `handoff` and `condition` strings state the transition and result passed onward, and the permission boundary. Existing records may describe these in their contribution text.

Modes are `human`, `agent`, `hybrid`, `software`, `unknown` and `none`. A human, agent or hybrid mode requires its corresponding contribution text. Software mode requires a non-empty `software_work` string; do not put ordinary software activity under an agent label. Task execution is separate from the accountable human shown below it. Agent-only execution can still have a named human accountable for its permitted operation.

Use `none` for an activity known to be absent from that version of the workflow. It displays “No activity in this workflow” and requires a null owner. It is different from `unknown`, where the allocation has not been established. This permits comparisons in which an activity is introduced or retired. A confirmed absent proposed activity may have a null owner because there is no activity to own.

Optional `ai_kind` is `assistant`, `agent` or `unknown`. It defaults to `agent` for compatibility with earlier records. For manually directed AI drafting, use `mode: hybrid` and `ai_kind: assistant`; the chart displays “Human + AI assistant” and labels the AI contribution accordingly. For hybrid work whose AI type is unresolved, use `ai_kind: unknown`. The existing `agent_work` field contains that AI contribution so the canonical record remains compatible. An assistant cannot use `mode: agent`, which would falsely imply agent-only execution. The same pictograms identify human and AI contributions; the text makes the distinction explicit. Do not infer a running service or coordinated swarm from manually prompted AI use.

Current owner IDs refer to `current_roles`; proposed owner IDs refer to `proposed_roles`. Use null when a draft has unresolved accountability. A confirmed proposed activity requires a known human owner, except when the activity is explicitly absent. A `person` or human `role` can hold accountability; a `team` or `unit` cannot substitute for one accountable human.

Statuses have these meanings:

- `changed`: an actual proposed difference from the recorded current arrangement.
- `retained`: the participant chose to keep the arrangement. The current and proposed execution modes must match.
- `clarified`: the proposal specifies something whose earlier practice was not established. Displayed as “Newly specified”.
- `unassessed`: the participant has not made a redesign decision. A repeated baseline does not establish confirmation.

The renderer checks structural consistency. The facilitator must check whether the words support the selected status; the renderer cannot infer historical evidence from prose.

## Reporting

Formal reporting uses `parent_id` in the complete record's current and proposed roles. No three-level limit is imposed. Use null for a parent whose identity is unresolved or outside scope; qualify it with `reporting_status`.

Optional per-role fields are:

```json
{
  "node_type": "role",
  "size": "One manager role; team count not supplied",
  "reporting_status": "known_parent"
}
```

`node_type` is `person`, `role`, `team` or `unit`. `size` is participant-supplied text. Do not infer agent instances or people counts. `reporting_status` is `known_parent`, `known_root`, `unknown` or `outside_scope`. A known parent requires a non-null `parent_id`; the other states require null. When these optional fields are absent, a non-null parent remains a known parent, and a null parent is explicitly unresolved.

The reporting comparison has this shape:

```json
{
  "status": "unassessed",
  "reason": "The participant has not proposed changes to formal reporting.",
  "current_context": "The recorded team and its formal managers.",
  "proposed_context": "The same baseline is shown until reporting is assessed.",
  "links": {"current": [], "proposed": []}
}
```

Supplementary links are `{from_id, to_id, kind, label}`. Both IDs belong to that side's role list. `kind` is `coordination` or `functional`; `label` states the relationship. These links appear separately with their own line patterns. They do not silently become formal reporting. A retained reporting comparison cannot change its role IDs or formal parent relationships.

Large organisations should first be scoped into participant-confirmed units and representative workflows. The renderer does not drop levels or roles. Its reporting diagram expands with the record, offers role-location controls, and provides an expandable complete role register. Very broad charts require horizontal scrolling. A unit-level chart makes claims only about the represented units; it does not establish that every job in them was assessed.

## Intermediate decomposition by current performer

After the initial hierarchy and before reassignment or post-count decisions, add `comparison.decomposition` to render each current position's work in two lanes. This object maps actual performers to the existing division rows; `owner_id` remains accountability and must not be used to infer who performs the task.

```json
{
  "note": "The participant's proposed work split, before deciding which posts remain.",
  "roles": [
    {
      "role_id": "service-adviser",
      "activity_ids": ["prepare-response"],
      "unexamined_work": ""
    }
  ]
}
```

`note` is nonempty plain text. Each mapping has a unique `role_id` from `current_roles`, unique `activity_ids` within that mapping referring to `comparison.division`, and an `unexamined_work` string. Fill that string from the participant's scope answer, including a supplied statement of no other duties; use an unresolved statement only when the scope is genuinely unknown. The same activity can appear under more than one current role when they actually share it; the display must identify sharing and must not count it as independent workloads. All current positions remain visible, including missing or empty mappings labelled unexamined. An unmapped activity remains visible separately, without inferring a performer from its owner. Do not add a current performer for an activity known to be absent in the current workflow.

The renderer takes AI, software and human contributions from each row's proposed side, preserving the current position grouping until the learner considers reassignment. It distinguishes AI assistance, delegated agents, ordinary software and unknown allocation. `mode: none` represents an explicitly absent activity, not missing knowledge. Basis, reason, handoff, condition and human accountability remain available with the activity. Do not erase partial contributions or infer the absence of human work from an unknown mode.

Use `human_work` to state any justified judgement, agreement-seeking or physical intervention in the participant's terms. Use `reason` and `basis` for why it remains and what supports that belief; use `history` to retain the initial judgement and subsequent confirmation or correction. A generic human-duty label is insufficient. No special trust or politics classification is required.

Use supplied role `size` text to show current counts. Do not parse arbitrary prose into staffing arithmetic. This intermediate view omits the proposed hierarchy, removed-post records and final capacity calculation even if the source contains them. It validates the canonical record and the mapping before writing and does not mutate the input.

```bash
python3 "$SKILL/scripts/render_decomposition.py" session.json role-decomposition.html --validate-only
python3 "$SKILL/scripts/render_decomposition.py" session.json role-decomposition.html
```

The participant never edits these fields. Preserve a separate snapshot of this intermediate record before recording later judgement transfers or staffing choices. Do not pass the completed staffing record to recreate this earlier stage: its contribution and reason text may already contain later decisions, and the renderer preserves supplied wording rather than deleting those decisions from prose. The older final comparison and workbook continue to accept records without this extension.

## Render and inspect

From the participant's working directory, with `$SKILL` set to this skill folder as described in [recording-guide.md](recording-guide.md):

```sh
python3 "$SKILL/scripts/render_comparison.py" record.json comparison.html \
  --division-svg division.svg \
  --reporting-svg reporting.svg \
  --decisions-svg decisions.svg
python3 "$SKILL/scripts/render_comparison.py" record.json --validate-only
python3 "$SKILL/scripts/render_comparison.py" current-draft.json current.html \
  --current-only --reporting-svg current-reporting.svg
```

All comparisons are present without JavaScript. With JavaScript, the initial view is the connected human-AI organisation and the controls select reporting or decision authority. Arrow keys, Home and End work on the view controls. Current and proposed contributions, accountability, basis, rationale and change status remain visible together. SVGs use the same rendering functions as the HTML.

The optional `--current-only` route renders only the supplied current reporting structure and its complete role register. It uses a valid draft version 1 record with the comparison extension; proposed roles may be empty and the division and decision lists empty. It does not create a proposed copy. Only the reporting SVG export is permitted with that route. Current-only HTML uses native disclosures and requires no JavaScript.

For a proposed arrangement, the HTML also includes expandable agent-service responsibilities from the canonical `services` list. It distinguishes the outcome owner, workflow supervisor and service maintenance owner, then records each agent role's tasks, boundaries, input, output, exception recipient and instance count. These services are explicitly proposed; their presence does not prove current deployment.

All CSS, scripts, icons and fonts have local fallbacks. The HTML needs no server, external asset or StyleRef service. It includes only a normal profile link. The command validates and renders all requested outputs before writing; source/output and duplicate-output paths are rejected.

Inspect actual rendered diagrams and read every unknown or newly specified label before delivery. SVG inspection does not prove browser interaction, mobile layout or printing. A large reporting SVG may shrink substantially in print; keep the HTML and complete role register available for detailed reading.

## Compact organisation view

The default view shows the human hierarchy with explicitly recorded AI associations on both sides. Add `comparison.organisation` with `current_note`, `proposed_note`, `current` and `proposed`. Each side is a list of groups: `{id, label, supervisor_id, summary, detail, status, ai_kind, instances, relationship}`. IDs are distinct from human role IDs. `supervisor_id` names the associated human on the same side, or null for unknown. `relationship` is `uses` or `supervises`; the field name alone must not turn a recorded user into a supervisor. `ai_kind` is `assistant`, `agent`, `mixed` or `unknown`; mixed means the explicitly labelled collection contains both assistants and agents. `instances` is null unless a positive count is actually supplied. A group symbol does not establish a swarm. Status uses the existing comparison meanings.

Use short, accurate `label` and `summary` text on AI shapes and keep permissions, counts, rationale and supervision limits in `detail`. Human roles may have a short `chart_caption` for a consequential reporting change. Known absent AI is an empty list with an explicit note; a missing organisation extension means associations were not recorded. Never derive current AI from proposed services or derive supervision from task accountability. Show a missing supervisor as a detached group.

For division/decision sides, supply `human_summary`, `agent_summary` or `software_summary` for a short action label, and a row `short_reason` for the visible rationale. These summarise the full fields without changing them. The compact diagram draws separate human and AI shapes for shared work; full contributions, conditions and evidence remain in native details. A plus sign establishes joint contribution without inventing an ordered handoff.

Export the organisation chart with `--organisation-svg organisation.svg`. Selectable human, group and activity nodes open their full records in HTML. Keep diagram labels short by authoring an accurate summary; do not clip essential text or substitute paragraphs in large boxes.

## Decision-level workflow view

When `workflows` is nonempty, the comparison includes a Workflow view alongside the existing four views. The ordinary opening remains Organisation. A `#view-workflow` fragment opens the workflow directly. Links from a person's record open the relevant workflow step, including when its panel was hidden. Every panel and native disclosure remains available without JavaScript.

The view uses the canonical ordered current/proposed steps. It never reconstructs a missing current sequence from a proposed allocation. Optional `current_note` and `proposed_note` strings explain each side; `policy` records standing rules outside routine execution. An empty side with a note displays that note. Without a note it says that no step-level sequence has been recorded.

Optional step fields add decision and handoff detail:

- `summary`: nonempty short action label; full `action` remains in the step record.
- `task_type`: nonempty plain-language description of the knowledge task. It does not determine the performer.
- `reasoning`: `evidence`, `prediction`, `judgement`, `action` or `mixed`.
- `knowledge`: `{rules, facts}`, both strings, separating reusable criteria from case observations.
- `authority`: `{may_decide, must_escalate, override_by_id, stop_by_id}`. The first two fields are nonempty strings. The latter two are nullable human role IDs on the same side. Null means unresolved authority.
- `escalation`: `{to_id, trigger, return_to_step_id}`. The recipient is a nullable same-side human role; the trigger is nonempty text; the return is null or a step ID in this workflow on this side. Returning work to an agent does not make that agent the human escalation recipient.
- `handoff_cost`: nonempty text describing known preparation, coordination or waiting effort. Record unknown measures without inventing estimates.
- `terminal`: optional `{label, condition}` with nonempty strings on the final recorded step, naming a conditional completion result. A return edge still needs its own condition; completion must not look like an inevitable loop. This is an end state, not another actor or work assignment.

`actor_type: unknown` requires null `actor_id` and a nonempty `actor_label`. It renders as unresolved execution, separate from software and agents. Unknown proposed execution is draft-only. Unknown historical execution can remain unknown in a confirmed proposal.

For a human step where one person is selected per instance, supply null `actor_id` and a nonempty unique `eligible_actor_ids` list of same-side human IDs. Optional boolean `exclude_maker` states the independence rule. This is one eligible performer, not joint execution. The step's accountable human remains a separate field; the eligible list does not silently assign an owner. Teams and units cannot serve as human authority references.

Optional `relations` contains both `current` and `proposed` arrays. Each item is `{from_step_id, to_step_id, kind, label}`. Endpoints must be distinct steps in the same workflow and side; `label` is nonempty. `kind` is `information`, `authority` or `escalation`. These appear as named solid information, heavier authority and dashed escalation lines. They never imply reporting. If relations are absent, a light unlabelled connector indicates only the recorded order. Do not label a return-to-work edge as escalation when it actually records the human's subsequent authorisation.

All optional objects require the complete keys above when present. Every field is escaped during HTML/SVG rendering. Existing records without this extension remain valid; validation establishes internal consistency, not historical attribution, actual access or operational readiness.

## Explicit human posts and staffing changes

Examine position counts after the participant has seen the work split and considered who can take the remaining human responsibilities. Use optional `comparison.staffing` for the resulting counted comparison when this contract fits the case. The opening Organisation view then draws individual posts; the other role views retain their grouped responsibilities. Without this extension, existing outputs are unchanged. Do not manufacture a roster or use this final contract to populate the discovery stage. An authored teaching scenario must identify its assumptions.

The counted-post chart requires established reporting within its scope. If any role's reporting is unknown, keep explicit counts in the ordinary role view and mark the missing links; do not invent a root or claim a number of reporting levels. A recorded manager outside the selected scope is different from an unknown manager.

Required fields:

- `basis`: nonempty text stating what the staffing comparison represents.
- `groups`: arrays of `{id, label}` identifying queues or work groups; these are not extra managers.
- `current` and `proposed`: arrays of `{id, role_id, parent_post_id, group_id, label}`. Every record means one human post. `role_id` identifies a same-side human role; `parent_post_id` identifies a same-side human post or is null. Its role must agree with the role-level parent. `group_id` identifies a group or is null. Represent every scoped role. Stable post IDs identify retained posts.
- `removed`: arrays of `{post_id, kind, reason, work_ids}` covering every current post absent from the proposal exactly once. `kind` is `vertical` for a management post with current reports, or `horizontal` for reduced parallel delivery positions. Each `work_ids` entry identifies a division row that explains the task destination. A removed post must not retain a proposed formal-reporting edge.
- `capacity`: either the calculation object below, or explicit `null` with a nonempty `capacity_note`. Do not omit the field. Use the note when the participant has a workload rationale that does not fit the case-volume formula. Record actual hours, coverage, other responsibilities and remaining uncertainties as supplied; never manufacture missing inputs. The chart shows the recorded post counts and the note without claiming calculated sufficiency. With a calculation object, the calculation covers explicitly named delivery posts; head and external-support work remain separately described.

Capacity requires positive integer `monthly_cases` and `minimum_posts`; positive finite `current_minutes_per_case`, `exception_minutes` and `hours_per_post`; nonnegative finite `review_minutes`, `operating_hours` and `shared_support_hours`; zero-to-one `automated_share` and `sample_share`; and a `planning_utilisation` fraction greater than zero and no greater than one. Booleans are not numbers. `current_officer_post_ids` and `proposed_officer_post_ids` must be unique, same-side delivery posts and include every post of the covered role. `assumption_note`, `shared_support_note` and `head_work_note` explain the remaining operational assumptions.

Monthly human hours equal residual cases times exception minutes, plus sampled automated cases times review minutes, divided by sixty, plus operating hours. Required posts are the larger of the stated coverage minimum and the rounded-up hours divided by per-post hours at the planning ceiling. This is a scenario calculation; it does not amend the recorded proposal. The displayed 70%, 50% and 30% comparisons test whether the same proposal still fits. Changes in staffing or escalation volume also require reassessing management capacity.

Each removed position opens its current reporting, reason and task-transfer links. A current-only render suppresses future removals, proposal details and capacity comparisons. The detailed workbook records every post and the same calculation or workload note. Both renderers reject invalid staffing data before rendering. No employee performance inference, live authority or redundancy decision follows from this record.
