"""
Stateful, Cyclic Self-Healing Competitive Programming AI Agent
Built with LangGraph - Solves Codeforces problems (1500-1700+ difficulty)
"""

import os
import re
import json
import subprocess
import tempfile
import time
from typing import TypedDict, Annotated, List, Optional, Dict, Any
from enum import Enum

# LangGraph imports
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

# G
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import SystemMessage, HumanMessage

# ─────────────────────────────────────────────
# STATE DEFINITION
# ─────────────────────────────────────────────

class AgentPhase(str, Enum):
    PARSE        = "parse"
    PLAN         = "plan"
    CODE         = "code"
    TEST         = "test"
    DEBUG        = "debug"
    OPTIMIZE     = "optimize"
    DONE         = "done"
    FAILED       = "failed"


class CPAgentState(TypedDict):
    # Problem context
    problem_id:         str
    problem_title:      str
    problem_statement:  str
    problem_rating:     int
    time_limit_ms:      int
    memory_limit_mb:    int
    sample_inputs:      List[str]
    sample_outputs:     List[str]

    # Agent reasoning
    analysis:           str          # problem analysis / strategy
    algorithm_plan:     str          # high-level algorithm plan
    solution_code:      str          # generated C++ code
    language:           str          # "cpp" or "python"

    # Self-healing state
    phase:              str          # current AgentPhase
    attempt:            int          # how many code-gen attempts
    max_attempts:       int
    compile_error:      str
    runtime_error:      str
    wrong_answer_info:  str
    tle_info:           str
    debug_notes:        List[str]    # accumulated debug history

    # Results
    test_results:       List[Dict]   # per-test-case results
    all_tests_passed:   bool
    final_verdict:      str


# ─────────────────────────────────────────────
# GEMINI API WRAPPER (Kept original name to avoid breaking changes)
# ─────────────────────────────────────────────

# ─────────────────────────────────────────────
# GEMINI API WRAPPER (Kept original name to avoid breaking changes)
# ─────────────────────────────────────────────

def call_claude(system_prompt: str, user_prompt: str, max_tokens: int = 4096) -> str:
    """Call Gemini with robust handling for rate limits, connection drops, and handshakes."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        temperature=0.2,
        max_tokens=max_tokens,
        google_api_key=api_key,
        timeout=30  # Gives slow SSL handshakes on local networks enough room to breathe
    )
    
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=user_prompt)
    ]
    
    # Try up to 5 times for any transient network/API issues
    for attempt in range(5):
        try:
            response = llm.invoke(messages)
            return str(response.content)
        except Exception as e:
            # Captures timeouts, handshake drops, or 429 rate limits unconditionally
            print(f"\n⏳ [Network/API Notice] Connection hitch encountered ({type(e).__name__}).")
            print(f"Sleeping 25 seconds to clear the line before retry (Attempt {attempt + 1}/5)...")
            time.sleep(25)
                
    raise Exception("System paused: Gemini API connectivity limits exceeded after maximum retries.")
# ─────────────────────────────────────────────

def parse_problem_node(state: CPAgentState) -> CPAgentState:
    """
    Parse the raw problem statement to extract structured information.
    """
    system = """You are an expert competitive programmer. 
    Parse the provided Codeforces problem and extract:
    1. A clean problem statement
    2. All sample inputs (as a JSON array of strings)
    3. All sample outputs (as a JSON array of strings)
    4. Time limit in milliseconds (integer)
    5. Memory limit in MB (integer)
    
    Return ONLY valid JSON with keys:
    {
      "clean_statement": "...",
      "sample_inputs": ["input1", "input2"],
      "sample_outputs": ["output1", "output2"],
      "time_limit_ms": 2000,
      "memory_limit_mb": 256
    }"""

    user = f"""Problem ID: {state['problem_id']}
Problem Rating: {state.get('problem_rating', 1500)}

