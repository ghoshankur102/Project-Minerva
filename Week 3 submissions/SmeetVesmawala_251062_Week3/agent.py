"""
Codeforces Autonomous Solver - LangGraph Stateful Cyclic Self-Healing Agent
============================================================================
Architecture:
  fetch_problem → generate_solution → compile_test → judge
                         ↑                                 |
                         └─────── self_heal ←─────────────┘ (on WA/TLE/CE)
"""

import os
import re
import subprocess
import tempfile
import time
from typing import Annotated, TypedDict

import requests
from langchain_groq import ChatGroq
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph

# ── Model ──────────────────────────────────────────────────────────────────────
llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    max_tokens=4096,
    api_key=os.environ.get("GROQ_API_KEY", ""),
)

MAX_ATTEMPTS = 5   # max self-heal cycles per problem
COMPILE_TIMEOUT = 10   # seconds
RUN_TIMEOUT = 5        # seconds per test case

# ── State ──────────────────────────────────────────────────────────────────────
class SolverState(TypedDict):
    problem_id: str          # e.g. "1700A"
    problem_url: str
    problem_statement: str   # full text scraped from CF
    sample_inputs: list[str]
    sample_outputs: list[str]
    solution_code: str       # latest C++ solution
    compile_error: str
    run_results: list[dict]  # [{input, expected, got, passed}]
    verdict: str             # PENDING / AC / WA / CE / TLE / FAILED
    attempt: int
    error_trace: str         # fed back to LLM for self-heal
    final_solution: str


# ── Node 1: Fetch Problem ──────────────────────────────────────────────────────
def fetch_problem(state: SolverState) -> SolverState:
    """Scrape problem statement + sample I/O from Codeforces."""
    pid = state["problem_id"]
    # Parse contest id and problem letter  e.g. 1700A → 1700 / A
    match = re.match(r"(\d+)([A-Za-z]\d*)", pid)
    if not match:
        state["verdict"] = "FAILED"
        state["error_trace"] = f"Cannot parse problem id: {pid}"
        return state

    contest_id, prob_letter = match.group(1), match.group(2).upper()
    url = f"https://codeforces.com/contest/{contest_id}/problem/{prob_letter}"
    state["problem_url"] = url

    print(f"[FETCH] {pid} → {url}")
    try:
        resp = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
    except Exception as e:
        state["verdict"] = "FAILED"
        state["error_trace"] = f"Network error: {e}"
        return state

    html = resp.text

    # Extract problem statement (rough but reliable)
    statement = _extract_statement(html)
    samples_in, samples_out = _extract_samples(html)

    state["problem_statement"] = statement
    state["sample_inputs"] = samples_in
    state["sample_outputs"] = samples_out
    state["verdict"] = "PENDING"
    state["attempt"] = 0
    state["error_trace"] = ""
    state["solution_code"] = ""
    state["run_results"] = []
    return state


def _extract_statement(html: str) -> str:
    """Pull readable problem text from raw HTML."""
    from html.parser import HTMLParser

    class TextExtractor(HTMLParser):
        def __init__(self):
            super().__init__()
            self.in_statement = False
            self.depth = 0
            self.parts = []

        def handle_starttag(self, tag, attrs):
            attrs_dict = dict(attrs)
            cls = attrs_dict.get("class", "")
            if "problem-statement" in cls:
                self.in_statement = True
                self.depth = 1
            elif self.in_statement:
                self.depth += 1

        def handle_endtag(self, tag):
            if self.in_statement:
                self.depth -= 1
                if self.depth <= 0:
                    self.in_statement = False

        def handle_data(self, data):
            if self.in_statement:
                self.parts.append(data)

    extractor = TextExtractor()
    extractor.feed(html)
    text = " ".join(extractor.parts)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text[:8000]  # cap to avoid huge context


