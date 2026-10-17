# Example output

This file shows the two JSON outputs for a fictional company, Example IT Services. The company, people and client names are invented.

## Contents

- Phase 1: skill map JSON
- Phase 2: course content JSON
- Key schema rules

## Phase 1: skill map JSON

```json
{
  "metadata": {
    "company": "Example IT Services",
    "role": "Presales",
    "level": "entry",
    "degree": "MBA",
    "sector": "IT Services",
    "source_jd": "filename or text reference"
  },
  "skill_map": {
    "technical": {
      "pillar_description": "Degree concepts that directly manifest in this role's daily work",
      "pillar_weight": 0.25,
      "atoms": [
        {
          "atom_id": "tech_project_planning",
          "atom_name": "Project planning",
          "difficulty": 3,
          "weight": 0.95,
          "flavor": "Bid plan, timelines, resource allocation. MBA teaches Gantt charts, critical path, WBS. In presales this becomes: manage a 3-week RFP response across 6 SMEs with 1 sign-off gate.",
          "sample_interview_q": "You have 3 weeks to respond to an RFP. 6 SMEs, 2 reviewers, 1 sign-off gate. The SME for the largest section is on leave for 5 of your 15 available days. Walk me through your bid plan.",
          "degree_concept_origin": "Project Management / Operations Management"
        },
        {
          "atom_id": "tech_stakeholder_analysis",
          "atom_name": "Stakeholder analysis",
          "difficulty": 2,
          "weight": 0.85,
          "flavor": "Power-interest mapping, conflict resolution. You're SPOC on a bid. Sales wants aggressive pricing, Delivery says it's undeliverable, Finance won't sign off.",
          "sample_interview_q": "Tell me about a time you managed conflicting priorities across teams. How did you decide whose input to prioritize?",
          "degree_concept_origin": "Organizational Behavior / Stakeholder Management"
        },
        {
          "atom_id": "tech_pricing_strategy",
          "atom_name": "Pricing strategy",
          "difficulty": 3,
          "weight": 0.80,
          "flavor": "Model selection for deal contexts. Client wants fixed-price but scope is vague. What pricing model protects margin while staying competitive?",
          "sample_interview_q": "A client insists on a fixed-price contract but the requirements document is incomplete. What risks does this create and how would you advise the sales team?",
          "degree_concept_origin": "Marketing / Pricing Strategy / Financial Management"
        }
      ]
    },
    "cognitive": {
      "pillar_description": "Thinking patterns this role's daily work demands",
      "pillar_weight": 0.25,
      "atoms": [
        {
          "atom_id": "cog_structured_breakdown",
          "atom_name": "Structured problem breakdown",
          "difficulty": 3,
          "weight": 0.90,
          "flavor": "Decompose a 150-requirement RFP into a manageable storyboard with clear CTQs before anyone starts writing.",
          "sample_interview_q": "You receive an RFP with 150 requirements across 6 sections. How do you create a response structure? What do you do first?"
        },
        {
          "atom_id": "cog_synthesis",
          "atom_name": "Synthesis under ambiguity",
          "difficulty": 3,
          "weight": 0.85,
          "flavor": "8 SMEs send 8 different write-ups in 8 formats with 3 contradictions. You produce ONE coherent proposal with a consistent win theme.",
          "sample_interview_q": "Two subject matter experts give you contradictory inputs for the same proposal section, and the deadline is tomorrow. How do you resolve this?"
        }
      ]
    },
    "behavioral": {
      "pillar_description": "How this company and role expect you to interact with people",
      "pillar_weight": 0.35,
      "atoms": [
        {
          "atom_id": "beh_communication",
          "atom_name": "Communication clarity",
          "difficulty": 3,
          "weight": 0.95,
          "flavor": "Translate a solution architect's technical jargon into a value proposition a CXO client will read. Multiple audiences, one message."
        },
        {
          "atom_id": "beh_stakeholder_orchestration",
          "atom_name": "Stakeholder orchestration",
          "difficulty": 3,
          "weight": 0.90,
          "flavor": "Coordinate SMEs, Sales, Finance, delivery and senior management, who all have different incentives and timelines, without formal authority."
        },
        {
          "atom_id": "beh_organizational_fit",
          "atom_name": "Organizational fit",
          "difficulty": 3,
          "weight": 0.75,
          "flavor": "Deadline tolerance. Grunt work willingness. Flexibility with ambiguous scope. MT level = 70% coordination work, 30% strategic thinking."
        }
      ]
    },
    "domain": {
      "pillar_description": "Industry and role-specific vocabulary that insiders use and outsiders don't know",
      "pillar_weight": 0.15,
      "atoms": [
        {
          "atom_id": "dom_bid_lifecycle",
          "atom_name": "Bid lifecycle terminology",
          "weight": 0.90,
          "glossary": [
            {"term": "RFP", "meaning": "Request for Proposal: formal document from client inviting vendors to propose a solution and pricing"},
            {"term": "Go/No-Go", "meaning": "Decision gate: should we pursue this bid or walk away?"},
            {"term": "Pursuit team", "meaning": "Cross-functional squad assembled specifically for one bid"},
            {"term": "SPOC", "meaning": "Single Point of Contact: the one person through whom all bid communication flows"},
            {"term": "Storyboard", "meaning": "Visual outline of proposal structure created BEFORE writing begins"},
            {"term": "CTQ", "meaning": "Critical to Quality: the non-negotiable requirements the client cares most about"},
            {"term": "Compliance matrix", "meaning": "Checklist mapping every RFP requirement to where it's addressed in your proposal"},
            {"term": "SME", "meaning": "Subject Matter Expert: specialist consulted for domain-specific proposal sections"},
            {"term": "Solutioning", "meaning": "Process of designing the technical and operational approach for a client's problem"},
            {"term": "Win theme", "meaning": "Central argument for why the client should pick you over competitors"},
            {"term": "Orals", "meaning": "Live presentation of proposal to client's evaluation panel: usually the final round"},
            {"term": "BAFO", "meaning": "Best and Final Offer: last round of negotiation before client decides"}
          ]
        },
        {
          "atom_id": "dom_it_services_commercial",
          "atom_name": "IT services commercial terms",
          "weight": 0.85,
          "glossary": [
            {"term": "T&M", "meaning": "Time & Material: client pays for hours worked, risk with client"},
            {"term": "Fixed-price", "meaning": "Vendor commits to total cost regardless of effort, risk with vendor"},
            {"term": "SoW", "meaning": "Statement of Work: defines scope, deliverables, timelines for a specific engagement"},
            {"term": "MSA", "meaning": "Master Service Agreement: umbrella contract governing overall client-vendor relationship"},
            {"term": "Rate card", "meaning": "Price list of hourly/daily rates by role and seniority level"},
            {"term": "FTE", "meaning": "Full-Time Equivalent: one person working full-time, used as a unit of staffing"},
            {"term": "Billability", "meaning": "Percentage of an employee's time that is billed to a client"},
            {"term": "Onsite-offshore", "meaning": "Delivery model splitting work between the client location (expensive) and an offshore delivery centre (cheaper)"},
            {"term": "SLA", "meaning": "Service Level Agreement: the measurable service standards the vendor commits to, often with penalties"}
          ]
        }
      ]
    }
  }
}
```

