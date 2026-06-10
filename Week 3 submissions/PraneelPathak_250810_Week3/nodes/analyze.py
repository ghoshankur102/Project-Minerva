from llm_router import call_analyzer
from langchain_core.messages import HumanMessage
from utils.run_logger import save_step, verify_step, load_step


def analyze_node(state):
    if verify_step(state["run_folder"], "analyze"):
        state["analysis"] = load_step(state["run_folder"], "analyze")["analysis"]
        print("Analysis already exists. Skipping.")
        return state

    prompt = f"""
You are an expert competitive programmer.

Analyze the following Codeforces problem.

Return ONLY:

CONSTRAINTS:
...

TOPICS:
...

EXPECTED COMPLEXITY:
...

EDGE CASES:
...

Problem:
{state["problem"]}
"""

    result = call_analyzer([HumanMessage(content=prompt)])

    state["analysis"] = result

    save_step(state["run_folder"], "analyze", state)
    
    print("Analysis complete. State updated and saved.")

    return state