def _extract_samples(html: str) -> tuple[list[str], list[str]]:
    """Extract sample test inputs and outputs."""
    # CF wraps them in <pre> inside .sample-test
    inputs, outputs = [], []

    sample_section_match = re.search(
        r'class="sample-test">(.*?)</div>\s*</div>',
        html,
        re.DOTALL,
    )
    if not sample_section_match:
        return inputs, outputs

    section = sample_section_match.group(1)
    pre_blocks = re.findall(r"<pre>(.*?)</pre>", section, re.DOTALL)

    # Alternate: input, output, input, output ...
    for i, block in enumerate(pre_blocks):
        # Remove inner tags
        clean = re.sub(r"<[^>]+>", "", block).strip()
        # Unescape HTML entities
        clean = clean.replace("&lt;", "<").replace("&gt;", ">").replace("&amp;", "&")
        if i % 2 == 0:
            inputs.append(clean)
        else:
            outputs.append(clean)

    return inputs, outputs


# ── Node 2: Generate Solution ──────────────────────────────────────────────────
SYSTEM_PROMPT = """You are an expert competitive programmer. You ONLY output raw C++ code — no markdown, no explanation, no triple backticks.

Rules:
- Use C++17. Start with the includes and using namespace std;
- For each test case read from stdin, write to stdout.
- Handle multiple test cases with a t variable when the problem says so.
- The code must be self-contained and compilable with: g++ -O2 -std=c++17 solution.cpp
- Think carefully about edge cases, constraints, and time complexity before writing.
"""

def generate_solution(state: SolverState) -> SolverState:
    """Ask LLM to produce a C++ solution."""
    attempt = state["attempt"]
    print(f"[GENERATE] attempt {attempt + 1}/{MAX_ATTEMPTS}")

    problem_ctx = f"""
Problem ID: {state['problem_id']}
URL: {state['problem_url']}

Problem Statement:
{state['problem_statement']}

Sample Inputs:
{chr(10).join(f'--- Input {i+1} ---{chr(10)}{s}' for i, s in enumerate(state['sample_inputs']))}

Sample Outputs:
{chr(10).join(f'--- Output {i+1} ---{chr(10)}{s}' for i, s in enumerate(state['sample_outputs']))}
"""

    if state["error_trace"]:
        problem_ctx += f"""
PREVIOUS ATTEMPT FAILED.
Your last solution:
```cpp
{state['solution_code']}
```

Failure reason:
{state['error_trace']}

Fix the solution. Output only corrected C++ code.
"""
    else:
        problem_ctx += "\nWrite a correct, efficient C++ solution."

    messages = [
        SystemMessage(content=SYSTEM_PROMPT),
        HumanMessage(content=problem_ctx),
    ]

    response = llm.invoke(messages)
    code = response.content.strip()

    # Strip accidental markdown fences
    code = re.sub(r"^```(?:cpp|c\+\+)?\s*", "", code, flags=re.MULTILINE)
    code = re.sub(r"^```\s*$", "", code, flags=re.MULTILINE)
    code = code.strip()

    state["solution_code"] = code
    state["attempt"] = attempt + 1
    return state


# ── Node 3: Compile & Test ─────────────────────────────────────────────────────
def compile_and_test(state: SolverState) -> SolverState:
    """Compile the C++ code and run sample test cases."""
    code = state["solution_code"]

    with tempfile.TemporaryDirectory() as tmpdir:
        src = os.path.join(tmpdir, "solution.cpp")
        exe = os.path.join(tmpdir, "solution")

        with open(src, "w") as f:
            f.write(code)

        # Compile
        compile_result = subprocess.run(
            ["g++", "-O2", "-std=c++17", "-o", exe, src],
            capture_output=True,
            text=True,
            timeout=COMPILE_TIMEOUT,
        )

        if compile_result.returncode != 0:
            state["verdict"] = "CE"
            state["compile_error"] = compile_result.stderr
            state["error_trace"] = f"Compilation Error:\n{compile_result.stderr}"
            print(f"[CE] {compile_result.stderr[:300]}")
            return state

        state["compile_error"] = ""

        # Run each sample
        run_results = []
        all_passed = True

        for i, (inp, expected) in enumerate(
            zip(state["sample_inputs"], state["sample_outputs"])
        ):
            try:
                run = subprocess.run(
                    [exe],
                    input=inp,
                    capture_output=True,
                    text=True,
                    timeout=RUN_TIMEOUT,
                )
                got = run.stdout.strip()
                expected_clean = expected.strip()
                passed = _outputs_match(got, expected_clean)
            except subprocess.TimeoutExpired:
                got = "TLE"
                passed = False
                state["verdict"] = "TLE"
                all_passed = False
            except Exception as e:
                got = f"RTE: {e}"
                passed = False
                all_passed = False

            run_results.append(
                {
                    "case": i + 1,
                    "input": inp,
                    "expected": expected,
                    "got": got,
                    "passed": passed,
                }
            )
            if not passed:
                all_passed = False
            print(f"  [Case {i+1}] {'✓' if passed else '✗'}  got={repr(got[:80])}")

        state["run_results"] = run_results

        if all_passed:
            state["verdict"] = "AC"
            state["final_solution"] = code
            state["error_trace"] = ""
        elif state["verdict"] not in ("TLE",):
            state["verdict"] = "WA"
            # Build detailed error trace for self-heal
            failed = [r for r in run_results if not r["passed"]]
            trace_parts = []
            for r in failed:
                trace_parts.append(
                    f"Case {r['case']}:\n"
                    f"  Input:    {r['input'][:200]}\n"
                    f"  Expected: {r['expected'][:200]}\n"
                    f"  Got:      {r['got'][:200]}"
                )
            state["error_trace"] = (
                f"Wrong Answer on {len(failed)} sample(s):\n"
                + "\n".join(trace_parts)
            )

    return state


