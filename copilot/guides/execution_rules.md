# Execution Rules

## Authority
This file is authoritative. All implementation and planning steps must comply.

## Plan Adherence
- No deviation from approved plan unless technically unavoidable.
- Before implementing any feature, re-read:
  - all files in `copilot/guides/`
  - the relevant phase plan in `copilot/plans/`
- Explicitly confirm during execution:
  - "This step aligns with the master plan and guide constraints."

## Deviation Protocol (Mandatory)
When unexpected behavior, architectural constraints, implementation difficulty, or better design opportunities are detected:
1. Pause implementation.
2. Analyze deviation against the current plan.
3. Update:
   - `copilot/plans/master_plan.md`
   - all affected phase plan files
4. Append entry under `Plan Revision Log` in impacted plan files.
5. Resume only after plan synchronization.

## Implementation Cadence
- Small, testable increments only.
- No large unverified change batches.
- Every meaningful step must include validation guidance before proceeding.

## Mandatory Step-by-Step Developer Guidance
After every meaningful implementation step:
1. Stop additional coding.
2. Provide explicit testing procedure:
   - exact commands
   - expected output
   - success criteria
   - failure indicators
3. Request developer confirmation.
4. Continue only after confirmation.

## Continuous Validation Loop
After each phase or major feature:
- Validate state transition correctness.
- Validate agent behavior correctness.
- Validate logging completeness.
- Validate reproducibility (same seed -> same result).
- Explicitly record: "Validation complete for this step."

## Ambiguity Handling
If any requirement is ambiguous:
- Stop.
- Ask a clarification question.
- Do not proceed under hidden assumptions.

## Safety and Sandbox Rules
- Keep the system fully sandboxed.
- Use abstract actions and synthetic state only.
- Avoid unsafe tooling, real exploit mechanisms, and live target operations.

## Quality and Documentation Requirements
- Every design decision must have technical rationale.
- Every module must define clear ownership, interface, and failure behavior.
- Every plan update must be traceable and versioned through git history.
- Documentation is part of delivery: when behavior, architecture, test flow, or contributor workflows change, update relevant docs in the same change.
- Keep collaborator instructions current in `README.md` and `tests/README.md` (especially run/test commands).
- Keep **all** README files current (root and scope-specific directories). README content must describe current scope status, operational usage, and contribution expectations—not only folder structure.

## Dependency Management Rules
- Maintain a single root dependency manifest at `requirements.txt`.
- When introducing a new external Python package, update `requirements.txt` in the same change.
- Prefer explicit version ranges and tighten to pinned versions after baseline validation milestones.
- Do not add unused dependencies; every dependency must map to an implemented component.
