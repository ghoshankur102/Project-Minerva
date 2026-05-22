import requests
from bs4 import BeautifulSoup as bs
from sentence_transformers import SentenceTransformer

import spacy

URL = "https://www.bbc.com/news/articles/c232z4yk437o"
response = requests.get(URL)
#print(response.text)

soup = bs(response.text,"html.parser")
results = soup.find_all("p")
cleanTxt=''
for result in results:
    cleanTxt+=result.text.strip()


nlp = spacy.load("en_core_web_sm")
doc = nlp(cleanTxt)
sentences = [str(sentence) for sentence in doc.sents]

model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
embeddings = model.encode(sentences)
print(embeddings)

