import csv
import requests
from bs4 import BeautifulSoup


def extract_problem_data(url):
    response = requests.get(url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")

    statement = soup.find("div", class_="problem-statement")

    if statement is None:
        raise Exception("Could not find problem statement.")

    problem_text = statement.get_text("\n", strip=True)

    sample_inputs = []

    for block in soup.find_all("div", class_="input"):

        pre = block.find("pre")

        if pre:
            sample_inputs.append(
                pre.get_text("\n", strip=True)
            )

    sample_outputs = []

    for block in soup.find_all("div", class_="output"):

        pre = block.find("pre")

        if pre:
            sample_outputs.append(
                pre.get_text("\n", strip=True)
            )

    return problem_text, sample_inputs, sample_outputs

def load_problem_by_index(csv_path, idx):

    rows = []

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            rows.append(row)

    row = rows[idx]

    problem_text, sample_inputs, sample_outputs = (
        extract_problem_data(row["Problems"])
    )

    url = row["Problems"]

    problem_name = (
        url.rstrip("/")
        .split("/")[-2]
        + url.rstrip("/").split("/")[-1]
    )

    return {
        "problem_name": problem_name,
        "url": url,
        "rating": int(row["ratings"]),
        "problem": problem_text,
        "sample_input": sample_inputs,
        "sample_output": sample_outputs
    }