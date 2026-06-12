"""
Testing Harness for the Codeforces Autonomous Solver
=====================================================
Usage:
    python harness.py                          # run all problems in PROBLEM_LIST
    python harness.py 1700A 1700B              # run specific problems
    python harness.py --export results.json    # save JSON report

Requires:
    ANTHROPIC_API_KEY environment variable set.
"""

import argparse
import json
import os
import sys
import time
from datetime import datetime
from pathlib import Path

from agent import solve

# ── Default problem list (1500–1700 range, manually curated) ──────────────────
# Format: (problem_id, name, rating)
PROBLEM_LIST = [
    # 1500
    ("1500A", "Going Home", 1500),
    ("1504A", "Run!", 1500),
    ("1506B", "Partial Replacement", 1500),
    # 1600
    ("1601A", "Array Reconstruction", 1600),
    ("1611C", "Polycarp Recovers", 1600),
    ("1612C", "Chat Ban", 1600),
    # 1700
    ("1700A", "Optimal Path", 1700),
    ("1701B", "Permutation", 1700),
    ("1703B", "ICPC Balloons", 1700),
]

# ── Harness ───────────────────────────────────────────────────────────────────
def run_harness(problem_ids: list[str], export_path: str | None = None) -> None:
    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("[ERROR] ANTHROPIC_API_KEY not set.")
        sys.exit(1)

    results = []
    summary = {"AC": 0, "WA": 0, "CE": 0, "TLE": 0, "FAILED": 0}

    print("=" * 60)
    print(f"  CF Autonomous Solver — {len(problem_ids)} problem(s)")
    print(f"  Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    for pid in problem_ids:
        print(f"\n{'─' * 60}")
        print(f"  PROBLEM: {pid}")
        print(f"{'─' * 60}")
        t0 = time.time()
        try:
            state = solve(pid)
        except Exception as e:
            print(f"[ERROR] Unhandled exception for {pid}: {e}")
            state = {"verdict": "FAILED", "attempt": 0, "final_solution": "", "error_trace": str(e)}

        elapsed = time.time() - t0
        verdict = state.get("verdict", "FAILED")
        summary[verdict] = summary.get(verdict, 0) + 1

        record = {
            "problem_id": pid,
            "verdict": verdict,
            "attempts": state.get("attempt", 0),
            "time_seconds": round(elapsed, 1),
            "solution_code": state.get("final_solution") or state.get("solution_code", ""),
            "error_trace": state.get("error_trace", ""),
            "run_results": state.get("run_results", []),
        }
        results.append(record)

        icon = "✓" if verdict == "AC" else "✗"
        print(
            f"\n  {icon} {pid}: {verdict} | "
            f"attempts={record['attempts']} | "
            f"time={record['time_seconds']}s"
        )

        if verdict == "AC":
            print(f"\n  ─── Accepted Solution ───")
            for line in record["solution_code"].splitlines()[:30]:
                print(f"  {line}")
            if len(record["solution_code"].splitlines()) > 30:
                print("  ... (truncated)")

    # Summary
    print(f"\n{'=' * 60}")
    print(f"  SUMMARY")
    print(f"  AC={summary['AC']}  WA={summary['WA']}  CE={summary['CE']}  TLE={summary['TLE']}  FAILED={summary.get('FAILED', 0)}")
    ac_rate = summary["AC"] / len(problem_ids) * 100 if problem_ids else 0
    print(f"  Accuracy: {ac_rate:.1f}%")
    print(f"{'=' * 60}")

    if export_path:
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": summary,
            "accuracy_pct": round(ac_rate, 1),
            "results": results,
        }
        Path(export_path).write_text(json.dumps(report, indent=2))
        print(f"\n  Report saved → {export_path}")


# ── CLI ───────────────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="CF Solver Testing Harness")
    parser.add_argument(
        "problems",
        nargs="*",
        help="Problem IDs to solve (e.g. 1700A 1600B). Defaults to built-in list.",
    )
    parser.add_argument(
        "--export",
        metavar="FILE",
        default=None,
        help="Export JSON report to this path.",
    )
    parser.add_argument(
        "--list",
        action="store_true",
        help="Print default problem list and exit.",
    )
    args = parser.parse_args()

    if args.list:
        print("Default problem list:")
        for pid, name, rating in PROBLEM_LIST:
            print(f"  {pid:8s}  {rating}  {name}")
        return

    if args.problems:
        ids = [p.upper() for p in args.problems]
    else:
        ids = [p[0] for p in PROBLEM_LIST]

    run_harness(ids, export_path=args.export)


if __name__ == "__main__":
    main()
