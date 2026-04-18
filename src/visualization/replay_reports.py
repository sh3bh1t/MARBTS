from __future__ import annotations

from html import escape
from pathlib import Path


def _count_compromised(snapshot: dict) -> int:
    total = 0
    for node_state in snapshot["nodes"].values():
        if node_state.get("compromised_state") in {"user", "privileged"}:
            total += 1
    return total


def _timeline_rows(run_artifacts: dict[str, object]) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for timestep in run_artifacts["timesteps"]:
        red_record = timestep["red_action_intent"]
        blue_record = timestep["blue_action_intent"]
        rows.append(
            {
                "timestep": timestep["timestep"],
                "red_action": f"{red_record['action_type']} {list(red_record['targets'])}",
                "blue_action": f"{blue_record['action_type']} {list(blue_record['targets'])}",
                "compromised_after": timestep["metric_delta"]["compromised_nodes_after"],
                "changed_nodes": len(timestep["post_state_diff"]["changed_nodes"]),
                "red_confidence": red_record.get("confidence", 0.0),
                "blue_confidence": blue_record.get("confidence", 0.0),
                "red_rationale": red_record.get("rationale", ""),
                "blue_rationale": blue_record.get("rationale", ""),
            }
        )
    return rows


def _sparkline(values: list[int]) -> str:
    if not values:
        return ""
    ticks = "▁▂▃▄▅▆▇█"
    maximum = max(values)
    if maximum == 0:
        return ticks[0] * len(values)
    return "".join(ticks[min(int((value / maximum) * (len(ticks) - 1)), len(ticks) - 1)] for value in values)


def write_run_replay_markdown(run_artifacts: dict[str, object], replay_frames: tuple[dict, ...], output_path: str | Path) -> str:
    metadata = run_artifacts["metadata"]
    final_snapshot = replay_frames[-1]["state_snapshot"] if replay_frames else run_artifacts["final_state"]
    timeline_rows = _timeline_rows(run_artifacts)
    compromised_series = [int(row["compromised_after"]) for row in timeline_rows]
    lines = [
        "# Run Replay Summary",
        "",
        f"- Run ID: `{metadata['run_id']}`",
        f"- Scenario: `{metadata['scenario_id']}`",
        f"- Seed: `{metadata['seed']}`",
        f"- Horizon: `{metadata['horizon']}`",
        f"- Logged timesteps: `{len(run_artifacts['timesteps'])}`",
        f"- Final compromised nodes: `{_count_compromised(final_snapshot)}`",
        f"- Compromise trend: `{_sparkline(compromised_series)}`",
        "",
        "## Timeline",
        "",
    ]

    for row in timeline_rows:
        lines.append(
            "- "
            f"t={row['timestep']}: red={row['red_action']}; blue={row['blue_action']}; "
            f"compromised_after={row['compromised_after']}; changed_nodes={row['changed_nodes']}; "
            f"red_confidence={row['red_confidence']}; blue_confidence={row['blue_confidence']}"
        )

    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return str(output)


