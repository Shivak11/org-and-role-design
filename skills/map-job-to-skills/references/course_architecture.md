# Course architecture

Every course built from a skill map follows this structure.

## Contents

- Course structure
- The eleven-screen template
- Why the screens follow this order
- Question counts per module
- Display modes
- Glossary distribution
- Situation formats by role
- Mapping atoms to modules
- Closing mock interview
- Tone

## Course structure

A course is built from a skill map, which is itself built from a job description. It has:

- Three modules, one per compound skill. Each compound skill combines one technical atom with related cognitive, behavioural and domain atoms.
- One closing mock interview covering all three modules.
- 34 screens in total: 33 module screens and the interview.

## The eleven-screen template

Every module has exactly eleven screens in this order. The order moves from impersonal concepts to applied scenarios, then to people, a complex case and a resolution.

### Screen 1: orient (read)

- Type: `read`. Pillar focus: domain, for context.
- Content: a warm introduction to the compound skill that explains what the role actually does, beyond what the job description says.
- Glossary: 4 to 6 terms appear in the prose as inline term notes. They are seen here and not tested.
- No questions.

### Screen 2: first apply (scenario and questions)

- Type: `scenario_mcq`. Display: `standard_cards`. Pillar focus: technical.
- Content: a short scenario of one or two paragraphs that introduces the role context and a first application of the concepts.
- Questions: 2 multiple-choice questions of easy to moderate difficulty that test comprehension.
- Glossary: 2 or 3 cards after the questions. Each card shows the term and meaning and can carry an optional practice question in an interview context.

### Screen 3: terms in context (situation and questions)

- Type: `situation_mcq`. Display: `chat_bubble`. Pillar focus: domain and technical.
- Content: a realistic work artifact in the role's situation format. Terms from screen 1 appear inside it and are highlighted.
- Questions: 2 multiple-choice questions shown as conversation replies.
- Glossary: 3 or 4 cards. Learners now see the terms in realistic use before practising them.

### Screen 4: deepen (read)

- Type: `read`. Pillar focus: technical and cognitive.
- Content: the academic concept explained with concrete examples from the role, connecting what the learner studied to what the role does.
- Glossary: 2 or 3 inline term notes.
- End with a short key takeaway written as a sentence or two.
- No questions.

### Screen 5: aptitude (scenario and questions)

- Type: `scenario_mcq`. Display: `standard_cards`. Pillar focus: cognitive.
- Content: aptitude questions that use the same reasoning as standard aptitude tests (ratios, time and work, percentages, logical deduction, data interpretation), with numbers and situations taken from the role's daily work. If the role involves FTE calculations, the question is an FTE calculation; if it involves campaign return on investment, the question is that calculation.
- Questions: 3, each testing a different reasoning pattern.
- Glossary: 1 or 2 cards for terms that appear in the aptitude context.

### Screen 6: spoken answer (about 60 seconds)

- Type: `voice`. Pillar focus: technical and cognitive.
- Content: one question that draws together screens 1 to 5. The learner answers aloud in about 60 seconds, or types a short answer where recording is not possible.
- After answering, the learner sees evaluator guidance on what interviewers listen for: structure, specificity, confidence and correct use of technical vocabulary.
- No glossary.

### Screen 7: people challenge (situation and questions)

- Type: `situation_mcq`. Display: `chat_bubble`. Pillar focus: behavioural.
- Content: an interpersonal scenario in the role's situation format, such as conflicting stakeholders, an awkward conversation or a difference in power.
- Questions: 2, shown as conversation replies. The options are things the learner could say or do.
- No new glossary; earlier terms may appear naturally.

### Screen 8: behavioural interview (written answer)

- Type: `subjective`. Pillar focus: behavioural.
- Content: a classic behavioural question ("Tell me about a time..." or "How would you handle...") with one or two paragraphs of framing linked to the module's theme.
- Input: a typed answer.
- After submission: evaluator guidance on what strong answers include, what to avoid and the underlying skill being tested.

### Screen 9: harder apply (scenario and questions)

- Type: `scenario_mcq`. Display: `standard_cards`. Pillar focus: technical and cognitive.
- Content: a longer scenario of two or three paragraphs with several variables, testing whether the learner can combine the module's concepts.
- Questions: 3, harder than screens 2 and 5, testing judgement as well as comprehension.
- Glossary: 2 or 3 cards that reinforce earlier terms and introduce one or two new ones.

### Screen 10: the case (written answer)

- Type: `case_subjective`. Pillar focus: behavioural and cognitive.
- Content: the module's main case, at least three paragraphs, with a specific situation, named characters and constraints, a real dilemma with no obviously correct answer, and differences in power, career risk and interpersonal detail.
- Input: a typed answer to "What do you actually do? Walk through your approach step by step."
- After submission: detailed evaluator guidance, longer than screen 8, covering the sequence of moves, what not to do and the underlying skill.

### Screen 11: resolution (scenario and questions)

- Type: `scenario_mcq`. Display: `standard_cards`. Pillar focus: technical and cognitive.
- Content: a final scenario that brings the module's story to its conclusion.
- Questions: 2. One tests a detail, such as an inconsistency or error; the other tests a strategic judgement.
- No new glossary.

## Why the screens follow this order

