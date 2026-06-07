# Source Cross-Check Notes

Primary source:

- `source/CIP81-1.pdf`

Repository facts verified before writing:

- The implemented CLI package is `src/marbts_cli/`; the paper corrects the report spelling `src/marbtscli/`.
- `pyproject.toml` requires Python `>=3.11` with `networkx`, `matplotlib`, and `packaging`; the development dependency is `pytest`.
- Console scripts include `marbts`, `marbts-multi-seed-report`, `marbts-policy-experiment-matrix`, `marbts-stress-test-suite`, `marbts-ablation-report`, `marbts-container-profile`, and `marbts-release-validation`.
- Agent actions are `scan`, `exploit`, `lateral_move`, `escalate`, `monitor`, `patch`, `block`, and `isolate`.
- Runtime node types are `server`, `database`, `iot`, and `endpoint`.
- Compromise states are `none`, `user`, and `privileged`; detection states are `undetected`, `suspected`, and `confirmed`.
- In the checked kernel, scan and monitor are informational actions and do not directly mutate graph state.
- `apply_exploit` is deterministic by default and becomes seeded/probabilistic only when exploit resistance is enabled.
- Remote model routing is configurable but disabled in the verified baseline configuration, with heuristic fallback enabled.

Metric facts verified from repository artifacts:

- Multi-seed baseline: scenario `rule-baseline`, seed count 3, horizon 8, final compromised mean 0.0, Blue containment mean 0.0, deterministic consistency ratio 1.0.
- Primary policy matrix: `Rule Red vs Rule Blue` gives final compromised mean 0.0 and containment mean 0.0.
- Primary policy matrix: `Adaptive Red vs Rule Blue` gives final compromised mean 1.0 and containment mean 2.0.
- Primary policy matrix: `Rule Red vs Adaptive Blue` gives final compromised mean 0.0 and containment mean 0.0.
- Primary policy matrix: `Adaptive Red vs Adaptive Blue` gives final compromised mean 1.0 and containment mean 0.0.
- The comparative report confirms the baseline run `c16f1aae9fb145be` and adaptive run `49b9e1e81edc1061` under seed 20260423 and horizon 2.