Raw Problem Statement:
{state['problem_statement']}"""

    raw = call_claude(system, user, max_tokens=2048)
    
    # Strip possible markdown fences
    raw = re.sub(r"```json|```", "", raw).strip()
    
    try:
        parsed = json.loads(raw)
        return {
            **state,
            "problem_statement": parsed.get("clean_statement", state["problem_statement"]),
            "sample_inputs":     parsed.get("sample_inputs", []),
            "sample_outputs":    parsed.get("sample_outputs", []),
            "time_limit_ms":     parsed.get("time_limit_ms", state.get("time_limit_ms", 2000)),
            "memory_limit_mb":   parsed.get("memory_limit_mb", state.get("memory_limit_mb", 256)),
            "phase":             AgentPhase.PLAN,
            "attempt":           0,
            "debug_notes":       [],
        }
    except json.JSONDecodeError:
        # Fallback: keep existing state, just advance phase
        return {
            **state,
            "phase":       AgentPhase.PLAN,
            "attempt":     0,
            "debug_notes": [],
        }


# ─────────────────────────────────────────────
# NODE: PLAN / ANALYSE
# ─────────────────────────────────────────────

def plan_node(state: CPAgentState) -> CPAgentState:
    """
    Analyse the problem and devise an algorithm plan.
    Uses chain-of-thought reasoning to identify the correct approach.
    """
    debug_context = ""
    if state.get("debug_notes"):
        debug_context = "\n\nPrevious failed attempts and notes:\n" + "\n".join(state["debug_notes"])

    system = """You are a world-class competitive programmer (grandmaster level).
    Analyse the problem carefully and produce:
    1. Problem category (DP, Graph, Greedy, Math, Segment Tree, etc.)
    2. Key observations / invariants
    3. Algorithm choice with justification
    4. Time/space complexity analysis
    5. Edge cases to handle
    6. Step-by-step implementation plan
    
    Think deeply. Be precise. Your plan will be used to generate the final code."""

    user = f"""Problem: {state['problem_id']} (Rating: {state.get('problem_rating', 1500)})

{state['problem_statement']}

Time limit: {state.get('time_limit_ms', 2000)}ms  Memory: {state.get('memory_limit_mb', 256)}MB
{debug_context}

Provide a thorough analysis and algorithm plan."""

    plan = call_claude(system, user, max_tokens=3000)

    return {
        **state,
        "algorithm_plan": plan,
        "analysis":       plan,
        "phase":          AgentPhase.CODE,
    }


# ─────────────────────────────────────────────
# NODE: GENERATE CODE
# ─────────────────────────────────────────────

def code_node(state: CPAgentState) -> CPAgentState:
    """
    Generate C++ solution code based on the algorithm plan.
    Includes self-healing context from previous attempts.
    """
    error_context = _build_error_context(state)
    prev_code = f"\n\nPrevious code (attempt {state['attempt']}):\n```cpp\n{state.get('solution_code', '')}\n```" if state.get("solution_code") else ""

    system = """You are an expert competitive programmer writing production-quality C++ code.

