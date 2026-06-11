import requests
from bs4 import BeautifulSoup
import os
import subprocess

# extracting the problem description and standard sample test cases
# def extract_problem (url: str):
#     # header = {"User-Agent" : "Mozilla/5.0"}
#     header = {
#         "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
#         "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
#         "Accept-Language": "en-US,en;q=0.9",
#         "Accept-Encoding": "gzip, deflate, br",
#         "Connection": "keep-alive",
#         "Upgrade-Insecure-Requests": "1"
#     }
#     res = requests.get (url, headers=header)

#     if res.status_code != 200:
#         raise Exception(f"failed to fetch page {res.status_code}")

#     soup = BeautifulSoup(res.text, "html.parser")

#     # extracting the body text of the ps
#     ps = soup.find("div", class_ = "problem-statement").get_text(separator="\n")

#     # grabbing all the input and output boxes on the page
#     inputs = [x.find("pre").get_text(separator="\n").strip() for x in soup.find_all("div", class_="input")]
#     outputs = [x.find("pre").get_text(separator="\n").strip() for x in soup.find_all("div", class_="output")]

#     # pairing them up nicely
#     sample_cases = list(zip(inputs, outputs))

#     return ps, sample_cases


import cloudscraper
from bs4 import BeautifulSoup

def extract_problem(url: str):
    # fetch page data directly without browser windows
    html = cloudscraper.create_scraper().get(url).text
    soup = BeautifulSoup(html, "html.parser")

    # extracting the body text of the ps
    ps = soup.find("div", class_="problem-statement").get_text(separator="\n")

    # grabbing all the input and output boxes on the page
    inputs = [div.find("pre").get_text(separator="\n").strip() for div in soup.find_all("div", class_="input") if div.find("pre")]
    outputs = [div.find("pre").get_text(separator="\n").strip() for div in soup.find_all("div", class_="output") if div.find("pre")]

    # pairing them up nicely
    sample_cases = list(zip(inputs, outputs))

    return ps, sample_cases




def run_local_tests(code: str, sample_test_cases: list):

    source_file = "temp_solution.cpp"
    # checks which os is being used to decide terminal run commands
    binary_file = "temp_solution.exe" if os.name == "nt" else "./temp_solution"

    # writing the generated code in a local file
    with open(source_file, "w", encoding="utf-8") as f:
        f.write(code)

    # compile the code
    compile_process = subprocess.run(    # subprocess is a python module that pauses the script and runs a native os command in the terminal
        ["g++", "-O3", source_file, "-o", binary_file.replace("./", "")],
        capture_output = True,
        text = True
    )

    # capture the compilation error
    if compile_process.returncode != 0: # a terminal command returns a status code of 0 if it runs successfully
        return {
            "success" : False,
            "error_log" : compile_process.stderr # stderr is the error stream
        }


    # iterating to check each sample test case
    for idx, (sample_input, expected_output) in enumerate(sample_test_cases):
        try:
            run_process = subprocess.run(
                [binary_file],
                input = sample_input,
                capture_output = True,
                text = True,
                timeout = 2.0
            )

            if run_process.returncode != 0:
                return {
                    "success" : False,
                    "error_log" : f"sample {idx+1}\n {run_process.stderr}"
                }

            actual_output = run_process.stdout.strip()
            expected_output = expected_output.strip()

            if actual_output != expected_output:
                error_msg = (
                    f"Wrong answer on sample {idx+1}!\n"
                    f"Input provided:\n{sample_input}\n"
                    f"Expected Output:\n{expected_output}\n"
                    f"Your Agent's Output:\n{actual_output}"
                )

                return {
                    "success" : False,
                    "error_log" : error_msg
                }

        except subprocess.TimeoutExpired:
            return {
                "success" : False,
                "error_log" : f"limit exceeded on sample {idx+1}"
            }

    if os.path.exists(source_file): os.remove(source_file)
    if os.path.exists(binary_file): os.remove(binary_file)

    return {
        "success" : True,
        "error_log" : ""
    }

