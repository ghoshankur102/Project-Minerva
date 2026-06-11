# Stateful, Cyclic Self-Healing CP Agent

## Architecture & Technical Documentation

---

## Overview

This agent is a **Stateful, Cyclic, Self-Healing AI system** built on [LangGraph](https://github.com/langchain-ai/langgraph) that autonomously solves Codeforces competitive programming problems rated **1500–1900+**.

The core hypothesis: by combining structured state machines, chain-of-thought planning, iterative code generation, and automated test execution with targeted error feedback, a single LLM can reliably solve algorithmic challenges without human intervention.

---

## Architecture Flowchart

```
┌─────────────────────────────────────────────────────────────────┐
│                    CP AGENT  (LangGraph)                        │
│                                                                 │
│   Problem Input                                                 │
│        │                                                        │
│        ▼                                                        │
│  ┌───────────┐                                                  │
│  │   PARSE   │  ← Structured extraction via Claude             │
│  │  (Node 1) │    (statement, I/O samples, constraints)        │
│  └─────┬─────┘                                                  │
│        │                                                        │
│        ▼                                                        │
│  ┌───────────┐                                                  │
│  │   PLAN    │  ← Chain-of-Thought Algorithm Analysis          │
│  │  (Node 2) │    (category, complexity, edge cases, plan)     │
│  └─────┬─────┘                                                  │
│        │                                                        │
│        ▼                                                        │
│  ┌───────────┐                                                  │
│  │   CODE    │  ← Generate C++17 solution                      │
│  │  (Node 3) │    (with error context from previous attempt)   │
│  └─────┬─────┘                                                  │
│        │                                                        │
│        ▼                                                        │
│  ┌───────────┐   Compile + Run vs sample cases                 │
│  │   TEST    │──────────────────────────────────────────────┐  │
│  │  (Node 4) │                                              │  │
│  └─────┬─────┘                                              │  │
│        │                                                    │  │
│   ┌────┴──────┬──────────────────┐                          │  │
│   │           │                  │                          │  │
│   ▼           ▼                  ▼                          │  │
│  ALL        WRONG/             TLE                          │  │
│ PASSED      RE/CE           DETECTED                        │  │
│   │           │                  │                          │  │
│   ▼           ▼                  ▼                          │  │
│  DONE      DEBUG           OPTIMIZE ◄────────────────────┘  │  │
│  (END)    (Node 5)         (Node 6)                          │  │
│             │                  │                             │  │
│     ┌───────┴──────┐           └──────────────────────────► │  │
│     │              │                                         │  │
│  needs           code                                        │  │
│  replan          fix                                         │  │
│     │              │                                         │  │
│     └──► PLAN       └──► CODE ◄──── self-healing loop ◄──── ┘  │
│                                     (max 5 attempts)            │
│                                                                 │
│   If max_attempts exceeded → FAILED (END)                      │
└─────────────────────────────────────────────────────────────────┘
```

---

## Node Descriptions

### 1. PARSE Node
**Purpose:** Convert raw problem text into structured data.

- Calls Claude with a JSON-output prompt
- Extracts: clean problem statement, sample I/O pairs, time/memory limits
- Falls back gracefully if parsing fails

**Inputs:** Raw problem statement string  
**Outputs:** `sample_inputs[]`, `sample_outputs[]`, `time_limit_ms`, `memory_limit_mb`

---

### 2. PLAN Node  
**Purpose:** Chain-of-thought algorithm analysis.

The planning prompt instructs Claude to reason through:
1. **Problem category** (DP, Graph, Greedy, Binary Search, Math, etc.)
2. **Key observations** and invariants
3. **Algorithm choice** with time/space justification
4. **Edge cases** to handle
5. **Implementation steps**

This node is re-entered if the debug node determines the algorithm is fundamentally wrong.

**Inputs:** Problem statement, previous debug notes  
**Outputs:** `algorithm_plan` (detailed strategy)

---

### 3. CODE Node
**Purpose:** Generate C++17 solution from the plan.

- Feeds the plan + any error context into Claude
- Strips markdown fences from output
- Increments `attempt` counter

**Error Context Injection:**
```
[Compile Error]  →  Exact stderr injected
[Runtime Error]  →  Crash output injected  
[Wrong Answer]   →  Failing cases injected (input/expected/actual)
[TLE]            →  Complexity note injected
```

---

### 4. TEST Node
**Purpose:** Automated compile + run validation.

```
g++ -O2 -std=c++17 -o sol sol.cpp
```

For each sample case:
- Runs `./sol` with piped stdin
- Compares stdout (stripped) to expected output
- Detects: CE, RE, WA, TLE

**Routing:**
- All AC → `DONE`
- Any failure → `DEBUG`

---

### 5. DEBUG Node (Self-Healing Core)
**Purpose:** Root-cause analysis of failures.

Asks Claude to:
1. Diagnose the exact failure reason
2. Determine if it's an **implementation bug** (→ re-generate code) or **wrong algorithm** (→ re-plan)
3. Output concrete fix instructions

Fix notes are appended to `debug_notes[]` for full history across attempts.

**Max Attempts Guard:** After `max_attempts` (default 5), transitions to `FAILED`.

---

### 6. OPTIMIZE Node
**Purpose:** Performance-focused rewrite for TLE cases.

- Activated when correctness is confirmed but speed is insufficient
- Prompts focus on reducing constants, better data structures, precomputation
- Returns to TEST node

---

## State Schema

```python
class CPAgentState(TypedDict):
    # Problem
    problem_id:         str
    problem_title:      str
    problem_statement:  str
    problem_rating:     int
    time_limit_ms:      int
    memory_limit_mb:    int
    sample_inputs:      List[str]
    sample_outputs:     List[str]

    # Reasoning
    analysis:           str
    algorithm_plan:     str
    solution_code:      str
    language:           str       # always "cpp"

    # Self-healing
    phase:              str       # AgentPhase enum
    attempt:            int
    max_attempts:       int
    compile_error:      str
    runtime_error:      str
    wrong_answer_info:  str
    tle_info:           str
    debug_notes:        List[str]

    # Results
    test_results:       List[Dict]
    all_tests_passed:   bool
    final_verdict:      str
```

---

## Cyclic Self-Healing Loop

The "self-healing" mechanism is the core innovation. Unlike a single-pass code generator, this agent:

```
attempt 1: generate → test → FAIL
           ↓
           debug: "off-by-one in binary search boundary"
           ↓
attempt 2: generate (with error context) → test → FAIL
           ↓
           debug: "algorithm wrong, need DP not greedy"
           ↓
           re-plan (new algorithm)
           ↓
attempt 3: generate → test → PASS ✅
```

The debug notes accumulate across all attempts, giving the code generator full context of what was tried and why it failed.

---

## Problem Selection

Problems are curated from Codeforces, targeting ratings 1500–1900:

| Problem ID | Title | Rating | Topic | URL |
|------------|-------|--------|-------|-----|
| 1374B | Multiply by 2, divide by 6 | 1500 | Math | [Link](https://codeforces.com/problemset/problem/1374/B) |
| 1295C | Obtain The String | 1500 | Strings/Greedy | [Link](https://codeforces.com/problemset/problem/1295/C) |
| 1352D | Count the Arrays | 1500 | Combinatorics | [Link](https://codeforces.com/problemset/problem/1352/D) |
| 1538F | Interesting Function | 1600 | Math/Digit DP | [Link](https://codeforces.com/problemset/problem/1538/F) |
| 1607D | Blue-Red Permutation | 1600 | Greedy/Sorting | [Link](https://codeforces.com/problemset/problem/1607/D) |
| 1536C | Painted Array | 1700 | Greedy | [Link](https://codeforces.com/problemset/problem/1536/C) |
| 1689C | Infected Tree | 1700 | Tree/Greedy | [Link](https://codeforces.com/problemset/problem/1689/C) |
| 1367F | Lena and Sequence | 1800 | Bitmask/Greedy | [Link](https://codeforces.com/problemset/problem/1367/F) |
| 1550E | Gregor and Two Painters | 1900 | Combinatorics | [Link](https://codeforces.com/problemset/problem/1550/E) |

---

## Setup & Usage

### Requirements

```bash
pip install langgraph langchain-core anthropic requests
```

Also requires `g++` (GCC with C++17 support):
```bash
# Ubuntu/Debian
sudo apt-get install g++

# macOS
xcode-select --install
```

### Environment

```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### Run

```bash
# Solve a single problem
python main.py --problem 1295C

# Solve all problems in the database
python main.py --all

# Solve problems in a rating range
python main.py --rating 1500 1700

# Solve a custom problem interactively
python main.py --custom

# Increase self-healing attempts (default 5)
python main.py --problem 1689C --attempts 8
```

### Output

Solutions are saved to `solutions/<PROBLEM_ID>.cpp`.  
A summary report is saved to `solutions/report.json`.

---

## Technical Design Decisions

### Why LangGraph?

LangGraph's `StateGraph` enables:
- **Typed state** — all agent data is in one immutable dict, making debugging easy
- **Conditional routing** — phase-based routing without nested if/else
- **Cycles** — native support for the debug → code → test loops
- **Tracing** — full execution graph visible via LangGraph Studio

### Why C++?
- Faster execution (critical for TLE-sensitive problems)
- Competitive programmers universally use C++ for its speed and STL
- `g++` is universally available on judge systems

### Why claude-sonnet-4-20250514?
- Strong reasoning for algorithm analysis
- Reliable code generation with error context
- Sufficient context window for full debug history

### Prompt Engineering Choices
- **System role separation:** Each node has a focused system prompt (parser, planner, coder, debugger) rather than a single monolithic prompt
- **Error injection:** Compile errors, wrong answers, and TLE info are injected verbatim into the next generation prompt
- **Debug accumulation:** `debug_notes[]` grows across all attempts, giving the model full failure history
- **Re-plan trigger:** Keywords like "wrong algorithm", "rethink", "TLE" in debug output trigger a full re-plan rather than just a code fix

---

## Effectiveness Measurement

The agent is evaluated on:

| Metric | Description |
|--------|-------------|
| **AC Rate** | % of problems where all sample tests pass |
| **Attempt Efficiency** | Average attempts needed to reach AC |
| **Rating Coverage** | Max rating successfully solved |
| **Compile Success** | % of code attempts that compile |

Expected performance:
- 1500-rated problems: ~95% first-attempt compile, ~85% AC within 3 attempts
- 1700-rated problems: ~90% first compile, ~70% AC within 5 attempts  
- 1900-rated problems: ~80% compile, ~50% AC within 5 attempts

---

## Directory Structure

```
cp_agent/
├── agent/
│   ├── __init__.py
│   └── cp_agent.py        ← LangGraph state machine (all nodes + routing)
├── problems/
│   ├── __init__.py
│   └── problem_db.py      ← Curated problem database (1500–1900)
├── solutions/             ← Auto-generated .cpp files + report.json
├── docs/
│   └── ARCHITECTURE.md    ← This document
├── main.py                ← CLI runner
└── requirements.txt
```

---

## Extending the Agent

### Add a new problem

```python
# In problems/problem_db.py, append to PROBLEMS list:
{
    "id": "1800X",
    "title": "My Problem",
    "rating": 1800,
    "url": "https://codeforces.com/problemset/problem/1800/X",
    "time_limit_ms": 2000,
    "memory_limit_mb": 256,
    "statement": "...",
    "sample_inputs": ["input1"],
    "sample_outputs": ["output1"],
}
```

### Fetch problems from Codeforces API

```python
import requests

def fetch_cf_problems(min_rating=1500, max_rating=1700):
    url = "https://codeforces.com/api/problemset.problems"
    r = requests.get(url)
    data = r.json()
    problems = [
        p for p in data["result"]["problems"]
        if "rating" in p and min_rating <= p["rating"] <= max_rating
    ]
    return problems
```

### Add Python fallback

In `debug_node`, if C++ fails repeatedly, switch `state["language"]` to `"python"` and adjust the CODE node prompt accordingly.

---

*Built for the Stateful AI Agent assignment — demonstrating autonomous competitive programming with cyclic self-healing via LangGraph.*
