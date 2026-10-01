---
name: adr-reviewer
description: Review an Architecture Decision Record and identify gaps, risks, inconsistencies, and missing evidence before the ADR is accepted. Use when reviewing ADR documents.
---

adr-reviewer

Purpose:
Review an Architecture Decision Record and identify gaps, risks,
inconsistencies, and missing evidence before the ADR is accepted.

Review areas:

1. Context
- Is the problem clearly defined?
- Are business and technical drivers explicit?
- Are assumptions and constraints documented?
- Is the scope/boundary clear?

2. Decision
- Is the chosen architecture unambiguous?
- Does the ADR say exactly what will change?
- Are affected systems/components identified?
- Are deployment/runtime boundaries clear?

3. Alternatives
- Were realistic alternatives considered?
- Is "do nothing / keep current architecture" considered where relevant?
- Are alternatives compared using consistent criteria?
- Is rejection rationale documented?

4. Trade-offs
- Benefits
- Costs
- Operational complexity
- Performance
- Scalability
- Reliability
- Security
- Maintainability
- Vendor lock-in
- Migration complexity

5. Evidence
- Are claims supported by benchmarks, experiments, documentation,
  incidents, cost estimates, or production observations?
- Flag unsupported assumptions.

6. Consequences
- Positive consequences
- Negative consequences
- New operational responsibilities
- Failure modes
- Long-term maintenance impact
- Reversibility / exit strategy

7. Implementation
- Migration strategy
- Rollback strategy
- Dependencies
- Observability requirements
- Security controls
- Required infrastructure changes

8. ADR lifecycle
- Status is valid: Proposed / Accepted / Rejected / Superseded
- Decision owner is identified
- Date is present
- Superseded ADRs are linked
- Related ADRs are referenced

Output:

## Summary
Brief description of the proposed decision.

## Critical Issues
Issues that should be resolved before accepting the ADR.

## Important Improvements
Issues that materially improve the architecture decision.

## Minor Improvements
Clarity/documentation improvements.

## Missing Evidence
Claims or assumptions that need validation.

## Questions
Questions the ADR author should answer.

## Suggested Changes
Concrete edits or additions to the ADR.

Do not rewrite the entire ADR unless requested.
Do not approve an ADR merely because the document is well written.
Prioritize architectural correctness, explicit trade-offs, operability,
security, and reversibility.
