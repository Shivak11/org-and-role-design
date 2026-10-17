# Show the current structure during discovery

For a new file-capable interview, use [recording-guide.md](recording-guide.md) and `scripts/session.py render session.json current-output --stage current`. Read the detailed contracts below only when handling an existing specialised record. Direct renderer validation is not the new exercise's final-completion check.

Create a useful current view from the participant's description or supplied current workflow, outcomes, contributors and relevant relationships. Reuse an existing chart or workbook instead of asking them to reconstruct it. A redesigned workflow alone does not establish current reporting or execution; ask only for the missing current facts needed to compare. It can contain unknowns. Keep participant records in their own session directory, outside the skill's examples and distribution.

Existing AI belongs in the current structure. If no AI is used operationally, show the actual human and software arrangement without an agent group. Label live experiments within their limited scope and keep planned pilots in the proposal. Do not assume either an all-human or an agent-using starting state. A person's tool use establishes neither a single agent nor autonomous execution, service ownership or permission to act.

## Choose the appropriate scope

For a small team, show supplied people or human roles. For a manager of managers, show known manager roles and team boundaries, then the selected team's detail. For a large function, show confirmed units and a labelled representative detail view. State what is aggregated, outside scope or unknown. Do not infer headcount or omit known levels without explanation.

Formal reporting is distinct from functional authority, project coordination, outcome ownership and AI usage. Label each relationship directly. A list of names does not establish reporting. A team or unit node is not an accountable human; use a supplied human role or leave ownership unresolved.

Ask for the number of people in each relevant position. Show parallel posts individually or through an explicit multiplicity, not one unexplained symbol. In the canonical renderer, use `size` for the supplied count and repeat it accurately in `chart_caption` where a shorter scope caption would otherwise conceal it. For example, a participant-confirmed four-officer group can use `size: "4 officer posts"` and the same chart caption. A role title never establishes a count. Unknown counts remain unknown. Do not use the final `comparison.staffing` extension merely to draw discovery: that contract requires proposed posts and capacity which have not yet been decided.

During discovery, keep unknown future arrangements unresolved. Use the general renderer's current-only view when Python is available:

```bash
python3 "$SKILL/scripts/render_comparison.py" session.json current-structure.html --current-only
```

Follow the canonical record and current-only requirements in [the comparison record](comparison-record.md). Its optional node type, size and reporting-status fields support human roles, teams and units. The current-only view must not present a copied baseline as an accepted future design. A host-native artifact remains an alternative when execution is unavailable.

The compact renderer below remains useful for its existing person-level records. It does not model multi-unit or matrix views fully; do not force those views into its `people` records.

## Compact renderer for a person-level current view

```bash
python3 "$SKILL/scripts/render_structure.py" current-structure.json current-structure.html
```

The input contains `organisation`, `title` and `subtitle` strings; `phase` set to `current`; `outcomes` as `{description, owner_id}` records; `people`; and `notes` stating scope limits or unresolved facts.

Each person has `id`, `name`, `role`, `reports_to`, `ai` and `tasks`. `reports_to` is another supplied human ID or null. When null, explain in notes whether reporting is unknown or outside scope; do not imply every disconnected person heads a department. Use the work described when a formal role title is unknown.

The `ai` object contains `tools` and `work` string lists and `count`, which remains null without an established count. Two people using the same product do not necessarily share an agent service. An adjacent AI group represents described usage, not an inferred number of agents. Routine use of prompts to draft or summarise can be AI assistance; it does not establish an agent service. Use the canonical comparison's optional `ai_kind` when the distinction matters, since the older compact input does not encode it separately.

Each task has `id`, `label`, `execution`, `human_work`, `agent_work`, `why` and `basis`. Supported execution values are `human`, `agent`, `hybrid` and `unknown`. The current compact renderer has no dedicated software mode; describe ordinary software explicitly in task detail, or use a native current artifact when a distinct software actor matters. The canonical comparison supports software separately.

- **Human only:** the person carries out the bounded task without AI contribution. Ordinary tools may still be used.
- **Agent only:** the agent completes a normal instance within its stated limits. Record human accountability and exceptions separately.
- **Human + agent:** state the human contribution, agent contribution and handoff.
- **Split to confirm:** some AI usage may be known, but the normal division remains incomplete. Preserve partial facts.

An unexplored reason stays unexplored. Do not fill it with a generic justification for automation. A person-to-AI usage line does not establish service maintenance or approval authority.

Show the current view and invite a correction before developing the proposal. Keep this view available for comparison. Do not require the participant to edit JSON or answer a second questionnaire inside the artifact.

## Show the work split before the final comparison

After the participant examines each current position's tasks, use `scripts/render_decomposition.py` with the canonical record and the `comparison.decomposition` mapping in [the comparison record](comparison-record.md). Show proposed AI/software contributions beside remaining human work under the actual current performer. Preserve supplied counts and unexamined work. Do not infer a performer from the accountable owner or show a final proposed hierarchy during this stage.

The participant then considers whether the remaining judgements and other justified human work need the same people, or can be assigned differently. Record their choices and count changes before using `scripts/render_comparison.py` for the final paired division of work, reporting and decision authority. Preserve stable IDs and show what is changed, retained, newly specified or not assessed. Instructions for all three visual stages are in [the output instructions](output-instructions.md).

Do not omit a reporting pair because the structure remains the same. If reporting has not been examined, repeat the baseline only as context and label it not assessed. If the participant explicitly chooses to keep it, label it retained. If a proposed owner or link is known but earlier practice is not, label it newly specified rather than showing a false transfer of responsibility.

For Human + agent work, show each contribution on both sides. When either earlier contribution is unknown, say so. Separate formal reporting changes from changed task allocation, delegated permission, maintenance or exception handling. A new exception recipient does not automatically become an approver.

## Earlier specialised records

The following renderers remain for compatibility with their existing inputs. They are not the default for a new manager's exercise:

| Renderer | Supported record and limit |
|---|---|
| `render_release_comparison.py` | The previously used release record, comparing independent human approval with a participant-selected class of bounded automatic release. |
| `render_org_proposal.py` | The earlier people/views/allocations record; it preserves one supplied reporting baseline and cannot establish arbitrary reporting changes. |
| `render_change_map.py` | That organisation-proposal record plus its release object; it focuses on the same bounded release arrangement and optional proposed workflows. |

Do not select a release renderer just because agents are involved. Never reinterpret a different department's work to fit that example. Migrate an older session to the canonical comparison by preserving facts and marking missing information explicitly.

Inspect the actual generated diagrams before sharing. Test HTML controls separately when permitted. SVG inspection does not establish browser, mobile or print behaviour. Preserve prior private revisions and keep them out of distributed examples.
