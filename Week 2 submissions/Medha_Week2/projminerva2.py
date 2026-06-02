import requests
from bs4 import BeautifulSoup
import nltk
# nltk.download('punkt')
# nltk.download('punkt_tab')
from nltk.tokenize import word_tokenize
from sentence_transformers import SentenceTransformer

import os
os.makedirs("corpus", exist_ok=True)


# RETRIEVING TEXT FROM ARTICLES

urls = ["https://www.bbc.com/future/article/20260515-the-1950s-blunder-which-causes-mass-hay-fever-in-japan",
        "https://www.bbc.com/news/articles/c5y8wjvd1ypo",
        "https://www.bbc.com/news/articles/cvgzyp93jq1o",
        "https://www.bbc.com/news/articles/cvgzy64j9l1o",
        "https://www.bbc.com/travel/article/20260527-estevanico-the-african-explorer-who-crossed-north-america"]

for i, url in enumerate(urls):
    response = requests.get(url)
    # print(response.text)

    soup = BeautifulSoup(response.text, 'html.parser')
    # print(soup.prettify()) 

    title = soup.find("h1").text

    paragraphs = soup.find_all("p")

    article_text = ""

    for p in paragraphs:
        article_text += p.text + "\n"

    with open(f"corpus/article_{i+1}.txt","w",encoding="utf-8") as f:
        f.write(title + "\n\n")
        f.write(article_text)

with open("full_corpus.txt", "w", encoding="utf-8") as out:

    for file in os.listdir("corpus"):
        with open(f"corpus/{file}","r",encoding="utf-8") as f:
            out.write(f.read())
            out.write("\n\n")

