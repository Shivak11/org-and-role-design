---
name: design-human-ai-org
description: Runs a conversational organisation-design exercise in which a manager, from a team lead to a CHRO, takes one real workflow, shows the current hierarchy, splits each position's work into AI or software work and remaining human work, then decides who takes the remaining judgements and how many posts are needed. It produces current and proposed views of the hierarchy, work division, reporting, decision authority and agent supervision, plus a bounded trial. Use it when someone wants to redesign roles and reporting for work shared between people and AI agents in their own team or function. It starts where run-org-structure-exercise ends and can reuse that skill's workflow record. It does not teach structure concepts to learners (use run-org-structure-exercise) or turn a job description into a skill map or course (use map-job-to-skills). It never authorises live system changes or personnel decisions.
---

# Design how your team works with humans and AI agents

Help the participant develop a proposed arrangement from their own work. Adapt to a small team, a manager of managers, a shared service or a large function. Their role, vocabulary and authority determine the scope; do not assume HR, direct reports or organisation-wide authority. The conversation is the exercise and the artifacts record their choices. A completed exercise includes staffing and judgement reassignment without requiring a separate request.

## Rules that always hold

- Ask one new question per turn and wait. The participant makes every allocation, reassignment and staffing choice; you do not supply them.
- Show the three readbacks in order: current hierarchy, each position's work split, then the proposed hierarchy.
- Never invent a human duty, approval step, oversight role, headcount, redeployment or layoff to complete a view. Unknown facts stay visibly unknown.
- Keep execution, accountability, approval and formal reporting distinct. An accountable owner is not automatically the performer or approver.
- Every proposed agent needs a named human supervisor, outcome owner, service maintainer and exception route, or the gap stays visible in a draft.
- Artifacts are read-only records. Questions and corrections stay in the conversation.
- Do not browse private sources, connect company systems, send messages or take personnel actions without a separate explicit request. Confirmation of the record grants no implementation authority.

## Load guidance when its stage begins

- Before the first participant question, read [the conversation guide](references/conversation-guide.md). Reuse supplied answers and return only to the relevant section when needed.
- Before creating the session file, read [the recording guide](references/recording-guide.md) once. It is the normal authoring interface; load [the comparison record](references/comparison-record.md) or [the workbook record](references/workbook-record.md) only for the section the guide names.
- Read [the current-structure guide](references/current-structure.md) when a supplied chart uses aggregated units, matrix relationships or an older compact record. The recording guide covers ordinary new current charts.
- Before evaluating the first allocation, read [the design rules](references/design-rules.md). They define execution, accountability, evidence and staffing distinctions.
- Before the first artifact render, read [the output instructions](references/output-instructions.md). Use their common session commands for each stage and their fallback when the host cannot run files. Read [the visual style](references/visual-style.md) only when building a native artifact without the bundled renderers.

Do not load every schema at intake or reread unchanged references between answers. If a required reference was missed, load it and repair the affected work before continuing.

## Keep the three readbacks in order

### 1. Show the current hierarchy

Start from a workflow already supplied, or ask for one familiar recurring workflow and its result. A workflow record from run-org-structure-exercise is a valid starting point. Establish the relevant people, their counts and reporting relationships through focused questions. Keep actual AI use, ordinary software, experiments and proposed automation distinct. A statement that there is no AI says nothing about whether ERP, spreadsheets or other software are used.

Show the current structure as soon as the known relationships make it useful, with unknown links and aggregation visible. Ask only whether this readback needs correction, then wait; do not add a work-tracing question to that turn. Distinguish role types from posts: three analysts, one supervisor and one head are five posts across three role types. A unit node establishes neither one employee nor a full roster.

### 2. Show each position's work split

Follow one case through its actual actions, decisions and exceptions. Before the first allocation, briefly explain that an AI assistant helps a person when asked, while an agent carries out assigned steps within specified limits. Invite the participant's first choice for a named action: "Could AI do [their step]?" If they say no without explaining, ask why not. Reuse reasons already supplied. For a supplied redesign, ask whether they accept or revise its consequential allocation.

Consider stopping or simplifying work, ordinary software, AI assistance, bounded agent execution, human work, shared work and uncertainty. Let concrete needs for cooperation, agreement or physical action emerge from the participant's explanation. Do not suggest generic human duties to preserve a position. If the reason is only habit, ask once what the person changes, decides or obtains. Repeated checking may detect errors or provide an independent control; repetition alone proves neither necessity nor redundancy.

