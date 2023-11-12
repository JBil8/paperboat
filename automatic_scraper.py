import requests
from bs4 import BeautifulSoup
import spacy
import datetime
import openai

API_URL = "https://api-inference.huggingface.co/models/bigscience/bloom"
headers = {"Authorization": "Bearer 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"}

def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.json()

num = 1
openai.api_key = "OPENAI_KEY"
#################
today = datetime.date.today() - datetime.timedelta(days=int(num)) # for biorxiv, three days ago TO GET ABSTRACTS (also 0 for titles), as DOI updates on biorxiv with about 3 days of delay

# biorXiv
url = "https://www.biorxiv.org/search/jcode%3Abiorxiv%20limit_from%3A"+str(today)+"%20limit_to%3A"+str(today)+"%20numresults%3A1000%20sort%3Arelevance-rank%20format_result%3Astandard"

# Fetch HTML content
response = requests.get(url)
html_content = response.content

# Parse HTML using BeautifulSoup
soup = BeautifulSoup(html_content, "html.parser")

# Extract the text from HTML
text = soup.get_text()

# Apply NLP for DOM understanding
nlp = spacy.load("en_core_web_sm")
document = nlp(text)

# Extract titles using NER
output = query({"inputs": "Give me the authors from the following text:\n" + document.text[:500],})

print(output)
# response = openai.ChatCompletion.create(
#   model="davinci",
#   prompt="Extract the titles from the following text:\n" + document,
#   max_tokens=200
# )

# titles = response['choices'][0]['text'].split("\n")
# titles = [title for title in titles if title.strip()]
# print(titles)
# # Initialize lists to store titles and authors
# titles = []
# authors = []

# # Extract titles using NER
# for ent in document.ents:
#     if ent.label_ == "WORK_OF_ART":  # Check for titles (may need adjustment)
#         titles.append(ent.text)
#     elif ent.label_ == "PERSON":  # Check for authors
#         authors.append(ent.text)

# # Print or use the extracted titles and authors
# print("Titles:", titles)
# print("Authors:", authors)