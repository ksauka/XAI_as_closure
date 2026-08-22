# Agentic Hiring Experiment Protocol
Version: 1.0
Study: Preserving Human Agency in Agentic AI-Assisted Hiring Through Explainability, Anthropomorphic Communication Cues, and Mixed-Initiative Control Cues

---

# 1. Study Overview

This study investigates how conversational explainability and anthropomorphic communication cues influence human decision-making during AI-assisted recruitment screening.

The study examines whether users become more likely to rely on AI recommendations when recommendations are delivered through persuasive conversational explanations and whether Mixed-Initiative Control Cues preserve human agency by maintaining user involvement in the decision process.

The experiment is situated in a realistic recruitment screening scenario in which participants act as recruiters responsible for evaluating a candidate for a Strategic Talent Operations Partner position.

An AI assistant reviews the candidate profile and provides a recommendation supported by conversational explanations and document-grounded provenance citations.

Participants remain solely responsible for the final hiring decision.

---

# 2. Research Model

## Independent Variables

### IV1: Explainability

Operationalised as task-level conversational explainability.

High Explainability:
- recommendation rationale provided
- explicit justification of strengths and weaknesses
- discussion of uncertainty
- references to relevant role and policy sections
- provenance citations embedded directly in conversation

Low Explainability:
- minimal justification
- no detailed rationale
- no explicit provenance references
- recommendation only

---

### IV2: Anthropomorphic Communication Cues

Operationalised through conversational delivery style.

High Anthropomorphism:
- socially fluent language
- warm communication style
- affiliative wording
- collaborative framing
- limited first-person language
- conversational explanation delivery

Low Anthropomorphism:
- neutral language
- impersonal wording
- transactional communication
- no social framing
- machine-like delivery

---

## Moderator

### Mixed-Initiative Control Cues

Operationalised through Interrogative Agendas.

Interrogative agendas preserve user control by introducing structured opportunities to influence and challenge AI recommendations.

Mixed-Initiative Control Cues are implemented in two stages:

Stage 1:
Pre-recommendation agenda setting.

Stage 2:
Post-recommendation challenge and clarification.

---

## Primary Outcomes

### Overreliance on AI Advice

The extent to which participants rely on the recommendation without independently evaluating supporting evidence.

Measured through:
- recommendation agreement
- evidence verification behaviour
- provenance inspection behaviour
- challenge behaviour
- final decision alignment
- self-report measures

---

### Sense of Agency

The extent to which participants experience ownership and control over the hiring decision.

Measured through:
- self-report scales
- behavioural indicators
- interaction logs
- steering behaviour
- challenge behaviour

---

## Secondary Outcomes

- Trust in AI recommendation
- Perceived AI competence
- Delegation willingness
- Judgement settledness
- Perceived recommendation quality

---

# 3. Experimental Design

## Design Structure

2 × 2 × 2 between-subjects design.

Factors:

Explainability:
- Low
- High

Anthropomorphic Communication Cues:
- Low
- High

Mixed-Initiative Control Cues:
- Absent
- Present

Total Conditions:

1. Low Explainability × Low Anthropomorphism × No MICC
2. Low Explainability × Low Anthropomorphism × MICC
3. High Explainability × Low Anthropomorphism × No MICC
4. High Explainability × Low Anthropomorphism × MICC
5. Low Explainability × High Anthropomorphism × No MICC
6. Low Explainability × High Anthropomorphism × MICC
7. High Explainability × High Anthropomorphism × No MICC
8. High Explainability × High Anthropomorphism × MICC

Participants are randomly assigned to one condition.

---

# 4. Experimental Materials

Participants review:

1. Company Summary
2. Strategic Talent Operations Partner Role Description
3. AI-Assisted Strategic Hiring Screening Policy
4. Candidate CV

All materials remain identical across conditions.

Only recommendation delivery differs.

---

# 5. Candidate Scenario

Participants evaluate a single candidate.

The candidate is intentionally realistic and moderately ambiguous.

The candidate demonstrates:

- coordination responsibilities
- stakeholder communication
- workflow management
- hiring-related support activities

The candidate does not clearly demonstrate:

- end-to-end recruitment ownership
- formal talent acquisition leadership

The candidate is neither clearly qualified nor clearly unqualified.

The scenario requires judgement rather than checklist matching.

---

# 6. Experimental Flow

---

## Screen 1
### Welcome and Consent

Participants receive:

- study introduction
- consent information
- confidentiality statement

Button:

Continue

---

## Screen 2
### Company Summary

Participants review:

- organisation overview
- business context
- hiring objective

Button:

Continue

---

## Screen 3
### Role Description Summary

Participants review:

- role purpose
- key responsibilities
- screening priorities

Button:

Continue

---

## Screen 4
### Screening Policy Summary

Participants review:

- evaluation principles
- transferable evidence guidance
- human oversight requirements

Button:

