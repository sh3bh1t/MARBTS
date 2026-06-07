# Comparative Report

Scenario pair: rule-baseline:rule_red_vs_rule_blue__vs__rule-baseline:adaptive_red_vs_rule_blue

## Comparison Overview
| Metric | Left Run | Right Run | Delta |
| --- | --- | --- | --- |
| Final compromised nodes | 0 | 1 | 1 |
| Blue containment actions | 0 | 2 | 2 |
| First containment timestep | -1 | 0 | 1 |
| Response latency | -1 | 0 | 1 |
| Containment-to-compromise ratio | 0 | 2 | 2 |

## Defense Efficiency Table
| Run ID | Blue containment actions | Final compromised nodes | Containment/compromise ratio | First containment timestep | Response latency |
| --- | --- | --- | --- | --- | --- |
| c16f1aae9fb145be | 0 | 0 | 0 | -1 | -1 |
| 49b9e1e81edc1061 | 2 | 1 | 2 | 0 | 0 |

## Figure Outputs
- Compromise trend: artifacts/figures/comparative_report_c16f1aae9fb145be_vs_49b9e1e81edc1061_compromise_trend.svg
- Defense efficiency: artifacts/figures/comparative_report_c16f1aae9fb145be_vs_49b9e1e81edc1061_defense_efficiency.svg
- Response latency: artifacts/figures/comparative_report_c16f1aae9fb145be_vs_49b9e1e81edc1061_response_latency.svg

## Trend Notes
- Left compromise trend: 0, 0
- Right compromise trend: 1, 1
