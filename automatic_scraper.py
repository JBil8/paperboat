import requests
from bs4 import BeautifulSoup
import spacy
import datetime
#import openai

API_URL = "https://api-inference.huggingface.co/models/bigscience/bloom"
headers = {"Authorization": "Bearer" + BLOOM_KEY}

#bloom query function for LLM
def query(payload):
	response = requests.post(API_URL, headers=headers, json=payload)
	return response.json()

def get_text(url):
	response = requests.get(url)
	#fetch HTML content
	html_content = response.content
	#parse HTML using BeautifulSoup
	soup = BeautifulSoup(html_content, "html.parser")
	text = soup.get_text()
	text = text.replace("\n\n", " ")
	return text

def set_day(num=1):
	"""Set the numeber of days to scrape starting from today
	If no input is given, the default is 1 day ago"""
	days = datetime.date.today() - datetime.timedelta(days=int(num)) # for biorxiv, three days ago TO GET ABSTRACTS (also 0 for titles), as DOI updates on biorxiv with about 3 days of delay
	return days

def set_url(journal, num=1):
	"""Set journal to scrape"""
	day = set_day(num)
	if journal == "biorxiv":
		url = "https://www.biorxiv.org/search/jcode%3Abiorxiv%20limit_from%3A"+str(day)+"%20limit_to%3A"+str(day)+"%20numresults%3A1000%20sort%3Arelevance-rank%20format_result%3Astandard"
	else:
		raise ValueError("Journal" + str(journal) + " not found")
	return url

#openai.api_key = "OPENAI_KEY"
#################
# # biorXiv
# url = "https://www.biorxiv.org/search/jcode%3Abiorxiv%20limit_from%3A"+str(today)+"%20limit_to%3A"+str(today)+"%20numresults%3A1000%20sort%3Arelevance-rank%20format_result%3Astandard"

# # Fetch HTML content
# url = str("https://www.nature.com/search?order=relevance&journal="+"nature"+"&date_range=2023-2023&page=" + str(1))

# Apply NLP for DOM understanding
# nlp = spacy.load("en_core_web_sm")
# document = nlp(text)

# Extract titles using NER
#output = query({"inputs": "Give me the authors from the following text:\n" + text[:800],})
# output = query({
# 	"inputs": "What does this text look like?\n" + text[:2000],
# })
# print(output)
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