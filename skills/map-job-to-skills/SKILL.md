---
name: map-job-to-skills
description: Turns a job description into a four-pillar skill map (technical, cognitive, behavioural and domain) as JSON, and can then build a complete learning course from that map, with modules of eleven fixed screens holding multiple-choice questions, scenarios, written and spoken answers, glossary practice and a closing mock interview script. Use it when someone pastes or uploads a job description and asks what the role really tests for, wants a skill breakdown, or wants course or interview-preparation content for a role in any function or discipline. It works on one role at a time and does not redesign teams, reporting lines or the split of work between people and AI (use design-human-ai-org), and it does not teach organisation-structure concepts (use run-org-structure-exercise).
---

# Map a job description to skills and a course

The skill has two phases. Phase 1 turns a job description into a skill map. Phase 2 turns a skill map into a course. Run Phase 2 only when the user asks for a course or supplies a skill map.

## Rules that always hold

- Include only skills the role requires. If the employer would not reject a candidate for lacking a skill, leave it out.
- Each atom tests one thing. "Pricing strategy and financial analysis" is two atoms; split it or keep the one the role needs.
- The same atom can appear in many roles. What changes per role is its difficulty (1 to 5), weight (0.0 to 1.0) and flavour, which is how the skill shows up in this particular job.
- Cognitive and behavioural atoms come only from the fixed menus in [the atom libraries](references/universal_libraries.md). Do not invent new ones.
- A skill map has 8 to 12 atoms in total, and the four pillar weights sum to about 1.0.
- Every course module has exactly eleven screens in the fixed slot order, and every multiple-choice question has exactly four options with a 0-indexed `correct` value.
- Every domain glossary term in the skill map appears on at least one glossary card in the course.
- Mark any fact you inferred about the employer or role, rather than read in the job description, as inferred.

## Phase 1: job description to skill map

Read [the atom libraries](references/universal_libraries.md) and the skill map schema in [the example output](examples/example_output.json.md) before writing.

1. Read the job description. Identify the company, role, level, degree or discipline and sector.
2. If company context is thin and web search is available, use it to understand the employer. Otherwise infer from the role, company and level, and say so.
3. Extract 3 to 5 technical atoms. Take the degree the role draws on, ask which of its subjects the role uses directly, and keep only subjects that appear in the responsibilities. Name each atom by its academic concept ("Project planning", not "Bid management"). Write flavour text that connects the classroom concept to daily work, a `sample_interview_q` and a `degree_concept_origin`. Set difficulty from the wording: "familiarity" is 2, "strong understanding" is 3, "deep experience" is 4, "led" or "architected" is 5. Entry-level roles lean towards 3 atoms.
4. Select 2 or 3 cognitive atoms from the library based on the responsibilities, with role-specific flavour text and a sample question.
5. Select 2 or 3 behavioural atoms from the library based on explicit mentions, the type of company and the structure of the role. Include demands the description does not state but the employer clearly tests; a very large services company hiring management trainees tests organisational fit even when the description never mentions it.
6. Build exactly two domain glossary clusters: role terms and industry terms, each with 8 to 15 terms and plain meanings. Include only terms a new graduate would not know and an insider uses daily. The test is whether a candidate who looked blank at the term mid-interview would lose credibility.
7. Apply the necessity filter, split any double-barrelled atom, then assign weights and difficulty.
8. Output one JSON object that matches the skill map schema.

If the description mentions skills the interview will not test, lower their weight or drop them. If it is generic, fall back on the role archetype below.

### Pillar weights by role archetype

| Role archetype | Technical | Cognitive | Behavioural | Domain |
|---|---|---|---|---|
| Engineering or software | 0.40 | 0.25 | 0.20 | 0.15 |
| Consulting | 0.20 | 0.35 | 0.30 | 0.15 |
| Sales, business development or presales | 0.25 | 0.25 | 0.35 | 0.15 |
| Marketing or brand | 0.30 | 0.20 | 0.25 | 0.25 |
| Finance or investment banking | 0.40 | 0.25 | 0.15 | 0.20 |
| HR | 0.30 | 0.20 | 0.35 | 0.15 |
| Operations or supply chain | 0.30 | 0.30 | 0.20 | 0.20 |
| Design | 0.35 | 0.25 | 0.20 | 0.20 |
| Law | 0.35 | 0.30 | 0.15 | 0.20 |

## Phase 2: skill map to course

Read [the course architecture](references/course_architecture.md) for the full screen specification and the course schema in [the example output](examples/example_output.json.md) before writing.

### Course structure

A course has three modules of eleven screens each and one closing mock interview, which makes 34 screens. If the role has only two technical atoms, use two modules and the interview, which makes 23 screens. If it has four or more, combine the most closely related pair into one module so there are still three.

Each module centres on one technical atom and adds related atoms:

