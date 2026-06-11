from llm_router import call_generator
from langchain_core.messages import HumanMessage
from utils.run_logger import save_step, verify_step
from utils.extract_code import extract_cpp_code


def generator_node(state):
    if state.get("code"):
        print("Code already exists. Skipping.")
        return state

    if not state.get("plan"):
        raise ValueError("plan missing from state")
    
    prompt = f"""
You are an expert competitive programmer.

Problem:
{state["problem"]}

Solution Plan:
{state["plan"]}

Generate a complete C++17 solution.

Requirements:
- Return ONLY code
- No markdown
- No explanations
- Must compile under g++17
"""

    result = call_generator([HumanMessage(content=prompt)])

    state["code"] = extract_cpp_code(result)

    save_step(state["run_folder"], "generate", state)

    print("Code generation complete. State updated and saved.")

    return state