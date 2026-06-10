from typing import TypedDict

class CPState(TypedDict):
    problem_name: str
    url: str
    rating: int
    run_folder: str

    problem: str

    analysis: str
    plan: str
    code: str

    sample_inputs: list[str]
    expected_outputs: list[str]

    compiled: bool
    compile_output: str
    compiler_stdout: str

    execution_success: bool
    run_stdout: str
    run_stderr: str

    reflection: str
    attempts: int

    solved: bool