# Test for analyzer node
# from nodes.analyze import analyze_node

# state = {
#     "problem": open("test_problem.txt", encoding="utf-8").read()
# }

# result = analyze_node(state)

# print(result)

# Test for planner node
# from nodes.analyze import analyze_node
# from nodes.planner import planner_node
# from llm import llm

# state = {
#     "problem": open("test_problem.txt", encoding="utf-8").read()
# }

# state.update(
#     analyze_node(state, llm)
# )
# print("Analysis done. Now planning...")
# state.update(
#     planner_node(state, llm)
# )

# print(state["plan"])

# Test for generator node
# from utils import load_state, save_state
# from nodes.analyze import analyze_node
# from nodes.planner import planner_node
# from nodes.generator import generator_node
# from llm import llm

# state = {
#     "problem": open("test_problem.txt", encoding="utf-8").read()
# }

# state.update(
#     analyze_node(state, llm)
# )
# save_state(state, "state_after_analysis.json")
# print("Analysis done. Now planning...")

# state.update(
#     planner_node(state, llm)
# )
# save_state(state, "state_after_planning.json")
# print("Planning done. Now generating code...")

# state.update(
#     generator_node(state, llm)
# )
# save_state(state, "state_after_generation.json")

# print(state["code"])

# Test for tools/code_runner.py
# from tools.code_runner import compile_cpp, run_cpp, compare_output
# from utils import load_state, save_state

# state = load_state("state_after_generation.json")

# result = compile_cpp(state["code"])

# # Compilation information
# state["compiled"] = result["success"]
# state["compile_output"] = result["stderr"]
# state["compiler_stdout"] = result["stdout"]

# # Sample test information
# sample_input = """
# 7 5
# 2 1 1 4 3 3 1
# 3 2 1 1 4
# """

# expected_output = "5 2 3 1 5"

# state["sample_input"] = sample_input.strip()
# state["expected_output"] = expected_output

# if result["success"]:

#     print("Compilation successful. Running the code...")

#     run_result = run_cpp(sample_input)

#     state["run_stdout"] = run_result["stdout"]
#     state["run_stderr"] = run_result["stderr"]
#     state["execution_success"] = run_result["success"]

#     if run_result["success"]:

#         print("Execution successful.")

#         passed = compare_output(
#             run_result["stdout"],
#             expected_output
#         )

#         state["solved"] = passed

#         print(f"Passed: {passed}")

#     else:

#         state["solved"] = False

# else:

#     print("Compilation failed.")

#     state["solved"] = False

#     # Keep fields present even if compilation fails
#     state["execution_success"] = False
#     state["run_stdout"] = ""
#     state["run_stderr"] = ""

# # Useful metadata for future repair loops
# state["attempts"] = state.get("attempts", 0)

# save_state(
#     state,
#     "state_after_code_runner.json"
# )

# Test for nodes/critic.py- first change code manually, then test(else it will just return that the solution is correct)
# from tools.code_runner import compile_cpp, run_cpp, compare_output
# from utils import load_state, save_state

# state = load_state("state_after_generation.json")

# result = compile_cpp(state["code"])

# # Compilation information
# state["compiled"] = result["success"]
# state["compile_output"] = result["stderr"]
# state["compiler_stdout"] = result["stdout"]

# # Sample test information
# sample_input = """
# 7 5
# 2 1 1 4 3 3 1
# 3 2 1 1 4
# """

# expected_output = "5 2 3 1 5"

# state["sample_input"] = sample_input.strip()
# state["expected_output"] = expected_output

# if result["success"]:

#     print("Compilation successful. Running the code...")

#     run_result = run_cpp(sample_input)

#     state["run_stdout"] = run_result["stdout"]
#     state["run_stderr"] = run_result["stderr"]
#     state["execution_success"] = run_result["success"]

#     if run_result["success"]:

#         print("Execution successful.")

#         passed = compare_output(
#             run_result["stdout"],
#             expected_output
#         )

#         state["solved"] = passed

#         print(f"Passed: {passed}")

#     else:

#         state["solved"] = False

# else:

#     print("Compilation failed.")

#     state["solved"] = False

#     # Keep fields present even if compilation fails
#     state["execution_success"] = False
#     state["run_stdout"] = ""
#     state["run_stderr"] = ""

# # Useful metadata for future repair loops
# state["attempts"] = state.get("attempts", 0)

# save_state(
#     state,
#     "state_after_code_runner.json"
# )

# from nodes.critic import critic_node
# from llm import llm
# from utils import load_state, save_state

# state = load_state("state_after_code_runner.json")

# result = critic_node(state, llm)

# state.update(result)

# save_state(
#     state,
#     "state_after_critic.json"
# )

# print("\n=== REFLECTION ===\n")
# print(state["reflection"])

# Test for nodes/repair.py
# from nodes.repair import repair_node
# from llm import llm
# from utils import load_state, save_state

# state = load_state("state_after_critic.json")

# result = repair_node(state, llm)

# state.update(result)

# save_state(
#     state,
#     "state_after_repair.json"
# )

# print("\n=== REPAIRED CODE ===\n")
# print(state["code"])