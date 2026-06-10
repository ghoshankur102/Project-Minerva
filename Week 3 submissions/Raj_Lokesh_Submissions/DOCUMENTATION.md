# Autonomous codeforces Solver 
> Stateful, Cyclic Self-Healing AI Agent · LangGraph + Gemini

**Submitted by:** Raj Choudhary &nbsp;|&nbsp; Lokesh Sharma

---

## What It Does

An autonomous agent that takes a Codeforces problem statement, thinks through an algorithm, writes a C++17 solution, self-generates test cases, critiques its own code, and **self-heals** by retrying up to 3 times if the solution is rejected — all without human intervention.

---

## Architecture

```
problem_statement
      │
      ▼
 diagnose_logic          → builds algorithm blueprint (strategy, category, complexity, edge cases)
      │
      ▼
 compile_production_source  → generates C++17 code (uses blueprint + past failure log)
      │
      ▼
 create_simulation_vectors  → generates 3 edge-case test scenarios
      │
      ▼
 run_critique_engine     → audits code vs test cases → verdict: APPROVED / REJECTED
      │
      ├── APPROVED ──────────────────────────────────► END
      │
      └── REJECTED (retries < 3)
            │
            ▼
      record_exception_state   → logs rejection, increments retry counter
            │
            └──────────────────────────────────────► compile_production_source (retry)
```

The self-healing loop feeds every rejection reason back into the next code generation attempt, so the model explicitly avoids repeating past mistakes.

---

## Agent State (`PuzzleContext`)

| Field | Purpose |
|---|---|
| `raw_challenge_text` | Input problem statement |
| `architectural_plan` | Algorithm blueprint from `diagnose_logic` |
| `candidate_source_code` | Generated C++ solution |
| `audit_verdict` | `APPROVED` or `REJECTED - <reason>` |
| `loop_index` | Retry counter (max 3) |
| `error_registry` | Cumulative list of past rejection reasons |
| `synthetic_test_matrix` | 3 auto-generated edge-case test inputs |

---

## Tech Stack

| | |
|---|---|
| Agent Framework | LangGraph |
| LLM | Gemini 2.5 Flash Lite |
| LLM Client | `langchain-google-genai` |
| Solution Language | C++17 |
| Environment | Python 3 / Google Colab |
| LLM Temperature | 0.2 |

---

## Problem Solved

**CF 1360E — Triangles Containing the Center**
🔗 https://codeforces.com/problemset/problem/1360/E
**Rating:** 1600 &nbsp;|&nbsp; **Retries used:** 3

**Problem:** Given `n` points on a circle (as angles), count triangles formed by choosing 3 points such that the triangle contains the center of the circle. Answer mod `10⁹+7`.

**Key Insight:** Instead of directly counting valid triangles, use the complementary approach:

```
valid = C(n, 3) − (triangles where all 3 points lie on a semicircle)
```

Semicircle triangles are counted using a **two-pointer sweep** on the sorted + doubled angle array. Division is handled via modular inverse (Fermat's Little Theorem).

**Complexity:** O(n log n) per test case.

---

## Setup & Usage

```bash
pip install langgraph langchain-google-genai
```

```python
# Set API key (Colab)
os.environ["GOOGLE_API_KEY"] = userdata.get("GOOGLE_API_KEY")

# Paste your problem into source_challenge, then:
runtime_results = runtime_agent.invoke(initialization_vector)
print(runtime_results["candidate_source_code"])
```

---

*CS Assignment 3 — Autonomous Competitive Programmer using LangGraph*