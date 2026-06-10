from tools.code_runner import compile_cpp, run_cpp, compare_output
from utils.run_logger import save_step


def test_node(state):
    if not state.get("code"):
        raise ValueError("code missing from state")

    compile_result = compile_cpp(state["code"])

    state["compiled"] = compile_result.get("success")
    state["compile_output"] = compile_result.get("stderr", "")
    state["compiler_stdout"] = compile_result.get("stdout","")

    if not compile_result["success"]:
        print("Compilation failed during testing.")
        state["solved"] = False
        save_step(state["run_folder"], "test", state)

        return state

    all_passed = True
    test_results = []

    sample_inputs = state.get("sample_inputs", [])

    expected_outputs = state.get("expected_outputs", [])

    for idx, (sample_input, expected_output) in enumerate(zip(sample_inputs, expected_outputs)):
        run_result = run_cpp(sample_input)

        if not run_result["success"]:
            all_passed = False
            state["run_stdout"] = run_result["stdout"]
            state["run_stderr"] = run_result["stderr"]
            state["failed_test"] = {
                "test_case": idx + 1,
                "input": sample_input,
                "expected": expected_output,
                "actual": run_result["stdout"],
                "error": run_result["stderr"]
            }
            break

        passed = compare_output(run_result["stdout"],expected_output)

        test_results.append({
            "test_case": idx + 1,
            "passed": passed,
            "input": sample_input,
            "expected": expected_output,
            "actual": run_result["stdout"]
        })

        if not passed:
            all_passed = False
            state["failed_test"] = {
                "test_case": idx + 1,
                "input": sample_input,
                "expected": expected_output,
                "actual": run_result["stdout"]
            }
            break

    state["test_results"] = test_results
    state["solved"] = all_passed

    save_step(state["run_folder"], "test", state)

    print(f"Testing complete. Solved: {state['solved']}")
    return state