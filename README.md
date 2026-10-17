# org-and-role-design

This plugin gives an AI assistant three skills for designing organisations and roles when people and AI share the work. Managers use it to redesign their team's work for AI agents, teachers use it to run an organisation-structure exercise with a class, and the third skill turns a job description into a skill map and a course.

A guide that helps you pick a skill is in [docs/index.html](docs/index.html).

## The three skills

| Skill | What it does | Use it when |
|---|---|---|
| [`design-human-ai-org`](skills/design-human-ai-org/SKILL.md) | Takes one real workflow from a manager's team, shows the current hierarchy, splits each position's work between AI or software and people, then asks who takes the remaining judgements and how many posts are needed. It renders current and proposed views of the hierarchy, work, reporting, decision authority and agent supervision. | You manage a team or function and want to work out how it would be organised if AI agents took on part of the work. |
| [`run-org-structure-exercise`](skills/run-org-structure-exercise/SKILL.md) | Has a learner describe an everyday workflow, such as a refund, propose a change, and then explains span of control, centralisation, standardisation, formalisation and coordination from the learner's own choices. | You teach organisation structure, or want to understand it, through a workflow you can describe. |
| [`map-job-to-skills`](skills/map-job-to-skills/SKILL.md) | Turns a job description into a skill map across technical, cognitive, behavioural and domain pillars, and can build a course of eleven-screen modules and a closing mock interview script from it. | You need to know what a role really tests for, or want learning content for one role. |

The first two skills connect. `run-org-structure-exercise` ends with a workflow record that `design-human-ai-org` can start from, so a class can learn the concepts first and then redesign the same workflow for people and agents. `map-job-to-skills` stands alone: it looks at one role, while the other two look at how several roles fit together.

None of the skills connects to a company system, sends a message or makes a personnel decision. Use role titles and fictional or anonymised examples.

## Worked examples

### design-human-ai-org

A service desk manager has four direct reports: a senior specialist, two associates and a coordinator. She chooses the workflow for incoming customer requests. The assistant draws the current hierarchy and asks her to correct it. They then trace one request, and for each step the assistant asks whether AI could do it. She decides that agents can propose a category for each request while the coordinator resolves uncertain or new categories, and that agents can send a status update only when it matches a template the senior specialist has approved. The assistant shows each position's work split into AI work and remaining human work. She keeps formal reporting unchanged for the trial and names the senior specialist as the agents' supervisor. The final views show the current and proposed hierarchy side by side with the agents attached to their supervisor, the changed decision rights, and a limited trial that pauses on any untraceable output or action beyond permission. The record for this case is in [`examples/small-team.json`](skills/design-human-ai-org/examples/small-team.json).

### run-org-structure-exercise

A student picks the refund workflow. She writes that an associate checks the receipt, messages the store manager, the manager decides, and accounts pays; six associates report to the manager. Her change is to let associates decide refunds below Rs 2,000 and to write that rule down. Only then does the assistant explain that she has decentralised ordinary refunds while the manager keeps the larger ones, that the written limit standardises and formalises the decision, and that the span of control stays at six because no reporting line changed. The full run is in [`examples/refund-workflow.md`](skills/run-org-structure-exercise/examples/refund-workflow.md).

### map-job-to-skills

A placement officer pastes a presales management trainee description from an IT services company. The skill returns a skill map with three technical atoms (project planning, stakeholder analysis, pricing strategy), two cognitive and three behavioural atoms from fixed menus, and two glossary clusters of bid and commercial terms. Asked for a course, it builds three modules of eleven screens, from a short orientation to a case about a senior colleague's proposal section that the client will find too technical, and ends with a fifteen-minute mock interview script and scoring guide. A fictional version is in [`examples/example_output.json.md`](skills/map-job-to-skills/examples/example_output.json.md).

## Install

### Claude Code

```sh
claude plugin marketplace add Shivak11/org-and-role-design
claude plugin install org-and-role-design@org-and-role-design
```

### Codex

```sh
codex plugin marketplace add Shivak11/org-and-role-design
codex plugin add org-and-role-design@org-and-role-design
```

### Other agents

Each folder under `skills/` is a self-contained skill with a `SKILL.md`. Copy the folder you need into your agent's skills directory, or upload it where your assistant accepts skill folders. `design-human-ai-org` uses Python 3 with the standard library only to render its views; without Python, the assistant builds the same views as native artifacts or tables in chat.

## Licence

MIT, copyright 2026 Shiva Kakkar. The Sketchyicons files in `skills/design-human-ai-org/assets/sketchyicons/` keep their own licence and notice, which are included in that folder.
