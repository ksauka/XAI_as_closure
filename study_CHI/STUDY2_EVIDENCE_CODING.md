# Study 2 decisive-evidence coding manual

Version study2-evidence-v2. Code the post-decision response, not the decision or a click trace. Present coders with a pseudonymous response ID, candidate reference and response text; hide condition, final decision, confidence, trust and interaction logs. Candidate identity is necessary to judge the decisive evidence.

## Codes

1: identifies the decisive requirement/evidence conflict. 0: a substantive response does not identify it, including explicit "None", general praise of experience, or generic references to certification without the decisive distinction. NA: missing, blank, unreadable or technically corrupted text. Do not infer evidence identification from the verdict or from a correct keyword copied without the relevant relationship.

## C-05: expiry

Code 1 when the response recognises that the recorded AIGP certification expired before screening and hence does not satisfy the current-certification requirement. The exact date is not essential if the before-screening relationship is unambiguous. Mentioning current membership alone is insufficient. Membership does not renew the certification.

Positive anchor (constructed, not participant data): "The AIGP expired before the screening window; current IAPP membership does not meet the certification requirement."
Negative anchor: "They have AIGP and good experience."

## C-06: whole-file reconciliation

Code 1 when the response links the current AIGP entry to current IAPP membership elsewhere in the file and recognises that the certification identity is established under JD 4.2.1. This is a task-specific screening rule; membership alone does not establish an unrecorded certification. Exact section numbers are unnecessary. Do not infer a recorded certification merely from membership alone. Generic "AIGP is enough" or "IAPP member" is insufficient without the evidence link.

Positive anchor (constructed): "The current AIGP entry and matching IAPP membership identify the required credential under the certification-identity rule in the job description."
Negative anchor: "AIGP could mean anything, so reject."

## C-01–C-04

For C-01/C-02, identify the accepted current certification and current relevant membership as satisfying the mandatory requirements. For C-03/C-04, identify the absence of a qualifying mandatory certification; adjacent technical training or employment does not substitute. Record additional correct general-requirement reasoning in a separate note, without using it to infer the mandatory-evidence code. These criteria are secondary measures and do not replace diagnostic reliance.

## Independent coding and adjudication

Select the fixed subset specified in STUDY2_ANALYSIS_PLAN.md. Train coders on constructed anchors, not by exposing outcomes. Two independent locked codes precede agreement calculation. A third reviewer adjudicates unresolved differences using the response and supplied documents. Preserve initial codes and adjudication notes. Any manual revision is versioned; if a boundary changes, recode the independent subset. Freeze the final manual before coding the remainder. Report the fraction sampled, seeds, margins, raw agreement, Cohen's kappa, missingness and adjudication counts. No automatic semantic classifier assigns the confirmatory evidence code.