def write_phase4_dashboard_html(
    report_payload: dict,
    validation_payload: dict,
    replay_markdown_path: str,
    output_path: str | Path,
) -> str:
    matrix_rows = []
    best_condition = min(report_payload["aggregates"], key=lambda item: item["mean_final_compromised_nodes"])
    rows = []
    for aggregate in report_payload["aggregates"]:
        ablation = aggregate.get("ablation", {})
        matrix_rows.append(
            {
                "condition_id": aggregate["condition_id"],
                "mean_final_compromised_nodes": aggregate["mean_final_compromised_nodes"],
            }
        )
        rows.append(
            "<tr>"
            f"<td>{escape(str(aggregate['condition_id']))}</td>"
            f"<td>{escape(str(aggregate.get('red_policy', '')))}</td>"
            f"<td>{escape(str(aggregate.get('blue_policy', '')))}</td>"
            f"<td>{escape(str(aggregate['mean_final_compromised_nodes']))}</td>"
            f"<td>{escape(str(aggregate['min_final_compromised_nodes']))}</td>"
            f"<td>{escape(str(aggregate['max_final_compromised_nodes']))}</td>"
            f"<td>{escape(str(ablation))}</td>"
            "</tr>"
        )

    replay_rows = []
    for row in validation_payload["timeline_rows"]:
        replay_rows.append(
            "<tr>"
            f"<td>{escape(str(row['timestep']))}</td>"
            f"<td>{escape(str(row['red_action']))}</td>"
            f"<td>{escape(str(row['blue_action']))}</td>"
            f"<td>{escape(str(row['compromised_after']))}</td>"
            f"<td>{escape(str(row['changed_nodes']))}</td>"
            "</tr>"
        )

    compromise_bars = []
    max_compromise = max((row["mean_final_compromised_nodes"] for row in matrix_rows), default=0.0)
    for row in matrix_rows:
        ratio = 0 if max_compromise == 0 else float(row["mean_final_compromised_nodes"]) / max_compromise
        width = max(8, int(ratio * 100)) if max_compromise else 8
        compromise_bars.append(
            "<div class='bar-row'>"
            f"<span>{escape(str(row['condition_id']))}</span>"
            f"<div class='bar'><i style='width:{width}%'></i></div>"
            f"<strong>{escape(str(row['mean_final_compromised_nodes']))}</strong>"
            "</div>"
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Phase 4 Demo Dashboard</title>
  <style>
    :root {{
      --bg: #f4efe6;
      --panel: #fffaf2;
      --ink: #1d2a38;
      --muted: #5f6b76;
      --accent: #b85c38;
      --accent-soft: #e6a77d;
      --success: #2d6a4f;
      --line: #d9cbb8;
    }}
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      color: var(--ink);
      background: radial-gradient(circle at top left, #fff7ea, var(--bg) 45%, #efe1d0 100%);
    }}
    main {{
      max-width: 1100px;
      margin: 0 auto;
      padding: 32px 20px 56px;
    }}
    .hero, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 18px;
      padding: 20px 22px;
      box-shadow: 0 12px 30px rgba(29, 42, 56, 0.07);
      margin-bottom: 18px;
    }}
    h1, h2 {{ margin-top: 0; }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      color: var(--muted);
    }}
    .meta-card {{
      background: rgba(184, 92, 56, 0.05);
      border-radius: 14px;
      padding: 10px 12px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 18px;
    }}
    .bar-row {{
      display: grid;
      grid-template-columns: minmax(160px, 1fr) 2fr auto;
      gap: 10px;
      align-items: center;
      margin-bottom: 10px;
      font-size: 14px;
    }}
    .bar {{
      height: 12px;
      background: #f0e1cf;
      border-radius: 999px;
      overflow: hidden;
    }}
    .bar i {{
      display: block;
      height: 100%;
      background: linear-gradient(90deg, var(--accent-soft), var(--accent));
      border-radius: 999px;
    }}
    .callout {{
      border-left: 4px solid var(--success);
      padding-left: 12px;
      color: var(--muted);
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      padding: 10px 8px;
      border-bottom: 1px solid var(--line);
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: var(--accent);
      font-weight: 700;
    }}
    a {{
      color: var(--accent);
    }}
  </style>
</head>
<body>
  <main>
    <section class="hero">
      <h1>Phase 4 Demo Dashboard</h1>
      <div class="meta">
        <div class="meta-card">Scenario: <strong>{escape(str(report_payload['scenario_id']))}</strong></div>
        <div class="meta-card">Version: <strong>{escape(str(report_payload['scenario_version']))}</strong></div>
        <div class="meta-card">Seed Count: <strong>{escape(str(report_payload['seed_count']))}</strong></div>
        <div class="meta-card">Log Completeness Ratio: <strong>{escape(str(validation_payload['log_completeness_ratio']))}</strong></div>
        <div class="meta-card">Events: <strong>{escape(str(validation_payload['event_count']))}</strong></div>
        <div class="meta-card">Max Compromised Nodes: <strong>{escape(str(validation_payload['max_compromised_nodes']))}</strong></div>
      </div>
    </section>
    <section class="panel">
      <div class="grid">
        <div>
          <h2>Comparison Trend</h2>
          {''.join(compromise_bars)}
        </div>
        <div>
          <h2>Best Defensive Outcome</h2>
          <p class="callout">
            Lowest mean final compromise came from <strong>{escape(str(best_condition['condition_id']))}</strong>
            at <strong>{escape(str(best_condition['mean_final_compromised_nodes']))}</strong>.
          </p>
          <p>Replay summary: <a href="{escape(replay_markdown_path)}">{escape(replay_markdown_path)}</a></p>
          <p>Red action mix: <strong>{escape(str(validation_payload['action_type_counts']['red']))}</strong></p>
          <p>Blue action mix: <strong>{escape(str(validation_payload['action_type_counts']['blue']))}</strong></p>
        </div>
      </div>
    </section>
    <section class="panel">
      <h2>Comparison Matrix</h2>
      <table>
        <thead>
          <tr>
            <th>Condition</th>
            <th>Red</th>
            <th>Blue</th>
            <th>Mean Final Compromise</th>
            <th>Min</th>
            <th>Max</th>
            <th>Ablation</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </section>
    <section class="panel">
      <h2>Replay Timeline</h2>
      <table>
        <thead>
          <tr>
            <th>Timestep</th>
            <th>Red Action</th>
            <th>Blue Action</th>
            <th>Compromised After</th>
            <th>Changed Nodes</th>
          </tr>
        </thead>
        <tbody>
          {''.join(replay_rows)}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return str(output)


