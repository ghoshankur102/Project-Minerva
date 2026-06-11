import time
import json
import random
import requests
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Referer": "https://codeforces.com/problemset",
    "Accept-Language": "en-US,en;q=0.9",
}

def scrape_single_problem(url: str) -> dict:
    r = requests.get(url, headers=HEADERS, timeout=15)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")

    problem = soup.find("div", class_="problem-statement")
    if problem is None:
        problem = soup.select_one("div.ttypography div.problem-statement")
    if problem is None:
        raise ValueError(f"Problem statement not found for {url}")

    title_tag = problem.find("div", class_="title")
    title = title_tag.get_text(strip=True) if title_tag else "No Title"

    statement = problem.get_text("\n", strip=True)

    samples = []
    sample_box = problem.find("div", class_="sample-test")
    if sample_box:
        inputs = sample_box.find_all("div", class_="input")
        outputs = sample_box.find_all("div", class_="output")
        n = min(len(inputs), len(outputs))
        for i in range(n):
            in_pre = inputs[i].find("pre")
            out_pre = outputs[i].find("pre")
            sample_input = in_pre.get_text("\n", strip=True) + "\n" if in_pre else ""
            sample_output = out_pre.get_text("\n", strip=True) + "\n" if out_pre else ""
            samples.append({"input": sample_input, "expected_output": sample_output})

    return {
        "url": url,
        "title": title,
        "statement": statement,
        "samples": samples,
    }


def scrape_many(urls, out_path="cf_problems.json"):
    data = []
    for url in urls:
        try:
            print("Scraping:", url)
            prob = scrape_single_problem(url)
            data.append(prob)
        except Exception as e:
            print("Failed:", url, e)
        # slow down: 2–4 seconds random sleep
        time.sleep(random.uniform(2.0, 4.0))
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    urls = [
        "https://codeforces.com/problemset/problem/1511/C",
        "http://codeforces.com/problemset/problem/1610/B",
        "https://codeforces.com/problemset/problem/414/B",
        "https://codeforces.com/problemset/problem/1167/C",
        "https://codeforces.com/problemset/problem/1350/B",
        "https://codeforces.com/problemset/problem/845/C",
        "https://codeforces.com/problemset/problem/1101/C",
        "https://codeforces.com/problemset/problem/891/A",
        "https://codeforces.com/problemset/problem/1084/C",
        "https://codeforces.com/problemset/problem/1106/D",
        "https://codeforces.com/problemset/problem/1475/E",
        "https://codeforces.com/problemset/problem/1610/C",
        "https://codeforces.com/problemset/problem/1775/C",
        "https://codeforces.com/problemset/problem/1516/C",
        "https://codeforces.com/problemset/problem/1598/D",
        "https://codeforces.com/problemset/problem/1625/C",
        "https://codeforces.com/problemset/problem/1792/D",
        "https://codeforces.com/problemset/problem/1893/B",
        "https://codeforces.com/problemset/problem/1290/B",
        "https://codeforces.com/problemset/problem/1338/B",
        "https://codeforces.com/problemset/problem/1509/C",
        "https://codeforces.com/problemset/problem/2044/F",
        "https://codeforces.com/problemset/problem/2014/H",
        "https://codeforces.com/problemset/problem/1925/D"]
    scrape_many(urls)