## Phase 2: course content JSON

Each module follows the eleven-screen template. Below is one module. A full course has three modules and one closing interview object.

```json
{
  "course": {
    "course_id": "example_presales_mt",
    "company": "Example IT Services",
    "role": "Presales Management Trainee",
    "total_modules": 3,
    "total_screens": 34,
    "situation_format": "slack",
    "modules": [
      {
        "module_id": "example_presales_project_planning",
        "module_number": 1,
        "module_title": "Planning the Bid",
        "compound_skill": {
          "technical_atom": "tech_project_planning",
          "cognitive_atoms": ["cog_structured_breakdown"],
          "behavioral_atoms": ["beh_stakeholder_orchestration"],
          "domain_clusters": ["dom_bid_lifecycle"]
        },
        "screens": [
          {
            "screen_number": 1,
            "slot": "orient",
            "type": "read",
            "title": "What This Job Actually Is",
            "content_html": "Warm prose with inline term markup around glossary terms...",
            "glossary_nudge": ["RFP", "SPOC", "Go/No-Go", "Pursuit team"],
            "questions": []
          },
          {
            "screen_number": 2,
            "slot": "first_apply",
            "type": "scenario_mcq",
            "display": "standard_cards",
            "title": "The RFP Lands",
            "scenario": "Short scenario paragraph...",
            "questions": [
              {
                "q_id": "m1_s2_q1",
                "question": "What's the FIRST thing you do with this 94-page RFP?",
                "options": ["Option A", "Option B", "Option C", "Option D"],
                "correct": 1,
                "explanation": "Why B is correct...",
                "pillar": "technical",
                "atom": "tech_project_planning"
              },
              {
                "q_id": "m1_s2_q2",
                "question": "Second question...",
                "options": ["A", "B", "C", "D"],
                "correct": 1,
                "explanation": "...",
                "pillar": "technical",
                "atom": "tech_project_planning"
              }
            ],
            "glossary_cards": [
              {
                "term": "CTQ",
                "meaning": "Critical to Quality: ...",
                "practice": {
                  "question": "Interview context question about CTQ...",
                  "options": ["A", "B", "C", "D"],
                  "correct": 1,
                  "explanation": "..."
                }
              },
              {
                "term": "Storyboard",
                "meaning": "Visual outline of...",
                "practice": {
                  "question": "...",
                  "options": ["A", "B", "C", "D"],
                  "correct": 0,
                  "explanation": "..."
                }
              }
            ]
          },
          {
            "screen_number": 3,
            "slot": "terms_in_context",
            "type": "situation_mcq",
            "display": "chat_bubble",
            "title": "Words in the Wild",
            "situation_format": "slack",
            "situation_content": {
              "channel": "#harbour-bank-bid",
              "sender": "Priya",
              "message": "Slack message with highlighted terms..."
            },
            "questions": [
              {
                "q_id": "m1_s3_q1",
                "question": "What is Priya really asking you to do?",
                "options": ["A", "B", "C", "D"],
                "correct": 1,
                "explanation": "...",
                "pillar": "domain",
                "atom": "dom_bid_lifecycle"
              }
            ],
            "glossary_cards": [
              {"term": "Compliance matrix", "meaning": "...", "practice": {"question": "...", "options": ["A","B","C","D"], "correct": 1, "explanation": "..."}}
            ]
          },
          {
            "screen_number": 4,
            "slot": "deepen",
            "type": "read",
            "title": "What Planning Actually Looks Like",
            "content_html": "Explanation with concrete examples from the role...",
            "key_takeaway": "The 3-week pattern: in week 1, schedule the independent sections first...",
            "glossary_nudge": ["Critical path", "Buffer management"],
            "questions": []
          },
          {
            "screen_number": 5,
            "slot": "aptitude",
            "type": "scenario_mcq",
            "display": "standard_cards",
            "title": "The Numbers Behind the Bid",
            "scenario": "Aptitude context paragraph...",
            "questions": [
              {
                "q_id": "m1_s5_q1",
                "question": "Contextualized aptitude question, such as an FTE calculation or a ratio",
                "options": ["A", "B", "C", "D"],
                "correct": 2,
                "explanation": "Step-by-step math...",
                "pillar": "cognitive",
                "atom": "cog_quantitative",
                "aptitude_pattern": "work-rate calculation"
              }
            ],
            "glossary_cards": [
              {"term": "FTE", "meaning": "...", "practice": {"question": "...", "options": ["A","B","C","D"], "correct": 0, "explanation": "..."}}
            ]
          },
          {
            "screen_number": 6,
            "slot": "voice",
            "type": "voice",
            "title": "Quick Fire: 60 Seconds",
            "question": "Walk me through how you'd plan a 3-week bid response when your key technical person is unavailable for the first week.",
            "duration_seconds": 60,
            "evaluator_guidance": "What interviewers listen for: (1) structure, (2) dependency awareness, (3) buffer thinking, (4) critical path."
          },
          {
            "screen_number": 7,
            "slot": "people_challenge",
            "type": "situation_mcq",
            "display": "chat_bubble",
            "title": "Day 7: Things Get Messy",
            "situation_format": "slack",
            "situation_content": {
              "messages": [
                {"sender": "Priya", "text": "Where's the infra section draft?"},
                {"sender": "You", "text": "Waiting on Raghav. He's back tomorrow."},
                {"sender": "Priya", "text": "We can't wait. Get Vikram from the telecom account team."},
                {"sender": "Vikram (DM)", "text": "I don't have context and have my own deadlines."}
              ]
            },
            "questions": [
              {
                "q_id": "m1_s7_q1",
                "question": "What do you say to Vikram?",
                "options": ["Authority play", "Make-it-easy approach", "Do it yourself", "Delay"],
                "correct": 1,
                "explanation": "...",
                "pillar": "behavioral",
                "atom": "beh_stakeholder_orchestration"
              }
            ]
          },
          {
            "screen_number": 8,
            "slot": "behavioral_interview",
            "type": "subjective",
            "title": "How Would You Answer This?",
            "context": "Framing paragraph connecting to module theme...",
            "question": "Tell me about a time you had to get work done through people who didn't report to you.",
            "evaluator_guidance": "Strong answers have 3 elements: (1) specific constraint, (2) the method, with the specific steps they took, (3) outcome + reflection. STAR format but 70% on A and R."
          },
          {
            "screen_number": 9,
            "slot": "harder_apply",
            "type": "scenario_mcq",
            "display": "standard_cards",
            "title": "Day 12: The Timeline Trap",
            "scenario": "Longer scenario with status update, multiple variables...",
            "questions": [
              {
                "q_id": "m1_s9_q1",
                "question": "Harder question requiring synthesis...",
                "options": ["A", "B", "C", "D"],
                "correct": 1,
                "explanation": "...",
                "pillar": "cognitive",
                "atom": "cog_structured_breakdown"
              }
            ],
            "glossary_cards": [
              {"term": "Win theme", "meaning": "...", "practice": {"question": "...", "options": ["A","B","C","D"], "correct": 1, "explanation": "..."}}
            ]
          },
          {
            "screen_number": 10,
            "slot": "case",
            "type": "case_subjective",
            "title": "The Hard Conversation",
            "case_setup": "3+ paragraphs: Raghav's brilliant-but-inaccessible architecture section, audience mismatch, power dynamics, career risk...",
            "question": "What do you actually do? Walk through your approach step by step.",
            "evaluator_guidance": "Best answers show a 3-move sequence: (1) frame as client need not criticism, (2) offer to do grunt work, (3) use win theme as bridge. Meta-skill: influence without authority."
          },
          {
            "screen_number": 11,
            "slot": "resolution",
            "type": "scenario_mcq",
            "display": "standard_cards",
            "title": "Day 20: The Final Call",
            "scenario": "Wrap scenario: proposal integrated, final checks...",
            "questions": [
              {
                "q_id": "m1_s11_q1",
                "question": "Detail-level catch question...",
                "options": ["A", "B", "C", "D"],
                "correct": 2,
                "explanation": "...",
                "pillar": "technical",
                "atom": "tech_project_planning"
              },
              {
                "q_id": "m1_s11_q2",
                "question": "Strategic judgment question...",
                "options": ["A", "B", "C", "D"],
                "correct": 1,
                "explanation": "...",
                "pillar": "cognitive",
                "atom": "cog_judgment"
              }
            ]
          }
        ]
      }
    ],
    "closing_interview": {
      "type": "mock_interview",
      "duration_minutes": 15,
      "covers_atoms": ["tech_project_planning", "tech_stakeholder_analysis", "tech_pricing_strategy", "cog_structured_breakdown", "cog_synthesis", "beh_stakeholder_orchestration", "beh_communication"],
      "uses_domain_vocabulary": true,
      "questions": [
        {"q_id": "int_q1", "atom": "tech_project_planning", "question": "Walk me through how you would plan a three-week RFP response with six SMEs and one sign-off gate.", "listen_for": "Dependencies, buffer for absent SMEs, a clear critical path."}
      ],
      "scoring_guide": {
        "technical": "What a strong, adequate and weak answer shows for each technical atom.",
        "cognitive": "...",
        "behavioral": "...",
        "domain": "Whether the candidate uses the role's terms correctly without prompting."
      }
    }
  }
}
```

## Key schema rules

1. Every module has exactly 11 screens in the exact slot order: orient, first_apply, terms_in_context, deepen, aptitude, voice, people_challenge, behavioral_interview, harder_apply, case, resolution
2. MCQ questions always have exactly 4 options (options[4])
3. correct field is a 0-indexed integer
4. display field is either "standard_cards" or "chat_bubble"; the mapping is fixed per slot
5. glossary_cards contain the full term+meaning+practice object
6. glossary_nudge is a list of term strings shown inline, without a test
7. Subjective screens (8 and 10) always include evaluator_guidance
8. situation_format matches the role archetype from course_architecture.md
9. aptitude_pattern field on Screen 5 questions identifies the underlying reasoning type (work-rate, ratio, data interpretation, etc.)
10. Each question has pillar and atom fields for scoring alignment