def write_phase4_comparison_html(report_payload: dict, output_path: str | Path) -> str:
    rows = []
    best_condition = min(report_payload["aggregates"], key=lambda item: item["mean_final_compromised_nodes"])
    worst_condition = max(report_payload["aggregates"], key=lambda item: item["mean_final_compromised_nodes"])

    for aggregate in report_payload["aggregates"]:
        rows.append(
            "<tr>"
            f"<td>{escape(str(aggregate['condition_id']))}</td>"
            f"<td>{escape(str(aggregate.get('red_policy', '')))}</td>"
            f"<td>{escape(str(aggregate.get('blue_policy', '')))}</td>"
            f"<td>{escape(str(aggregate['mean_final_compromised_nodes']))}</td>"
            f"<td>{escape(str(aggregate['min_final_compromised_nodes']))}</td>"
            f"<td>{escape(str(aggregate['max_final_compromised_nodes']))}</td>"
            f"<td>{escape(str(aggregate.get('ablation', {})))}</td>"
            "</tr>"
        )

    html = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Phase 4 Comparison Report</title>
  <style>
    body {{
      margin: 0;
      font-family: Georgia, "Times New Roman", serif;
      background: linear-gradient(180deg, #f7f1e7 0%, #efe3d4 100%);
      color: #1d2a38;
    }}
    main {{
      max-width: 1080px;
      margin: 0 auto;
      padding: 28px 18px 48px;
    }}
    section {{
      background: rgba(255, 251, 245, 0.94);
      border: 1px solid #d8c6b2;
      border-radius: 18px;
      padding: 20px 22px;
      margin-bottom: 18px;
      box-shadow: 0 12px 30px rgba(29, 42, 56, 0.06);
    }}
    .meta {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
      gap: 12px;
    }}
    table {{
      width: 100%;
      border-collapse: collapse;
      font-size: 14px;
    }}
    th, td {{
      padding: 10px 8px;
      border-bottom: 1px solid #d8c6b2;
      text-align: left;
      vertical-align: top;
    }}
    th {{
      color: #a44f2f;
    }}
  </style>
</head>
<body>
  <main>
    <section>
      <h1>Phase 4 Comparison Report</h1>
      <div class="meta">
        <div>Scenario: <strong>{escape(str(report_payload['scenario_id']))}</strong></div>
        <div>Version: <strong>{escape(str(report_payload['scenario_version']))}</strong></div>
        <div>Seed Count: <strong>{escape(str(report_payload['seed_count']))}</strong></div>
        <div>Best Condition: <strong>{escape(str(best_condition['condition_id']))}</strong></div>
        <div>Worst Condition: <strong>{escape(str(worst_condition['condition_id']))}</strong></div>
      </div>
    </section>
    <section>
      <h2>Condition Comparison</h2>
      <table>
        <thead>
          <tr>
            <th>Condition</th>
            <th>Red</th>
            <th>Blue</th>
            <th>Mean Final Compromise</th>
            <th>Min</th>
            <th>Max</th>
            <th>Ablation</th>
          </tr>
        </thead>
        <tbody>
          {''.join(rows)}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(html, encoding="utf-8")
    return str(output)