def _outputs_match(got: str, expected: str) -> bool:
    """Token-level comparison (handles trailing spaces / newlines)."""
    return got.split() == expected.split()


# ── Node 4: Judge (routing) ────────────────────────────────────────────────────
def judge(state: SolverState) -> str:
    """Decide next node based on verdict."""
    v = state["verdict"]
    if v == "AC":
        print(f"[JUDGE] ✓ AC after {state['attempt']} attempt(s)")
        return "accept"
    if state["attempt"] >= MAX_ATTEMPTS:
        print(f"[JUDGE] ✗ Giving up after {MAX_ATTEMPTS} attempts. Last: {v}")
        return "give_up"
    print(f"[JUDGE] → self_heal (verdict={v}, attempt={state['attempt']})")
    return "self_heal"


# ── Node 5: Self-Heal ──────────────────────────────────────────────────────────
def self_heal(state: SolverState) -> SolverState:
    """Analyze the failure and prepare context for re-generation."""
    # The error_trace is already set by compile_and_test.
    # This node can optionally do deeper analysis (e.g., ask LLM to diagnose).
    print(f"[SELF_HEAL] Diagnosing failure...")
    
    # For TLE: explicitly hint at complexity
    if state["verdict"] == "TLE":
        state["error_trace"] += (
            "\nYour solution exceeded the time limit. "
            "Consider a more efficient algorithm (reduce time complexity)."
        )

    # Loop back to generate_solution — the error_trace is in state
    return state


# ── Graph ──────────────────────────────────────────────────────────────────────
def build_graph() -> StateGraph:
    g = StateGraph(SolverState)

    g.add_node("fetch_problem", fetch_problem)
    g.add_node("generate_solution", generate_solution)
    g.add_node("compile_and_test", compile_and_test)
    g.add_node("self_heal", self_heal)

    g.set_entry_point("fetch_problem")
    g.add_edge("fetch_problem", "generate_solution")
    g.add_edge("generate_solution", "compile_and_test")
    g.add_conditional_edges(
        "compile_and_test",
        judge,
        {
            "accept": END,
            "give_up": END,
            "self_heal": "self_heal",
        },
    )
    g.add_edge("self_heal", "generate_solution")

    return g.compile()


# ── Public API ─────────────────────────────────────────────────────────────────
def solve(problem_id: str) -> SolverState:
    """Run the agent on a single problem. Returns final state."""
    graph = build_graph()
    initial: SolverState = {
        "problem_id": problem_id,
        "problem_url": "",
        "problem_statement": "",
        "sample_inputs": [],
        "sample_outputs": [],
        "solution_code": "",
        "compile_error": "",
        "run_results": [],
        "verdict": "PENDING",
        "attempt": 0,
        "error_trace": "",
        "final_solution": "",
    }
    result = graph.invoke(initial)
    return result