Screens 1 and 2 cover concepts and easy application, with no characters. Screens 3 to 5 add scenarios, terms in context and aptitude. Screen 6 is the learner's first spoken output. Screens 7 and 8 bring in people and the first written answer. Screens 9 and 10 present hard scenarios and the case. Screen 11 closes with a judgement. Every module, role and domain keeps this order.

## Question counts per module

| Screen | MCQs | Written | Spoken | Total |
|---|---|---|---|---|
| 1 Orient | 0 | 0 | 0 | 0 |
| 2 First apply | 2 plus glossary practice | 0 | 0 | 2 or more |
| 3 Terms in context | 2 plus glossary practice | 0 | 0 | 2 or more |
| 4 Deepen | 0 | 0 | 0 | 0 |
| 5 Aptitude | 3 plus glossary practice | 0 | 0 | 3 or more |
| 6 Spoken answer | 0 | 0 | 1 | 1 |
| 7 People | 2 | 0 | 0 | 2 |
| 8 Behavioural | 0 | 1 | 0 | 1 |
| 9 Harder apply | 3 plus glossary practice | 0 | 0 | 3 or more |
| 10 Case | 0 | 1 | 0 | 1 |
| 11 Resolution | 2 | 0 | 0 | 2 |
| Total | 14 plus glossary practice | 2 | 1 | 17 or more |

Glossary practice questions are optional. A learner can read a card without answering its practice question.

## Display modes

All multiple-choice questions share one data structure: `{question, options[4], correct, explanation}`.

1. `standard_cards`: lettered options A to D in a vertical list. Used on screens 2, 5, 9 and 11.
2. `chat_bubble`: the same four options shown as replies in a conversation, without letters. Used on screens 3 and 7.

The mapping is fixed: standard cards for concept and aptitude screens, conversation replies for situation and people screens. A host that cannot style either mode can show both as a plain list.

## Glossary distribution

Terms are spread across screens and never collected on a glossary-only screen.

- Inline (screens 1 and 4): terms appear in ordinary sentences with their meaning available, without a test.
- In context (screen 3): terms appear inside a realistic work artifact, followed by cards.
- Practice (screens 2, 5 and 9): cards after the questions show the term and meaning, with an optional practice question such as "Your manager says X. What does that mean?"

Each term appears at least twice in a module, once inline or in context and once on a card. The five or six most important terms can appear three times. A module holds about 15 to 18 unique terms; a course holds about 25 to 35 after reinforcement.

## Situation formats by role

Screens 3 and 7 use a situation format that depends on the role. This is the only part of the template that changes by role. The `situation_format` value in the course JSON is one of the keys in the second column.

| Role archetype | `situation_format` | Format | Screen 3 artifact | Screen 7 artifact |
|---|---|---|---|---|
| Presales, business development or sales | `slack` | Team chat | Manager's message in the bid channel | Direct message with a reluctant colleague |
| Brand or marketing | `report` | Report extract and meeting | Market research data extract | Disagreement in a meeting |
| Software engineering | `code_review` | Code review and stand-up | Pull request review thread | Disagreement at stand-up |
| Consulting | `email` | Client email and debrief | Client email with a request | Debrief call with a partner |
| Finance or investment banking | `memo` | Model and memo | Financial memo extract | Senior banker's feedback on a model |
| HR | `policy` | Policy document and conversation | Policy document update | Conversation with an employee |
| Operations or supply chain | `dashboard` | Dashboard and supplier messages | Operations dashboard alert | Call or message with a supplier |
| Law | `contract` | Contract and hearing | Contract clause with tracked changes | Exchange with opposing counsel |
| Design | `brief` | Brief and critique | Client design brief | Design review session |

## Mapping atoms to modules

Each module centres on one technical atom, with related cognitive, behavioural and domain atoms added:

- Module 1: technical atom A, the strongest cognitive atom, the strongest behavioural atom and domain cluster 1.
- Module 2: technical atom B, the second cognitive and behavioural atoms, domain cluster 2 and reinforced terms from module 1.
- Module 3: technical atom C, cognitive and behavioural atoms revisited, the remaining terms and further reinforcement.

With only two technical atoms, use two modules and the interview, 23 screens in all. With four or more, combine the most closely related pair into one module, so there are still three.

## Closing mock interview

The last screen of every course is a mock interview script of 10 to 15 minutes that:

- covers all technical atoms from the modules;
- tests at least two behavioural atoms through situational questions;
- uses the domain vocabulary naturally, so the candidate is expected to use it too;
- includes a scoring guide by pillar.

A person or any AI interviewer can run the script. The skill writes the script and scoring guide; it does not run the interview or score it.

## Tone

Write warmly and directly for a capable new graduate:

- Screens 1 to 4: explain what the role involves that a degree course does not cover, with concrete examples.
- Screens 5 and 6: encouraging and demanding, showing where a subject the learner studied is used in the job.
- Screens 7 and 8: empathetic, acknowledging that there is no perfect answer while some approaches work better.
- Screens 9 and 10: respectful of how hard the situation is.
- Screen 11: a confident close that names what the learner has just worked through.

Never write in a cold, corporate, textbook or patronising tone. Prefer specific detail from the role to general encouragement, and use an analogy only when it explains more than a direct example.
