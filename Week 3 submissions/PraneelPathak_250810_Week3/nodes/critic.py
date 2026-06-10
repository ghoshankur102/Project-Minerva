from llm_router import call_critic
from langchain_core.messages import HumanMessage
from utils.run_logger import save_step


def critic_node(state):

    if state.get("solved", False):
        print("Problem already solved. No reflection needed.")
        return state
    
    prompt = f"""
You are a highly experienced Codeforces competitor and code reviewer.

A generated solution failed during testing.

Problem:
{state.get("problem", "")}

Plan:
{state.get("plan", "")}

Code:
{state.get("code", "")}

Compiled Successfully:
{state.get("compiled", False)}

Compiler Output:
{state.get("compile_output", "")}

Expected Output:
{state.get("expected_output", "")}

Actual Output:
{state.get("run_stdout", "")}

Runtime Errors:
{state.get("run_stderr", "")}

========================
TASK
========================

Determine:

1. FAILURE_TYPE
Choose exactly one:
- Compilation Error
- Runtime Error
- Wrong Answer
- Logic Error
- Edge Case Failure

2. ROOT_CAUSE
Explain precisely what went wrong.

3. FIX_STRATEGY
Describe the exact modifications needed to fix the solution.

4. CONFIDENCE
Give a confidence score from 1-10.

Return your answer in exactly this format:

FAILURE_TYPE:
...

ROOT_CAUSE:
...

FIX_STRATEGY:
...

CONFIDENCE:
...
"""

    result = call_critic([HumanMessage(content=prompt)])

    state["reflection"] = result

    save_step(state["run_folder"], "critic", state)
    
    print("Reflection complete. State updated and saved.")

    return state