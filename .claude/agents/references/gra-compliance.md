# GRA Compliance Protocol — All Research Agents

This file is the shared reference for all 11 research agents in the Sermon Research Workflow.
Every research agent MUST follow these rules when generating output.

## 1. GroundedClaim Output Format

ALL research findings must be expressed as GroundedClaims:

```yaml
claims:
  - id: "{PREFIX}-{NNN}"
    text: "The actual claim statement"
    claim_type: FACTUAL | LINGUISTIC | HISTORICAL | THEOLOGICAL | INTERPRETIVE | APPLICATIONAL
    sources:
      - type: PRIMARY | SECONDARY | TERTIARY
        reference: "Specific reference (author, page, section)"
        verified: true | false
    confidence: 0-100
    uncertainty: "Expression of uncertainty" | null
```

### Claim ID Convention
- Use your assigned prefix (e.g., OTA for original-text-analyst)
- Sequential numbering: OTA-001, OTA-002, ...
- Never reuse IDs within a single output

### ClaimType Source Requirements

| ClaimType | Required Source | Min Count | Min Confidence |
|-----------|---------------|-----------|----------------|
| FACTUAL | PRIMARY or SECONDARY | 1 | 95 |
| LINGUISTIC | PRIMARY (mandatory) | 1 | 90 |
| HISTORICAL | SECONDARY or TERTIARY | 1 | 80 |
| THEOLOGICAL | SECONDARY or TERTIARY | 1 | 70 |
| INTERPRETIVE | None required | 0 | 70 |
| APPLICATIONAL | None required | 0 | 60 |

## 2. Hallucination Firewall — Self-Check Before Output

Before finalizing ANY claim, check your text against these rules:

### BLOCK — Remove immediately
- "All scholars agree" / "Every scholar consensus"
- "100% certain/sure/accurate"
- "Without (any) exception"
- "Universally accepted"
- "No scholar disagrees"
- "모든 학자가 동의" / "모든 학자들이 합의"
- "예외 없이"
- "보편적으로 인정"
- "반론의 여지가 없" / "반론이 없"

### REQUIRE_SOURCE — Add source or remove
- "Exactly N" (specific numbers need citation)
- "BC/BCE YYYY" dates without source
- "Precisely N" counts without verification

### SOFTEN — Replace with hedged language
- "Certainly" → "Likely" or "Probably"
- "Clearly" → "Arguably" or "It appears that"
- "Obviously" → "Notably" or "Significantly"
- "Undeniably" → "Strongly suggested"
- "Undoubtedly" → "With high probability"

### VERIFY — Add verification tag
- "Dr./Prof. X argues..." → Add [VERIFY: attribution] tag
- "Traditionally..." → Add [VERIFY: tradition] tag
- "According to tradition..." → Add [VERIFY: tradition] tag

## 3. Thinking Process

Choose the appropriate thinking process for your analysis:

### CoT (Chain of Thought) — Sequential reasoning
```
Step 1: [Observation] → Step 2: [Analysis] → Step 3: [Conclusion]
```
Use when: Analysis flows logically from observation to conclusion.

### ToT (Tree of Thought) — Multiple hypothesis exploration
```
       Root: Problem
      /     |     \
   Hyp.A  Hyp.B  Hyp.C
     |      |      |
   Test    Test   Test
     \      |      /
      Final Conclusion
```
Use when: Multiple interpretive possibilities exist.

### Thought Loop (max 3 iterations)
```
Loop 1: Initial analysis → Insufficient
Loop 2: Additional exploration → Needs refinement
Loop 3: Final analysis → Conclusion
(If no conclusion after 3 loops → return [FAILURE:LOOP_EXHAUSTED])
```
Use when: Iterative refinement needed to reach satisfactory conclusion.

## 4. Error Handling

If you encounter a problem, output the appropriate failure tag:

| Tag | When to Use |
|-----|------------|
| `[FAILURE:LOOP_EXHAUSTED]` | 3 thought loops without conclusion |
| `[FAILURE:SOURCE_UNAVAILABLE]` | Required reference inaccessible |
| `[FAILURE:INPUT_INVALID]` | Input text/passage invalid |
| `[FAILURE:CONFLICT_UNRESOLVABLE]` | Contradictory evidence, no resolution |
| `[FAILURE:OUT_OF_SCOPE]` | Analysis beyond your expertise domain |

Always include partial results before the failure tag.
Always save partial results to your output file.

## 5. Dense Checkpoint Pattern (DCP)

For analyses requiring more than 10 turns:

- **CP-1 (5 turns)**: Save intermediate findings to output file
- **CP-2 (8 turns)**: Update output file with refined analysis
- **CP-3 (10 turns)**: Finalize and ensure complete output

## 6. Output File Structure

```markdown
# [Analysis Title]

## Summary
[2-3 sentence overview of findings]

## Detailed Analysis
[Main analysis content with GroundedClaims inline]

## Claims
```yaml
claims:
  - id: "PREFIX-001"
    ...
```

## Cross-References
[References to other agents' findings when applicable]

## Methodology Notes
[Thinking process used, sources consulted]
```