Continue

---

## Screen 5
### Candidate CV

Participants review candidate CV.

Displayed as a structured markdown document.

Buttons:

- Request AI Recommendation
- View Full Role Description
- View Full Screening Policy

All interactions logged.

---

# 7. Mixed-Initiative Control Cues
## Stage 1

Only shown when MICC = Present.

Before recommendation generation.

Purpose:

Allow recruiter to steer evaluation priorities.

Prompt:

Before I complete the review, which aspects would you like me to pay particular attention to?

Participants may select up to two:

- Recruitment ownership
- Stakeholder coordination
- Process improvement capability
- Operational reliability
- Growth potential
- Risk indicators
- Evidence gaps

Optional free-text box available.

Selections are logged.

Selected priorities influence recommendation framing.

---

# 8. AI Recommendation Generation

Participants request recommendation.

AI assistant evaluates:

- role description
- screening policy
- candidate CV

Recommendation is generated according to assigned condition.

Recommendation appears as a conversational message.

---

# 9. Conversational Explainability

High Explainability conditions:

Recommendations contain:

- strengths identified
- concerns identified
- explanation of reasoning
- discussion of uncertainty
- embedded provenance citations

Example:

Section 5.2 of the Role Description

Policy Section 7.2

Policy Section 7.3

Citations appear inside conversational text.

Citations are clickable.

Citation clicks are logged.

---

Low Explainability conditions:

Recommendations contain:

- recommendation only
- minimal rationale

No provenance references displayed.

---

# 10. Anthropomorphic Communication Cue Manipulation

High Anthropomorphism:

Recommendations include:

- conversational style
- collaborative framing
- warm language
- socially fluent wording
- limited first-person references

Example:

"I would keep this candidate in consideration because..."

---

Low Anthropomorphism:

Recommendations include:

- neutral wording
- procedural language
- impersonal delivery

Example:

"Assessment indicates..."

---

# 11. Mixed-Initiative Control Cues
## Stage 2

Only shown when MICC = Present.

Immediately after recommendation.

Purpose:

Allow participants to challenge, interrogate, or refine the recommendation.

Prompt:

Would you like to examine any aspect of this recommendation more closely?

Options:

- Show strongest evidence supporting progression
- Show strongest evidence supporting caution
- Identify remaining uncertainties
- Explain missing information
- Reassess with greater emphasis on transferable evidence
- Reassess with greater emphasis on direct experience
- Ask a custom question

Responses are conversational.

Additional provenance citations may be provided.

All interactions logged.

---

# 12. Judgement Settledness

Participants complete a single-item assessment.

Question:

At this point, how settled is your judgement about the recommendation?

Scale:

1 = I still need to examine it further

7 = My judgement is fully settled

Recorded before final decision.

---

# 13. Final Human Decision

Participants make final decision.

Options:

- Reject Application
- Advance to Human Interview
- Hold for Further Review

Decision recorded.

Decision time recorded.

Agreement with AI recommendation recorded.

---

# 14. Questionnaire Measures

Participants complete post-task questionnaire.

Measures include:

Sense of Agency

Trust

Perceived AI Competence

Perceived Recommendation Quality

Overreliance Indicators

Manipulation Checks

Demographics

Prior AI Familiarity

Recruitment Experience

---

# 15. Behavioural Logging

The following interactions are logged.

## Document Behaviour

- role description opened
- policy document opened
- time spent reading
- return actions

---

## Provenance Behaviour

- citation clicks
- citation frequency
- citation dwell time
- section access history

---

## Mixed-Initiative Behaviour

Stage 1:

- selected priorities
- free-text entries
- response time

Stage 2:

- challenge selections
- clarification requests
- custom questions

---

## Recommendation Behaviour

- recommendation viewing time
- scrolling behaviour
- judgement settledness

---

## Final Decision Behaviour

- final decision
- recommendation agreement
- decision latency

---

# 16. Expected Mechanism

Explainability and anthropomorphic communication cues are expected to increase the perceived legitimacy and acceptability of AI recommendations.

These cues may increase reliance on AI advice.

Mixed-Initiative Control Cues are expected to preserve human agency by maintaining participant involvement before and after recommendation generation.

The intervention is therefore expected to reduce the extent to which recommendation acceptance translates into agency loss.

---

# 17. Experimental Hypotheses

H1.
High explainability increases reliance on AI recommendations.

H2.
High anthropomorphic communication cues increase reliance on AI recommendations.

H3.
The combination of explainability and anthropomorphic communication cues produces greater reliance than either cue alone.

H4.
Greater reliance on AI recommendations is associated with lower perceived human decision agency.

H5.
Mixed-Initiative Control Cues weaken the negative relationship between AI recommendation reliance and perceived human decision agency.

H6.
The effects of explainability and anthropomorphic communication cues on perceived human decision agency are mediated through reliance on AI recommendations.

---
End of Protocol