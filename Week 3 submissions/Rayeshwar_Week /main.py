#!/usr/bin/env python3
"""
Competitive Programming Agent - Main Runner
Usage:
  python main.py --problem 1374B          # solve a problem from DB
  python main.py --all                    # solve all problems in DB
  python main.py --rating 1500 1700       # solve problems in rating range
  python main.py --custom                 # solve from stdin
"""

import argparse
import json
import os
import sys
import time
from pathlib import Path

# Ensure the parent package is importable
sys.path.insert(0, str(Path(__file__).parent))

from cp_agent import solve_problem
from problem_db import PROBLEMS, get_problem_by_id, get_problems_by_rating


SOLUTIONS_DIR = Path(__file__).parent / "solutions"
SOLUTIONS_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────

def print_header(text: str):
    width = 70
    print("\n" + "=" * width)
    print(f"  {text}")
    print("=" * width)


def print_result(result: dict):
    pid    = result["problem_id"]
    passed = result["all_tests_passed"]
    status = "✅ ALL TESTS PASSED" if passed else "❌ FAILED"
    print(f"\n{'─'*60}")
    print(f"  Problem  : {pid}")
    print(f"  Verdict  : {result['verdict']}")
    print(f"  Status   : {status}")
    print(f"  Attempts : {result['attempts']}")
    print(f"{'─'*60}")

    if result["test_results"]:
        print("  Test Cases:")
        for t in result["test_results"]:
            icon = "✅" if t["status"] == "AC" else "❌"
            print(f"    {icon} Case {t['case']} [{t['status']}]")
            if t["status"] != "AC":
                print(f"       Input   : {str(t['input'])[:80]}")
                print(f"       Expected: {str(t['expected'])[:80]}")
                print(f"       Got     : {str(t['actual'])[:80]}")

    if result.get("debug_notes"):
        print("\n  Debug History:")
        for note in result["debug_notes"]:
            print(f"    • {note[:120]}...")

    if result["solution_code"]:
        out_path = SOLUTIONS_DIR / f"{pid}.cpp"
        out_path.write_text(result["solution_code"])
        print(f"\n  Solution saved → {out_path}")


def run_problem(p: dict, max_attempts: int = 5) -> dict:
    """Run the agent on one problem and print results."""
    print_header(f"Solving {p['id']} – {p['title']} (Rating: {p['rating']})")
    print(f"  URL: {p.get('url', 'N/A')}")
    start = time.time()

    result = solve_problem(
        problem_id        = p["id"],
        problem_title     = p["title"],
        problem_statement = p["statement"],
        problem_rating    = p.get("rating", 1500),
        time_limit_ms     = p.get("time_limit_ms", 2000),
        memory_limit_mb   = p.get("memory_limit_mb", 256),
        sample_inputs     = p.get("sample_inputs", []),
        sample_outputs    = p.get("sample_outputs", []),
        max_attempts      = max_attempts,
    )
    elapsed = time.time() - start
    result["elapsed_sec"] = round(elapsed, 1)
    print(f"  Time taken: {elapsed:.1f}s")
    print_result(result)
    return result


def save_report(results: list):
    """Save a JSON summary report."""
    report_path = SOLUTIONS_DIR / "report.json"
    summary = []
    for r in results:
        summary.append({
            "problem_id":       r["problem_id"],
            "verdict":          r["verdict"],
            "all_tests_passed": r["all_tests_passed"],
            "attempts":         r["attempts"],
            "elapsed_sec":      r.get("elapsed_sec", 0),
        })
    report_path.write_text(json.dumps(summary, indent=2))
    print(f"\nReport saved → {report_path}")

    total   = len(summary)
    passed  = sum(1 for r in summary if r["all_tests_passed"])
    print(f"\n{'='*60}")
    print(f"  FINAL SCORE: {passed}/{total} problems solved")
    print(f"{'='*60}")


# ─────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="CP Agent – Competitive Programming Solver")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--problem",  type=str, help="Solve a specific problem by ID, e.g. 1374B")
    group.add_argument("--all",      action="store_true", help="Solve all problems in DB")
    group.add_argument("--rating",   nargs=2, type=int, metavar=("MIN", "MAX"),
                       help="Solve problems in rating range, e.g. --rating 1500 1700")
    group.add_argument("--custom",   action="store_true", help="Input a custom problem from stdin")
    parser.add_argument("--attempts", type=int, default=5, help="Max self-healing attempts per problem")

    args = parser.parse_args()

    if args.problem:
        p = get_problem_by_id(args.problem)
        if not p:
            print(f"Problem {args.problem} not found in database.")
            sys.exit(1)
        result = run_problem(p, max_attempts=args.attempts)
        save_report([result])

    elif args.all:
        results = []
        for p in PROBLEMS:
            results.append(run_problem(p, max_attempts=args.attempts))
        save_report(results)

    elif args.rating:
        min_r, max_r = args.rating
        problems = get_problems_by_rating(min_r, max_r)
        if not problems:
            print(f"No problems found with rating {min_r}–{max_r}")
            sys.exit(1)
        results = []
        for p in problems:
            results.append(run_problem(p, max_attempts=args.attempts))
        save_report(results)

    elif args.custom:
        print("Enter problem ID: ", end="")
        pid = input().strip()
        print("Enter problem title: ", end="")
        title = input().strip()
        print("Enter problem rating (e.g. 1500): ", end="")
        rating = int(input().strip())
        print("Enter time limit in ms (e.g. 2000): ", end="")
        tl = int(input().strip())
        print("Enter problem statement (end with '---END---' on a new line):")
        lines = []
        while True:
            line = input()
            if line.strip() == "---END---":
                break
            lines.append(line)
        statement = "\n".join(lines)

        print("Enter number of sample inputs: ", end="")
        n_samples = int(input().strip())
        sample_inputs  = []
        sample_outputs = []
        for i in range(n_samples):
            print(f"Sample input {i+1} (end with '---'): ")
            inp_lines = []
            while True:
                l = input()
                if l.strip() == "---":
                    break
                inp_lines.append(l)
            print(f"Sample output {i+1} (end with '---'): ")
            out_lines = []
            while True:
                l = input()
                if l.strip() == "---":
                    break
                out_lines.append(l)
            sample_inputs.append("\n".join(inp_lines))
            sample_outputs.append("\n".join(out_lines))

        custom_problem = {
            "id": pid, "title": title, "rating": rating,
            "time_limit_ms": tl, "memory_limit_mb": 256,
            "statement": statement,
            "sample_inputs": sample_inputs,
            "sample_outputs": sample_outputs,
        }
        result = run_problem(custom_problem, max_attempts=args.attempts)
        save_report([result])


if __name__ == "__main__":
    main()