Rules:
- Use C++17 features freely
- Always include necessary headers (use #include <bits/stdc++.h>)
- Use fast I/O: ios_base::sync_with_stdio(false); cin.tie(NULL);
- Handle all edge cases mentioned in the analysis
- Write clean, correct, efficient code
- Output ONLY the complete C++ code — no explanations, no markdown fences
- The code must compile with: g++ -O2 -o sol sol.cpp"""

    user = f"""Problem: {state['problem_id']}

{state['problem_statement']}

Algorithm Plan:
{state['algorithm_plan']}

Time limit: {state.get('time_limit_ms', 2000)}ms  Memory: {state.get('memory_limit_mb', 256)}MB
{error_context}
{prev_code}

Write the complete, correct C++ solution:"""

    code = call_claude(system, user, max_tokens=4096)
    
    # Strip any accidental markdown fences
    code = re.sub(r"```(?:cpp|c\+\+)?", "", code)
    code = re.sub(r"```", "", code).strip()

    return {
        **state,
        "solution_code": code,
        "language":      "cpp",
        "phase":         AgentPhase.TEST,
        "attempt":       state.get("attempt", 0) + 1,
        "compile_error": "",
        "runtime_error": "",
        "wrong_answer_info": "",
        "tle_info":      "",
    }


def _build_error_context(state: CPAgentState) -> str:
    parts = []
    if state.get("compile_error"):
        parts.append(f"COMPILE ERROR to fix:\n{state['compile_error']}")
    if state.get("runtime_error"):
        parts.append(f"RUNTIME ERROR to fix:\n{state['runtime_error']}")
    if state.get("wrong_answer_info"):
        parts.append(f"WRONG ANSWER details:\n{state['wrong_answer_info']}")
    if state.get("tle_info"):
        parts.append(f"TIME LIMIT EXCEEDED - need to optimize:\n{state['tle_info']}")
    return ("\n\n" + "\n\n".join(parts)) if parts else ""


# ─────────────────────────────────────────────
# NODE: TEST / VALIDATE
# ─────────────────────────────────────────────

def test_node(state: CPAgentState) -> CPAgentState:
    """
    Compile and run the solution against all sample test cases.
    Produces structured test results for the self-healing loop.
    """
    code    = state.get("solution_code", "")
    inputs  = state.get("sample_inputs", [])
    outputs = state.get("sample_outputs", [])
    tl_sec  = state.get("time_limit_ms", 2000) / 1000.0

    if not code:
        return {**state, "phase": AgentPhase.DEBUG,
                "compile_error": "No code generated"}

    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = os.path.join(tmpdir, "sol.cpp")
        bin_path = os.path.join(tmpdir, "sol")

        with open(src_path, "w") as f:
            f.write(code)

        # ── Compile ──
        compile_result = subprocess.run(
            ["g++", "-O2", "-std=c++17", "-o", bin_path, src_path],
            capture_output=True, text=True, timeout=30
        )
        if compile_result.returncode != 0:
            return {
                **state,
                "phase":         AgentPhase.DEBUG,
                "compile_error": compile_result.stderr[:2000],
            }

        # ── Run each sample test ──
        test_results = []
        all_passed   = True

        for i, (inp, expected) in enumerate(zip(inputs, outputs)):
            try:
                run = subprocess.run(
                    [bin_path],
                    input=inp, capture_output=True, text=True,
                    timeout=tl_sec + 1.0
                )
                actual = run.stdout.strip()
                exp    = expected.strip()

                if run.returncode != 0:
                    test_results.append({
                        "case": i + 1, "status": "RE",
                        "input": inp, "expected": exp,
                        "actual": run.stderr[:500]
                    })
                    all_passed = False
                elif actual == exp:
                    test_results.append({
                        "case": i + 1, "status": "AC",
                        "input": inp, "expected": exp, "actual": actual
                    })
                else:
                    test_results.append({
                        "case": i + 1, "status": "WA",
                        "input": inp, "expected": exp, "actual": actual
                    })
                    all_passed = False

            except subprocess.TimeoutExpired:
                test_results.append({
                    "case": i + 1, "status": "TLE",
                    "input": inp, "expected": expected, "actual": "TIMEOUT"
                })
                all_passed = False

        # Determine next phase
        if all_passed:
            return {
                **state,
                "test_results":    test_results,
                "all_tests_passed": True,
                "phase":           AgentPhase.DONE,
                "final_verdict":   "ALL_SAMPLE_TESTS_PASSED",
            }
        else:
            # Collect error info for debugger
            wa_cases  = [r for r in test_results if r["status"] == "WA"]
            re_cases  = [r for r in test_results if r["status"] == "RE"]
            tle_cases = [r for r in test_results if r["status"] == "TLE"]

            wrong_answer_info = ""
            runtime_error     = ""
            tle_info          = ""

            if wa_cases:
                wrong_answer_info = "\n".join(
                    f"Case {r['case']}: input={r['input']!r} expected={r['expected']!r} got={r['actual']!r}"
                    for r in wa_cases[:3]
                )
            if re_cases:
                runtime_error = "\n".join(
                    f"Case {r['case']}: {r['actual']}"
                    for r in re_cases[:2]
                )
            if tle_cases:
                tle_info = f"{len(tle_cases)} test(s) exceeded time limit"

            return {
                **state,
                "test_results":      test_results,
                "all_tests_passed":  False,
                "wrong_answer_info": wrong_answer_info,
                "runtime_error":     runtime_error,
                "tle_info":          tle_info,
                "phase":             AgentPhase.DEBUG,
            }


# ─────────────────────────────────────────────
# NODE: DEBUG / SELF-HEAL
# ─────────────────────────────────────────────

def debug_node(state: CPAgentState) -> CPAgentState:
    """
    Analyse failures and produce targeted fix instructions.
    This is the self-healing core of the agent.
    """
    error_summary = _build_error_context(state)

    system = """You are a debugging expert for competitive programming.
    Analyse the error and produce:
    1. Root cause diagnosis
    2. Specific fix instructions (concrete, actionable)
    3. Whether the algorithm needs to change or just the implementation

    Be concise and direct. Your output will be appended to debug_notes and
    used in the next code-generation attempt."""

    user = f"""Problem: {state['problem_id']}
Attempt: {state['attempt']} / {state['max_attempts']}

Algorithm Plan:
{state['algorithm_plan']}

Current Code:
```cpp
{state.get('solution_code', 'N/A')}
```

{error_summary}

Diagnose and provide exact fix instructions:"""

    diagnosis = call_claude(system, user, max_tokens=2000)

    notes = list(state.get("debug_notes", []))
    notes.append(f"[Attempt {state['attempt']}] {diagnosis}")

    # Decide: retry code generation or give up
    max_att = state.get("max_attempts", 5)
    if state["attempt"] >= max_att:
        return {
            **state,
            "debug_notes":    notes,
            "phase":          AgentPhase.FAILED,
            "final_verdict":  f"FAILED after {state['attempt']} attempts",
        }

    # Check if algorithm needs a full rethink (re-plan)
    needs_replan = any(kw in diagnosis.lower() for kw in [
        "wrong algorithm", "different approach", "rethink", "fundamentally",
        "time complexity", "tle", "completely wrong"
    ])

    next_phase = AgentPhase.PLAN if needs_replan else AgentPhase.CODE
    return {
        **state,
        "debug_notes": notes,
        "phase":       next_phase,
    }


# ─────────────────────────────────────────────
# NODE: OPTIMIZE (TLE recovery)
# ─────────────────────────────────────────────

def optimize_node(state: CPAgentState) -> CPAgentState:
    """
    Dedicated optimization pass when TLE is detected after correctness confirmed.
    """
    system = """You are a performance optimization expert for competitive programming.
    The solution is logically correct but too slow. Optimize it:
    - Reduce time complexity if possible
    - Optimize constants (avoid unnecessary copies, use arrays vs vectors where helpful)
    - Consider memoization, precomputation, better data structures
    - Use __builtin functions where applicable
    
    Output ONLY the optimized C++ code, no explanations."""

    user = f"""Problem: {state['problem_id']}
Time limit: {state.get('time_limit_ms', 2000)}ms

Original code (too slow):
```cpp
{state.get('solution_code', '')}
```

Algorithm Plan:
{state['algorithm_plan']}

TLE Info: {state.get('tle_info', '')}

Provide optimized solution:"""

    code = call_claude(system, user, max_tokens=4096)
    code = re.sub(r"```(?:cpp|c\+\+)?|```", "", code).strip()

    return {
        **state,
        "solution_code": code,
        "phase":         AgentPhase.TEST,
        "tle_info":      "",
    }


# ─────────────────────────────────────────────
# ROUTING LOGIC
# ─────────────────────────────────────────────

def route(state: CPAgentState) -> str:
    """Central router based on current phase."""
    phase = state.get("phase", AgentPhase.PARSE)
    return phase


# ─────────────────────────────────────────────
# BUILD THE LANGGRAPH
# ─────────────────────────────────────────────

def build_graph() -> StateGraph:
    workflow = StateGraph(CPAgentState)

    # Register nodes
    workflow.add_node("parse",    parse_problem_node)
    workflow.add_node("plan",     plan_node)
    workflow.add_node("code",     code_node)
    workflow.add_node("test",     test_node)
    workflow.add_node("debug",    debug_node)
    workflow.add_node("optimize", optimize_node)

    # Entry point
    workflow.set_entry_point("parse")

    # Edges from parse → plan (always)
    workflow.add_edge("parse", "plan")

    # plan → code (always)
    workflow.add_edge("plan", "code")

    # code → test (always)
    workflow.add_edge("code", "test")

    # test → conditional (done / debug / optimize)
    workflow.add_conditional_edges(
        "test",
        route,
        {
            AgentPhase.DONE:     END,
            AgentPhase.DEBUG:    "debug",
            AgentPhase.OPTIMIZE: "optimize",
        }
    )

    # debug → conditional (plan / code / failed)
    workflow.add_conditional_edges(
        "debug",
        route,
        {
            AgentPhase.PLAN:   "plan",
            AgentPhase.CODE:   "code",
            AgentPhase.FAILED: END,
        }
    )

    # optimize → test
    workflow.add_edge("optimize", "test")

    return workflow.compile()


# ─────────────────────────────────────────────
# PUBLIC API
# ─────────────────────────────────────────────

def solve_problem(
    problem_id:        str,
    problem_title:     str,
    problem_statement: str,
    problem_rating:    int  = 1500,
    time_limit_ms:     int  = 2000,
    memory_limit_mb:   int  = 256,
    sample_inputs:     List[str] = None,
    sample_outputs:    List[str] = None,
    max_attempts:      int  = 5,
) -> Dict[str, Any]:
    """
    Solve a single Codeforces problem.
    Returns a dict with solution_code, verdict, test_results, debug_notes.
    """
    graph = build_graph()

    initial_state: CPAgentState = {
        "problem_id":        problem_id,
        "problem_title":     problem_title,
        "problem_statement": problem_statement,
        "problem_rating":    problem_rating,
        "time_limit_ms":     time_limit_ms,
        "memory_limit_mb":   memory_limit_mb,
        "sample_inputs":     sample_inputs or [],
        "sample_outputs":    sample_outputs or [],
        "analysis":          "",
        "algorithm_plan":    "",
        "solution_code":     "",
        "language":          "cpp",
        "phase":             AgentPhase.PARSE,
        "attempt":           0,
        "max_attempts":      max_attempts,
        "compile_error":     "",
        "runtime_error":     "",
        "wrong_answer_info": "",
        "tle_info":          "",
        "debug_notes":       [],
        "test_results":      [],
        "all_tests_passed":  False,
        "final_verdict":     "",
    }

    final_state = graph.invoke(initial_state)

    return {
        "problem_id":       problem_id,
        "solution_code":    final_state.get("solution_code", ""),
        "language":         final_state.get("language", "cpp"),
        "verdict":          final_state.get("final_verdict", "UNKNOWN"),
        "all_tests_passed": final_state.get("all_tests_passed", False),
        "test_results":     final_state.get("test_results", []),
        "debug_notes":      final_state.get("debug_notes", []),
        "attempts":         final_state.get("attempt", 0),
        "algorithm_plan":   final_state.get("algorithm_plan", ""),
    }
