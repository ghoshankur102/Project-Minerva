# Codeforces Autonomous Solver

## What is this?

This project started from a simple question: can an LLM actually solve competitive programming problems end-to-end, without any human in the loop? Not just generate code, but fetch the problem, compile it, test it, and fix its own mistakes?

The answer turned out to be yes, at least for problems in the 1100–1900 range. The agent went 24/24 on the evaluation sheet, including a few problems where it had to catch its own bug and retry.

The core idea is a cycle: generate a solution, compile it, run the samples, and if something goes wrong, feed the exact failure back to the model and try again. LangGraph makes this loop explicit and easy to reason about — each step is a node, the retry logic is just a conditional edge.

---

## How it works — the flow

```
                        ┌──────────────────┐
                        │   START (input)  │
                        │   problem_id     │
                        └────────┬─────────┘
                                 │
                                 ▼
                    ┌────────────────────────┐
                    │    fetch_problem        │
                    │  • scrape CF HTML       │
                    │  • extract statement    │
                    │  • extract sample I/O   │
                    └────────────┬───────────┘
                                 │
                                 ▼
               ┌─────────────────────────────────┐
               │       generate_solution          │◄────────────────────┐
               │  • system prompt: expert CP      │                     │
               │  • if error_trace: include it    │                     │
               │  • LLM outputs raw C++ code      │                     │
               └──────────────┬──────────────────┘                     │
                              │                                         │
                              ▼                                         │
               ┌──────────────────────────────────┐                    │
               │       compile_and_test            │                    │
               │  • g++ -O2 -std=c++17             │                    │
               │  • run each sample test case      │                    │
               │  • compare output token-by-token  │                    │
               └──────────────┬───────────────────┘                    │
                              │                                         │
                              ▼                                         │
               ┌──────────────────────────────────┐                    │
               │         judge() router            │                    │
               └──────┬───────────────┬────────────┘                   │
                      │               │                                 │
               verdict=AC      verdict=WA/CE/TLE                        │
               or FAILED         (attempt < 5)                          │
                      │               │                                 │
                      ▼               ▼                                 │
               ┌──────────┐   ┌───────────────────┐                    │
               │   END    │   │    self_heal        │                   │
               │(AC/FAIL) │   │  • enrich trace     │                   │
               └──────────┘   │  • add TLE hint     │                   │
                              └─────────┬────────────┘                  │
                                        │                                │
                                        └────────────────────────────────┘
                                             (loops back to generate)
```

The cycle can repeat up to 5 times per problem. In practice, most problems were solved on the first attempt. The self-healing kicked in on 891A, where the model accidentally wrote Python-style `//` division inside C++ code — the compiler error went straight back into the next prompt and the model fixed it immediately.

---

## The nodes

**fetch_problem** — takes a problem ID like `1700A`, builds the Codeforces URL, scrapes the HTML, and pulls out the problem statement and sample test cases. Nothing fancy here, just requests + a custom HTML parser targeting the `.problem-statement` div. This initializes the state for everything downstream.

**generate_solution** — this is where the LLM does its job. On the first attempt it gets a clean prompt: the problem statement, constraints, and sample I/O. On retries it also gets its own previous code and the exact failure — compiler stderr for CE, or a diff of input/expected/got for WA. The system prompt tells the model to output raw C++17 only, no markdown, no explanation.

**compile_and_test** — writes the code to a temp file, compiles with `g++ -O2 -std=c++17`, and runs each sample test case with a 5-second timeout. Comparison is token-level (same as how the actual CF judge works), so trailing whitespace and newlines don't cause false failures. If anything goes wrong it builds a detailed error trace that gets stored in state.

**judge** — a simple router, not an LLM call. If the verdict is AC, we're done. If we've hit the attempt limit, we give up. Otherwise, route to self_heal. The control flow here is deterministic Python, not model-driven — this is intentional (more on this below).

**self_heal** — enriches the error trace before looping back. For TLE it adds an explicit hint about time complexity. For CE/WA the trace from compile_and_test is already detailed enough. Then it routes back to generate_solution with all that context in state.

---

## State

Everything the agent knows at any point in time lives in one TypedDict:

```python
class SolverState(TypedDict):
    problem_id: str          # e.g. "1700A"
    problem_url: str         # full CF URL
    problem_statement: str   # scraped text, capped at 8000 chars
    sample_inputs: list[str]
    sample_outputs: list[str]
    solution_code: str       # latest C++ attempt
    compile_error: str       # g++ stderr if CE
    run_results: list[dict]  # per-case: {input, expected, got, passed}
    verdict: str             # PENDING | AC | WA | CE | TLE | FAILED
    attempt: int             # how many times we've tried
    error_trace: str         # fed back to the LLM on retry
    final_solution: str      # set only on AC
```

LangGraph passes this dict through every node. Nodes read what they need and write back what they produce. The error_trace field is essentially the agent's short-term memory — it carries the failure context from compile_and_test all the way back to generate_solution on the next cycle.

---

## A real example of self-healing

Problem 891A, attempt 1: the model generated this line inside C++ code —

```cpp
ans = min(n, b // (m - a) + 1) * a + ...
```

`//` is Python floor division. C++ doesn't have it. The compiler threw an error. The agent caught the stderr, put it in error_trace, and on attempt 2 the model produced:

```cpp
ans = min(n, b/(m-a) + 1)*a + max(0, n - min(n, b/(m-a) + 1))*min(n, b/m);
```

