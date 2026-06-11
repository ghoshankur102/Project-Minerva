import os
import json

def get_run_folder(problem_name: str):
    safe_name = problem_name.lower().replace(" ", "_")

    path = os.path.join("runs", safe_name)
    os.makedirs(path, exist_ok=True)

    return path


def save_step(folder: str, step_name: str, state: dict):
    path = os.path.join(folder, f"{step_name}.json")

    with open(path, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)

def verify_step(folder: str, step_name: str):
    path = os.path.join(folder, f"{step_name}.json")
    return os.path.exists(path)

def load_step(folder: str, step_name: str):
    path = os.path.join(folder, f"{step_name}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)