import pandas as pd
import requests
import os
import re
import random
import json
import datetime
from bs4 import BeautifulSoup
import numpy as np
import scipy
import matplotlib.pyplot as plt
import openai
import pandas as pd
import time
import datetime
import math
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

#importing links to all journals
links = pd.read_csv("paperboat_linksBIOLOGY.csv")

today = str(datetime.date.today())

# OpenAI API key
openai.api_key = "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"
client = openai.OpenAI(api_key="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" ) # Initialize the OpenAI client
# pass key to client


# chat_completion = client.chat.completions.create(
#     messages=[
#         {
#             "role": "user",
#             "content": "Say this is a test",
#         }
#     ],
#     model="gpt-3.5-turbo",
# )
# #extrect content from chat_completion



def safe_api_call(call_function, *args, **kwargs):
    while True:
        try:
            return call_function(*args, **kwargs)
        except openai.error.RateLimitError as e:

            match = re.search(r'Please try again in (\d+(\.\d+)?)s.', str(e))
            if match:
                wait_time = float(match.group(1)) + 1  
                print(f"Rate limit reached, waiting for {wait_time} seconds.")
                time.sleep(wait_time)
            else:
                raise

# Initializing the dataframe to store all data
combined_df = pd.DataFrame(columns=["Title", "Date", "Journal", "Field"])

from datetime import datetime

for i in range(0, links.shape[0]):

    print(np.array(links['Journal'])[i])
    
    url = np.array(links['Link'])[i]
    journal = np.array(links['Journal'])[i]
    field = np.array(links['Topic/Field'])[i]
    
    response = requests.get(url).text 
    soup = BeautifulSoup(response, 'html.parser')
    titles = str(soup.get_text().replace("\n\n", " ")) ##### for the limit on gpt4

    if titles == 'Just a moment...Enable JavaScript and cookies to continue\n':
        print("in")
        options = Options()
        options.headless = True 
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        driver.get(url)
        time.sleep(5)
        page_content = driver.page_source
        driver.quit()
        soup = BeautifulSoup(page_content, 'html.parser')
        titles = str(soup.get_text().replace("\n\n", " "))


    max_context_length = 4096  # Adjust this based on the maximum context allowed by the GPT API

    for k in range(math.ceil(len(titles) / max_context_length)):
        extracted_titles = []
        
        start_idx = k * max_context_length
        end_idx = min((k + 1) * max_context_length, len(titles))
        
        current_titles = titles[start_idx:end_idx]


        response = safe_api_call(
            client.chat.completions.create,
            model="gpt-3.5-turbo-0125", ###############
            messages=[{
                "role": "user", 
                "content": ("Extract paper TITLES from this text. "
                            "For example, for  'November 2, 2023 |"
    "https://doi.org/10.1371/journal.pgen.1011021    Central metabolism is a key player in E. coli biofilm stimulation by sub-MIC antibiotics   "          
    "              Luke N. Yaeger,              Shawn French,              Eric D. Brown,              Jean Philippe Côté,              Lori L. Burrows        "
    "PLOS Genetics: published' you will return """"Central metabolism is a key player in E. coli biofilm stimulation by sub-MIC antibiotics"""""
                            "Return one title per line. If there are no paper titles, "
                            "return '\nNO TITLE'. We are dealing with scientific "
                            "paper titles, so return only what's reasonable (e.g., something like "
                            "'Clinical Trials', 'Developmental Biology', 'Ecology' is likely NOT a title "
                            "of a paper, it's too generic). Just return the PLAUSIBLE titles. do NOT format "
                            "with dashes or numbers, just plain titles. remember, it's IMPERATIVE "
                            "that you change line between subsequent titles!\n\n\n" + current_titles)
            }]
        )

        extracted_titles.extend(response.choices[0].message.content.split('\n'))

        df = pd.DataFrame(extracted_titles, columns=["Title"])
        df['Date'] = datetime.today().strftime('%Y-%m-%d')
        df['Journal'] = journal
        df['Field'] = field
        combined_df = pd.concat([combined_df, df], ignore_index=True)
        
        print(combined_df)