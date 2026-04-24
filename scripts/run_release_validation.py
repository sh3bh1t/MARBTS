from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from utils.release_validation import run_release_validation  # noqa: E402


def main() -> None:
    result = run_release_validation()
    report = result["report"]

    status_tag = "RELEASE_READY" if report.all_gates_pass else "RELEASE_NOT_READY"
    print(status_tag)
    print(f"timestamp_utc={report.timestamp_utc}")
    print(f"gate_count={report.gate_count}")
    print(f"pass_count={report.pass_count}")
    print(f"fail_count={report.fail_count}")
    print(f"all_gates_pass={str(report.all_gates_pass).lower()}")
    for gate in report.gates:
        symbol = "PASS" if gate.status == "pass" else "FAIL"
        detail = gate.evidence if gate.status == "pass" else gate.failure_detail
        print(f"  [{symbol}] {gate.gate_id}: {detail or gate.description}")

    if not report.all_gates_pass:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
