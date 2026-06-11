import csv
import json
import os
from pathlib import Path
from time import sleep

from graphs.graph import build_graph
from utils.run_logger import get_run_folder
from load_problem import extract_problem_data


CSV_FILE = "problems.csv"
PROGRESS_FILE = "progress.json"

if os.path.exists(PROGRESS_FILE):
    with open(PROGRESS_FILE, "r", encoding="utf-8") as f:
        progress = json.load(f)

else:
    progress = {}

graph = build_graph()

output_dir = Path("outputs")
output_dir.mkdir(exist_ok=True)

with open(CSV_FILE, newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    rows = list(reader)


for idx, row in enumerate(rows):
    try:
        url = row["Problems"]

        problem_name = url.split("/")[-2] + "_" + url.split("/")[-1]
        if progress.get(problem_name, False):
            print(f"Skipping {problem_name} (already completed)")
            continue

        print(f"\n[{idx + 1}/{len(rows)}] {url}")

        problem_text, sample_inputs, sample_outputs = (extract_problem_data(url))

        parts = url.rstrip("/").split("/")

        problem_name = (parts[-2] + "_" + parts[-1])

        initial_state = {
            "problem_name": problem_name,
            "problem": problem_text,

            "sample_inputs": sample_inputs,
            "expected_outputs": sample_outputs,

            "attempts": 0,
            "solved": None
        }

        initial_state["run_folder"] = get_run_folder(problem_name)
        
        print(f"Running graph for {problem_name}...")
        result = graph.invoke(initial_state)

        with open(os.path.join(initial_state["run_folder"], "final_state.json" ), "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)

        cpp_file = (output_dir / f"{problem_name}.cpp")

        with open(cpp_file, "w", encoding="utf-8") as f:
            f.write(result.get("code",""))

        print(f"Saved -> {cpp_file}")
        
        progress[problem_name] = result.get("solved")

        with open(PROGRESS_FILE, "w", encoding="utf-8") as f:
            json.dump(progress, f, indent=2)

    except Exception as e:
        print(f"FAILED: {url}")
        print(e)

    sleep(1)