- Module 1: technical atom A, the strongest cognitive and behavioural atoms, and domain cluster 1.
- Module 2: technical atom B, the second cognitive and behavioural atoms, domain cluster 2, and terms from module 1 again.
- Module 3: technical atom C, cognitive and behavioural atoms revisited, the remaining terms and further reinforcement.

### The eleven screens

| Screen | Slot | Type | Display | MCQs | Written | Spoken | Glossary |
|---|---|---|---|---|---|---|---|
| 1 | orient | read | none | 0 | 0 | 0 | 4 to 6 inline terms |
| 2 | first_apply | scenario_mcq | standard_cards | 2 | 0 | 0 | 2 or 3 cards |
| 3 | terms_in_context | situation_mcq | chat_bubble | 2 | 0 | 0 | 3 or 4 cards |
| 4 | deepen | read | none | 0 | 0 | 0 | 2 or 3 inline terms |
| 5 | aptitude | scenario_mcq | standard_cards | 3 | 0 | 0 | 1 or 2 cards |
| 6 | voice | voice | none | 0 | 0 | 1 | 0 |
| 7 | people_challenge | situation_mcq | chat_bubble | 2 | 0 | 0 | 0 |
| 8 | behavioral_interview | subjective | none | 0 | 1 | 0 | 0 |
| 9 | harder_apply | scenario_mcq | standard_cards | 3 | 0 | 0 | 2 or 3 cards |
| 10 | case | case_subjective | none | 0 | 1 | 0 | 0 |
| 11 | resolution | scenario_mcq | standard_cards | 2 | 0 | 0 | 0 |

The screens move from impersonal concepts (1 and 2), through scenarios, terms and aptitude (3 to 5), a first spoken answer (6), people and the first written answer (7 and 8), hard scenarios and the case (9 and 10), to a closing judgement (11). Keep this order in every module.

### Questions and display

Every multiple-choice question uses `{question, options[4], correct, explanation}`. There are no true-or-false questions, sliders or drag-and-drop items. `standard_cards` shows lettered options in a list; `chat_bubble` shows the same options as replies in a conversation. The display is fixed per slot.

Screen 5 uses standard aptitude patterns (work-rate, ratio, percentage, data interpretation, logical deduction) set in the role's daily work, such as an FTE calculation for a staffing role. Tag each question with its `aptitude_pattern`.

Screens 8 and 10 carry `evaluator_guidance` that the learner sees after answering. Screen 8 is a "Tell me about a time" question with one or two paragraphs of framing. Screen 10 is a case of three or more paragraphs with named characters, a real dilemma, power dynamics and no obviously correct answer.

Screen 6 asks one question the learner answers aloud in about 60 seconds. Where the learner cannot record audio, they type a short answer instead.

### Glossary

Terms are spread across screens; there are no glossary-only screens. Screens 1 and 4 show terms inline in the prose, without a test. Screen 3 places terms inside a realistic work artifact. Screens 2, 5 and 9 add glossary cards after the questions; each card shows the term and meaning and can carry an optional practice question in an interview context. The five or six most important terms in each cluster appear two or three times across the course.

### Situation format by role

Screens 3 and 7 use a work artifact that matches the role, and `situation_format` takes one of the keys listed in the course architecture (`slack`, `report`, `code_review`, `email`, `memo`, `policy`, `dashboard`, `contract`, `brief`): a team chat thread for presales, a research extract for marketing, a code review for engineering, a client email for consulting, a memo for finance, a policy update for HR, a dashboard alert for operations, a contract clause for law and a design brief for design.

### Tone

Write warmly and directly for a capable new graduate. Use concrete examples from the role's daily work, and use an analogy only when it explains more than a direct example would. Keep the tone encouraging on the early screens, empathetic on the people screens, and respectful of difficulty on the case. Never be cold, corporate or patronising.

### Phase 2 workflow

1. Read the skill map, or accept one the user supplies.
2. Choose the situation format from the role archetype.
3. Map one technical atom to each module and assign cognitive and behavioural atoms.
4. Distribute every domain term across the modules: inline, then in context, then on cards.
5. Write the eleven screens of each module in slot order.
6. Write the closing mock interview script: 10 to 15 minutes, covering all technical atoms and at least two behavioural atoms, using the domain vocabulary, with a scoring guide by pillar. A person or any AI interviewer can run it.
7. Check that every domain term appears on at least one card, then output one JSON object matching the course schema.

### Checks before output

1. Every module has eleven screens in slot order, and every display value matches its slot.
2. Every multiple-choice question has four options.
3. Screen 5 questions test standard reasoning patterns with only the context changed.
4. Screens 8 and 10 have evaluator guidance, and the screen 10 case has three or more paragraphs with named characters and a real dilemma.
5. Every domain term appears on at least one glossary card.
6. The tone stays warm and concrete throughout.
