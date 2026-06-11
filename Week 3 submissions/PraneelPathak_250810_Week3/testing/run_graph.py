# This was used for testing the graph.
import os
from pathlib import Path
from graphs.graph import build_graph
import json
from utils.run_logger import get_run_folder

graph = build_graph()

initial_state = {
    "problem_name": "414B",
    "problem": open(
        "test_problem.txt",
        encoding="utf-8"
    ).read(),

    "sample_inputs": """
3 2
""".strip(),

    "expected_outputs": """
5
""".strip(),

    "attempts": 0,
    "solved": False
}
initial_state["run_folder"] = get_run_folder(initial_state["problem_name"])

result = graph.invoke(initial_state)

with open(os.path.join(initial_state["run_folder"], "final_state.json"), "w", encoding="utf-8") as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(result["solved"])
print("DONE!!!!!")

output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)

cpp_file = output_dir / f"{result['problem_name']}.cpp"

with open(cpp_file, "w", encoding="utf-8") as f:
    f.write(result["code"])

print(f"Saved code to {cpp_file}")