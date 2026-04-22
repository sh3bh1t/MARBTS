# Execution Rules

## Authority
This file is authoritative. All implementation and planning steps must comply.

## Plan Adherence
- No deviation from approved plan unless technically unavoidable.
- Before implementing any feature, re-read:
  - all files in `.agent/guides/`
  - the relevant phase plan in `.agent/plans/`
- Explicitly confirm during execution:
  - "This step aligns with the master plan and guide constraints."

## Deviation Protocol (Mandatory)
When unexpected behavior, architectural constraints, implementation difficulty, or better design opportunities are detected:
1. Pause implementation.
2. Analyze deviation against the current plan.
3. Update:
  - `.agent/plans/master_plan.md`
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
- Commands in docs must be repo-root relative and environment-agnostic; do not use machine-specific absolute paths.

## Shared Foundation Module Rules (`src/hart/`)
- Treat `src/hart/` as the centralized shared foundation layer.
- Place reusable enums under `src/hart/enums/`.
- Place reusable data models (dataclasses/contracts) under `src/hart/models/`.
- Place other reusable, import-safe assets in `hart` when they are cross-module and do not require immediate runtime state (for example: shared constants, typed contracts, protocol definitions, validation helpers, portable serialization helpers).
- Avoid redefining shared contracts in feature modules; import from `hart` instead.
- Keep `hart` modules runtime-light and side-effect-free so they can be imported by runtime services, offline tooling, and future hosted/online components.
- When introducing a new shared contract, add/adjust the relevant `hart` module first, then consume it from implementation modules.

## Dependency Management Rules
- Maintain a single root dependency manifest at `requirements.txt`.
- When introducing a new external Python package, update `requirements.txt` in the same change.
- Prefer mature external libraries over custom native implementations when they provide meaningful gains in correctness, maintainability, testability, or safety.
- Before adding a library, justify the benefit briefly in the related plan/doc update and avoid dependency bloat.
- Prefer explicit version ranges and tighten to pinned versions after baseline validation milestones.
- Do not add unused dependencies; every dependency must map to an implemented component.

## Scaffold Stub Lifecycle Rules
- `STUB.md` files are temporary scaffolding markers only.
- As soon as a directory receives substantive implementation files (code/tests/config/docs), remove that directory's `STUB.md` in the same change.
- Keep `STUB.md` only in intentionally empty directories that still need to persist in git.

## Generated Artifact Version-Control Rules
- Generated runtime/research outputs must not pollute the repository history.
- For artifact-heavy directories (for example under `artifacts/runs`, `artifacts/metrics`, `artifacts/figures`, `artifacts/reports`), keep only a tracked `README.md` and ignore generated files by default via `.gitignore`.
- If a generated artifact must be shared for reproducibility evidence, include it only through an explicit, intentional change and document why.

## Public Naming Convention Rules
- Use capability-based, stable names for reusable modules/scripts/tests/artifacts (for example `multi_seed_report`, `policy_experiment_matrix`) instead of implementation-phase labels.
- Do not encode roadmap phase identifiers (`phase1`, `phase2`, `phase3`, etc.) in source module filenames, script filenames, test filenames, public function names, or generated artifact filenames unless the artifact is intentionally phase-specific archival evidence.
- Prefer names that communicate behavior and ownership domain, not delivery chronology.
- When renaming for clarity, update imports, CLI commands, tests, docs, and plan references in the same change.
