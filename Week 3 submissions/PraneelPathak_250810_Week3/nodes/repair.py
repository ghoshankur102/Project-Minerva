from llm_router import call_repair
from langchain_core.messages import HumanMessage
from utils.run_logger import save_step
from utils.extract_code import extract_cpp_code


def repair_node(state):

    if state.get("solved", False):
        return state

    if not state.get("reflection"):
        raise ValueError("reflection missing from state")

    prompt = f"""
You are an expert competitive programmer.

A previously generated solution failed.

Problem:
{state.get("problem", "")}

Plan:
{state.get("plan", "")}

Failed Code:
{state.get("code", "")}

Failure Reflection:
{state.get("reflection", "")}

========================
TASK
========================

Generate a corrected C++17 solution.

Requirements:
- Fix the identified issue(s)
- Preserve correct parts of the solution
- Return ONLY valid C++17 code
- No markdown
- No explanations
- Must compile under g++17
"""

    result = call_repair([HumanMessage(content=prompt)])

    state["code"] = extract_cpp_code(result)

    state["attempts"] = state.get("attempts", 0) + 1

    save_step(state["run_folder"], "repair", state)

    print("Repair attempt complete. State updated and saved.")

    return state