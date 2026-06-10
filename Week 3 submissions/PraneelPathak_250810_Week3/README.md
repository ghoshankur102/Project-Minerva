# Programmed Competitive Programmer

## Overview

Programmed Competitive Programmer is a Stateful, Cyclic, Self-Healing AI Agent built using LangGraph. The system is designed to autonomously solve competitive programming problems from Codeforces by combining problem analysis, planning, code generation, testing, reflection, and repair into a single iterative workflow.

Unlike a simple one-shot code generation system, this agent maintains state across multiple stages, stores intermediate outputs, resumes interrupted executions, and continuously improves solutions through an automated feedback loop.

The project was developed to evaluate whether a structured agent architecture can reliably solve algorithmic programming problems in the 1500–1700 Codeforces rating range and beyond.

---

# Architecture

The system is implemented as a LangGraph state machine.

```text
Analyze
    ↓
Plan
    ↓
Generate Code
    ↓
Test
    ↓
Solved?
 ┌──Yes──► End
 │
 No
 │
 ▼
Critic
    ↓
Repair
    ↓
Test Again
```

The graph continues cycling through Critic → Repair → Test until:

* The solution passes all sample tests.
* The maximum number of repair attempts is reached.

---

# Agent Nodes

## 1. Analyze Node

Responsibilities:

* Extract constraints.
* Identify algorithmic topics.
* Estimate expected complexity.
* Detect important edge cases.

Output:

```text
analysis
```

---

## 2. Planner Node

Responsibilities:

* Transform analysis into a concrete solution strategy.
* Decide data structures.
* Decide algorithm.
* Outline implementation steps.

Output:

```text
plan
```

---

## 3. Generator Node

Responsibilities:

* Generate complete C++ solution.
* Follow planner guidance.
* Produce compilable code.

Output:

```text
code
```

---

## 4. Test Node

Responsibilities:

* Compile generated code.
* Run against all sample test cases.
* Compare outputs.

Output:

```text
compiled
solved
compile_output
run_stdout
run_stderr
```

---

## 5. Critic Node

Activated only when testing fails.

Responsibilities:

* Inspect compilation errors.
* Inspect runtime failures.
* Inspect incorrect outputs.
* Identify root cause.

Output:

```text
reflection
```

---

## 6. Repair Node

Activated only after Critic.

Responsibilities:

* Modify existing solution.
* Preserve correct logic.
* Fix identified issues.

Output:

```text
repaired code
```

---

# State Management

A major focus of this project is efficient state persistence.

Every node saves its output to disk immediately after execution.

```text
runs/
└── 1511_c/
    ├── analyze.json
    ├── plan.json
    ├── generate.json
    ├── test.json
    ├── critic.json (optional)
    ├── repair.json (optional)
    └── final_state.json
```

This provides:

* Full traceability.
* Easy debugging.
* Experiment reproducibility.
* Crash recovery.

---

# Persistent Execution

The system is designed to survive interruptions.

When the agent starts:

1. It checks whether a saved state already exists.
2. If a completed state exists, it loads it.
3. The problem is skipped instead of consuming additional API calls.

This prevents re-solving previously processed problems.

Benefits:

* Faster reruns.
* Lower API costs.
* Protection against crashes.
* Easy continuation of large batches.

---

# Progress Tracking

The system maintains a persistent progress file.

```text
progress.json
```

Example:

```json
{
  "1511_C": true,
  "1610_B": true,
  "414_B": false
}
```

Before solving a problem:

* The agent checks progress.json.
* Solved problems are skipped automatically.

This allows processing hundreds of problems across multiple sessions without wasting computation.

---

# API Cost Optimization

A significant portion of the engineering effort was focused on minimizing API usage.

## 1. Node-Level State Saving

Every node stores its results.

This prevents:

* Re-analysis
* Re-planning
* Re-generation

when a run is interrupted.

Benefits:

* Reduced token usage.
* Reduced execution time.
* Lower API costs.

---

## 2. Selective Model Usage

Different models can be assigned to different stages.
These can also be modified from `llm_router.py`

Example configuration:

| Stage    | Model             |
| -------- | ----------------- |
| Analyze  | Gemini Flash      |
| Plan     | Gemini Flash      |
| Generate | Gemini Flash      |
| Critic   | Gemini Pro        |
| Repair   | Gemini Pro        |

Benefits:

* Expensive models only where necessary.
* Better performance-per-token.
* Higher throughput.

---

# Batch Processing

The system supports automated evaluation over an entire problem set.

Workflow:

1. Load problems from CSV.
2. Check cache.
3. Check progress.
4. Load saved state if available.
5. Run LangGraph pipeline.
6. Save generated solution.
7. Save final state.
8. Update progress.

Outputs:

```text
outputs/
├── 1511_C.cpp
├── 414_B.cpp
├── 845_C.cpp
└── ...
```

---

# Directory Structure

```text
src/
│
├── cache/
│   ├── solution.cpp
│   └── solution.exe
│
├── graphs/
│   ├── graph.py
│   └── state.py
│
├── nodes/
│   ├── analyze.py
│   ├── critic.py
│   ├── generator.py
│   ├── planner.py
│   ├── repair.py
│   └── test_node.py
│
├── outputs/
│   
├── runs/
│
├── testing
│   ├── run_graph.py
│   ├── test.py
│   └── test_problem.txt
│
├── tools
│   └── code_runner.py
│
├── utils
│   ├── extract_code.py
│   └── run_logger.py
│
├── .env.example
├── main.py
├── llm_router.py
├── load_problem.py
├── problems.csv
├── progress.json
├── README.md
└── requirements.txt
```

---

# Key Features

This project goes beyond basic code generation by incorporating:

* Stateful execution.
* Cyclic self-repair loops.
* Automated testing.
* Reflection-driven debugging.
* Persistent progress tracking.
* Disk-based state recovery.
* Problem caching.
* API cost optimization.
* Batch evaluation pipeline.

The resulting system behaves more like an autonomous competitive programmer than a traditional prompt-response chatbot.

---

# Outputs

For every solved problem the system produces:

* Complete C++ source code.
* Full execution trace.
* Intermediate reasoning artifacts.
* Final state snapshot.
* Persistent success record.

This enables large-scale evaluation while maintaining reproducibility and minimizing repeated computation.
