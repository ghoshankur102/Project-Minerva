import subprocess
import tempfile
import os


def compile_cpp(code):

    with open("cache/solution.cpp", "w", encoding="utf-8") as f:
        f.write(code)

    result = subprocess.run(
        [
            "g++",
            "cache/solution.cpp",
            "-std=c++17",
            "-O2",
            "-o",
            "cache/solution"
        ],
        capture_output=True,
        text=True
    )

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": result.stderr
    }

def run_cpp(input_data):

    result = subprocess.run(
        ["cache/solution.exe"],  # Windows: solution.exe
        input=input_data,
        capture_output=True,
        text=True
    )

    return {
        "success": result.returncode == 0,
        "stdout": result.stdout.strip(),
        "stderr": result.stderr.strip()
    }

def compare_output(actual, expected):

    actual = actual.strip()
    expected = expected.strip()

    return actual == expected