AC.

---

## Why a workflow, not a full agent

The LangGraph docs make a distinction between workflows (control flow decided by code) and agents (control flow decided by the LLM). This system is deliberately a workflow.

The routing logic — compile after generating, test after compiling, retry on failure — is completely predictable. There's no reason to ask an LLM what to do next. Letting the model drive the control flow would add latency, cost, and unpredictability without any real benefit. The LLM is only used where it actually adds value: writing and fixing code.

---

## File structure

```
week 3/
├── agent.py          ← LangGraph graph + all node logic
├── harness.py        ← CLI test runner, JSON export
├── requirements.txt
└── ARCHITECTURE.md   ← this file
```

---

## Running it

```bash
# install dependencies
pip install -r requirements.txt

# set your API key (PowerShell)
$env:GROQ_API_KEY = "your-key-here"

# solve one problem
python harness.py 1700A

# run a batch
python harness.py 1511C 1610B 414B

# run everything and export a report
python harness.py --export results.json
```

---

## Problems solved — official evaluation sheet

Ran the agent against all 24 problems from the test sheet. Results below.

| # | Problem | Rating | Link | Result |
|---|---------|--------|------|--------|
| 1 | 1511C | 1100 | https://codeforces.com/problemset/problem/1511/C | AC (1 attempt) |
| 2 | 1610B | 1100 | https://codeforces.com/problemset/problem/1610/B | AC (1 attempt) |
| 3 | 414B | 1400 | https://codeforces.com/problemset/problem/414/B | AC (1 attempt) |
| 4 | 1167C | 1400 | https://codeforces.com/problemset/problem/1167/C | AC (1 attempt) |
| 5 | 1350B | 1400 | https://codeforces.com/problemset/problem/1350/B | AC (1 attempt) |
| 6 | 845C | 1500 | https://codeforces.com/problemset/problem/845/C | AC (1 attempt) |
| 7 | 1101C | 1500 | https://codeforces.com/problemset/problem/1101/C | AC (1 attempt) |
| 8 | 891A | 1500 | https://codeforces.com/problemset/problem/891/A | AC (2 attempts — self-healed CE) |
| 9 | 1084C | 1500 | https://codeforces.com/problemset/problem/1084/C | AC (1 attempt) |
| 10 | 1106D | 1500 | https://codeforces.com/problemset/problem/1106/D | AC (1 attempt) |
| 11 | 1475E | 1600 | https://codeforces.com/problemset/problem/1475/E | AC (1 attempt) |
| 12 | 1610C | 1600 | https://codeforces.com/problemset/problem/1610/C | AC (1 attempt) |
| 13 | 1775C | 1600 | https://codeforces.com/problemset/problem/1775/C | AC (1 attempt) |
| 14 | 1516C | 1700 | https://codeforces.com/problemset/problem/1516/C | AC (1 attempt) |
| 15 | 1598D | 1700 | https://codeforces.com/problemset/problem/1598/D | AC (1 attempt) |
| 16 | 1625C | 1700 | https://codeforces.com/problemset/problem/1625/C | AC (1 attempt) |
| 17 | 1792D | 1700 | https://codeforces.com/problemset/problem/1792/D | AC (1 attempt) |
| 18 | 1893B | 1700 | https://codeforces.com/problemset/problem/1893/B | AC (1 attempt) |
| 19 | 1290B | 1800 | https://codeforces.com/problemset/problem/1290/B | AC (1 attempt) |
| 20 | 1338B | 1800 | https://codeforces.com/problemset/problem/1338/B | AC (1 attempt) |
| 21 | 1509C | 1800 | https://codeforces.com/problemset/problem/1509/C | AC (1 attempt) |
| 22 | 2044F | 1900 | https://codeforces.com/problemset/problem/2044/F | AC (1 attempt) |
| 23 | 2014H | 1900 | https://codeforces.com/problemset/problem/2014/H | AC (1 attempt) |
| 24 | 1925D | 1900 | https://codeforces.com/problemset/problem/1925/D | AC (1 attempt) |

24/24. The self-healing loop only had to fire once across the entire run.

Additional problems can be found via the [TLE Eliminators CP Sheet](https://www.tle-eliminators.com/cp-sheet) or the [Codeforces API](https://codeforces.com/apiHelp).

---

## Some notes on design choices

**C++ over Python** — CF gives C++ a faster time limit than Python for the same problem. An O(n²) solution that scrapes through in C++ will TLE in Python. Since we're targeting higher-rated problems where the intended solution might be tight on time, C++ was the obvious call.

**Token-level output comparison** — The actual Codeforces judge compares output token by token, not character by character. Matching that behavior in the local harness means a solution that passes locally is very likely to pass on the real judge too. Doing string comparison would cause false WA verdicts on things like trailing newlines.

**Capping the statement at 8000 characters** — Some CF problems have very long statements with elaborate stories. The actual constraint and sample sections are always near the top. Capping at 8000 chars keeps the context window manageable without losing anything the model actually needs.

**MAX_ATTEMPTS = 5** — If the model can't fix a problem in 5 tries, throwing more retries at it rarely helps. The failure is usually architectural (wrong algorithm) rather than a small bug. Keeping this low also keeps API costs predictable.

**self_heal as a separate node** — It would have been easy to just loop directly from compile_and_test back to generate_solution. Making self_heal its own node keeps the graph readable and makes it easy to upgrade later — for example, adding a step where the model first explains what went wrong before attempting a fix.
