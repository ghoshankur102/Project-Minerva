from llm_router import call_planner
from langchain_core.messages import HumanMessage
from utils.run_logger import save_step, verify_step, load_step


def planner_node(state):
    if verify_step(state["run_folder"], "plan"):
        state["plan"] = load_step(state["run_folder"], "plan")["plan"]
        print("Plan already exists. Skipping.")
        return state
    
    if not state.get("analysis"):
        raise ValueError("analysis missing from state")

    prompt = f"""
You are an expert competitive programmer.

Problem:
{state["problem"]}

Analysis:
{state["analysis"]}

Create a solution plan.

Return ONLY:

OBSERVATION:
...

ALGORITHM:
...

CORRECTNESS IDEA:
...

TIME COMPLEXITY:
...

SPACE COMPLEXITY:
...
"""

    result = call_planner([HumanMessage(content=prompt)])

    state["plan"] = result

    save_step(state["run_folder"], "plan", state)

    print("Planning complete. State updated and saved.")

    return state