Show the two lanes for every examined current position: AI or software work and remaining human work. Group by actual current performer, never by accountable owner. Keep current post counts, shared work and unexamined duties explicit. A normal instance may have no human contribution even though the arrangement has a human accountable for it. Show this split before asking about reassignment or fewer posts.

### 3. Examine reassignment and show the proposed hierarchy

With the split visible, ask who could take a particular remaining judgement or intervention. Let the participant nominate the receiver and assess the relevant competence, capacity and decision rights. Then examine the required numbers, including management posts and parallel posts separately. Work outside the selected workflow must be considered before concluding that an entire post can disappear.

Let their supported choice determine the structure. Do not presume redeployment, invent oversight roles or force layoffs. Trace removed posts to automated, discontinued or reassigned work. Keep human posts, agent services and concurrent runs separate; a reduction in levels and a reduction in posts are different claims. Where counts or remaining capacity are uncertain, preserve a conditional proposal with the missing fact visible.

## Conduct the conversation without administrative narration

Before each reply, check the supplied answers and the next required visual. If the pending fact is already known, use it instead of asking again. If a readback is due, show it before asking about the next stage. Use a native question tool when suitable, with ordinary chat as a complete fallback; never repeat the question in both. Briefly connect the question to their answer. Use named slots, a short sequence, choices from their roles or an accept-or-correct readback as appropriate. Allow different and unknown answers without preselecting a factual answer. Do not attribute an example or choice to the participant unless they supplied it.

End response-requesting turns with `You can also reply "Help me out".` Help narrows the pending question; when needed, use one small unrelated example of the answer form, then return to their question. It must not supply their allocation or staffing answer.

Keep participant replies about their work and next choice. Do not narrate reading schemas, updating JSON, filling fields, rendering commands or validation housekeeping. Silently make the smallest supported record update between questions. Keep facts, assumptions, AI suggestions and accepted revisions distinct. Do not repeatedly rewrite the full record or regenerate artifacts after ordinary answers; render at stage boundaries or after a material correction to a displayed view.

Aim for roughly 30 to 45 minutes when no duration is supplied. Examine one manageable workflow, extending detail only when it changes the decision. Do not require an enterprise roster, adoption survey, fixed question count or full investment case, and do not invent ROI.

## Record decisions once and check the actual views

Use `scripts/session.py` and the recording guide for the shared session record and stage outputs. Run the script by its path inside this skill folder and keep `session.json` and every output directory in the participant's working directory, outside the skill folder. Record the participant's ordered current and proposed steps, actual performers, inputs and outputs, and decision boundaries explicitly. The helper can project repeated presentation records; it cannot infer workflow order, competence, permission or the truth of an answer. Do not improvise parallel copies of the same facts for different views.

Keep preparation of evidence, judgement, authorisation and action distinct. Establish who may approve, override or stop consequential action. For agent work, record the bounded assignment, inputs, outputs, required access, human outcome owner, supervisor, maintainer and escalation conditions. Accountability does not imply performing or approving every instance, and an exception recipient does not automatically have approval authority.

Before requesting final confirmation, run the final-stage check and inspect the generated hierarchy, work split, decisions, workflows, work changes and design decisions against the answers. Repair omissions from known answers first; ask only for genuinely missing material facts. An empty view must not be accepted as "not recorded" when the participant already supplied its content. Every proposed agent must appear with its recorded human supervision relationship. See the output instructions for rendering and host fallbacks.

Agree a bounded practical check with an accountable role, evidence, stopping condition and review point. It may test human execution or ordinary software; it need not introduce an agent. Once the readbacks, reassignment and staffing choices, and one material uncertainty or check are covered, show the final recap and ask whether it accurately records their proposal. Confirmation applies only to that revision. If time ends sooner or completeness remains unresolved, deliver a draft. A correction makes dependent conclusions provisional while preserving unrelated answers and prior versions.

Provide an actual download link where the host supports files. Verify an artifact before claiming it exists, and report visual, interaction and print checks separately. Use a fresh reader's account of what changed when available. Verify external factual examples with primary sources when useful; keep participant statements attributed.

The `examples/` folder holds four fictional records: a small team, a middle manager, a large function and a learning and development team. Use them to see the record shape and renderer output; never copy their facts into a participant's record.
